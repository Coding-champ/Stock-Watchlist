# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Static HTML/CSS/JavaScript (static/index.html)       │  │
│  │  - Watchlist cards                                     │  │
│  │  - Stock table with filtering/sorting                  │  │
│  │  - Stock detail modal                                  │  │
│  │  - Alert management                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↕ HTTP/JSON                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Routes (backend/app/routes/)                    │   │
│  │  - watchlists.py  : Watchlist CRUD                   │   │
│  │  - stocks.py      : Stock CRUD + Move                │   │
│  │  - stock_data.py  : Stock data management            │   │
│  │  - alerts.py      : Alert CRUD                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↕                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Pydantic Schemas (backend/app/schemas.py)           │   │
│  │  - Request/Response validation                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↕                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Database Layer (backend/app/database.py)            │   │
│  │  - SQLAlchemy session management                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tables:                                             │   │
│  │  - watchlists    (id, name, description, ...)       │   │
│  │  - stocks        (id, watchlist_id, isin, ...)      │   │
│  │  - stock_data    (id, stock_id, price, pe, ...)     │   │
│  │  - alerts        (id, stock_id, type, condition...) │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Model Relationships

```
┌──────────────┐         ┌────────────┐
│  Watchlist   │1      *│   Stock    │
│──────────────│◄────────│────────────│
│ id           │         │ id         │
│ name         │         │ watchlist_id│
│ description  │         │ isin       │
│ created_at   │         │ ticker     │
│ updated_at   │         │ name       │
└──────────────┘         │ country    │
                         │ industry   │
                         │ sector     │
                         │ position   │
                         └────────────┘
                              │1
                              │
                         ┌────┴────┐
                         │         │*
                    *│   │         │
              ┌───────┴──▼───┐  ┌──▼─────────┐
              │  StockData   │  │   Alert    │
              │──────────────│  │────────────│
              │ id           │  │ id         │
              │ stock_id     │  │ stock_id   │
              │ current_price│  │ alert_type │
              │ pe_ratio     │  │ condition  │
              │ rsi          │  │ threshold  │
              │ volatility   │  │ is_active  │
              │ timestamp    │  └────────────┘
              └──────────────┘
```

## Key Features

### 1. Watchlist Management
- Create multiple watchlists
- Each watchlist can contain many stocks
- Update and delete watchlists

### 2. Stock Management
- Add stocks with ISIN, ticker, name, country, industry, sector
- Move stocks between watchlists
- Automatic position management
- Delete stocks

### 3. Stock Data
- Current price
- P/E ratio (KGV - Kurs-Gewinn-Verhältnis)
- RSI (Relative Strength Index)
- Volatility
- Historical data support

### 4. Alerts
- Price alerts
- Metric alerts (P/E, RSI, Volatility)
- Conditions: above, below, equals
- Enable/disable alerts
- Multiple alerts per stock

### 5. Frontend Features
- Responsive design
- Filter stocks by name, ISIN, ticker
- Sort by any column
- Click watchlist to view stocks
- Click stock to view details
- Modal dialogs for forms
- German language interface

## API Design

All endpoints follow REST conventions:
- GET for retrieving data
- POST for creating new resources
- PUT for updating existing resources
- DELETE for removing resources

Response formats are consistent using Pydantic schemas for validation.

## Deployment Options

### Docker (Recommended)
```bash
docker-compose up -d
```
- Automatically sets up PostgreSQL
- Runs application in container
- Easy to deploy and maintain

### Local Development
```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```
- Requires local PostgreSQL installation
- Hot reload for development
- Direct access to database
