# 🚀 Future Features (Roadmap) - Stock Watchlist App

## ✅ Recently Completed (2025-10-09)

### Volume Profile Overlay - Phase 4
**Status:** ✅ Implemented (needs fine-tuning)  
**Completion Date:** October 9, 2025

**Implemented Features:**
- ✅ Volume Profile Overlay rechts vom Chart
- ✅ POC, VAH, VAL Labels und horizontale Linien
- ✅ Price-range Clipping für saubere Bar-Darstellung
- ✅ Backend-Limit erhöht (365 → 3650 Tage)
- ✅ Render-Loop Bug behoben (useCallback für onLoad)
- ✅ Kalibrierungs-System mit `heightAdjustment` Parameter
- ✅ Debug-Modus (aktivierbar für Entwicklung)

**Pending:**
- 🔧 Perfekte vertikale Ausrichtung mit Recharts (heightAdjustment Feintuning)
  - Aktuell: `heightAdjustment={90}` in StockChart.js
  - Todo: Wert anpassen bis Bars perfekt mit Preislinien übereinstimmen

**Technical Details:**
- Component: `VolumeProfileOverlay.js`
- Integration: `StockChart.js` (Zeile ~1245)
- Backend: `volume_profile_service.py` (period_days: 1-3650)
- Calibration: `DEBUG_MODE = true` für detaillierte Console-Ausgaben

---

## 🔄 Implementierungsstatus (Stand: 21.11.2025)

| Bereich | Status | Hinweise |
|--------|--------|----------|
| Volume Profile Overlay | ✅ Fertig | Feintuning heightAdjustment offen |
| RSI / MACD / Bollinger | ✅ Aktiv | Backend + Chart integriert |
| Ichimoku Cloud | ✅ Implementiert | Umschaltbar im Chart (`showIchimoku`) |
| Divergenz-Erkennung (RSI) | ✅ Basis | Historisierung & Erfolgsauswertung fehlen |
| Composite Alerts (AND) | ✅ Basis | Nur AND-Logik; OR/Chains fehlen |
| Trailing Stop Alert | ✅ Implementiert | `_check_trailing_stop_alert` vorhanden |
| Prozent-von-SMA / Volumen-Spike Alerts | ✅ Implementiert | In `alert_service.py` |
| Screener (Basis) | ✅ Minimal | Fundamentale & einfache technische Filter |
| Seasonality Tab | ✅ | Endpoint aktiv |
| Sector / Peer Comparison | ✅ | `SectorComparisonTab` + Service |
| Relative Strength / Benchmark Vergleich | ✅ | `comparison_service` |
| Correlation Heatmap | ✅ | Frontend `CorrelationHeatmap.js` |
| Watchlist Notizen / Gründe | ✅ Einfach | `observation_notes` / `observation_reasons` |
| Smart Watchlists | ❌ | Phase 15 pending |
| Multi-Condition Alerts (ODER, Chains) | ❌ Teilweise | Nur AND umgesetzt |
| Pattern-Based Alerts (Candlestick) | ❌ | Kein Erkennungsmodul |
| Velocity / ROC Alerts | ❌ | Keine Rate-of-Change Logik |
| Zeitfenster / Session Alerts | ❌ | Felder `active_from/active_to` fehlen |
| Alert-Kanäle / Webhooks | ❌ | Kein Versandadapter |
| Portfolio Management | ❌ | Keine Tabellen/Services |
| Historical Divergence Tracking | ❌ | Keine Persistenz |
| Divergence Success Rate | ❌ | Keine Evaluation |
| News Integration | ❌ | Kein `news_service` |
| Sentiment Analysis | ❌ | Keine NLP-Pipeline |
| Export (PDF/Excel/SVG) | ❌ | Nicht begonnen |
| User Authentication | ❌ | Keine User-Modelle |
| Redis / Caching Layer | ❌ | Nur Kommentare |
| Celery / Background Queue | ❌ | Nicht vorhanden |
| WebSockets | ❌ | Nicht vorhanden |
| Custom Columns Builder | ❌ | Nicht vorhanden |
| Earnings / Corporate Actions | ❌ | Keine Tabelle |
| Analysten-Historie & Revisionen | ❌ Teilweise | Aktuelle Revisionenzählung aus yfinance; keine eigene Persistenz |
| Options Volatilität (IV) | ❌ | Nicht vorhanden |
| Anomalie-Erkennung (ML) | ❌ | Nicht vorhanden |
| RRG-Light Erweiterung | ❌ | Nur Grund-RS vorhanden |

Kurzfazit: Kern-Indikatoren & Vergleichsfunktionen stehen; nächster Hebel sind Portfolio, erweiterte Alerts & Smart-Watchlists plus Infrastruktur (Auth, Caching).

---

## 🔴 Hohe Priorität - Datenbankmigrationen zentralisieren

**Status:** ❌ Offen
**Priorität:** 🔴 Hoch
**Einschätzung:** Aktuell besteht ein mittleres Risiko in der lokalen Entwicklung und ein hohes Risiko für Produktion oder mehrere Umgebungen. Das Backend verwendet beim Start `Base.metadata.create_all()`, führt bestehende Migrationen aber nicht automatisch aus. Die eigentlichen Schemaänderungen liegen in einzelnen, manuell auszuführenden Skripten unter `backend/app/migrations/`; eine zentrale Versionsverwaltung fehlt.

### Risiken

