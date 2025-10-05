"""Test API endpoints after migration"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_watchlists():
    print("=" * 60)
    print("Testing Watchlists API")
    print("=" * 60)
    
    try:
        # Test GET /watchlists
        print("\n1. GET /watchlists")
        response = requests.get(f"{BASE_URL}/watchlists", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            watchlists = response.json()
            print(f"   ✅ Found {len(watchlists)} watchlists")
            for wl in watchlists:
                print(f"      - ID {wl['id']}: {wl['name']}")
        else:
            print(f"   ❌ Error Response:")
            try:
                print(f"   {response.json()}")
            except:
                print(f"   {response.text}")
            return False
            
        # Test GET /stocks for first watchlist
        if watchlists:
            wl_id = watchlists[0]['id']
            print(f"\n2. GET /stocks (watchlist_id={wl_id})")
            response = requests.get(f"{BASE_URL}/stocks", params={"watchlist_id": wl_id}, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                stocks = response.json()
                print(f"   ✅ Found {len(stocks)} stocks")
                for stock in stocks[:3]:  # Show first 3
                    print(f"      - {stock.get('ticker_symbol')}: {stock.get('name')}")
            else:
                print(f"   ❌ Error: {response.text}")
                return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - is backend running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_watchlists()
