# Integration von Indizes

## Plan

### Multi-Asset Index-Analyse mit wiederverwendbarer Infrastruktur

Ihre Stock-Watchlist wird um Marktindizes (Haupt- + Sektor-Indizes) erweitert zur Benchmark-Analyse. Maximale Code-Wiederverwendung durch Nutzung existierender Services (HistoricalPriceService, ChartDataService, yfinance-Integration). Neue Unterordner backend/app/services/indices/ und frontend/src/components/indices/ für saubere Trennung. CSV-basiertes Constituent-Management mit Status-Historie (nur bei tatsächlichen Änderungen). Index-Berechnungsmethodik als Metadaten erfasst.

## Steps

### Backend

- Index-Ordnerstruktur & erweiterte Datenmodelle — Ordner backend/app/services/indices/ mit: __init__.py; Neue Tabellen in __init__.py: (1) market_indices (id, ticker_symbol unique, name, region [US/EU/ASIA/LATIN], index_type [broad/sector], calculation_method [market_cap_weighted/price_weighted/equal_weighted], constituents_count, base_currency, benchmark_index VARCHAR nullable für Sektor-Indizes, description, created_at, updated_at), (2) index_constituents (id, index_id FK, stock_id FK, weight DECIMAL(8,4), status ENUM [active/inactive], date_added DATE, date_removed DATE nullable, reason_removed VARCHAR nullable, created_at) mit Unique-Constraint auf (index_id, stock_id) WHERE status='active';

- Zentralisierte Service-Nutzung — backend/app/services/indices/index_data_service.py nutzt bestehende HistoricalPriceService (nicht neu implementieren!): Klasse IndexDataService(db) mit Methoden: create_index(ticker_symbol, name, region, index_type, calculation_method) -> MarketIndex, fetch_and_store_prices(index_id, period='max') ruft intern HistoricalPriceService(db).load_and_save_historical_prices() auf; get_index_by_symbol(symbol) -> MarketIndex; update_recent_prices(index_id) nutzt HistoricalPriceService.update_recent_prices(); Wiederverwendung auch von ChartDataService für Index-Charts (funktioniert bereits, da ticker-basiert)

- Constituent-Management-Service — backend/app/services/indices/constituent_service.py: import_constituents_from_csv(index_id, csv_file_path) liest CSV (Spalten: ticker_symbol, name, weight, date_added), prüft gegen DB: wenn Ticker neu → füge hinzu mit status=active; wenn existierender Ticker NICHT in CSV → setze status=inactive + date_removed=today + reason_removed="Removed from index"; wenn existierender Ticker MIT Weight-Änderung → update weight; get_active_constituents(index_id, as_of_date=None) -> List[Constituent] (optional historisch); get_constituent_changes(index_id, start_date, end_date) -> List[ChangeEvent] für Historie

- Vergleichs-Services (Beta & Korrelation) — backend/app/services/indices/comparison_service.py: calculate_beta(stock_id, index_id, period_days=252) holt Preise via HistoricalPriceService.get_price_dataframe() für beide, berechnet Returns, nutzt numpy.cov() und numpy.var(); calculate_correlation(asset1_id, asset2_id, period_days=252, asset1_type='stock', asset2_type='index') nutzt pandas.DataFrame.corr(); calculate_relative_strength(stock_id, index_id, start_date) normalisiert beide auf 100; get_correlation_matrix(index_ids: List[int], period_days=252) gibt DataFrame zurück; Wiederverwendung von time_series_utils.py (falls vorhanden) für gemeinsame Berechnungen

- Market-Breadth-Service — backend/app/services/indices/market_breadth_service.py: calculate_advance_decline(index_id, date=today) holt alle active constituents, prüft für jeden: latest_price > sma_200 (nutzt CalculatedMetricsService wenn möglich ODER berechnet SMA direkt via Pandas), gibt {advancing: 250, declining: 240, unchanged: 10, percentage_advancing: 51.0} zurück; get_new_highs_lows(index_id, date=today) prüft close == 52w_high bzw. 52w_low; calculate_mcclellan_oscillator(index_id, days=90) nutzt historische A/D-Daten