- Neue Spalten, Constraints oder Indizes werden bei bestehenden Tabellen nicht automatisch angelegt.
- Das Backend kann trotz nicht aktualisiertem Schema starten; Fehler treten dann erst bei betroffenen API-Aufrufen auf.
- Migrationen können vergessen oder in falscher Reihenfolge ausgeführt werden.
- Es ist nicht zuverlässig nachvollziehbar, welche Migrationen auf einer Datenbank bereits angewendet wurden.
- Wiederholte Ausführung einzelner älterer Skripte ist nicht durchgehend sicher.
- Tests mit `Base.metadata.create_all()` können Unterschiede zwischen Modell und realem Migrationspfad verdecken.

### Empfohlene Maßnahmen

1. Bestehende Produktions- und Entwicklungsdatenbanken sichern und den aktuellen Schemazustand erfassen.
2. Einen einheitlichen Migrationsmechanismus festlegen, vorzugsweise Alembic oder alternativ einen zentralen, versionierten eigenen Migration-Runner.
3. Die vorhandenen Migrationen unter `backend/app/migrations/` in eine nachvollziehbare Versionshistorie überführen.
4. Eine zentrale Versions-/Status-Tabelle einführen, damit jede Migration genau einmal und in definierter Reihenfolge ausgeführt wird.
5. Migrationen beim Deployment beziehungsweise vor dem Backend-Start kontrolliert ausführen.
6. `Base.metadata.create_all()` nicht mehr als Produktionsmigration verwenden; für Tests darf es weiterhin mit einer isolierten Testdatenbank eingesetzt werden.
7. Tests ergänzen, die eine bestehende ältere Datenbank auf die aktuelle Version migrieren.
8. `alembic.ini` und die Alembic-Abhängigkeit erst entfernen, nachdem entschieden wurde, ob Alembic verwendet oder bewusst durch einen eigenen Runner ersetzt wird.

### Erfolgskriterien

- Jede Datenbank besitzt eine eindeutig bekannte Schema-Version.
- Migrationen laufen reproduzierbar, in definierter Reihenfolge und ohne manuelle Einzelaufrufe.
- Ein Deployment schlägt sichtbar fehl, wenn eine erforderliche Migration nicht ausgeführt werden kann.
- Eine neue oder bestehende Datenbank kann anhand einer dokumentierten Anleitung auf den aktuellen Stand gebracht werden.

## 📊 Analysten-Historie & Revisionen

**Status:** ❌ Geplant
**Priorität:** 🟡 Mittel-Hoch
**Ziel:** In der Aktienansicht nicht nur den aktuellen Analystenstand, sondern die Entwicklung von Empfehlungen, Analystenzahl und Kurszielen über frei wählbare Zeiträume (z. B. 1 Monat, 3 Monate, 6 Monate, 1 Jahr) anzeigen.

### Ausgangslage

- Die Aktienansicht lädt den Analystenüberblick aktuell über `GET /stocks/{stock_id}/analyst-ratings`.
- `revisions_1m` und `revisions_3m` werden aus der von yfinance gelieferten Recommendation-Zeitreihe berechnet.
- Diese Daten werden derzeit nicht dauerhaft als Anwendungshistorie gespeichert.
- Kursziele (`mean`, `high`, `low`, `median`) und `numberOfAnalystOpinions` sind momentan nur aktuelle Snapshots.
- Der bestehende Cache enthält pro Aktie nur einen Datensatz und ist daher keine Historientabelle.

### Geplanter Umsetzungsplan

#### 1. Datenmodell & Speicherung

- Neue Tabelle für Analysten-Snapshots, z. B. `analyst_data_snapshots`.
- Pro Snapshot speichern:
  - `stock_id`, `observed_at` und Datenquelle
  - Kurszielwerte: `current`, `high`, `low`, `mean`, `median`
  - Anzahl der Analysten
  - Empfehlungssummen: `strong_buy`, `buy`, `hold`, `sell`, `strong_sell`
  - optional den unveränderten Provider-Payload für spätere Nachberechnung
- Eindeutigkeit bzw. Deduplizierung definieren, damit wiederholte Abrufe ohne Datenänderung keine unnötigen Datensätze erzeugen.
- Aufbewahrungsstrategie und Fehlerstatus festlegen; fehlerhafte Abrufe dürfen keinen gültigen Snapshot überschreiben.
- Migration, Indizes auf `(stock_id, observed_at)` und Bereinigung vorhandener Cache-Annahmen ergänzen.

#### 2. Erfassung & Aktualisierung

- Analystendaten über einen zentralen Service abrufen und nach erfolgreichem Abruf als Snapshot persistieren.
- Aktualisierungsintervall festlegen (z. B. höchstens einmal täglich pro Aktie; manuelles Refresh weiterhin ermöglichen).
- Zeitzonen und den Beobachtungszeitpunkt einheitlich als UTC speichern.
- Provider-Zeitreihen von yfinance weiterhin nutzen, aber klar von der eigenen Snapshot-Historie unterscheiden.

#### 3. Historische Berechnung

- Revisionen aus eigenen Snapshots berechnen und nicht nur die aktuell von yfinance gelieferte Tabelle zählen.
- Für jeden Zeitraum liefern:
  - Anzahl tatsächlicher Änderungen
  - Änderung der Konsensbewertung
  - Änderung der Analystenzahl
  - Änderung von durchschnittlichem, niedrigstem und höchstem Kursziel
- Gleiche Datenstände deduplizieren; Änderungen an einzelnen Empfehlungskategorien oder Kurszielen nachvollziehbar erfassen.
- Fehlende Daten und Provider-Lücken explizit kennzeichnen, statt sie als unveränderte Werte zu interpretieren.

#### 4. API & Aktienansicht

