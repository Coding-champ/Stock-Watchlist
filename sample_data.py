"""
Sample data script for Stock Watchlist application
Run this after setting up the database to populate with sample data
"""
import requests
import json

API_BASE = "http://localhost:8000"


def create_watchlist(name, description):
    """Create a watchlist"""
    response = requests.post(
        f"{API_BASE}/watchlists/",
        json={"name": name, "description": description}
    )
    return response.json()


def add_stock(watchlist_id, isin, ticker, name, country=None, industry=None, sector=None):
    """Add a stock to a watchlist"""
    response = requests.post(
        f"{API_BASE}/stocks/",
        json={
            "watchlist_id": watchlist_id,
            "isin": isin,
            "ticker_symbol": ticker,
            "name": name,
            "country": country,
            "industry": industry,
            "sector": sector
        }
    )
    return response.json()


def add_stock_data(stock_id, price, pe_ratio=None, rsi=None, volatility=None):
    """Add stock data"""
    response = requests.post(
        f"{API_BASE}/stock-data/",
        json={
            "stock_id": stock_id,
            "current_price": price,
            "pe_ratio": pe_ratio,
            "rsi": rsi,
            "volatility": volatility
        }
    )
    return response.json()


def create_alert(stock_id, alert_type, condition, threshold):
    """Create an alert"""
    response = requests.post(
        f"{API_BASE}/alerts/",
        json={
            "stock_id": stock_id,
            "alert_type": alert_type,
            "condition": condition,
            "threshold_value": threshold,
            "is_active": True
        }
    )
    return response.json()


def main():
    print("Creating sample data...")
    
    # Create watchlists
    print("\n1. Creating watchlists...")
    tech_watchlist = create_watchlist("Tech Stocks", "Technology companies")
    print(f"   Created: {tech_watchlist['name']}")
    
    auto_watchlist = create_watchlist("Automotive", "Car manufacturers")
    print(f"   Created: {auto_watchlist['name']}")
    
    # Add stocks to Tech watchlist
    print("\n2. Adding stocks to Tech Stocks watchlist...")
    
    apple = add_stock(
        tech_watchlist['id'],
        "US0378331005",
        "AAPL",
        "Apple Inc.",
        "USA",
        "Consumer Electronics",
        "Technology"
    )
    print(f"   Added: {apple['name']}")
    add_stock_data(apple['id'], 178.50, 28.5, 52.3, 1.2)
    create_alert(apple['id'], "price", "below", 170.0)
    
    microsoft = add_stock(
        tech_watchlist['id'],
        "US5949181045",
        "MSFT",
        "Microsoft Corporation",
        "USA",
        "Software",
        "Technology"
    )
    print(f"   Added: {microsoft['name']}")
    add_stock_data(microsoft['id'], 378.25, 32.1, 55.8, 1.5)
    
    google = add_stock(
        tech_watchlist['id'],
        "US02079K3059",
        "GOOGL",
        "Alphabet Inc.",
        "USA",
        "Internet Services",
        "Technology"
    )
    print(f"   Added: {google['name']}")
    add_stock_data(google['id'], 142.30, 24.8, 48.9, 1.8)
    create_alert(google['id'], "rsi", "above", 70.0)
    
    # Add stocks to Automotive watchlist
    print("\n3. Adding stocks to Automotive watchlist...")
    
    vw = add_stock(
        auto_watchlist['id'],
        "DE0007664005",
        "VOW3.DE",
        "Volkswagen AG",
        "Germany",
        "Automotive",
        "Consumer Cyclical"
    )
    print(f"   Added: {vw['name']}")
    add_stock_data(vw['id'], 112.45, 15.2, 45.3, 2.1)
    
    bmw = add_stock(
        auto_watchlist['id'],
        "DE0005190003",
        "BMW.DE",
        "BMW AG",
        "Germany",
        "Automotive",
        "Consumer Cyclical"
    )
    print(f"   Added: {bmw['name']}")
    add_stock_data(bmw['id'], 95.80, 13.8, 42.1, 2.3)
    create_alert(bmw['id'], "pe_ratio", "below", 12.0)
    
    tesla = add_stock(
        auto_watchlist['id'],
        "US88160R1014",
        "TSLA",
        "Tesla Inc.",
        "USA",
        "Electric Vehicles",
        "Consumer Cyclical"
    )
    print(f"   Added: {tesla['name']}")
    add_stock_data(tesla['id'], 242.80, 65.5, 58.7, 3.5)
    create_alert(tesla['id'], "volatility", "above", 4.0)
    
    print("\n✓ Sample data created successfully!")
    print(f"\nAccess the application at: http://localhost:8000/static/index.html")
    print(f"API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure the API server is running at http://localhost:8000")
        print("Run: uvicorn backend.app.main:app --reload")
