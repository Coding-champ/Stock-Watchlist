"""
Quick test for the update-market-data endpoint
Run with: python tests/test_update_market_data.py
"""

import requests

BASE_URL = "http://localhost:8000"

def test_update_market_data():
    """Test the POST /stocks/{id}/update-market-data endpoint"""
    
    print("\n" + "="*60)
    print("Testing POST /stocks/{id}/update-market-data")
    print("="*60)
    
    # Get first stock
    response = requests.get(f"{BASE_URL}/watchlists/")
    if response.status_code != 200:
        print("❌ Could not get watchlists")
        return
    
    watchlists = response.json()
    if not watchlists or not watchlists[0].get('stocks'):
        print("❌ No stocks found in watchlist")
        return
    
    stock = watchlists[0]['stocks'][0]
    stock_id = stock['id']
    ticker = stock['ticker_symbol']
    
    print(f"\n✅ Testing with stock: {ticker} (ID: {stock_id})")
    
    # Test update
    print(f"\nUpdating market data for {ticker}...")
    response = requests.post(f"{BASE_URL}/stocks/{stock_id}/update-market-data")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"\nResult:")
        print(f"  Success: {data['success']}")
        print(f"  Ticker: {data['ticker_symbol']}")
        print(f"  Message: {data['message']}")
        print(f"\nMarket Data:")
        market_data = data['data']
        print(f"  Current Price: ${market_data.get('current_price', 'N/A')}")
        print(f"  PE Ratio: {market_data.get('pe_ratio', 'N/A')}")
        print(f"  Change: {market_data.get('change', 'N/A')} ({market_data.get('change_percent', 'N/A')}%)")
        print(f"  Volume: {market_data.get('volume', 'N/A'):,}" if market_data.get('volume') else "  Volume: N/A")
        print(f"  Date: {market_data.get('date', 'N/A')}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("\n❌ Backend server not reachable!")
            print("Start it with: python -m uvicorn backend.app.main:app --reload")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend server not running!")
        print("Start it with: python -m uvicorn backend.app.main:app --reload")
        exit(1)
    
    test_update_market_data()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