- Historien-Endpunkt ergänzen, z. B. `GET /stocks/{stock_id}/analyst-history`.
- Parameter für Zeitraum, Granularität und optional Limit vorsehen.
- Antwortformat als Zeitreihe mit Snapshot-Daten und berechneten Veränderungen definieren.
- In der Analysten-Ansicht:
  - Zeitraum-Auswahl (1M, 3M, 6M, 1J)
  - Verlauf für durchschnittliches Kursziel und Analystenzahl
  - Liste/Timeline der Empfehlungsänderungen
  - klare Kennzeichnung des letzten Aktualisierungszeitpunkts
  - Hinweis bei unvollständiger Historie
- Die bestehende aktuelle Zusammenfassung und die bisherigen Revisionenzähler zunächst rückwärtskompatibel halten.

#### 5. Qualität & Tests

- Unit-Tests für Snapshot-Deduplizierung und Zeitraumberechnung.
- API-Tests für leere, lückenhafte und vollständig vorhandene Historien.
- Tests für unveränderte Daten, echte Änderungen und Provider-Fehler.
- Frontend-Test für Zeitraumwechsel und fehlende Historie.
- Logging/Metriken für Abrufzeitpunkt, Datenalter und fehlgeschlagene Snapshot-Erfassung.

### Abgrenzung

- Keine historische Bewertung einzelner namentlich bekannter Analysten in der ersten Version; yfinance liefert primär aggregierte Empfehlungen.
- Keine rückwirkende Rekonstruktion von Daten, die vor Einführung der Snapshot-Erfassung nicht gespeichert wurden.
- Options-IV-Historie bleibt ein separates Feature und wird nicht in dieses Datenmodell integriert.

### Erfolgskriterium

Für eine Aktie können Nutzer in der Aktienansicht einen Zeitraum auswählen und sehen, wie sich Konsens, Analystenzahl und Kursziele seit Beginn der eigenen Datenerfassung verändert haben. Jede angezeigte Änderung ist auf einen gespeicherten Snapshot mit Zeitstempel zurückführbar.

---

## 🕯️ Phase 6 - Candlestick Pattern Recognition

### 6.1 Reversal Patterns
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Patterns zu erkennen:**
- **Hammer** (Bullish Reversal)
- **Shooting Star** (Bearish Reversal)
- **Bullish Engulfing** (grüne Kerze umschließt vorherige rote)
- **Bearish Engulfing** (rote Kerze umschließt vorherige grüne)
- **Morning Star** (3-Kerzen Bullish Pattern)
- **Evening Star** (3-Kerzen Bearish Pattern)
- **Doji** (Indecision)

**Technische Details:**
- Backend: `detect_candlestick_patterns(ohlc_data)`
- Algorithmus: Verhältnisse von Body/Shadow analysieren
- Frontend: Icons/Badges über den Kerzen
- Alert Integration möglich

---

### 6.2 Continuation Patterns
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐ Mittel  
**Priorität:** 🟢 Niedrig

**Patterns:**
- **Three White Soldiers** (3 aufeinanderfolgende grüne Kerzen)
- **Three Black Crows** (3 aufeinanderfolgende rote Kerzen)
- **Spinning Top** (kleiner Body, lange Shadows)
- **Marubozu** (kein/minimaler Shadow, starker Trend)

---

## 🎯 Phase 7 - Erweiterte Alert-Funktionen

### 7.1 Multi-Condition Alerts
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🔴 Hoch

**Features:**
- **UND-Verknüpfung:** "RSI < 30 UND Preis < Support Level"
- **Komplexe Chains:** "(RSI < 30 UND Volume > AVG) ODER Price < 50-SMA"
- Condition Builder UI mit Drag & Drop
- Template Library ("Oversold Stock", "Breakout Alert", etc.)

**Technische Details:**
- Backend: Alert-Engine mit JSON-basierter Condition-Logik
- Neue Tabelle: `alert_conditions` mit parent/child relationships
- Evaluation Engine: Prüft alle Conditions täglich

---

### 7.2 Pattern-Based Alerts
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Alert Types:**
- "Golden/Death Cross detected"
- "Hammer Pattern at Support Level"
- "Price touched Fibonacci 61.8% Retracement"
- "Bollinger Band Squeeze (Breakout imminent)"
- "RSI Divergence detected"

---

### 7.3 Alert-Historie & Management
**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**
- Getriggerte Alerts History mit Timestamp
- Performance Tracking: "Wie oft war der Alert richtig?"
- Snooze/Pause für x Tage
- Alert Groups/Categories

**Technische Details:**
- Neue Tabelle: `alert_history` mit trigger_time, stock_price, outcome
- Background Job: Alert Checker läuft alle 120 Minuten

---

### 7.4 Historical Divergence Tracking
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐ Mittel  
**Priorität:** 🟢 Niedrig

**Features:**
- Speicherung jeder erkannten Divergenz in Datenbank
- Historie-Ansicht: "Wann gab es letzte Divergenzen?"
- Verhindert doppelte Alerts für gleiche Divergenz (7-Tage-Window)
- Divergence Points als JSON speichern für spätere Visualisierung
- Filter nach Indicator Type (RSI/MACD) und Divergence Type (Bullish/Bearish)
- Status-Tracking: Active/Resolved/Expired

**Technische Details:**
- Neue Tabelle: `divergence_detections`
  - stock_id, indicator_type, divergence_type, detected_at
  - price_at_detection, indicator_value, confidence_score
  - divergence_points (JSON), is_active, resolved_at
- API Endpoint: `GET /stock-data/{stock_id}/divergence-history`
- Integration in `alert_service.py`: Speichert bei Detection
- Frontend: Divergence History Tab mit Timeline

**Use Cases:**
- User sieht historische Divergenzen im Chart
- Analyse: "Wie oft gab es Divergenzen in letzten 6 Monaten?"
- Alert-Throttling: Keine mehrfachen Alerts für gleiche Divergenz

---

