"""
Test script for Phase 6 new endpoints:
- GET /stock-data/{id}/price-history
- POST /stock-data/{id}/refresh-history
- GET /stock-data/{id}/fundamentals
- POST /stock-data/{id}/refresh-fundamentals

Run with: python tests/test_phase6_endpoints.py
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_price_history(stock_id: int = 1):
    """Test getting historical price data"""
    print(f"\n{'='*60}")
    print(f"Testing GET /stock-data/{stock_id}/price-history")
    print('='*60)
    
    # Test 1: Get last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    response = requests.get(
        f"{BASE_URL}/stock-data/{stock_id}/price-history",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "limit": 30
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Stock: {data['ticker_symbol']}")
        print(f"Count: {data['count']}")
        print(f"Date range: {data['date_range']['start']} to {data['date_range']['end']}")
        
        if data['data']:
            print("\nSample data (first 3 records):")
            for record in data['data'][:3]:
                print(f"  {record['date']}: Open={record['open']}, Close={record['close']}, Volume={record['volume']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)


def test_refresh_history(stock_id: int = 1):
    """Test refreshing historical data from yfinance"""
    print(f"\n{'='*60}")
    print(f"Testing POST /stock-data/{stock_id}/refresh-history")
    print('='*60)
    
    response = requests.post(
        f"{BASE_URL}/stock-data/{stock_id}/refresh-history",
        params={"period": "1mo"}
    )
    
    if response.status_code == 202:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Stock: {data['ticker_symbol']}")
        print(f"Records saved: {data['records_saved']}")
        print(f"Date range: {data.get('date_range', {})}")
        print(f"Success: {data['success']}")
        print(f"Message: {data['message']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)


def test_fundamentals(stock_id: int = 1):
    """Test getting fundamental data"""
    print(f"\n{'='*60}")
    print(f"Testing GET /stock-data/{stock_id}/fundamentals")
    print('='*60)
    
    # Test 1: Get latest only
    response = requests.get(
        f"{BASE_URL}/stock-data/{stock_id}/fundamentals",
        params={"latest_only": True}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Stock: {data['ticker_symbol']}")
        print(f"Count: {data['count']}")
        
        if data['quarters']:
            latest = data['quarters'][0]
            print("\nLatest quarter:")
            print(f"  Period: {latest['period']}")
            print(f"  End Date: {latest['period_end_date']}")
            print(f"  Revenue: ${latest['revenue']:,.0f}" if latest['revenue'] else "  Revenue: N/A")
            print(f"  Earnings: ${latest['earnings']:,.0f}" if latest['earnings'] else "  Earnings: N/A")
            print(f"  EPS (basic): ${latest['eps_basic']:.2f}" if latest['eps_basic'] else "  EPS: N/A")
            print(f"  Profit Margin: {latest['profit_margin']:.2%}" if latest['profit_margin'] else "  Profit Margin: N/A")
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)
    
    # Test 2: Get last 4 quarters
    print("\n--- Getting last 4 quarters ---")
    response = requests.get(
        f"{BASE_URL}/stock-data/{stock_id}/fundamentals",
        params={"limit": 4}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} quarters")
        for quarter in data['quarters']:
            print(f"  {quarter['period']}: Revenue=${quarter['revenue']:,.0f}" if quarter['revenue'] else f"  {quarter['period']}: Revenue=N/A")
    else:
        print(f"❌ Status: {response.status_code}")


def test_refresh_fundamentals(stock_id: int = 1):
    """Test refreshing fundamental data from yfinance"""
    print(f"\n{'='*60}")
    print(f"Testing POST /stock-data/{stock_id}/refresh-fundamentals")
    print('='*60)
    
    response = requests.post(
        f"{BASE_URL}/stock-data/{stock_id}/refresh-fundamentals"
    )
    
    if response.status_code == 202:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Stock: {data['ticker_symbol']}")
        print(f"Quarters saved: {data['quarters_saved']}")
        print(f"Success: {data['success']}")
        print(f"Message: {data['message']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)


def main():
    print("\n" + "="*60)
    print("PHASE 6 ENDPOINT TESTING")
    print("="*60)
    print("\nTesting new endpoints for historical and fundamental data")
    print("Make sure the backend server is running on localhost:8000")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("\n❌ Backend server not reachable!")
            print("Start it with: uvicorn backend.app.main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend server not running!")
        print("Start it with: uvicorn backend.app.main:app --reload")
        return
    
    # Get first stock ID
    response = requests.get(f"{BASE_URL}/watchlists/")
    if response.status_code == 200:
        watchlists = response.json()
        if watchlists and 'stocks' in watchlists[0] and watchlists[0]['stocks']:
            stock_id = watchlists[0]['stocks'][0]['id']
            print(f"\n✅ Found stock ID {stock_id} for testing")
        else:
            print("\n⚠️ No stocks found! Create one first")
            stock_id = 1
    else:
        print("\n⚠️ Using stock ID 1 (might not exist)")
        stock_id = 1
    
    # Run tests
    test_price_history(stock_id)
    test_fundamentals(stock_id)
    
    # Refresh tests (commented out by default to avoid rate limiting)
    print("\n" + "="*60)
    print("REFRESH TESTS (uncomment to run)")
    print("="*60)
    print("⚠️ Refresh tests are disabled by default to avoid yfinance rate limits")
    print("Uncomment the lines below to test refresh functionality")
    # test_refresh_history(stock_id)
    # test_refresh_fundamentals(stock_id)
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
