# Stock-Watchlist
Simple Watchlist for Stocks

## Features

- **Watchlist Management**: Create, read, update, and delete watchlists
- **Stock Management**: Add stocks to watchlists, delete, and move between watchlists
- **Stock Data**: Track current price, P/E ratio (KGV), RSI, and volatility
- **Filtering & Sorting**: Filter stocks by name, ISIN, or ticker; sort by any column
- **Detail View**: Click on any stock to see detailed information
- **Alerts**: Create price and metric alerts with customizable conditions
- **Columns**: ISIN, Ticker Symbol, Name, Current Price, Country, Industry, Sector, P/E Ratio, RSI, Volatility

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

See `tests/README.md` for detailed test documentation.

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

### Stock Data
- `GET /stock-data/{stock_id}` - Get historical data for a stock
- `POST /stock-data/` - Add new stock data entry

### Alerts
- `GET /alerts/` - Get all alerts (with filtering)
- `GET /alerts/{id}` - Get specific alert
- `POST /alerts/` - Create new alert
- `PUT /alerts/{id}` - Update alert
- `DELETE /alerts/{id}` - Delete alert

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
│       ├── models/         # Database models
│       ├── routes/         # API endpoints
│       ├── schemas.py      # Pydantic schemas
│       ├── database.py     # Database configuration
│       └── main.py         # FastAPI application
├── frontend/
│   ├── public/             # Static assets
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.js          # Main App component
│   │   ├── App.css         # Global styles
│   │   └── index.js        # Entry point
│   └── package.json        # Frontend dependencies
└── requirements.txt        # Python dependencies
```

## License

MIT