### 7.5 Divergence Success Rate Tracking
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- Automatische Evaluation: War die Divergenz erfolgreich?
- Preis-Tracking nach 5/10/20 Tagen
- Success-Definition:
  - Bullish Divergence: Preis steigt nach X Tagen
  - Bearish Divergence: Preis fällt nach X Tagen
- Outcome: successful/failed/neutral (bei <2% Bewegung)
- Success Rate pro Stock anzeigen
- Confidence Correlation: Höhere Confidence = höhere Success Rate?

**Technische Details:**
- Erweitert `divergence_detections` Tabelle:
  - price_after_5_days, price_after_10_days, price_after_20_days
  - outcome (successful/failed/neutral/pending)
  - actual_direction (up/down/sideways)
- Background Job (APScheduler/Celery):
  - Läuft täglich um 2 Uhr
  - Evaluiert alle pending Divergenzen
  - Fetcht aktuelle Preise via yfinance
- API Endpoint: `GET /stock-data/{stock_id}/divergence-stats`
- Frontend: 
  - Success Rate Badge im Divergence Analysis Tab
  - "This stock has 72% success rate for bullish divergences"
  - Performance Chart: Success Rate über Zeit

**Algorithmus:**
```python
# Nach 20 Tagen evaluieren
price_change = (price_after_20_days - price_at_detection) / price_at_detection * 100

if divergence_type == 'bullish':
    if price_change > 2%: outcome = 'successful'
    elif price_change < -2%: outcome = 'failed'
    else: outcome = 'neutral'
```

**Use Cases:**
- User sieht: "AAPL hat 75% Success Rate bei Divergenzen"
- Trading-Entscheidung: Höhere Success Rate = mehr Vertrauen
- Filter: Nur Stocks mit hoher Divergence Success Rate
- Alert-Priorität: Höhere Priorität bei Stocks mit guter Success Rate

**Performance Ranking:**
- Top 10 Stocks mit bester Divergence Success Rate
- Minimum 5 Divergenzen für Ranking

---

### 7.6 Trailing- und Follow-Alerts

**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🔴 Hoch

**Features:**

- Trailing Alerts relativ zum letzten Hoch/Tief (z. B. "Alarm, wenn -3% unter letztem Swing High")
- Follow-Alerts: Folge Stop-Level X% hinter dem Kurs (dynamisch)
- Cooldown/De-Dupe: Verhindert mehrfaches Auslösen innerhalb eines Zeitfensters

**Technische Details:**

- Backend: Erweiterung `alert_conditions` um Felder `trailing_percent`, `baseline` (high/low/close), `lookback`, `cooldown_minutes`
- Evaluation: `alert_service.py` berechnet laufend Referenz (Rolling High/Low) und prüft Schwellwert
- Frontend: Zusätzlicher Alert-Typ in `alerts`-UI mit Live-Vorschau der aktuellen Schwelle

---

### 7.7 Velocity-/Rate-of-Change-Alerts

**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** � Mittel

**Features:**

- Alarm bei Bewegung >X% in Y Minuten (Momentum-/News-Alerts)
- Wahlweise absolut ($) oder relativ (%)
- Optionales Volumen-Filter (Vol > 1.5x Avg)

**Technische Details:**

- Backend: ROC-Berechnung über Rolling Returns im `historical_price_service.py`
- Condition: `delta_pct >= threshold` innerhalb `window_minutes`
- Frontend: Kompakter Editor mit Previews (letzte 15/30/60 Min)

---

### 7.8 Time-Window & Session-Alerts

**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐ Mittel  
**Priorität:** 🟢 Niedrig

**Features:**

- Alerts nur in bestimmten Zeitfenstern aktiv (z. B. 15:30–22:00 UTC, nur Handelssession)
- Earnings-Week-Only: Aktiviere Alerts nur ±N Tage um Earnings

**Technische Details:**

- `alert_conditions`: Felder `active_from`, `active_to`, `sessions` (pre/regular/post)
- Backend: Session-Logik im Scheduler; Earnings-Termine aus Kalender (siehe Phase 16)

---

### 7.9 Alert-Kanäle, Webhooks & Throttling

**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**

- Kanäle: E-Mail, Telegram/Discord, Web Push
- Webhooks (Zapier/Make): POST mit Payload bei Trigger
- Throttling & De-Dupe pro Alert/Stock/User

**Technische Details:**

- Backend: Channel-Adapter in `alert_service.py` (Strategy-Pattern), Queue für Zustellung
- Tabelle `alert_history` nutzen für De-Dupe/Throttle-Fenster
- Frontend: Kanal-Settings pro Alert + Testversand

## �📈 Phase 8 - Portfolio Management

### 8.1 Virtuelle Portfolios
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟡 Mittel

**Features:**
- Mehrere Portfolios erstellen ("Growth", "Value", "Dividends")
- Transaktionen tracken:
  - Buy: Anzahl Shares, Preis, Datum, Gebühren
  - Sell: Partial/Full, Realized Gain/Loss
  - Dividends: Automatic tracking
- Cost Basis Tracking (FIFO, LIFO, Average)
- Current Holdings mit Gewinn/Verlust
- Cash Management

**Technische Details:**
- Neue Tabellen: `portfolios`, `transactions`, `holdings`
- Backend: `portfolio_service.py` mit PnL calculations
- Frontend: Portfolio Dashboard mit Holdings Table

---

### 8.2 Performance Analytics
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟡 Mittel

**Metrics:**
- **ROI (Return on Investment):** (Current Value - Cost Basis) / Cost Basis
- **Total Return:** Absoluter Gewinn/Verlust in $
- **Annualized Return:** Durchschnittliche jährliche Performance
- **Max Drawdown:** Größter Verlust von Peak zu Trough
- **Sharpe Ratio:** Risk-adjusted Return
- **Win Rate:** % profitable Trades
- **Average Gain/Loss per Trade**
- **Benchmark Comparison:** vs. S&P 500, NASDAQ, MSCI World

