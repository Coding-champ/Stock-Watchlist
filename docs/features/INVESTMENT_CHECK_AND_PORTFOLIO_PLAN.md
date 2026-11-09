# Plan: Portfolio (v1) und Investitions-Check

Stand: 2026-11-07  
Status: **Implementierung läuft** (Schritt 1 erledigt)  
Reihenfolge: **zuerst Portfolio, danach Investitions-Check** (der Check startet ohne Bestand nicht).

Dieses Dokument hält die im Planungsgespräch getroffenen Entscheidungen fest. UI-Referenz für den Check: mehrstufiger Stepper (Screenshot „Investitions-Check“), Texte und Farben an diese App anpassen — **nicht** das Mint/Bankgrün der Vorlage kopieren.

---

## 1. Ausgangslage im Projekt

Die App ist eine Watchlist-App (Beobachtungslisten), kein Depot.

- Navigation und Views sitzen in `frontend/src/App.js` (`activeView`: Übersicht, Watchlist, Screener, Earnings, Alerts, Indizes, Stock-Detail).
- `watchlists` / `stocks_in_watchlist` haben **keine** Stückzahl, keinen Einstand, kein Cash.
- In `docs/FUTURE_FEATURES.md` ist **Portfolio Management (Phase 8) explizit offen**. Dieses v1-Portfolio ist bewusst schlanker als Phase 8 (keine Transaktionshistorie, kein FIFO, kein Cash, keine mehreren Depots in der UI).
- Wiederverwendbare Bausteine für den Check existieren bereits: Charts/Indikatoren, Fundamentals, Calculated Metrics, Sektor-Peers, Benchmark-Vergleich, Saisonalität, Korrelationsmatrix, Index-Kurse über `asset_price_data`.
- **Kein** Candlestick-Pattern-Modul, **kein** FX, **kein** Holdings-Modell.

Der Investitions-Check ist ein **eigener Wizard**, kein weiterer Tab auf der Aktienstrecke. Portfolio und Check sind **eigene Topnav-Views**.

---

## 2. Portfolio v1

### 2.1 Produkt

- **Genau ein** implizites Portfolio („Mein Portfolio“). Keine Namenswahl in der UI.
- Trotzdem Tabelle `portfolios` mit einer Default-Zeile anlegen, damit später mehrere Depots ohne Umbau möglich sind. Die UI blendet die Auswahl nicht ein.
- Nur **Bestand**: anlegen, Nachkauf, Position komplett löschen. **Kein** Teilverkauf, **kein** FIFO, **keine** Transaktionsliste.

### 2.2 Einbauort

**Frontend**

- Neuer `activeView === 'portfolio'` und Topnav-Punkt in `frontend/src/App.js`.
- View: `frontend/src/components/portfolio/PortfolioView.js` (Tabelle + Formular).
- Darstellung analog `StockTable.js`; Suche Ticker/ISIN analog `StockModal.js` / `StockSearchBar.js`.

**Backend**

- `backend/app/routes/portfolio.py`, Router in `backend/app/main.py` registrieren.
- `backend/app/services/portfolio_service.py`
- Modelle in `backend/app/models/__init__.py`, Schemas in `backend/app/schemas.py`

Holdings **müssen nicht** in einer Watchlist stehen. Fehlt die Aktie in `stocks`, Stammdaten wie bisher über Identifier-Auflösung anlegen (`get_stock_info_by_identifier` / ISIN→Ticker).

### 2.3 Datenmodell

**Feature Implementiert** (Modelle `Portfolio` / `Holding`, Migration `20261107_add_portfolios_and_holdings.py`, Default-Zeile „Mein Portfolio“ via Migration und `ensure_default_portfolio` beim App-Start.)

**Persistiert (Holding, eine Zeile pro Aktie / Ticker / ISIN)**

| Feld | Bedeutung |
|------|-----------|
| `stock_id` | FK auf `stocks` → **Name**, **ISIN** |
| `quantity` | Stückzahl (Summe der Käufe) |
| `purchase_price` | Einstandskurs, **stückgewichtet** |
| `purchase_date` | **Datum des ersten Kaufs**, danach unverändert |

**Berechnet, nicht speichern**

| Feld | Bedeutung |
|------|-----------|
| Aktueller Kurs | aus `stock_price_data` (gleiche Logik wie Watchlist) |
| Aktueller Wert | Stück × aktueller Kurs |
| GuV absolut | (aktueller Kurs − Einstandskurs) × Stück |
| GuV % | GuV absolut / (Einstandskurs × Stück) |

Gewinn/Verlust ist **reine Anzeige**.

### 2.4 Bestandsregeln (im Code kommentieren)

Diese Regeln gehören als Kommentare an **Modell, Mittelungsfunktion, Nachkauf-API und Formular**, damit später niemand FIFO, ungewichtete Kurse oder Edit der Mittelwerte einbaut.