- API-Endpoints & Schemas — backend/app/routes/index_routes.py registriert via app.include_router(index_routes.router) in main.py: GET /api/indices/?region=US&type=broad&include_constituents=false (Liste), POST /api/indices/ (Admin: Neuer Index mit Body: {ticker_symbol, name, region, type, calculation_method}), GET /api/indices/{symbol} (Details inkl. calculation_method), GET /api/indices/{symbol}/chart?period=1y&interval=1d&indicators=sma50,sma200 (nutzt ChartDataService direkt!), GET /api/indices/{symbol}/constituents?status=active, POST /api/indices/{symbol}/constituents/import (CSV-Upload via UploadFile), GET /api/indices/correlation-matrix?symbols=^GSPC,^IXIC,^GDAXI&period=1y, GET /api/stocks/{stock_id}/benchmark-comparison?index_symbol=^GSPC&period=1y gibt {beta, correlation, relative_performance, drawdown_comparison}; Schemas in schemas.py

- API-Quota-Manager (In-Memory) — backend/app/services/api_quota_manager.py OHNE Redis (einfacher für Start): Klasse QuotaManager mit In-Memory-Dict [_usage: Dict[str, Dict[str, int]] = {}](http://vscodecontentref/35) (Struktur: {provider: {date: count}}), Methoden: check_and_increment(provider: str, daily_limit: int) -> bool prüft _usage[provider][today] < daily_limit, get_usage(provider: str) -> int, reset_if_new_day() (checked bei jedem Call); Thread-safe via threading.Lock(); Decorator @rate_limited(provider='alpha_vantage', limit=500) für Service-Methoden; Endpoint GET /api/quota/status zeigt {alpha_vantage: {used: 120, limit: 500, remaining: 380}} — Redis später optional für Multi-Instance-Deployments

### Frontend

- Index-Ordnerstruktur — frontend/src/components/indices/ mit: (IndexOverview.js, IndexCard.js, IndexList.js, IndexComparisonChart.js, CorrelationHeatmap.js, MarketBreadthDashboard.js, ConstituentTable.js, BenchmarkSelector.js), frontend/src/hooks/ (useIndices.js, useIndexChart.js, useCorrelationMatrix.js, useBenchmarkComparison.js basiert auf useApiQuery), frontend/src/utils/ (indexFormatters.js); Route /indices in App.js mit Subroutes /indices (Overview), /indices/:symbol (Detail), /indices/comparison, /indices/breadth

- Index-Navigation & Overview mit Sektor-Indizes — Neue Hauptnavigation "Market Indices"; IndexOverview.js: Tab-Navigation "Main Indices" | "Sector Indices", Grid-Layout mit IndexCard zeigt: Name, aktueller Stand, Änderung (1D/5D/1M/YTD), Sparkline (nutzt existierende Watchlist-Komponente!), Click → Detail-Seite; Haupt-Indizes: S&P 500 (^GSPC), Nasdaq 100 (^NDX), Dow Jones (^DJI), DAX 40 (^GDAXI), MDAX (^MDAXI), SDAX (^SDAXI), Euro Stoxx 50 (^STOXX50E), Euro Stoxx 600 (^STOXX), Nikkei 225 (^N225), Hang Seng (^HSI); Sektor-Indizes: S&P 500 Sectors via SPDR ETFs (XLK Tech, XLF Finance, XLE Energy, XLV Health, XLY Consumer Discr., XLP Consumer Staples, XLI Industrial, XLB Materials, XLRE Real Estate, XLU Utilities, XLC Communication) — alle sofort implementiert

- Vergleichs- & Analyse-Dashboards — IndexComparisonChart.js: Multi-Select-Dropdown (max 5 Indizes), Zeitraum-Buttons, Recharts LineChart mit normalisierter Basis 100, Toggle "Absolute Values" zeigt zweite Y-Achse; CorrelationHeatmap.js: Custom SVG-Grid (alternativ: Recharts Heatmap via ScatterChart + custom cells), Farbskala mit Gradient (-1 rot → 0 weiß → +1 grün), Hover-Tooltip; MarketBreadthDashboard.js: Grid mit 3 Cards: (1) Advance/Decline-Line (Recharts AreaChart, kumuliert über Zeit), (2) Current A/D Ratio (Gauge-Chart oder Radial Bar mit Prozent), (3) New Highs vs. Lows (Recharts BarChart, täglich letzte 30 Tage)

- Stock-Detail Market-Context-Integration — In StockDetails.js neuer Tab "Market Context": BenchmarkSelector (Auto-detect via stock.country: DE→DAX, US→S&P500, manual Override-Dropdown), RelativePerformanceChart (beide Assets normalisiert 100, Zeitraum-Picker 1Y/3Y/5Y), Metriken-Grid: Beta (mit Interpretation: <0.8 "Low", 0.8-1.2 "Market", >1.2 "High Volatility"), Correlation (mit Strength: >0.7 "Strong", 0.3-0.7 "Moderate", <0.3 "Weak"), Outperformance (% Differenz, grün/rot Badge), Max Drawdown-Vergleich (Side-by-Side Bars); Hook useBenchmarkComparison cached via React-Query (staleTime: 1 Stunde)

- CSV-Daten & Initiale Index-Befüllung — Ordner data/index_constituents/ mit manuelle CSVs: sp500.csv, dax40.csv, nasdaq100.csv (Struktur: ticker_symbol,name,weight,date_added); Python-Script backend/app/scripts/seed_indices.py erstellt alle Indizes + importiert CSVs, lädt historische Preise via IndexDataService.fetch_and_store_prices(period='max'); Keine Automatisierung, manuelle CSV-Updates bei Bedarf (z.B. quartalsweise)

## Further Considerations

### Calculation Method Beispiele

Market-Cap-Weighted (S&P 500, DAX, Nasdaq): Größere Unternehmen haben mehr Einfluss, Formel: weight_i = market_cap_i / sum(all_market_caps)
Price-Weighted (Dow Jones): Teurere Aktien dominieren, Formel: index = sum(all_prices) / divisor
Equal-Weighted (S&P 500 Equal Weight): Jede Aktie 1/500 Gewicht, periodisches Rebalancing
Free-Float-Adjusted (Euro Stoxx 50): Nur handelbare Aktien gezählt
→ Gespeichert in calculation_method-Spalte zur Transparenz, aber nicht selbst berechnet (yfinance liefert Index-Stand direkt)
Constituent Status-Update nur bei Änderungen: CSV-Import prüft Diff: current_db_tickers = {c.stock.ticker_symbol for c in active_constituents}, csv_tickers = set(csv_data['ticker_symbol']), removed = current_db_tickers - csv_tickers → nur diese auf inactive setzen. Verhindert unnötige DB-Writes bei unveränderter CSV.

### Code-Wiederverwendung Details

HistoricalPriceService funktioniert identisch für Indizes (yfinance behandelt ^GSPC wie Stock-Ticker)
ChartDataService.get_chart_data() benötigt nur ticker_symbol → direkt nutzbar
CalculatedMetricsService enthält SMA-Berechnungen → wiederverwendbar für Market Breadth
useApiQuery Hook im Frontend → wiederverwendbar für alle Index-Endpoints

### Alternative Datenquellen-Integration (später)

Services vorbereitet in backend/app/services/external_apis/ (alpha_vantage_service.py, twelve_data_service.py), zunächst NICHT implementiert (yfinance genügt für zunächst), bei Bedarf via Fallback-Pattern: try: yfinance → except: twelve_data. Quota-Manager tracked Aufrufe pro Provider.

### Sektor-Index Calculation Method

SPDR-ETFs (XLK, XLF, etc.) sind Market-Cap-Weighted innerhalb des Sektors, speichern als calculation_method='market_cap_weighted', benchmark_index='^GSPC' (Sektor relativ zu S&P 500). Ermöglicht später Relative-Rotation-Graphs via Benchmark-Referenz.

### Performance bei 65 Indizes (Haupt + Sektor) (später)

Tägliches Update via Cron (4 AM UTC) ruft IndexDataService.update_recent_prices(index_id) für alle, nutzt yfinance 1 Req/Sec Throttling (time.sleep(1) in Loop) → 65 Sekunden Gesamtdauer. On-Demand-Charts nutzen 15-Min-Cache via ChartDataService (bereits implementiert). Frontend-Queries via React-Query mit staleTime: 15*60*1000.
