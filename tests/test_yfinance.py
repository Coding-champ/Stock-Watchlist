#!/usr/bin/env python3
"""
Test script for the new yfinance stock functionality
"""

import requests
import json

def test_stock_functionality():
    base_url = "http://localhost:8000"
    
    try:
        # Test 1: Erstelle eine Test-Watchlist
        print("1. Creating test watchlist...")
        watchlist_data = {
            "name": "Test Watchlist für Aktien",
            "description": "Test für yfinance Integration"
        }
        response = requests.post(f"{base_url}/watchlists/", json=watchlist_data)
        if response.status_code == 201:
            watchlist_id = response.json()["id"]
            print(f"✅ Watchlist created with ID: {watchlist_id}")
        else:
            print(f"❌ Failed to create watchlist: {response.text}")
            return False
        
        # Test 2: Suche nach einer Aktie
        print("\n2. Searching for Apple stock (AAPL)...")
        response = requests.get(f"{base_url}/stocks/search/AAPL")
        if response.status_code == 200:
            search_result = response.json()
            print(f"✅ Search result: {json.dumps(search_result, indent=2)}")
        else:
            print(f"❌ Search failed: {response.text}")
        
        # Test 3: Füge Aktie per Ticker zur Watchlist hinzu
        print("\n3. Adding Apple stock to watchlist...")
        stock_data = {
            "ticker_symbol": "AAPL",
            "watchlist_id": watchlist_id
        }
        response = requests.post(f"{base_url}/stocks/add-by-ticker", json=stock_data)
        if response.status_code == 201:
            stock = response.json()
            print(f"✅ Stock added: {stock['name']} ({stock['ticker_symbol']})")
            print(f"   Sector: {stock['sector']}, Industry: {stock['industry']}")
            stock_id = stock["id"]
        else:
            print(f"❌ Failed to add stock: {response.text}")
            return False
        
        # Test 4: Füge eine weitere Aktie hinzu (Microsoft)
        print("\n4. Adding Microsoft stock to watchlist...")
        stock_data = {
            "ticker_symbol": "MSFT",
            "watchlist_id": watchlist_id
        }
        response = requests.post(f"{base_url}/stocks/add-by-ticker", json=stock_data)
        if response.status_code == 201:
            stock = response.json()
            print(f"✅ Stock added: {stock['name']} ({stock['ticker_symbol']})")
        else:
            print(f"❌ Failed to add Microsoft stock: {response.text}")
        
        # Test 5: Hole alle Aktien in der Watchlist
        print("\n5. Getting all stocks in watchlist...")
        response = requests.get(f"{base_url}/stocks/?watchlist_id={watchlist_id}")
        if response.status_code == 200:
            stocks = response.json()
            print(f"✅ Found {len(stocks)} stocks in watchlist:")
            for stock in stocks:
                print(f"   - {stock['name']} ({stock['ticker_symbol']})")
                if stock.get('latest_data'):
                    print(f"     Price: ${stock['latest_data'].get('current_price', 'N/A')}")
        else:
            print(f"❌ Failed to get stocks: {response.text}")
        
        # Test 6: Aktualisiere Marktdaten
        print(f"\n6. Updating market data for stock ID {stock_id}...")
        response = requests.post(f"{base_url}/stocks/{stock_id}/update-market-data")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Market data updated: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Failed to update market data: {response.text}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return False

if __name__ == "__main__":
    test_stock_functionality()