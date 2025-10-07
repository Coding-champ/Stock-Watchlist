# Stock-Watchlist
Professional Stock Analysis & Watchlist Management System

## ✨ Features

### Core Features
- **Watchlist Management**: Create, read, update, and delete watchlists
- **Stock Management**: Add stocks to watchlists, delete, and move between watchlists
- **Stock Data Tracking**: Real-time price, P/E ratio (KGV), RSI, and volatility
- **Filtering & Sorting**: Advanced filtering by name, ISIN, ticker; sort by any column
- **Detail View**: Click on any stock to see comprehensive information
- **Price Alerts**: Create customizable price and metric alerts

### 🚀 Advanced Analytics (NEW!)

#### **Calculated Metrics System**
Comprehensive stock analysis with 3-phase metric calculation:

**Phase 1: Basic Indicators**
- 52-week distance and position analysis
- SMA 50/200 crossover detection (Golden Cross/Death Cross)
- Relative volume comparison
- Free cashflow yield calculation

**Phase 2: Valuation Scores** (0-100 scale)
- **Value Score**: Combined P/E, P/B, P/S analysis
- **Quality Score**: Profitability metrics (ROE, ROA, margins)
- **Dividend Safety Score**: Dividend sustainability assessment

**Phase 3: Advanced Technical Analysis**
- **MACD**: Trend analysis with histogram
- **Stochastic Oscillator**: Overbought/oversold signals
- **Volatility Metrics**: 30d, 90d, 1y annualized volatility
- **Maximum Drawdown**: Risk assessment
- **Beta-Adjusted Risk Metrics**:
  - Sharpe Ratio (risk-adjusted return)
  - Alpha (excess return vs CAPM)
  - Treynor Ratio (systematic risk-adjusted return)
  - Sortino Ratio (downside risk adjustment)
  - Information Ratio (consistency of outperformance)
- **Risk-Adjusted Performance Score**: Composite 0-100 score with rating

**Performance:**
- ⚡ < 10ms calculation time
- 🔄 1-hour intelligent caching
- 📊 Real-time yfinance integration

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: React

## Data Models

