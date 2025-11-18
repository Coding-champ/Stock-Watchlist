# Indices Integration - Noch offene Punkte

Stand: 18.11.2025

## Bereits implementiert ✅

- ✅ Backend-Ordnerstruktur (`backend/app/services/indices/`)
- ✅ Datenmodelle (`MarketIndex`, `IndexConstituent`)
- ✅ Index Data Service (Preisdaten via `AssetPriceService`)
- ✅ Constituent Management Service
- ✅ API-Endpoints:
  - GET `/indices/` (Liste)
  - GET `/indices/{ticker}` (Details)
  - GET `/indices/{ticker}/constituents` (Bestandteile)
  - GET `/indices/{ticker}/statistics` (umfangreiche Statistiken)
  - GET `/indices/{ticker}/sector-breakdown` (Sektoranalyse)
- ✅ Frontend-Ordnerstruktur (`frontend/src/components/`)
- ✅ Index-Overview-Seite mit Grid-Layout nach Regionen gruppiert
- ✅ Index-Detail-Seite mit Chart, Statistiken & Bestandteilen
- ✅ Benchmark-Vergleich (Outperformance-Visualisierung im Chart)
- ✅ Sektor-Analyse mit PieChart, BarChart & Tabelle
- ✅ Navigation "Indizes" in Hauptmenü integriert

## Noch offen ❌

### 1. Correlation Matrix
**Beschreibung:** Heatmap zur Visualisierung der Korrelationen zwischen mehreren Indizes

**Backend:**
- Service `backend/app/services/indices/comparison_service.py`:
  - `calculate_correlation(asset1_id, asset2_id, period_days=252, asset1_type='stock', asset2_type='index')`
    - Nutzt `AssetPriceService.get_price_dataframe()` für beide Assets
    - Berechnet Returns via pandas
    - Nutzt `pandas.DataFrame.corr()` für Korrelation
  - `get_correlation_matrix(index_ids: List[int], period_days=252)`
    - Gibt DataFrame mit allen Korrelationen zurück
- Endpoint: GET `/api/indices/correlation-matrix?symbols=^GSPC,^IXIC,^GDAXI&period=1y`

**Frontend:**
- Component `frontend/src/components/CorrelationHeatmap.js`:
  - Custom SVG-Grid ODER Recharts Heatmap (via ScatterChart)
  - Farbskala: Gradient -1 (rot) → 0 (weiß) → +1 (grün)
  - Hover-Tooltip mit Werten
- Hook `frontend/src/hooks/useCorrelationMatrix.js`
- Integration in neue Route `/indices/correlation` oder als Tab in IndexOverview

---

### 2. Market Breadth Dashboard
**Beschreibung:** Analyse der Marktbreite (Advance/Decline, New Highs/Lows)

**Backend:**
- Service `backend/app/services/indices/market_breadth_service.py`:
  - `calculate_advance_decline(index_id, date=today)`
    - Holt alle active constituents
    - Prüft für jeden: `latest_price > sma_200`
    - Returns: `{advancing: 250, declining: 240, unchanged: 10, percentage_advancing: 51.0}`
  - `get_new_highs_lows(index_id, date=today)`
    - Prüft: `close == 52w_high` bzw. `52w_low`
  - `calculate_mcclellan_oscillator(index_id, days=90)` (optional)
    - Nutzt historische A/D-Daten
- Endpoints:
  - GET `/api/indices/{symbol}/breadth?date=2025-11-18`
  - GET `/api/indices/{symbol}/breadth/history?days=30`

**Frontend:**
- Component `frontend/src/components/MarketBreadthDashboard.js`:
  - Grid mit 3 Cards:
    1. **Advance/Decline-Line**: Recharts AreaChart (kumuliert über Zeit)
    2. **Current A/D Ratio**: Gauge-Chart oder Radial Bar (Prozent)
    3. **New Highs vs. Lows**: Recharts BarChart (letzte 30 Tage)
- Hook `frontend/src/hooks/useMarketBreadth.js`
- Integration als Tab in IndexDetailPage oder eigene Route `/indices/breadth`

---

### 3. Stock Market Context Integration (Beta & Correlation)
**Beschreibung:** Beta und Korrelation eines Stocks zu einem Benchmark-Index

**Backend:**
- Service `backend/app/services/indices/comparison_service.py`:
  - `calculate_beta(stock_id, index_id, period_days=252)`
    - Holt Preise via `AssetPriceService.get_price_dataframe()` für beide
    - Berechnet Returns (daily % change)
    - Beta = `numpy.cov(stock_returns, index_returns)[0,1] / numpy.var(index_returns)`
  - `calculate_relative_strength(stock_id, index_id, start_date)`
    - Normalisiert beide auf 100 am start_date
- Endpoint: GET `/api/stocks/{stock_id}/benchmark-comparison?index_symbol=^GSPC&period=1y`
  - Returns: `{beta, correlation, relative_performance, drawdown_comparison}`

**Frontend:**
- Integration in `StockDetails.js` (neuer Tab "Market Context"):
  - **BenchmarkSelector**: Auto-detect via `stock.country` (DE→DAX, US→S&P500) + Manual Override
  - **RelativePerformanceChart**: Beide Assets normalisiert auf 100, Zeitraum-Picker
  - **Metriken-Grid**:
    - Beta (mit Interpretation: <0.8 "Low", 0.8-1.2 "Market", >1.2 "High Volatility")
    - Correlation (mit Strength: >0.7 "Strong", 0.3-0.7 "Moderate", <0.3 "Weak")
    - Outperformance (% Differenz, grün/rot Badge)
    - Max Drawdown-Vergleich (Side-by-Side Bars)
- Hook `frontend/src/hooks/useBenchmarkComparison.js`
  - React-Query mit `staleTime: 1 Stunde`

---

## Technische Details

### Code-Wiederverwendung
- `AssetPriceService` funktioniert identisch für Indizes (yfinance behandelt `^GSPC` wie Stock-Ticker)
- `ChartDataService.get_chart_data()` benötigt nur `ticker_symbol` → direkt nutzbar
- Bestehende Recharts-Komponenten wiederverwendbar

### Formeln
- **Beta**: `cov(stock_returns, index_returns) / var(index_returns)`
- **Correlation**: `pandas.DataFrame.corr()` zwischen Returns
- **Relative Strength**: Beide auf 100 normalisieren am Start-Datum

### Performance-Hinweise
- Market Breadth für große Indizes (S&P 500): ~500 Abfragen → Caching wichtig
- Korrelationsmatrix: N×N Berechnungen → Backend-seitig cachen (Redis später)
- Beta-Berechnungen: 252 Tage (1 Jahr Trading Days) als Default

---

## Prioritäten-Vorschlag

1. **Stock Market Context** (Beta & Correlation) - direkt nützlich für Stock-Analyse
2. **Correlation Matrix** - gute Übersicht über Index-Beziehungen
3. **Market Breadth** - fortgeschrittenes Feature, optional

---

## Notizen
- Alle Features nutzen bestehende Infrastruktur (AssetPriceService, Recharts)
- Keine neuen Dependencies nötig
- Backend-Services folgen bestehendem Pattern (Service-Klassen mit DB-Session)