1. **Eine Zeile pro Aktie.**
2. **Nachkauf** (Aktie schon im Portfolio): nur Stück + Kurs entgegennehmen. Stück addieren. Einstandskurs neu als **stückgewichtetes** Mittel:
   \[
   \bar{p} = \frac{\sum_i n_i p_i}{\sum_i n_i}
   \]
   Nicht: ungewichtetes Mittel der Kaufkurse, nicht letzter Kurs, nicht FIFO.
3. **Einstandsdatum** bleibt das Datum des **ersten** Kaufs. Nachkauf-Datum wird ignoriert.
4. **Kein direktes Überschreiben** von Stück, Einstandskurs oder Datum in der UI.
5. **Korrektur:** Position löschen und neu anlegen.
6. **Neue Aktie:** Ticker/ISIN + Stück + Kurs + Datum → neue Zeile.

Beispiel Nachkauf: 10 Stück zu 50, danach 90 Stück zu 100 → Einstand \( (10 \times 50 + 90 \times 100) / 100 = 95 \), Datum = Datum des 10-Stück-Kaufs.

### 2.5 Währung

- **Kein FX in v1.** Es gibt im Projekt keine Umrechnung (`currencyUtils.js` formatiert nur).
- Jede Zeile in der **Börsenwährung der Rohdaten**.
- Portfolio-Gesamtsumme = **naive Addition** aller Zeilenwerte (ggf. gemischte Währungen).
- **Kleiner Hinweis in der UI**, dass diese Summe bei mehreren Währungen **inkorrekt / nicht vergleichbar** ist.
- Dasselbe im Code kommentieren (Service, API-Summenfeld, UI).

### 2.6 Bewusst nicht in v1

Aus Phase 8 / `FUTURE_FEATURES.md` **nicht** mitbauen: mehrere sichtbare Portfolios, Buy/Sell-Ledger, Dividenden, Cash, FIFO/LIFO, historische FX am Kaufdatum, PDF-Export.

---

## 3. Investitions-Check

Regelbasierter Prozess: Symbol/ISIN + Stückzahl, plus **hypothetische** Wirkung auf das Portfolio. Schreibt **nichts** ins Portfolio. Läufe nur in der **Session**, kein Verlauf, keine History-Tabelle.

### 3.1 Einbauort

**Frontend**

- `activeView === 'investment-check'` + Topnav **Investitions-Check**.
- `frontend/src/components/investment-check/InvestmentCheckView.js` (Wizard-Hülle).
- Ein Component je Schritt.
- `frontend/src/hooks/useInvestmentCheck.js` (Eingabe, Schrittstatus, API).

**Zusätzliche Einstiege (Abkürzung)**

- Button auf **Portfolio-Zeile** und **Aktienstrecke** / `StockDetailPage`.
- Symbol vorausgefüllt, Stückzahl leer.
- Stepper startet trotzdem bei Schritt 1 (Eingabe).

**Startbedingung:** mindestens **eine** Portfolio-Position. Sonst kein Stepper, nur Hinweis „Zuerst Bestand anlegen“ (Nav und Buttons).

**Backend**

- `backend/app/routes/investment_check.py` + Registrierung in `main.py`.
- `backend/app/services/investment_check_service.py` (Orchestrator, keine Doppelberechnung).
- `backend/app/services/investment_check_rules.py` (Schwellen, Pass/Fail, Begründung).

Ein Endpoint in der Art: Check für Identifier + Stück gegen das Default-Portfolio. Antwort: Daten + Kriterien + Status je Schritt.

Bestehende Services nur **zusammenziehen**: u. a. `chart_core` / `technical_indicators_service`, `fundamental_data_service`, `calculated_metrics_service`, `comparison_service`, `seasonality_service`, Korrelation / `CorrelationHeatmap`-Defaults, Portfolio-Holdings.

Unbekannte Ticker/ISIN: wie `StockModal` auflösen, Stammdaten und Kurse **bei Bedarf anlegen**, damit `stock_id`-Endpoints greifen. **Portfolio unverändert.**

### 3.2 UI / Stepper

Variante **C**, alles **im selben Stepper** (9 Stationen):

1. Eingabe  
2. Chart / Muster  
3. Finanzkennzahlen  
4. Aktienkennzahlen  
5. Peer / Markt  
6. Saisonalität  
7. Abhängige Kapitalmarkt-Assets  
8. Risiko-Allocation  
9. Ergebnis  

**Abgekürzte Darstellung:** nur **vorheriger, aktueller und nächster** Schritt groß (Kreis + Label). Alle anderen nur als Punkte. Zurück = voriger Schritt. Fortschritt analog `n/m` im Screenshot, Texte an die App angepasst.

