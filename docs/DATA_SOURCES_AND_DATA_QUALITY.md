# Datenquellen und Datenqualität

## Zweck

Dieses Dokument beschreibt, welche Daten das Projekt verwendet, woher sie kommen,
wie sie verarbeitet und gespeichert werden und welche Aussagen zur Aktualität
heute belastbar sind. Es ist eine Bestandsaufnahme des aktuellen Codes, keine
Garantie für eine bestimmte Börsen- oder Datenanbieter-SLA.

## Kurzfassung

| Bereich | Quelle | Art der Daten | Speicherung bzw. Verwendung |
|---|---|---|---|
| Markt- und Stammdaten | Yahoo Finance über `yfinance` | Kurse, Volumen, Unternehmensstammdaten, Kennzahlen, Börse, Währung | Live-Abruf, Cache/API-Antworten und teilweise PostgreSQL |
| Historische Kurse | Yahoo Finance über `Ticker.history()` | OHLC(V), Adjusted Close, Dividenden, Splits | `stock_price_data` |
| Fundamentaldaten | Yahoo Finance über `Ticker.info` und Finanzdaten-Endpunkte | GuV, Bilanz, Cashflow, Bewertungs- und Wachstumskennzahlen | `stock_fundamental_data` und erweiterte Cache-Daten |
| Corporate Actions | Yahoo Finance über `ticker.dividends` und `ticker.splits` | Dividenden und Aktiensplits | Kursdaten bzw. erweiterte API-Antworten |
| Analysten, Kalender, Halter | Yahoo Finance über `yfinance` | Earnings-Termine, Schätzungen, Ratings, Kursziele, Eigentümerdaten | JSON-Felder bzw. API-Antworten |
| Indexdaten | überwiegend Yahoo Finance; Index-/Konstituenten-Stammdaten zusätzlich durch Seed-/Anwendungslogik | Indexkurse, Bestandteile, Gewichte, Marktkapitalisierung | Index- und Kursdatentabellen |
| Benutzer- und Geschäftsobjekte | Anwendung bzw. Benutzer | Watchlists, Aktienzuordnung, Beobachtungsnotizen, Alerts, Portfolio | PostgreSQL |
| Abgeleitete Daten | Anwendung | RSI, MACD, ATR, gleitende Durchschnitte, Volatilität, Breadth und weitere Metriken | Berechnet zur Laufzeit oder aus gespeicherten Kursen |

Die zentrale externe Quelle ist somit derzeit nicht die Börse selbst, sondern
Yahoo Finance, angesprochen über die Python-Bibliothek `yfinance`. `yfinance`
normalisiert Daten aus Yahoo-Finance-Diensten; daraus folgt keine direkte
Garantie, dass jedes Feld eine Primärquelle der jeweiligen Börse darstellt.

## 1. Externe Datenquelle: Yahoo Finance / `yfinance`

### 1.1 Identifikation und Auflösung

Aktien werden im Normalfall über das Ticker-Symbol angesprochen. Für ISINs
existiert zusätzlich eine Auflösung über `yf.utils.get_ticker_by_isin()`.
Ticker, ISIN, Börse und Währung dürfen nicht als gleichwertige Identifikatoren
behandelt werden: Ein Ticker kann je nach Börsenplatz mehrdeutig sein.

Die relevante Implementierung liegt in
[`backend/app/services/yfinance/client.py`](../backend/app/services/yfinance/client.py)
und
[`backend/app/services/yfinance/stock_info.py`](../backend/app/services/yfinance/stock_info.py).

### 1.2 Gelieferte Datengruppen

#### Stammdaten und Instrument-Metadaten

- Symbol, Name und Kurzname
- ISIN, CUSIP, SEDOL oder LEI, sofern von der Quelle geliefert
- Land, Sektor, Branche und Unternehmensbeschreibung
- Quote-Typ, Börse, Währung, Zeitzone und Marktstatus

#### Aktuelle Marktdaten

- aktueller bzw. letzter Kurs
- vorheriger Schlusskurs, Tageshoch und Tagestief
- 52-Wochen-Hoch und -Tief
- Volumen und Durchschnittsvolumen
- Marktkapitalisierung und Aktienanzahl

