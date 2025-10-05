"""
Test script for Phase 3a alert features
- Earnings alerts
- Composite alerts
- Alert Dashboard data
"""

import sys
import os
from datetime import datetime, timedelta

# Adjust path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from backend.app.database import get_db
from backend.app.models import Alert

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_SYMBOL = "AAPL"

def test_earnings_alert():
    """Test creating an earnings alert"""
    print("\n=== Testing Earnings Alert ===")
    
    alert_data = {
        "stock_symbol": TEST_SYMBOL,
        "alert_type": "earnings",
        "condition": "before",
        "threshold": 7,  # 7 days before earnings
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    if response.status_code in [200, 201]:
        alert = response.json()
        print(f"✅ Earnings alert created: ID {alert['id']}")
        print(f"   - Symbol: {alert['stock_id']} (stock_id)")
        print(f"   - Condition: {alert['condition']} {alert['threshold_value']} days")
        return alert['id']
    else:
        print(f"❌ Failed to create earnings alert: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_composite_alert():
    """Test creating a composite alert"""
    print("\n=== Testing Composite Alert ===")
    
    # Composite: price > $200 AND pe_ratio < 30
    alert_data = {
        "stock_symbol": TEST_SYMBOL,
        "alert_type": "composite",
        "condition": "and",  # AND logic
        "threshold": 0,
        "is_active": True,
        "composite_conditions": [
            {
                "type": "price",
                "condition": "above",
                "value": 200
            },
            {
                "type": "pe_ratio",
                "condition": "below",
                "value": 30
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    if response.status_code in [200, 201]:
        alert = response.json()
        print(f"✅ Composite alert created: ID {alert['id']}")
        print(f"   - Symbol: {alert['stock_id']} (stock_id)")
        print(f"   - Conditions: {len(alert.get('composite_conditions', []))}")
        return alert['id']
    else:
        print(f"❌ Failed to create composite alert: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_dashboard_data():
    """Test fetching alert dashboard data"""
    print("\n=== Testing Alert Dashboard Data ===")
    
    # Get all alerts
    response = requests.get(f"{BASE_URL}/alerts/")
    if response.status_code == 200:
        alerts = response.json()
        total = len(alerts)
        active = sum(1 for a in alerts if a.get('is_active'))
        triggered = sum(1 for a in alerts if a.get('last_triggered'))
        
        print(f"✅ Dashboard data fetched:")
        print(f"   - Total alerts: {total}")
        print(f"   - Active alerts: {active}")
        print(f"   - Triggered alerts: {triggered}")
        
        # Show alert types breakdown
        types = {}
        for alert in alerts:
            alert_type = alert.get('alert_type', 'unknown')
            types[alert_type] = types.get(alert_type, 0) + 1
        
        print(f"   - Alert types:")
        for alert_type, count in types.items():
            print(f"     • {alert_type}: {count}")
        
        return alerts
    else:
        print(f"❌ Failed to fetch dashboard data: {response.text}")
        return None

def test_check_alerts():
    """Test manual alert checking"""
    print("\n=== Testing Manual Alert Check ===")
    
    response = requests.post(f"{BASE_URL}/alerts/check-all")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Alert check completed:")
        print(f"   - Checked: {result.get('checked', 0)} alerts")
        print(f"   - Triggered: {result.get('triggered', 0)} alerts")
        
        if result.get('triggered', 0) > 0:
            print(f"   - Triggered alert IDs: {result.get('triggered_ids', [])}")
        
        return result
    else:
        print(f"❌ Failed to check alerts: {response.text}")
        return None

def cleanup_test_alerts(alert_ids):
    """Delete test alerts"""
    print("\n=== Cleaning Up Test Alerts ===")
    
    for alert_id in alert_ids:
        if alert_id:
            response = requests.delete(f"{BASE_URL}/alerts/{alert_id}")
            if response.status_code in [200, 204]:
                print(f"✅ Deleted alert {alert_id}")
            else:
                print(f"❌ Failed to delete alert {alert_id}")

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 3a Alert System Test")
    print("=" * 60)
    
    created_alerts = []
    
    try:
        # Test 1: Earnings alert
        earnings_id = test_earnings_alert()
        if earnings_id:
            created_alerts.append(earnings_id)
        
        # Test 2: Composite alert
        composite_id = test_composite_alert()
        if composite_id:
            created_alerts.append(composite_id)
        
        # Test 3: Dashboard data
        test_dashboard_data()
        
        # Test 4: Manual alert check
        test_check_alerts()
        
        print("\n" + "=" * 60)
        print("✅ Phase 3a tests completed!")
        print("=" * 60)
        
    finally:
        # Cleanup
        cleanup_test_alerts(created_alerts)