**Farben aus vorhandenen Tokens**, nicht aus der Screenshot-Vorlage:

- Chrome / aktiver Schritt: `--brand-primary`, `--brand-surface-muted` (`frontend/src/styles/variables.css`)
- Erfüllt: Grün wie `.toast--success` / `.performance-metric--positive` (`#166534` / `#15803d`)
- Nicht erfüllt: Rot wie `.toast--error` / `.performance-metric--negative`
- Neutral / ausstehend / nicht bewertet: `--text-muted`

Keine neuen Farbtokens, außer sie fehlen wirklich.

### 3.3 Regel-Engine (alle Check-Schritte)

- Zentral in `investment_check_rules.py`.
- Schwellenwerte trägt der Nutzer **später** ein → offene `TODO`-Platzhalter (`null`).
- Solange eine Schwelle `null` ist: Daten und Kriterien **anzeigen**, Status **„nicht bewertet“** (weder erfüllt noch durchgefallen).
- Dasselbe Verhalten für Chart, Finanzen, Aktienkennzahlen, Peer/Markt, Saisonalität, Korrelation.
- **Ergebnis (Schritt 9):** nur Statusliste der Stationen. **Keine Gesamtampel**, solange mindestens eine vorgesehene Schwelle noch `null` ist. Im Code kommentieren, damit niemand still eine Ampel einbaut.
- Eingabe zählt als erledigt, sobald gültiges Symbol + Stückzahl vorliegen.

### 3.4 Schritte im Detail

**1 — Eingabe**  
Aktiensymbol oder ISIN + Anzahl zu kaufender Aktien. Auflösung/Anlage von Stammdaten wie oben.

**2 — Chart / Muster**  
Nur vorhandene Technik (SMA, RSI, MACD, Bollinger, … über `StockChart.js` / `technical_indicators_service.py`). **Kein** Pattern-Recognition in v1 (`FUTURE_FEATURES.md`: Candlestick Recognition fehlt). Schwellen TODO.

**3 — Finanzkennzahlen**  
Unternehmenszahlen: Umsatz, Gewinn, Margen, ROE, Verschuldung, … (`fundamental_data_service`). Schwellen TODO.

**4 — Aktienkennzahlen**  
Bewertung/Markt: KGV, Marktkapitalisierung, 52-Wochen, Beta, Volumen, Scores (`calculated_metrics_service`). Schwellen TODO.

**5 — Peer / Markt**  
**Beides** auf einer Karte: Benchmark-Index (wie Detailseite / `useBenchmarkComparison` / `comparison_service`) **und** Sektor-/Branche-Peers (`SectorComparisonTab`). Schwellen (z. B. Outperformance, Rang vs. Peers) TODO.

**6 — Saisonalität**  
Volle Monatsübersicht als Kontext (`seasonality_service`, `SeasonalityTab.js`). Die **Regel** bezieht sich nur auf den **aktuellen Kalendermonat** vs. historisches Mittel. Schwelle TODO.

**7 — Abhängige Kapitalmarkt-Assets**  
Korrelation **nur gegen Indizes in v1**, Defaults der Heatmap:

`^GSPC`, `^IXIC`, `^GDAXI`, `^FTSE`, `^N225`

Nicht gegen Portfolio-Titel. Die Implementierung darf **nicht** hart an „Index“ koppeln, sondern an eine **konfigurierbare Referenzliste** (`symbol` + `asset_type`). Später Rohstoffe und Anleihen in dieselbe Liste (`AssetType` kennt bereits `index`, `etf`, `bond`, `crypto`; **kein** `commodity` — bei Rohstoffen Enum/Preise nachziehen). Schwelle (z. B. max. Korrelation) TODO.

**8 — Risiko-Allocation**  
Geplanten Kauf **hypothetisch** zum Portfolio addieren (Stück aus dem Formular, Kurs = aktueller Marktpreis), **nicht persistieren**. Gewichte **vorher vs. nachher** als Tabelle.  
Sitzt die Aktie schon im Depot: im Speicher dieselbe **Nachkauf-Regel** (stückgewichtet, Erstkaufdatum unverändert).  
Währung wie Portfolio: Börsenwährung, naive Summe + Disclaimer.  
In v1 **keine** Pass/Fail-Kriterien (kein max. Einzelgewicht etc.). Status **„nicht bewertet“**, bis Schwellen und Kriteriumsnamen nachgezogen werden.

**9 — Ergebnis**  
Liste der Schritt-Status. Keine Gesamtampel, solange Pflicht-Schwellen fehlen.

### 3.5 Session

Kein Speichern von Check-Läufen. Verlassen der View / Neu starten = neu rechnen.

---

## 4. Offene TODOs für den Nutzer (keine Dev-Blocker für das Gerüst)

