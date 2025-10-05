"""
Complete Phase 3a Integration Test
Tests all Phase 3a features end-to-end
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests

BASE_URL = "http://localhost:8000"
TEST_SYMBOL = "AAPL"

def test_earnings_alert_full():
    """Test complete earnings alert flow"""
    print("\n" + "="*60)
    print("TEST 1: Earnings Alert Full Flow")
    print("="*60)
    
    # Create earnings alert
    alert_data = {
        "stock_symbol": TEST_SYMBOL,
        "alert_type": "earnings",
        "condition": "before",
        "threshold": 7,
        "is_active": True,
        "notes": "Test earnings alert"
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    assert response.status_code in [200, 201], f"Failed to create: {response.status_code}"
    
    alert = response.json()
    alert_id = alert['id']
    print(f"✅ Created earnings alert: ID {alert_id}")
    
    # Check the alert manually
    check_response = requests.post(f"{BASE_URL}/alerts/check/{alert_id}")
    assert check_response.status_code == 200, f"Failed to check: {check_response.status_code}"
    
    check_result = check_response.json()
    print(f"✅ Alert check result: {check_result.get('status', 'unknown')}")
    
    # Cleanup
    delete_response = requests.delete(f"{BASE_URL}/alerts/{alert_id}")
    assert delete_response.status_code in [200, 204], f"Failed to delete: {delete_response.status_code}"
    print(f"✅ Cleaned up alert {alert_id}")
    
    return True

def test_composite_alert_full():
    """Test complete composite alert flow"""
    print("\n" + "="*60)
    print("TEST 2: Composite Alert Full Flow")
    print("="*60)
    
    # Create composite alert: price > 180 AND pe_ratio < 35
    alert_data = {
        "stock_symbol": TEST_SYMBOL,
        "alert_type": "composite",
        "condition": "and",
        "threshold": 0,
        "is_active": True,
        "composite_conditions": [
            {
                "type": "price",
                "condition": "above",
                "value": 180
            },
            {
                "type": "pe_ratio",
                "condition": "below",
                "value": 35
            }
        ],
        "notes": "Test composite alert"
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    assert response.status_code in [200, 201], f"Failed to create: {response.status_code}"
    
    alert = response.json()
    alert_id = alert['id']
    conditions = alert.get('composite_conditions', [])
    print(f"✅ Created composite alert: ID {alert_id} with {len(conditions)} conditions")
    
    # Check the alert manually
    check_response = requests.post(f"{BASE_URL}/alerts/check/{alert_id}")
    assert check_response.status_code == 200, f"Failed to check: {check_response.status_code}"
    
    check_result = check_response.json()
    print(f"✅ Alert check result: {check_result.get('status', 'unknown')}")
    
    # Cleanup
    delete_response = requests.delete(f"{BASE_URL}/alerts/{alert_id}")
    assert delete_response.status_code in [200, 204], f"Failed to delete: {delete_response.status_code}"
    print(f"✅ Cleaned up alert {alert_id}")
    
    return True

def test_dashboard_statistics():
    """Test dashboard statistics"""
    print("\n" + "="*60)
    print("TEST 3: Dashboard Statistics")
    print("="*60)
    
    # Get all alerts
    response = requests.get(f"{BASE_URL}/alerts/")
    assert response.status_code == 200, f"Failed to fetch alerts: {response.status_code}"
    
    alerts = response.json()
    
    # Calculate statistics
    total = len(alerts)
    active = sum(1 for a in alerts if a.get('is_active'))
    triggered = sum(1 for a in alerts if a.get('trigger_count', 0) > 0)
    
    # Group by type
    by_type = {}
    for alert in alerts:
        alert_type = alert.get('alert_type', 'unknown')
        by_type[alert_type] = by_type.get(alert_type, 0) + 1
    
    print(f"✅ Dashboard Statistics:")
    print(f"   Total: {total}")
    print(f"   Active: {active}")
    print(f"   Triggered: {triggered}")
    print(f"   By Type:")
    for alert_type, count in sorted(by_type.items()):
        print(f"     - {alert_type}: {count}")
    
    return True

def test_bulk_check():
    """Test bulk alert checking"""
    print("\n" + "="*60)
    print("TEST 4: Bulk Alert Check")
    print("="*60)
    
    # Create multiple test alerts
    alert_ids = []
    
    for i in range(3):
        alert_data = {
            "stock_symbol": TEST_SYMBOL,
            "alert_type": "price",
            "condition": "above",
            "threshold": 100 + (i * 10),
            "is_active": True,
            "notes": f"Bulk test alert {i+1}"
        }
        
        response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
        if response.status_code in [200, 201]:
            alert_ids.append(response.json()['id'])
    
    print(f"✅ Created {len(alert_ids)} test alerts")
    
    # Check all alerts
    check_response = requests.post(f"{BASE_URL}/alerts/check-all")
    assert check_response.status_code == 200, f"Failed bulk check: {check_response.status_code}"
    
    result = check_response.json()
    print(f"✅ Bulk check completed:")
    print(f"   Checked: {result.get('checked_count', 0)}")
    print(f"   Triggered: {result.get('triggered_count', 0)}")
    
    if result.get('triggered_alerts'):
        print(f"   Triggered Alert Details:")
        for ta in result['triggered_alerts'][:3]:  # Show first 3
            print(f"     - {ta.get('stock_name')} ({ta.get('ticker_symbol')}): {ta.get('alert_type')}")
    
    # Cleanup
    for alert_id in alert_ids:
        requests.delete(f"{BASE_URL}/alerts/{alert_id}")
    
    print(f"✅ Cleaned up {len(alert_ids)} test alerts")
    
    return True

def test_toast_notification_data():
    """Test that check-all returns data suitable for toast notifications"""
    print("\n" + "="*60)
    print("TEST 5: Toast Notification Data")
    print("="*60)
    
    # Create a simple price alert
    alert_data = {
        "stock_symbol": TEST_SYMBOL,
        "alert_type": "price",
        "condition": "above",
        "threshold": 50,  # Very low threshold to trigger
        "is_active": True,
        "notes": "Toast test alert"
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    assert response.status_code in [200, 201], f"Failed to create: {response.status_code}"
    alert_id = response.json()['id']
    print(f"✅ Created test alert: ID {alert_id}")
    
    # Check all alerts
    check_response = requests.post(f"{BASE_URL}/alerts/check-all")
    result = check_response.json()
    
    # Verify response structure for toast notifications
    assert 'checked_count' in result, "Missing checked_count"
    assert 'triggered_count' in result, "Missing triggered_count"
    assert 'triggered_alerts' in result, "Missing triggered_alerts"
    
    print(f"✅ Response structure valid for toast notifications")
    print(f"   Keys: {list(result.keys())}")
    
    if result.get('triggered_alerts'):
        first_trigger = result['triggered_alerts'][0]
        required_fields = ['stock_name', 'ticker_symbol', 'alert_type', 'condition', 'threshold_value']
        for field in required_fields:
            assert field in first_trigger, f"Missing field: {field}"
        print(f"✅ Trigger data contains all required fields")
        print(f"   Sample: {first_trigger.get('stock_name')} - {first_trigger.get('alert_type')}")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/alerts/{alert_id}")
    print(f"✅ Cleaned up test alert")
    
    return True

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# Phase 3a Complete Integration Test")
    print("#"*60)
    
    all_passed = True
    
    try:
        test_earnings_alert_full()
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        all_passed = False
    
    try:
        test_composite_alert_full()
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        all_passed = False
    
    try:
        test_dashboard_statistics()
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        all_passed = False
    
    try:
        test_bulk_check()
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        all_passed = False
    
    try:
        test_toast_notification_data()
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        all_passed = False
    
    print("\n" + "#"*60)
    if all_passed:
        print("# ✅ ALL TESTS PASSED - Phase 3a Complete!")
    else:
        print("# ⚠️ Some tests failed - check output above")
    print("#"*60 + "\n")