**Technische Details:**
- Backend: `calculate_portfolio_metrics(portfolio_id)`
- Benchmarks: Fetch ^GSPC (S&P 500) data via yfinance
- Frontend: Performance Charts mit Recharts (Line, Area)

---

### 8.3 Portfolio Dashboard
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟡 Mittel

**Visualizations:**
- **Asset Allocation Pie Chart:** % pro Stock
- **Sector Allocation:** % Tech, Healthcare, Finance, etc.
- **Performance Timeline:** Portfolio Value über Zeit
- **Dividend Tracker:** Jährliche Dividenden-Einnahmen
- **Top Gainers/Losers Table**
- **Recent Transactions Log**

---

## 🔍 Phase 9 - Stock Screener

### 9.1 Filter System
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟡 Mittel

**Filter Categories:**

**Technical Filters:**
- RSI: Range (0-100)
- MACD: Bullish/Bearish Crossover in last X days
- Volume: Above/Below Average Volume
- ATR (Volatility): High/Medium/Low
- Recent Patterns: Golden Cross, Support Touch, etc.

**Fundamental Filters:**
- Market Cap: Mega/Large/Mid/Small Cap
- P/E Ratio: Range
- Dividend Yield: > X %

**Price Action Filters:**
- 52-Week High/Low: Within X% of High/Low
- Recent Breakout: Price > Resistance
- Gap Up/Down: > X%

**Technische Details:**
- Backend: `screener_service.py` mit SQL Query Builder
- Neue Tabelle: `saved_screens` (user_id, filter_json, name)
- Frontend: Filter Builder UI mit Multi-Select, Range Sliders
- Performance: Index auf wichtigsten Spalten

---

### 9.2 Pre-built Screens
**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Screen Templates:**
1. **Oversold Stocks**
   - RSI < 30
   - Price > $10
   - Volume > 1M

2. **Golden Cross Recently**
   - Golden Cross in last 7 days
   - Price > 50-SMA
   - Volume increasing

3. **Near Support Level**
   - Price within 2% of Support
   - RSI < 50
   - No recent Bearish patterns

4. **High Volume Breakout**
   - Volume > 2x Average
   - Price > 52-week high
   - Market Cap > 1B

5. **Value Stocks**
   - P/E < 15
   - Dividend Yield > 3%
   - Positive Earnings Growth

6. **Momentum Stocks**
   - Price > 200-SMA
   - RSI 50-70
   - MACD Bullish
   - 3-Month Performance > 10%

**Frontend:** Gallery mit Screen-Cards, Click to Run

---

## 10. Anomalie-Erkennung
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐ Mittel  
**Priorität:** 🟢 Niedrig

**Features:**
- Ungewöhnliche Preisbewegungen (>3 Standardabweichungen)
- Volume Spikes (>5x Average)
- Gap Detection (>5% Overnight Change)
- Correlation Breaks (Stock divergiert von Sektor)

**Technische Details:**
- Isolation Forest Algorithm
- Z-Score Analysis

---

## 📰 Phase 11 - News Integration

### 11.1 News Feed
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- Aktuelle Nachrichten pro Stock
- Filtering: Latest, Most Relevant, By Source
- Article Preview mit Thumbnail
- Link zum Full Article
- Publish Date & Source

**APIs:**
- NewsAPI.org (Free: 100 requests/day)
- Alpha Vantage News (Free mit API Key)
- Finnhub.io (Free Tier)
- Yahoo Finance RSS

**Technische Details:**
- Backend: `news_service.py` mit API Integration
- Caching: News für 1 Stunde cachen
- Frontend: News Tab neben Chart

---

### 11.2 Sentiment Analysis
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- Positiv/Negativ/Neutral Sentiment Score
- Sentiment aus News Headlines
- Social Media Sentiment:
  - Twitter/X mentions
  - Reddit r/wallstreetbets mentions
  - StockTwits
- Sentiment Trend über Zeit (Line Chart)
- Sentiment vs. Price Chart (Correlation?)

**Technische Details:**
- NLP Library: NLTK oder spaCy
- Pre-trained Models: FinBERT (Finance-specific BERT)
- Social APIs: Twitter API v2, Reddit API (PRAW)
- Neue Tabelle: `sentiment_data`

---

## 📊 Phase 12 - Multi-Stock Analysis

### 12.1 Stock Comparison
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**
- Mehrere Aktien im gleichen Chart überlagern
- Normalisierte Ansicht (alle starten bei 100%)
- Performance-Vergleich Tabelle:
  - 1D, 1W, 1M, 3M, 6M, 1Y, YTD
- Side-by-Side Metrics Comparison
- Correlation Chart

**Technische Details:**
- Frontend: Multi-Stock Selector (Dropdown + Tags)
- Recharts: Multiple Line Series mit verschiedenen Farben
- Normalisierung: `(price / start_price) * 100`

---

### 12.2 Correlation Matrix
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐ Mittel  
**Priorität:** 🟢 Niedrig

**Features:**
- Heatmap: Korrelation zwischen Stocks in Watchlist
- Correlation Coefficient: -1 (inverse) bis +1 (perfekt korreliert)
- Identify Diversification Opportunities
- Sector Correlation

**Technische Details:**
- Backend: pandas `df.corr()` auf historical returns
- Frontend: Heatmap mit react-heatmap-grid
- Colors: Rot (negative), Weiß (0), Grün (positive)

---

### 12.3 Sector Analysis
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐ Mittel  
**Priorität:** 🟡 Mittel

**Features:**
- Sektor-Performance Dashboard
- Relative Strength vs. Sektor
- Sektor-Rotation Radar
- Top Performers per Sector