Diese Werte sind zeitabhängig und können während der Handelszeit verzögert,
unvollständig oder vom tatsächlichen Primärmarkt abweichend sein. Ein
`last_updated`-Feld wird aus den gelieferten Informationen übernommen, aber
nicht für alle Datenarten garantiert und derzeit nicht als einheitliche
Provenienz im Datenmodell geführt.

#### Historische Kursdaten

Über `Ticker.history()` werden je nach Anfrage Zeitreihen geladen:

- Open, High, Low, Close
- Volumen
- Adjusted Close
- Dividenden und Splits
- Tages-, Wochen- oder Intraday-Intervalle, abhängig von den Grenzen der Quelle

Die Anwendung lädt für technische Indikatoren teilweise einen längeren Zeitraum
als den im Chart angezeigten Zeitraum, damit Aufwärmwerte wie SMA 200 vorhanden
sind. Das ist eine technische Ladeoptimierung und keine höhere Aktualitätsgarantie.

#### Fundamentaldaten

- Bewertungskennzahlen wie KGV, PEG, Kurs-Buchwert und Kurs-Umsatz
- Margen, ROE, ROA, Umsatz- und Gewinnwachstum
- Bilanzwerte, Cashflow, Verschuldung und Liquidität
- Dividendenkennzahlen

Fundamentaldaten sind periodisch und werden mit Veröffentlichung, Korrekturen
oder nachträglichen Anpassungen des Anbieters gültig. Ein Abrufzeitpunkt ist
nicht dasselbe wie der Berichtszeitraum der Kennzahl.

#### Ereignis-, Analysten- und Besitzdaten

- Dividendenhistorie und Aktiensplits
- Earnings-Termine, EPS-Schätzungen und berichtete EPS-Werte
- Analystenempfehlungen, Kursziele und Schätzungen
- institutionelle Halter, Fondsbesitz und größere Halter

Diese Daten haben jeweils eigene fachliche Zeitbezüge (z. B. Ex-Datum,
Berichtsperiode, Prognoseperiode oder Meldedatum). Sie dürfen deshalb nicht
alle mit einem einzigen `updated_at`-Wert bewertet werden.

## 2. Interne und abgeleitete Daten

### 2.1 Benutzer- und Stammdaten

Watchlists, Zuordnungen von Aktien, Beobachtungsgründe, Notizen, Alerts und
Portfolio-Bestände werden von der Anwendung bzw. dem Benutzer erzeugt. Diese
Daten haben keine externe Marktdatenquelle. Ihre Datenqualität betrifft vor
allem Pflichtfelder, gültige Referenzen, fachliche Plausibilität und
Änderungshistorie.

Das Portfolio enthält aktuell Positionen und gewichtete Kaufpreise, aber kein
Transaktionsjournal. Kaufdaten sind daher nicht mit einer externen
Abrechnung oder einem Brokerbestand abgleichbar.

### 2.2 Technische Indikatoren und Kennzahlen

RSI, MACD, ATR, gleitende Durchschnitte, Volatilität, Volumenprofile,
Korrelationen, Marktbreite und Vergleichsmetriken werden aus Kursdaten
berechnet. Sie sind keine zusätzlichen Datenquellen. Ihre Qualität hängt von
der Vollständigkeit, Intervallkonsistenz, Adjustierung und Zeitzone der
zugrunde liegenden Kursreihe ab.

## 3. Aktualität und Aktualisierungsverhalten

### Was aktuell belegt ist

1. Markt- und Fundamentaldaten werden bei API-Aufrufen oder expliziten
   Refresh-Endpunkten über `yfinance` angefordert.
2. Es gibt Refresh-Endpunkte für historische Kurse und Fundamentaldaten, zum
   Beispiel in
   [`backend/app/routes/stock_data.py`](../backend/app/routes/stock_data.py).
3. Der Hintergrund-Scheduler prüft aktive Alerts standardmäßig alle 15 Minuten.
   Er ist in
   [`backend/app/services/scheduler.py`](../backend/app/services/scheduler.py)
   implementiert.
