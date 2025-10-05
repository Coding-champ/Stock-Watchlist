# 🚀 Database Refactoring - ToDo Liste

## Ziel
Umstrukturierung der Datenbank für historische Kursdaten und Fundamentaldaten mit Beibehaltung der API-Kompatibilität für das Frontend.

---

## ✅ Phase 1: Analyse & Planung
- [x] Anforderungen klären
- [x] Datenstruktur definieren
- [x] ToDo-Liste erstellen
- [ ] Bestehende Models analysieren

---

## 📊 Phase 2: Neue Database Models erstellen

### 2.1 Stock Model (Stammdaten) - ANPASSEN
- [ ] `wkn` Feld hinzufügen
- [ ] `business_summary` Feld hinzufügen
- [ ] `watchlist_id` entfernen
- [ ] `position` entfernen
- [ ] `observation_reasons` entfernen
- [ ] `observation_notes` entfernen
- [ ] Beziehung zu `stocks_in_watchlist` hinzufügen

### 2.2 StockInWatchlist Model - NEU ERSTELLEN
- [ ] `id` (Primary Key)
- [ ] `watchlist_id` (Foreign Key)
- [ ] `stock_id` (Foreign Key)
- [ ] `position` (Integer)
- [ ] `exchange` (String)
- [ ] `currency` (String)
- [ ] `observation_reasons` (JSON/Array)
- [ ] `observation_notes` (Text)
- [ ] `created_at` (DateTime)
- [ ] `updated_at` (DateTime)
- [ ] UNIQUE Constraint (watchlist_id, stock_id)
- [ ] Beziehungen definieren

### 2.3 StockPriceData Model - NEU ERSTELLEN
- [ ] `id` (Primary Key)
- [ ] `stock_id` (Foreign Key)
- [ ] `date` (Date)
- [ ] `open` (Float)
- [ ] `high` (Float)
- [ ] `low` (Float)
- [ ] `close` (Float)
- [ ] `volume` (BigInteger)
- [ ] `adjusted_close` (Float)
- [ ] `dividends` (Float, nullable)
- [ ] `stock_splits` (Float, nullable)
- [ ] `created_at` (DateTime)
- [ ] UNIQUE Constraint (stock_id, date)
- [ ] Index auf (stock_id, date)

### 2.4 StockFundamentalData Model - NEU ERSTELLEN
- [ ] `id` (Primary Key)
- [ ] `stock_id` (Foreign Key)
- [ ] `period` (String, z.B. "FY2025Q3")
- [ ] `period_end_date` (Date)
- [ ] `revenue` (Float)
- [ ] `earnings` (Float / Net Income)
- [ ] `eps_basic` (Float)
- [ ] `eps_diluted` (Float)
- [ ] `operating_income` (Float)
- [ ] `gross_profit` (Float)
- [ ] `ebitda` (Float)
- [ ] `total_assets` (Float)
- [ ] `total_liabilities` (Float)
- [ ] `shareholders_equity` (Float)
- [ ] `operating_cashflow` (Float)
- [ ] `free_cashflow` (Float)
- [ ] `profit_margin` (Float)
- [ ] `operating_margin` (Float)
- [ ] `return_on_equity` (Float)
- [ ] `return_on_assets` (Float)
- [ ] `debt_to_equity` (Float)
- [ ] `current_ratio` (Float)
- [ ] `quick_ratio` (Float)
- [ ] `created_at` (DateTime)
- [ ] `updated_at` (DateTime)
- [ ] UNIQUE Constraint (stock_id, period)

---

## 🔄 Phase 3: Database Migration

### 3.1 Alembic Migration erstellen
- [ ] Migration Script generieren
- [ ] Neue Tabellen erstellen
- [ ] Alte Tabelle `stock_data` droppen

### 3.2 Datenmigration
- [ ] Daten von `stocks` nach `stocks_in_watchlist` migrieren
  - [ ] watchlist_id
  - [ ] stock_id
  - [ ] position
  - [ ] observation_reasons
  - [ ] observation_notes
- [ ] `stocks` Tabelle bereinigen (Felder droppen)
- [ ] Foreign Keys und Constraints prüfen

### 3.3 Migration testen
- [ ] Backup der aktuellen DB erstellen
- [ ] Migration in Test-DB ausführen
- [ ] Datenintegrität prüfen
- [ ] Rollback testen

---

## 📦 Phase 4: Pydantic Schemas anpassen

### 4.1 Bestehende Schemas anpassen
- [ ] `StockBase` - observation_reasons/notes entfernen
- [ ] `Stock` - watchlist_id/position entfernen, aber in Response behalten (für API-Kompatibilität)
- [ ] `StockCreate` - watchlist_id behalten (wird intern verarbeitet)
- [ ] `StockUpdate` - anpassen

### 4.2 Neue Schemas erstellen
- [ ] `StockInWatchlistBase`
- [ ] `StockInWatchlistCreate`
- [ ] `StockInWatchlistUpdate`
- [ ] `StockInWatchlist` (Response)
- [ ] `StockPriceDataBase`
- [ ] `StockPriceData` (Response)
- [ ] `StockFundamentalDataBase`
- [ ] `StockFundamentalData` (Response)
- [ ] `HistoricalPriceRequest` (für Abfragen)
- [ ] `HistoricalPriceResponse`

