# Indices Integration – Status & Nächste Schritte

Stand: 20.11.2025

## Bereits implementiert ✅

- ✅ Backend-Ordnerstruktur (`backend/app/services/indices/`)
- ✅ Datenmodelle (`MarketIndex`, `IndexConstituent`)
- ✅ Index Data Service (Preisdaten via `AssetPriceService`)
- ✅ Constituent Management Service
- ✅ API-Endpoints Kern:
  - GET `/indices/` (Liste)
  - GET `/indices/{ticker}` (Details)
  - GET `/indices/{ticker}/constituents` (Bestandteile)
  - GET `/indices/{ticker}/statistics` (umfangreiche Statistiken)
  - GET `/indices/{ticker}/sector-breakdown` (Sektoranalyse)
- ✅ Frontend-Ordnerstruktur (`frontend/src/components/`)
- ✅ Index-Overview mit Regionen-Gruppierung
- ✅ Index-Detail-Seite (Chart + Stats + Constituents)
- ✅ Benchmark-Vergleich (Stock Market Context Tab in `StockDetailPage` – Beta, Korrelation, Relative Performance, Drawdowns)
- ✅ Sektor-Analyse (PieChart, BarChart & Tabelle)
- ✅ Navigation "Indizes" im Hauptmenü
- ✅ Korrelationsmatrix:
  - Backend: `ComparisonService.get_correlation_matrix` + Endpoint `GET /indices/correlation-matrix`
  - Frontend: `CorrelationHeatmap` Komponente + Navigationseintrag "Korrelationen"
- ✅ Market Breadth:
  - Backend: `MarketBreadthService` (Advance/Decline, New Highs/Lows, History, McClellan Oscillator)
  - Endpoints: `GET /indices/{symbol}/breadth`, `GET /indices/{symbol}/breadth/history`
  - Frontend: Integration direkt im Indizes-Overview (kein eigener Tab) via `MarketBreadthDashboard` mit:
    - Kumulative A/D-Linie (konfigurierbare Tage 30/60/90)
    - Aktuelles A/D Verhältnis (Radial Gauge)
    - Multi-Day neue Hochs vs. Tiefs (Stacked Bar, tägliche History)
- ✅ Multi-Day Erweiterung: tägliche `new_highs`/`new_lows` in History integriert
- ✅ Days Selector für Market Breadth (30/60/90)
- ✅ Tops/Flops des Tages:
  - Backend: `IndexService.get_index_top_flops` – berechnet Tages-Gewinner/-Verlierer basierend auf täglicher %-Veränderung
  - Endpoint: `GET /indices/{ticker_symbol}/top-flops?limit=5`
  - Frontend: `TopFlopsPanel` Komponente mit zweispaltiger Darstellung (Top 5 / Flop 5)
  - Features: Pill-Indikatoren (↑/↓), Sektor-Badges, Card-Shadows, Hover-Effekte, Shimmer Loading Skeleton
  - Integration: Index-Detail-Seite zwischen "Performance & Risiko-Statistiken" und "Marktbreite"

## Optional / Verbesserungen 🔧

1. Cache-Layer (Redis) für:
   - Korrelationsmatrix Ergebnisse (period + symbol set Key)
   - Market Breadth History (index + days)
2. Performance-Optimierung: Batch-Queries für große Indizes (S&P 500) – aktuell pro Stock individuelle Abfragen.
3. Erweiterte Visualisierung:
   - Ratio-Line (new_highs - new_lows) oder (new_highs / new_lows) zur Trend-Identifikation
   - Glättung (EMA 7 / 10) über A/D-Linie
4. Export-Funktion (CSV/PNG) für Korrelationsmatrix & Breadth Charts
5. Tooltip-Verfeinerung (Zusatz: Beta-Klassifikationstext, Korrelation-Stärke im Heatmap-Hover)
6. Optionaler Tab "Breadth" in Index-Detail-Seite (falls vertiefte Einzelanalyse gewünscht)
7. Watchlist-Favoriten für Indizes (Schnellzugriff auf spezifische Benchmarks)

## Erledigte ursprüngliche "Noch offen" Punkte ✅

Alle drei initialen Featureblöcke (Korrelationsmatrix, Market Breadth Dashboard, Stock Market Context) sind vollständig umgesetzt und erweitert (Multi-Day High/Low History + Days Selector).

## Aktueller Fokus / Nächste sinnvolle Schritte ▶️

Priorität jetzt eher auf: Stabilität & Performance

1. Caching implementieren (Korrelationsmatrix + Breadth History)
2. Query-Optimierung für sehr große Indizes
3. Kleine UI-Verfeinerungen (Ratio-Line, Export)
4. Evtl. Dokumentation ergänzen (README Abschnitt "Market Breadth" & "Correlation")

## Technische Zusammenfassung

- Wiederverwendung: `AssetPriceService`, einheitliche Preis-Datenhaltung
- Recharts für alle Visualisierungen (Line, Area, Bar, RadialBar)
- Daily Returns → Korrelation via pandas `.corr()`
- Beta: `cov(stock_returns, index_returns) / var(index_returns)`
- Relative Performance: Normalisierung erster gemeinsamer Tag = 100
- Breadth SMA200: arithmetischer Durchschnitt der letzten ≤200 Schlusskurse (Fallback bei <200 Datenpunkten)
- 52W High/Low Approx: Rolling 252-Tage Fenster
- McClellan: EMA19 & EMA39 Differenz auf (Adv - Dec)

## Notizen

- Keine neuen externen Dependencies nötig
- Muster der bestehenden Service-Klassen eingehalten
- Erweiterungen modular (eigene Services / Hooks / Komponenten)
- Frontend integriert zusätzliche Analysen ohne Navigationsüberfrachtung
