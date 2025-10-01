#!/usr/bin/env python3
"""
Test script to verify the API is working
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    try:
        # Test GET /watchlists/
        print("Testing GET /watchlists/...")
        response = requests.get(f"{base_url}/watchlists/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ GET /watchlists/ works successfully!")
        else:
            print(f"❌ GET /watchlists/ failed with status {response.status_code}")
            
        # Test POST /watchlists/
        print("\nTesting POST /watchlists/...")
        new_watchlist = {
            "name": "Test Watchlist",
            "description": "A test watchlist to verify the API is working"
        }
        response = requests.post(f"{base_url}/watchlists/", json=new_watchlist)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ POST /watchlists/ works successfully!")
            return True
        else:
            print(f"❌ POST /watchlists/ failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Could not connect to the API server: {e}")
        print("Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_api()