---

## 🛠️ Phase 5: Services erstellen/anpassen

### 5.1 Stock Service anpassen
- [ ] CRUD-Operationen für neue Struktur anpassen
- [ ] `get_stock_with_watchlist_info()` - joined query
- [ ] `create_stock()` - Stock + StockInWatchlist in Transaction
- [ ] `update_stock()` - beide Tabellen aktualisieren
- [ ] `delete_stock()` - Cascade handling
- [ ] `move_stock()` - position in StockInWatchlist
- [ ] `copy_stock()` - neuer Eintrag in StockInWatchlist

### 5.2 Historical Price Data Service - NEU
- [ ] `load_historical_prices(stock_id, period="max")` - yfinance
- [ ] `save_historical_prices(stock_id, dataframe)`
- [ ] `get_historical_prices(stock_id, start_date, end_date)`
- [ ] `get_latest_price(stock_id)`
- [ ] `update_prices(stock_id)` - nur neue Daten laden
- [ ] Bulk-Insert-Optimierung

### 5.3 Fundamental Data Service - NEU
- [ ] `load_fundamental_data(stock_id)` - yfinance quarterly
- [ ] `save_fundamental_data(stock_id, data)`
- [ ] `get_fundamental_data(stock_id, periods=4)` - letzte N Quartale
- [ ] `get_latest_fundamental_data(stock_id)`

### 5.4 Calculated Metrics Service - ERWEITERN
- [ ] Cache-System implementieren (TTL 30-60 min)
- [ ] `calculate_metrics_from_history(stock_id)` - aus DB-Daten
- [ ] RSI aus historical prices
- [ ] MACD aus historical prices
- [ ] SMA50/200 aus historical prices
- [ ] Volatility aus historical prices
- [ ] Beta-Berechnung
- [ ] Sharpe/Sortino Ratio

---

## 🌐 Phase 6: API Routes anpassen

### 6.1 Stocks Routes anpassen (`/stocks`)
- [ ] `GET /watchlists/{id}/stocks` - joined query anpassen
- [ ] `POST /watchlists/{id}/stocks` - Stock + StockInWatchlist erstellen + History laden
- [ ] `GET /stocks/{id}` - mit joined data
- [ ] `PUT /stocks/{id}` - beide Tabellen
- [ ] `DELETE /stocks/{id}` - Cascade
- [ ] `POST /stocks/{id}/move` - StockInWatchlist updaten
- [ ] `POST /stocks/{id}/copy` - neuer StockInWatchlist Eintrag
- [ ] Response-Format für Frontend-Kompatibilität beibehalten

### 6.2 Stock Data Routes - NEU/ANPASSEN
- [ ] `GET /stocks/{id}/price-history` - historische Kurse
  - Query params: start_date, end_date, interval
- [ ] `POST /stocks/{id}/price-history/refresh` - Update von yfinance
- [ ] `GET /stocks/{id}/fundamentals` - Quartaldaten
- [ ] `POST /stocks/{id}/fundamentals/refresh` - Update von yfinance
- [ ] `GET /stocks/{id}/calculated-metrics` - gecachte Metriken

### 6.3 Alte Routes entfernen
- [ ] Alte `stock_data` Endpoints entfernen/umleiten

---

## 🧪 Phase 7: Testing

### 7.1 Unit Tests
- [ ] Models testen (Beziehungen, Constraints)
- [ ] Services testen (CRUD, Berechnungen)
- [ ] Schemas testen (Validierung)

### 7.2 Integration Tests
- [ ] Complete Flow: Stock hinzufügen → History laden → Metrics berechnen
- [ ] Migration Test: Alte Daten → Neue Struktur
- [ ] API Tests: Frontend-Kompatibilität

### 7.3 Performance Tests
- [ ] Bulk-Insert historical data
- [ ] Query Performance (Joins, Indexes)
- [ ] Cache Performance

---

## 📚 Phase 8: Dokumentation

- [ ] API-Dokumentation aktualisieren
- [ ] Datenbank-Schema dokumentieren (ERD)
- [ ] Migration Guide erstellen
- [ ] README aktualisieren
- [ ] Code-Kommentare vervollständigen

---

## 🎯 Erfolg-Kriterien

- ✅ Frontend funktioniert ohne Änderungen
- ✅ Historische Daten werden beim Stock-Import geladen
- ✅ Calculated Metrics basieren auf echten historischen Daten
- ✅ Migration der bestehenden Daten erfolgreich
- ✅ Performance ist akzeptabel (< 2s für Stock-Import mit History)
- ✅ Alle Tests bestehen

---

## ⚠️ Risiken & Rollback

- [ ] Backup-Strategie definiert
- [ ] Rollback-Migration vorbereitet
- [ ] Test-Umgebung eingerichtet
- [ ] Production-Deployment-Plan

---

## 📝 Notizen

- Frontend bleibt unverändert
- API-Response-Format muss kompatibel bleiben
- Calculated Metrics: Option B+C (On-the-fly mit Caching)
- Historische Daten: Maximum verfügbar, nur Tagesschlusskurse
- Updates: On-demand (kein Scheduler vorerst)