**Technische Details:**
- Sector ETFs als Benchmark (XLK, XLV, XLF, etc.)
- Relative Strength: Stock Performance / Sector Performance

---

### 12.4 Relative Strength (RRG-Light)

**Schwierigkeit:** ⭐⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**

- Relative Strength vs. Benchmark/Sektor (Ratio + Smoothed Change)
- Mini-RRG-Ansicht: Quadranten (Leading, Weakening, Lagging, Improving)

**Technische Details:**

- Backend: Aggregation historischer Returns (pandas resample/groupby)
- Endpoints: `GET /stock-data/{stock_id}/seasonality`, `GET /relative-strength?base=XLK`
- Frontend: Heatmap (Monate x Jahre) + kleines RS-Rotation-Panel

## 🎨 Phase 13 - UX Verbesserungen

### 13.1 Custom Layouts
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- Drag & Drop Dashboard (React-Grid-Layout)
- Widgets: Chart, News, Metrics, Watchlist, Portfolio
- Speichern von Layouts pro User
- Preset Layouts: "Trader", "Investor", "Analyst"
- Dark/Light Theme Toggle
- Custom Color Schemes

**Technische Details:**
- Library: react-grid-layout
- Neue Tabelle: `user_layouts`
- Theme: CSS Variables + Context API

---

### 13.2 Export Funktionen
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- **PDF Reports:**
  - Chart Snapshot
  - Key Metrics Table
  - Technical Analysis Summary
  - Portfolio Performance Report
  
- **Excel Export:**
  - Historical Price Data
  - All Calculated Metrics
  - Transaction History
  
- **Chart als Bild:**
  - PNG/SVG Download
  - Include/Exclude Indicators

**Technische Details:**
- PDF: jsPDF + html2canvas
- Excel: XLSX library
- Chart: Recharts SVG Export

---

### 13.3 Mobile Responsiveness
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- Touch-optimierte Charts (Pinch-to-Zoom)
- (Mobile-first Design)
- Bottom Navigation Bar
- Swipe Gestures (zwischen Tabs)
- PWA (Progressive Web App):
  - Offline Functionality
  - Add to Home Screen
  - Push Notifications
  - Background Sync

**Technische Details:**
- CSS: Media Queries, Flexbox, Grid
- PWA: Service Worker, Web App Manifest
- Touch: Hammer.js oder React Touch Events

---

### 13.4 Notizen & Tags pro Stock

**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**

- Kurznotizen, Setups, Checklisten je Ticker
- Tags (filterbar): z. B. "Earnings-Setup", "Breakout Watch"

**Technische Details:**

- Neue Tabellen: `stock_notes` (id, stock_id, text, created_at, user_id), `stock_tags` (stock_id, tag)
- Endpoints: `POST/GET/DELETE /stocks/{id}/notes|tags`
- Frontend: Notizfeld in Detail-Panel, Tag-Chips + Filter

---

### 13.5 Portfolio-Heatmap & Smart-Sort

**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**

- Heatmap-Ansicht: Tages-/Wochen-/Monats-Performance
- Multi-Sort & gespeicherte Sortierungen (z. B. RS desc, dann Vol% desc)

**Technische Details:**

- Backend: Aggregierte Returns je Zeitraum; Cache 5–15 Min
- Frontend: Heatmap-Komponente; Sort-Layouts persistent pro User

---

### 13.6 Custom Columns Builder

**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**

- Nutzerdefinierte Spalten basierend auf Indikatorwerten/Formeln
- Validierung & Sandbox (nur Whitelist-Variablen)

**Technische Details:**

- Backend: Formelauswertung mit sicherer Evaluierung (z. B. `asteval`/Whitelist)
- Speicher: `user_custom_columns` (user_id, name, formula_json)
- Frontend: Editor mit Autocomplete verfügbarer Felder

---

## �🔐 Phase 14 - Backend & Infrastruktur

### 14.1 Caching & Performance
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟢 Niedrig

**Optimierungen:**
- **Redis Cache:**
  - Cache API Responses (15 Min TTL)
  - Cache Calculated Metrics (1 Hour TTL)
  - Session Storage
  
- **Websockets:**
  - Real-time Price Updates
  - Live Alert Notifications
  - Collaborative Features
  
- **Background Jobs:**
  - Celery + Redis
  - Daily Data Updates (nachts um 2 Uhr)
  - Alert Checking (alle 15 Min)
  - ML Model Retraining (wöchentlich)
  
- **Database Optimization:**
  - Indices auf häufig genutzte Spalten
  - Materialized Views für komplexe Queries
  - Connection Pooling

**Technische Details:**
- Redis: In-memory Cache
- Celery: Distributed Task Queue
- Websockets: FastAPI WebSocket Support
- Monitoring: Prometheus + Grafana

---

### 14.2 User Authentication
**Schwierigkeit:** ⭐⭐⭐⭐ Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🟢 Niedrig

**Features:**
- **Login/Registrierung:**
  - Email + Password
  - OAuth (Google, GitHub)
  - 2FA (Two-Factor Authentication)
  
- **User Management:**
  - Profile Settings
  - Password Reset
  - Email Verification
  
- **Persönliche Daten:**
  - Private Watchlists pro User
  - Private Portfolios
  - Private Alerts
  - Saved Screens
  
- **Cloud-Sync:**
  - Data Sync zwischen Geräten
  - Backup & Restore

**Technische Details:**
- JWT (JSON Web Tokens) für Auth
- Libraries: FastAPI Users oder Authlib
- OAuth: Google/GitHub APIs
- 2FA: TOTP (pyotp)
- Neue Tabellen: `users`, `user_sessions`

---