1. **Watchlist**: Organizes stocks into groups
2. **Stock**: Individual stock information
3. **StockData**: Current market data for stocks
4. **Alert**: Price and metric alerts

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Node.js 14+ and npm (for frontend development)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Coding-champ/Stock-Watchlist.git
cd Stock-Watchlist
```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database:
   - Create a PostgreSQL database named `stock_watchlist`
   - Copy `.env.example` to `.env` and update the `DATABASE_URL` if needed

## Testing

The project includes a comprehensive test suite located in the `tests/` directory.

### Quick Testing
For rapid development feedback:
```bash
cd tests
python quick_test.py
```

### Full Test Suite
Run all tests with detailed reporting:
```bash
cd tests
python run_all_tests.py
```

### Test Categories
- **Environment Tests**: Database connectivity and configuration
- **API Tests**: Backend endpoint validation  
- **yfinance Tests**: Stock data service integration
- **Debug Tools**: Environment and data debugging utilities

See `tests/README.md` for detailed testing documentation.

4. Build the React frontend:
```bash
cd frontend
npm install
npm run build
cd ..
```

5. Run the application:
```bash
uvicorn backend.app.main:app --reload
```

6. Load sample data (optional):
```bash
python sample_data.py
```

7. Initialize the database:
```bash
cd tests
python init_db.py
cd ..
```

8. Access the application:
   - Frontend: http://localhost:8000/
   - API Documentation: http://localhost:8000/docs

## 🧪 Testing

### Quick Test Run

**Windows:**
```bash
cd tests
run_tests.bat
```

**Linux/Mac:**
```bash
cd tests
./run_tests.sh
```

**Manual:**
```bash
cd tests
python run_all_tests.py
```

### Individual Tests

- **Database Setup:** `python tests/init_db.py`
- **Environment Check:** `python tests/debug_env.py`
- **yfinance Service:** `python tests/test_yfinance_simple.py`
- **API Tests:** `python tests/test_api.py`
- **Full Integration:** `python tests/test_yfinance.py`
- **Calculated Metrics (Service):** `pytest tests/test_service_calculated_metrics.py -v` ⭐
- **Performance Tests:** `pytest tests/test_performance_metrics.py -v` ⭐

See `tests/README.md` for detailed test documentation.

#### 🧪 Calculated Metrics Tests (NEW!)

**Service Layer Tests:**
```bash
pytest tests/test_service_calculated_metrics.py -v
```

**Coverage:**
- ✅ All 3 phases tested (9/9 tests passed)
- ✅ Beta-adjusted metrics validation
- ✅ Risk-adjusted performance scoring
- ✅ Edge cases (missing data, short history)
- ✅ Performance validation (< 10ms)

**Performance Benchmarks:**
```bash
pytest tests/test_performance_metrics.py -v
```

**Tests:**
- Calculation speed for each phase
- Memory usage and leak detection
- Large dataset handling (2 years)
- Batch calculations (10+ stocks)
- Cache effectiveness

**Results:**
- Average: 0.007s per stock
- 286x faster than 2s requirement
- Memory stable: < 50MB for 10 calculations

### Development Mode

For frontend development with hot reload:

1. Start the backend (from the root directory):
```bash
uvicorn backend.app.main:app --reload
```

2. In a separate terminal, start the React development server:
```bash
cd frontend
npm start
```

The React app will run on http://localhost:3000 and proxy API requests to the backend on http://localhost:8000.

## API Endpoints

### Watchlists
- `GET /watchlists/` - Get all watchlists
- `GET /watchlists/{id}` - Get specific watchlist with stocks
- `POST /watchlists/` - Create new watchlist
- `PUT /watchlists/{id}` - Update watchlist
- `DELETE /watchlists/{id}` - Delete watchlist

### Stocks
- `GET /stocks/` - Get all stocks (with filtering and sorting)
- `GET /stocks/{id}` - Get specific stock
- `POST /stocks/` - Add stock to watchlist
- `PUT /stocks/{id}` - Update stock
- `POST /stocks/{id}/move` - Move stock to another watchlist
- `DELETE /stocks/{id}` - Delete stock
- **`GET /stocks/{id}/with-calculated-metrics`** ⭐ - Get stock with complete analysis

### Stock Data
- `GET /stock-data/{stock_id}` - Get historical data for a stock
- `POST /stock-data/` - Add new stock data entry
- **`GET /stock-data/{stock_id}/calculated-metrics`** ⭐ - Get comprehensive calculated metrics

### Alerts
- `GET /alerts/` - Get all alerts (with filtering)
- `GET /alerts/{id}` - Get specific alert
- `POST /alerts/` - Create new alert
- `PUT /alerts/{id}` - Update alert
- `DELETE /alerts/{id}` - Delete alert

### 📊 Calculated Metrics API (NEW!)

#### Get Calculated Metrics
```http
GET /api/stock-data/{stock_id}/calculated-metrics?period=1y&use_cache=true
```

**Parameters:**
- `stock_id` (required): Stock database ID
- `period` (optional): `"1mo"`, `"3mo"`, `"6mo"`, `"1y"`, `"2y"` (default: `"1y"`)
- `use_cache` (optional): Enable caching (default: `true`)

**Response:** Complete 3-phase metrics analysis

**Example:**
```bash
curl "http://localhost:8000/api/stock-data/1/calculated-metrics?period=1y"
```

#### Get Stock with Calculated Metrics
```http
GET /api/stocks/{stock_id}/with-calculated-metrics?period=1y
```

**Response:** Stock info + extended data + calculated metrics

**Use Cases:**
- Stock detail pages
- Dashboard widgets
- Portfolio analysis tools

**Performance:**
- Cached: < 1ms
- Uncached: 7-50ms
- Cache TTL: 1 hour

📖 **Full API Documentation:** See `API_DOCUMENTATION_CALCULATED_METRICS.md`

## Database Schema

```sql
Watchlist:
  - id (PK)
  - name (unique)
  - description
  - created_at
  - updated_at

Stock:
  - id (PK)
  - watchlist_id (FK)
  - isin
  - ticker_symbol
  - name
  - country
  - industry
  - sector
  - position
  - created_at
  - updated_at

StockData:
  - id (PK)
  - stock_id (FK)
  - current_price
  - pe_ratio (KGV)
  - rsi
  - volatility
  - timestamp

Alert:
  - id (PK)
  - stock_id (FK)
  - alert_type (price, pe_ratio, rsi, volatility)
  - condition (above, below, equals)
  - threshold_value
  - is_active
  - created_at
  - updated_at