4. Der Scheduler ist kein allgemeiner Datenimport: Aus seiner Implementierung
   folgt keine regelmäßige Aktualisierung sämtlicher Kurse, Fundamentaldaten,
   Indizes oder Corporate Actions.
5. Gespeicherte Zeitstempel wie `created_at`, `updated_at` oder ein Kursdatum
   beschreiben nicht automatisch den Zeitpunkt, zu dem Yahoo Finance den Wert
   ursprünglich veröffentlicht oder aktualisiert hat.

### Vorläufige Aktualitätsklassifikation

| Datenklasse | Fachlicher Zeitbezug | Erwartbare Aktualität | Verbindliche SLA vorhanden? |
|---|---|---|---|
| Intraday-/aktuelle Kurse | Marktzeit bzw. letzter Kurs | abhängig vom Abruf, Markt und Anbieter | Nein |
| Tageskurse | Handelstag | nach Abruf und Verfügbarkeit des abgeschlossenen Handelstags | Nein |
| Dividenden/Splits | Ex-Datum bzw. Ereignisdatum | nach Übernahme durch den Anbieter | Nein |
| Fundamentaldaten | Berichtsperiode | quartals-/jahresweise, nach Veröffentlichung | Nein |
| Earnings und Analysten | Termin-, Prognose- oder Meldedatum | ändert sich ereignisbezogen | Nein |
| Watchlists und Portfolio | Änderungszeitpunkt der Anwendung | bei Benutzeränderung | Nur technisch über lokale Zeitstempel |

Für produktive Qualitätsaussagen sollten künftig mindestens `source`,
`source_recorded_at`, `retrieved_at`, `effective_at` bzw. `period_start` und
`period_end` gespeichert werden. Diese Zeitpunkte müssen fachlich getrennt
bleiben.

## 4. Relevante Qualitätsdimensionen

Vollständigkeit ist wichtig, aber nicht ausreichend. Für dieses Projekt gehören
mindestens folgende Dimensionen in ein Datenqualitätskonzept:

1. **Vollständigkeit:** erwartete Wertfelder, Handelstage, Perioden und
   Instrumente sind vorhanden.
2. **Aktualität/Freshness:** Zeit seit erfolgreichem Abruf und Zeit seit dem
   fachlichen Datenereignis liegen innerhalb eines definierten Schwellenwerts.
3. **Korrektheit/Genauigkeit:** Werte sind plausibel und, wo möglich, gegen
   eine autoritative Quelle oder einen zweiten Anbieter abgeglichen.
4. **Gültigkeit:** Datentypen, Währungen, Einheiten, Wertebereiche und
   Zeitformate entsprechen dem Vertrag.
5. **Konsistenz:** Kurs, Währung, Börse, Ticker, Corporate Actions und
   berechnete Kennzahlen widersprechen sich nicht.
6. **Eindeutigkeit:** keine doppelten Instrumente, Kurstage oder
   Fundamentalperioden; die Datenbank-Constraints sind dabei nur ein Teil der
   Prüfung.
7. **Nachvollziehbarkeit (Lineage):** Quelle, Abruf, Transformation,
   Fallbacks, Fehler und verwendete Versionen sind reproduzierbar.
8. **Verfügbarkeit:** Anbieter, Endpunkte und einzelne Datenkategorien sind
   erreichbar; Fehler dürfen nicht wie gültige leere Daten aussehen.
9. **Stabilität/Semantik:** Änderungen an `yfinance`, Yahoo-Feldern, Einheiten
   oder Adjustierungslogik werden erkannt und bewertet.
10. **Reconciliation:** wichtige Werte und Aggregationen stimmen mit
    Kontrollsummen, Vorperioden oder Referenzdaten überein.

## 5. Vorschlag für ein späteres Python-Qualitätsprüfskript

Das geplante Skript sollte nicht nur „ist ein Wert vorhanden?“ prüfen, sondern
pro Datenquelle und Instrument einen Prüfdatensatz erzeugen:

```text
run_id
instrument_id / ticker / isin
data_category
provider
exchange
requested_at
retrieved_at
source_timestamp
effective_date_or_period
status
error_code
error_message
row_count
missing_fields
quality_checks
```

### Sinnvolle Prüfungen

- erwartete Instrumente gegen Watchlist- und Indexbestandteile abgleichen
- fehlende Handelstage unter Berücksichtigung von Börsenkalendern erkennen
- Freshness-Schwellen je Kategorie definieren, nicht global
- `open <= high`, `low <= close`, positive Volumina und plausible Sprünge prüfen
- Währung und Börse gegen Instrument-Stammdaten abgleichen
- Splits und Dividenden bei auffälligen Kurssprüngen berücksichtigen
- Fundamentalperioden auf Duplikate, Lücken und Überschneidungen prüfen
- berechnete Indikatoren nur bei ausreichender Historie als gültig markieren
- HTTP-/Providerfehler, leere Antworten und Teilantworten unterscheiden
- Quelle und Abrufzeit pro Datensatz protokollieren
- Ergebnis nach `PASS`, `WARN` und `FAIL` klassifizieren und messbar speichern

Die Frage „wurde der Wert von der jeweiligen Börse oder vom Dienstleister
geliefert?“ sollte als Provenienzmodell umgesetzt werden. Ein einzelnes
Boolean-Feld reicht dafür nicht: Es sollte zwischen `provider=yahoo_finance`,
`upstream_exchange` (soweit bekannt), `derived_by_application` und
`user_entered` unterschieden werden.

## 6. Offene Entscheidungen vor der Implementierung

- Welche Instrumente und Datenkategorien sind geschäftskritisch?
- Welche Freshness-Schwellen gelten für Intraday, Tageskurse,
  Fundamentaldaten und Earnings?
- Welche Börsenkalender und Zeitzonen sind maßgeblich?
- Ist Yahoo Finance für produktive Nutzung ausreichend oder wird für kritische
  Werte ein lizenzierter Primäranbieter benötigt?
- Sollen fehlende Werte als `NULL`, „nicht geliefert“, „Abruf fehlgeschlagen“
  oder „nicht anwendbar“ unterschieden werden?
- Wie lange sollen Rohantworten, Prüfprotokolle und Fehlerhistorien aufbewahrt
  werden?
- Wer wird bei `FAIL` informiert und wie wird ein Fehler behoben bzw.
  bestätigt?

## 7. Technische Lücken im aktuellen Stand

- Kein einheitliches Provenienz- und Ingestion-Modell für alle Datenkategorien.
- Kein zentraler erfolgreicher/fehlgeschlagener Abrufstatus je Quelle.
- Keine verbindliche Freshness-SLA oder Datenqualitätsampel.
- `created_at`/`updated_at` ersetzen nicht `retrieved_at` und den fachlichen
  Gültigkeitszeitpunkt.
- Provider- und Teilantwortfehler werden nicht überall als eigener,
  persistierter Status geführt.
- Ein automatisierter Vollständigkeits- und Plausibilitätsreport ist noch nicht
  Bestandteil des Projekts.

Diese Punkte sind die sinnvollste Grundlage für einen nächsten Schritt: zuerst
ein kleines Ingestion-/Provenienzmodell, danach das Python-Prüfskript und
anschließend die Darstellung der Ergebnisse im Backend oder in einem
administrativen Bericht.

## 8. Admin-Panel v1

Die erste Admin-Ansicht ist unter `/admin` verfügbar und verwaltet aktuell
Stocks. Sie bietet Stammdaten-CRUD, Archivieren statt physischem Löschen,
Ticker-Import inklusive historischer Kurse und Fundamentaldaten sowie einen
gezielten Reload je Asset.

Die Datenqualitätsanzeige vergleicht den letzten gespeicherten Tageskurs mit
dem letzten erwarteten Wochentag. Wochenenden und Börsenfeiertage werden in v1
nicht über einen Börsenkalender berücksichtigt. Die Quelle wird deshalb
transparent als `yfinance` angezeigt; ein persistiertes Abrufprotokoll und
eine feinere Provenienz bleiben Folgearbeiten.