### 14.3 API Rate Limiting & Security
**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**
- Rate Limiting (100 requests/min per User)
- API Key Management
- CORS Configuration
- Input Validation & Sanitization
- SQL Injection Protection
- XSS Prevention
- HTTPS Only
- Logging & Monitoring

**Technische Details:**
- Rate Limiting: slowapi
- Security Headers: FastAPI Middleware
- Logging: structlog + ELK Stack

---

### 14.4 Feature Flags & Rollouts

**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**

- Staged Rollouts, A/B-Tests, Canary Releases für neue Indikatoren/Alerts

**Technische Details:**

- Simple: Feature-Flags in DB + Cache; Advanced: Integration LaunchDarkly/Unleash (optional)

---

### 14.5 Monitoring & Telemetry

**Schwierigkeit:** ⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**

- Live-Metriken für Latenz, Fehlerquote, API-Throughput
- Alerting bei Slowness/Fehler-Spikes

**Technische Details:**

- Prometheus-Exporter, Grafana-Dashboards, Sentry für FE/BE

---

## 🧠 Phase 15 - Smart-Watchlists (regelbasiert)

**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐⭐ Sehr hoch  
**Priorität:** 🔴 Hoch

**Features:**

- Automatische Mitgliedschaft basierend auf Regeln (z. B. RSI<30 UND Vol>1.5x)
- Live-Refresh oder tägliche Aktualisierung
- "Screen zu Smart-Watchlist umwandeln" (Bridge zu Phase 9)

**Technische Details:**

- Neue Tabelle: `smart_watchlists` (id, user_id, name, filter_json, refresh_policy)
- Backend: Wiederverwendung `screener_service.py` Query-Builder; Scheduler-Job zur Aktualisierung
- Endpoints: `GET/POST/PUT /smart-watchlists`, `POST /smart-watchlists/{id}/refresh`
- Frontend: Rule-Builder UI (Re-Use vom Screener), Toggle "Auto-Update"

---

## 📅 Phase 16 - Earnings/Dividends/Splits Kalender

**Schwierigkeit:** ⭐⭐⭐ Mittel  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟡 Mittel

**Features:**

- Badges in Watchlist: "Earnings in D-5", Dividendendatum, Split-Historie
- Kalender-/Timeline-Ansicht je Ticker und global

**Technische Details:**

- Datenquellen: yfinance Kalender/Dividenden (sofern verfügbar), sonst optionale APIs
- Tabelle: `corporate_actions` (stock_id, type, date, meta_json)
- Caching: 24h TTL; UI-Badges + Filter in Watchlist

---

## ⚙️ Phase 17 - Options-Volatilität (IV/IVR, Light)

**Schwierigkeit:** ⭐⭐⭐ Mittel-Schwer  
**Nutzen:** ⭐⭐⭐⭐ Hoch  
**Priorität:** 🟢 Niedrig

**Features:**

- IV/IVR-Anzeige (Kontext für Squeeze/Breakout-Strategien)
- Kachel "Ungewöhnliches Optionsvolumen" (basic)

**Technische Details:**

- Datenquellen abhängig von Verfügbarkeit (optional, hinter Feature-Flag 14.4)
- Frontend: Kompakte Tiles und Spalten in Watchlist

## 🎯 Prioritäts-Matrix

### 🔴 Hohe Priorität (Next Steps)
1. **Smart-Watchlists** (Phase 15)
   - Regelbasierte, auto-aktualisierte Watchlists
   - Brücke zum Screener, hoher Nutzen
   - **Status:** 🎯 Hoch

4. **Portfolio Management** (Phase 8.1, 8.2, 8.3)
   - Macht App von Watchlist zu Portfolio-Tracker
   - Unique Value Proposition
   - User Retention
   - **Status:** 🔜 Nach technischen Indikatoren

5. **Multi-Condition Alerts** (Phase 7.1)
   - Erweitert bestehende Alert-Funktionalität
   - Sehr nützlich für aktive Trader
   - **Status:** 🔜 Q2 2025

6. **Alert-Erweiterungen** (7.6–7.9)
   - Trailing, ROC, Zeitfenster, Kanäle/Webhooks
   - **Status:** 🔜 Nach 7.1

## 🎯 Aktualisierte Prioritäts-Matrix (Stand 21.11.2025)

### 🔴 Hohe Priorität (Q4 2025 – Q1 2026)
1. Portfolio Management (Phase 8) – Schema, Transaktionen, Performance
2. Erweiterte Multi-Condition Alerts – ODER / Nested Chains, Template Library
3. Smart-Watchlists (Phase 15) – Regel-Engine + Auto-Refresh
4. Infrastruktur Basis – Auth (Grundlage), Redis Cache, erste Background Jobs
5. Alert-Erweiterungen – Follow-Trailing, ROC, Zeitfenster, Kanäle/Webhooks

### 🟡 Mittlere Priorität
- Screener Ausbau (technische Filter + Saved Screens)
- News Integration (Phase 11.1)
- Pattern-Based Alerts (Candlestick) nach Grundmodulen
- Export Funktionen (PDF/Excel/SVG)
- Mobile Responsiveness / PWA
- Custom Columns Builder
- Earnings / Corporate Actions Kalender
- Historical Divergence Tracking (Persistenz)
- Relative Strength Rotation (RRG-Light)

### 🟢 Niedrige Priorität
- Divergence Success Rate Evaluation
- Sentiment Analysis
- Options-Volatilität / IV Tiles
- Anomalie-Erkennung / ML
- Feature Flags & A/B Tests
- Kollaboration / Teilen

---

## 📝 Aktualisierte Implementierungs-Roadmap (Nov 2025 → Q1/Q2 2026)