```

## Usage

1. **Create a Watchlist**: Click "Neue Watchlist erstellen" and enter a name
2. **Add Stocks**: Select a watchlist, then click "Aktie hinzufügen"
3. **View Stocks**: Click on a watchlist card to see all stocks in a sortable/filterable table
4. **Stock Details**: Click on any stock row to see detailed information
5. **Create Alerts**: In the stock detail view, click "Alarm hinzufügen"
6. **Move Stocks**: Click "Verschieben" on any stock to move it to another watchlist
7. **Delete**: Use the "Löschen" button to remove stocks or alerts

## Development

The application follows a clean architecture:

```
Stock-Watchlist/
├── backend/
│   └── app/
│       ├── models/                # Database models
│       ├── routes/                # API endpoints
│       │   ├── watchlists.py
│       │   ├── stocks.py
│       │   ├── stock_data.py     # ⭐ Includes calculated metrics
│       │   └── alerts.py
│       ├── services/              # Business logic
│       │   ├── yfinance_service.py
│       │   ├── calculated_metrics_service.py  # ⭐ NEW
│       │   └── cache_service.py   # ⭐ Caching system
│       ├── schemas.py             # Pydantic schemas
│       ├── database.py            # Database configuration
│       └── main.py                # FastAPI application
├── frontend/
│   ├── public/                    # Static assets
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── App.js                 # Main App component
│   │   ├── App.css                # Global styles
│   │   └── index.js               # Entry point
│   └── package.json               # Frontend dependencies
├── tests/                         # Test suite
│   ├── test_service_calculated_metrics.py  # ⭐ Service tests
│   └── test_performance_metrics.py         # ⭐ Performance tests
└── requirements.txt               # Python dependencies
```

## 📚 Documentation

### For Developers

- **[CALCULATED_METRICS_DOCUMENTATION.md](CALCULATED_METRICS_DOCUMENTATION.md)** - Implementation guide (400+ lines)
- **[BETA_ADJUSTED_METRICS_GUIDE.md](BETA_ADJUSTED_METRICS_GUIDE.md)** - Deep dive into risk metrics (600+ lines)
- **[API_DOCUMENTATION_CALCULATED_METRICS.md](API_DOCUMENTATION_CALCULATED_METRICS.md)** - Complete API reference (526 lines)
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Test results and benchmarks
- **[IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md)** - Development progress (89% complete)

### Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Features Documented

#### Calculated Metrics System
- 3-phase metric calculation (Basic, Valuation, Advanced)
- Beta-adjusted risk metrics (Sharpe, Alpha, Treynor, Sortino)
- Risk-adjusted performance scoring (0-100 scale)
- Intelligent caching (1-hour TTL)
- Performance optimization (< 10ms calculations)

#### API Endpoints
- Complete request/response examples
- Error handling documentation
- Performance benchmarks
- Usage examples (Python, JavaScript, cURL)

#### Testing
- Service layer: 9/9 tests passed (100%)
- Performance: 286x faster than requirement
- Memory usage: Stable < 50MB
- Edge cases: Handles missing data gracefully

## 🚀 Quick Start Examples

### Get Calculated Metrics (Python)

```python
import requests

# Get comprehensive metrics
response = requests.get(
    "http://localhost:8000/api/stock-data/1/calculated-metrics",
    params={"period": "1y", "use_cache": True}
)

metrics = response.json()

# Access specific metrics
sharpe_ratio = metrics['advanced_analysis']['beta_adjusted_metrics']['sharpe_ratio']
risk_score = metrics['advanced_analysis']['risk_adjusted_performance']['overall_score']

print(f"Sharpe Ratio: {sharpe_ratio:.3f}")
print(f"Risk-Adjusted Score: {risk_score:.1f}/100")
```

### Get Stock with Metrics (JavaScript)

```javascript
// Fetch stock with complete analysis
fetch('http://localhost:8000/api/stocks/1/with-calculated-metrics?period=1y')
  .then(response => response.json())
  .then(data => {
    const stock = data;
    const metrics = stock.calculated_metrics;
    
    console.log(`${stock.name} (${stock.ticker_symbol})`);
    console.log(`Value Score: ${metrics.valuation_scores.value_metrics.value_score}/100`);
    console.log(`Quality Score: ${metrics.valuation_scores.quality_metrics.quality_score}/100`);
  });
```

### Check Performance (cURL)

```bash
# Get metrics with timing
time curl -s "http://localhost:8000/api/stock-data/1/calculated-metrics?period=1y"

# Force refresh (bypass cache)
curl "http://localhost:8000/api/stock-data/1/calculated-metrics?use_cache=false"
```

## License

MIT