In `investment_check_rules.py` (und analog UI-Kriterien) Platzhalter lassen:

- [ ] Chart/Indikator-Schwellen (SMA, RSI, MACD, Bollinger, …)
- [ ] Fundamental-Schwellen
- [ ] Aktienkennzahlen-Schwellen
- [ ] Peer-/Benchmark-Schwellen
- [ ] Saisonalität: Schwelle für den aktuellen Monat
- [ ] Max. Korrelation (und später weitere Referenz-Assets: Rohstoffe, Anleihen)
- [ ] Risiko-Allocation: Kriteriumsnamen + Schwellen (Einzelgewicht, Sektor, …)

Solange `null`: Status „nicht bewertet“.

---

## 5. Implementierungsreihenfolge

1. Modelle `portfolios` + `holdings`, Migration, Default-Portfolio. **Feature Implementiert**
2. `portfolio_service` + API (CRUD Bestand, Nachkauf-Mittelung, berechnete Felder, naive Summe + Flag/Hinweis). **Feature Implementiert**
3. `PortfolioView` + Topnav. **Feature Implementiert**
4. Investment-Check: Rule-Datei mit `null`-Schwellen, Orchestrator-Endpoint. **Feature Implementiert**
5. Wizard-UI (9 Schritte, abgekürzter Stepper, Farbtokens). **Feature Implementiert**
6. Einstiege (Nav, Portfolio-Button, Stock-Button) + Gate „mindestens eine Holding“. **Feature Implementiert**
7. Nutzer füllt Schwellen (dann erst echte Pass/Fail- und später Gesamtampel-Diskussion).

---

## 6. Entscheidungsprotokoll (kurz)

| Thema | Entscheidung |
|-------|----------------|
| Portfolio-Anzahl | Eins, Default-Zeile in DB |
| Zeilen | Eine pro Aktie |
| Mittel | Stückgewichtet |
| Datum | Erster Kauf |
| Nachkauf vs. Edit | Nur Nachkauf; Korrektur = löschen + neu |
| Verkäufe | Keine (nur Bestand / volle Löschung) |
| GuV | Nur Anzeige |
| Währung | Rohdaten-Börsenwährung; naive Summe + Disclaimer |
| Check-Simulation | Hypothetisch addieren, nicht schreiben |
| Stepper | 9 Stationen inkl. Eingabe und Ergebnis |
| Stepper-UI | Nur Prev / Current / Next groß |
| Farben | Projekt-Tokens |
| Unbekannte Titel | Stammdaten anlegen, Portfolio unangetastet |
| Leeres Portfolio | Check startet nicht |
| Verlauf | Keine Persistence |
| Chart-Muster | Nur vorhandene Indikatoren |
| Finanzen vs. Aktien | Unternehmen vs. Bewertung/Markt |
| Peer/Markt | Index + Peers |
| Saisonalität | Übersicht voll, Regel = aktueller Monat |
| Abhängige Assets | Nur Indizes (Heatmap-Defaults), Liste erweiterbar |
| Allocation-Regel | v1 nur Vorher/Nachher, kein Pass/Fail |
| Schwellen | Nutzer-TODO, sonst „nicht bewertet“ |
| Gesamtampel | Keine, solange Schwellen fehlen |

---

## 7. Umsetzungsdetails

Die Schwellenwerte werden in v1 ausschließlich zentral in
`backend/app/services/investment_check_rules.py` gepflegt (`STEP_RULES`).
Eine Datenbank, Umgebungsvariable oder separate UI-Konfiguration wird bewusst
nicht verwendet, solange Kriterien und Grenzwerte noch iteriert werden. Die
Auswertung erhält eine Kopie der Regeln, damit Laufzeitcode die zentrale
Konfiguration nicht verändern kann.

Für die Datenaktualität gelten Kursdaten bis zu drei Kalendertage als aktuell.
Der Endpoint liefert `data_quality.price` mit Alter und Status (`current`,
`stale` oder `missing`). Veraltete oder fehlende Daten werden nicht
stillschweigend als bestanden bewertet; ein automatischer Refresh ist in v1
nicht Teil des Checks.

Die Stationen werden mit einem 60-Sekunden-Timeout im Frontend ausgeführt.
Teilfehler brechen den gesamten Check nicht ab: `step_errors` und
`step_timings_ms` kennzeichnen betroffene Stationen und deren Laufzeit. Das UI
zeigt bei Teilfehlern einen Warnhinweis; die betroffene Station bleibt
„nicht bewertet“.

Die Peer-Daten im Check verwenden die vorhandenen Stammdaten: bevorzugt die
gleiche Branche, ansonsten den gleichen Sektor. Es werden nur Peers mit
aktuellem Kurs angezeigt; Mock-Peers der bestehenden UI-Route werden im Check
nicht verwendet.