### Q4 2025 (laufend)
Fokus: Fundament & Architektur
- Portfolio: Datenmodell, Service-Skelett, Basis-Endpoints
- Alerts: OR-Gruppierungen & Template-Struktur designen
- Smart-Watchlists: Regelformat (JSON) + Scheduler-Konzept
- Konsolidierung Indikator-/Alert-Code (Dupes reduzieren)

### Q1 2026
Fokus: Nutzwert-Erweiterung
- Portfolio Transaktionen (FIFO/Average Cost), Performance-Metriken, erste Charts
- Alert Condition Builder (UI + Persistenz) mit Template Library
- Smart-Watchlists Auto-Refresh + UI Builder (Reuse Screener)
- Redis Cache (Metrics & Screener Facets)
- Basis Auth (JWT, User Tabelle) falls nicht gestartet

### Q2 2026
Fokus: Kontext & Distribution
- News Feed Integration + Caching
- Alert-Kanäle (E-Mail/Webhook MVP) + Throttling & De-Dupe
- Export (PDF/Excel/SVG) & Chart Snapshot
- Earnings / Corporate Actions Basis
- Relative Strength Rotation (RRG-Light)

### Nachgelagert
- Candlestick Pattern Recognition & Pattern-Based Alerts
- Historical Divergence Storage + Success Rate
- Sentiment / ML Anomalie-Erkennung
- Options IV / Volumen Specials
- Feature Flags / A/B Testing

### Evaluierungskriterien
User Impact • Entwicklungsaufwand • Dependencies • Technical Debt • Markt-Relevanz


## 💡 Technologie-Stack Erweiterungen

### Zu Erwägen:
- **Redis:** Caching & Session Storage
- **Celery:** Background Task Queue
- **WebSockets:** Real-time Updates
- **Docker:** Containerization für Deployment
- **Nginx:** Reverse Proxy & Load Balancing
- **GitHub Actions:** CI/CD Pipeline
- **Sentry:** Error Tracking & Monitoring
- **Stripe:** Payment Processing (wenn Premium Features)

---

## 📚 Nächste Schritte

### Mittelfristig (Nächste 4-6 Wochen)

### Langfristig (Q2 2025)
6. **Portfolio Management Vorbereitung**
   - Database Schema Design
   - API Architecture Planning
   - UI/UX Mockups
   - User Stories & Requirements

7. **Multi-Condition Alerts Konzept**
   - Alert Engine Architecture
   - Condition Builder UI Design
   - JSON Schema für Conditions

### Ongoing (Kontinuierlich) 🔄
- **User Feedback sammeln:** Welche Indikatoren werden am meisten genutzt?
- **Performance Monitoring:** Chart Loading Times, API Response Times
- **Bug Fixes:** Issues aus GitHub/User Reports
- **Dokumentation:** API Docs, User Guides aktualisieren
- **Code Quality:** Refactoring, Tests, Code Reviews

---

## 🎓 Learning Resources

### Für aktuelle Features (RSI, MACD, Volume Profile, Ichimoku):
- **Investopedia:** Technical Analysis Guides
- **TA-Lib Documentation:** Python Technical Analysis Library

### Für zukünftige Features:
- **Portfolio Management:** Modern Portfolio Theory, Sharpe Ratio
- **Machine Learning:** scikit-learn, TensorFlow für Predictions
- **Real-time Data:** WebSockets, Redis Pub/Sub
- **Mobile Development:** React Native oder PWA Best Practices

---

## 💡 Entscheidungs-Kriterien für Feature-Priorisierung

Bei der Auswahl des nächsten Features berücksichtigen:

1. **User Impact:** Wie viele Nutzer profitieren davon?
2. **Effort vs. Value:** ROI des Features
3. **Dependencies:** Welche Features sind Voraussetzung?
4. **Market Trends:** Was nutzen professionelle Trader?
5. **Technical Debt:** Muss bestehender Code refactored werden?
6. **Learning Opportunity:** Neue Skills für dich als Developer?

**Aktueller Fokus:** Technical Indicators (RSI, MACD, Volume Profile, Ichimoku) haben:
- ✅ Hohen User Impact (Standard Tools)
- ✅ Gutes Effort/Value Ratio (Libraries verfügbar)
- ✅ Keine großen Dependencies (nur Chart Integration)
- ✅ Hohes Market Interest (jeder Trader nutzt sie)
- ✅ Geringer Technical Debt (saubere Erweiterung)

---

**Stand:** 21.11.2025 (Analyse & Status konsolidiert)  
**Version:** 2.3  
**Letztes Update:** Implementierungsstatus, Prioritäts-Matrix & Roadmap erneuert  
**Nächstes Review:** Anfang Februar 2026

---

## 📝 Change Log

### 2025-10-09 (v2.1)
- ✅ Volume Profile Overlay implementiert
- ✅ Backend period_days Limit erhöht (365 → 3650 Tage)
- ✅ Render-Loop Bugs behoben
- 🔧 Kalibrierungs-System für Overlay-Ausrichtung hinzugefügt
- 📌 Pending: Feintuning der vertikalen Ausrichtung

### 2025-10-10 (v2.2)
- ➕ Neue Alert-Typen: Trailing, ROC, Zeitfenster, Kanäle/Webhooks (7.6–7.9)
- ➕ Smart-Watchlists (Phase 15) geplant inkl. Backend/Frontend-Spezifikation
- ➕ Watchlist-UX: Notizen/Tags, Heatmap, Custom Columns (13.4–13.6)
- ➕ Seasonality & Relative Strength (12.4); Monitoring & Feature-Flags (14.4–14.5)

### 2024-10-08 (v2.0)
- Initial feature planning document created
- RSI, MACD, Volume Profile features defined
- Alert system expanded
- Divergence detection planned
