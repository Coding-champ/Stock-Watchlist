"""
Schnelles Test-Skript zum Prüfen der Alert-API
"""
import requests
import json

API_BASE = "http://localhost:8000"

def test_alert_endpoints():
    print("🔍 Testing Alert API Endpoints...\n")
    
    # 1. Test: API erreichbar?
    print("1. Testing if API is running...")
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code == 200:
            print("   ✅ API is running!")
        else:
            print(f"   ❌ API returned status code: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot reach API: {e}")
        print("\n   💡 Starte das Backend mit: uvicorn backend.app.main:app --reload")
        return
    
    # 2. Test: Gibt es Stocks?
    print("\n2. Checking for stocks...")
    try:
        response = requests.get(f"{API_BASE}/stocks/")
        stocks = response.json()
        if len(stocks) > 0:
            print(f"   ✅ Found {len(stocks)} stocks")
            test_stock = stocks[0]
            print(f"   Using stock: {test_stock['name']} ({test_stock['ticker_symbol']})")
        else:
            print("   ⚠️  No stocks found. Please add a stock first.")
            return
    except Exception as e:
        print(f"   ❌ Error fetching stocks: {e}")
        return
    
    # 3. Test: Alert erstellen
    print("\n3. Testing alert creation...")
    alert_data = {
        "stock_id": test_stock['id'],
        "alert_type": "price",
        "condition": "below",
        "threshold_value": 100.0,
        "is_active": True,
        "notes": "Test-Alarm vom Skript",
        "expiry_date": None
    }
    
    print(f"   Payload: {json.dumps(alert_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/alerts/",
            json=alert_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            alert = response.json()
            print(f"   ✅ Alert created successfully!")
            print(f"   Alert ID: {alert['id']}")
            
            # 4. Test: Alert abrufen
            print("\n4. Testing alert retrieval...")
            response = requests.get(f"{API_BASE}/alerts/?stock_id={test_stock['id']}")
            alerts = response.json()
            print(f"   ✅ Found {len(alerts)} alert(s) for this stock")
            
            # 5. Test: Alert löschen
            print(f"\n5. Cleaning up (deleting test alert)...")
            response = requests.delete(f"{API_BASE}/alerts/{alert['id']}")
            if response.status_code == 204:
                print("   ✅ Test alert deleted successfully!")
            else:
                print(f"   ⚠️  Delete returned status code: {response.status_code}")
                
        else:
            print(f"   ❌ Failed to create alert!")
            print(f"   Response: {response.text}")
            
            # Prüfe ob es ein Datenbankfehler ist
            if "column" in response.text.lower() or "expiry_date" in response.text.lower():
                print("\n   💡 Hinweis: Es sieht so aus, als wären die neuen Spalten noch nicht in der Datenbank.")
                print("      Führe die Migration aus:")
                print("      ALTER TABLE alerts ADD COLUMN expiry_date TIMESTAMP NULL;")
                print("      ALTER TABLE alerts ADD COLUMN notes TEXT NULL;")
            
    except Exception as e:
        print(f"   ❌ Error creating alert: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_alert_endpoints()
