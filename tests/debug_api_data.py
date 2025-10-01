#!/usr/bin/env python3
"""
Debug script to check the data structure returned by the API
"""

import requests
import json

def debug_api_data():
    base_url = "http://localhost:8000"
    
    try:
        print("=== Debugging API Data Structure ===\n")
        
        # Step 1: Create a test watchlist
        print("1. Creating test watchlist...")
        watchlist_data = {
            "name": "Debug Test Watchlist",
            "description": "Testing data structure"
        }
        response = requests.post(f"{base_url}/watchlists/", json=watchlist_data)
        
        if response.status_code == 201:
            watchlist_id = response.json()["id"]
            print(f"✅ Watchlist created with ID: {watchlist_id}")
            
            # Step 2: Add a stock via yfinance
            print("\n2. Adding Apple stock via yfinance...")
            stock_data = {
                "ticker_symbol": "AAPL",
                "watchlist_id": watchlist_id
            }
            response = requests.post(f"{base_url}/stocks/add-by-ticker", json=stock_data)
            
            if response.status_code == 201:
                added_stock = response.json()
                print("✅ Stock added successfully!")
                print("Stock data structure:")
                print(json.dumps(added_stock, indent=2, default=str))
                
                # Step 3: Get all stocks in watchlist
                print(f"\n3. Getting all stocks in watchlist {watchlist_id}...")
                response = requests.get(f"{base_url}/stocks/?watchlist_id={watchlist_id}")
                
                if response.status_code == 200:
                    stocks = response.json()
                    print("✅ Stocks retrieved successfully!")
                    print(f"Number of stocks: {len(stocks)}")
                    
                    if stocks:
                        print("\nFirst stock data structure:")
                        print(json.dumps(stocks[0], indent=2, default=str))
                        
                        # Check if latest_data exists
                        if 'latest_data' in stocks[0] and stocks[0]['latest_data']:
                            print("\n📊 Latest data found:")
                            print(json.dumps(stocks[0]['latest_data'], indent=2, default=str))
                        else:
                            print("\n❌ No latest_data found in stock")
                            
                else:
                    print(f"❌ Failed to get stocks: {response.text}")
            else:
                print(f"❌ Failed to add stock: {response.text}")
        else:
            print(f"❌ Failed to create watchlist: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_api_data()