"""
Test script to verify all dependencies are working correctly after refactoring
"""
import sys
sys.path.append('d:/Programmieren/Projekte/Produktiv/Web Development/Stock-Watchlist')

def test_imports():
    """Test that all imports work correctly"""
    print("=" * 80)
    print("TESTING IMPORTS AFTER REFACTORING")
    print("=" * 80)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Technical Indicators Service
    print("\n1. Testing technical_indicators_service imports...")
    try:
        from backend.app.services.technical_indicators_service import (
            calculate_rsi,
            calculate_macd,
            detect_rsi_divergence,
            detect_macd_divergence,
            analyze_technical_indicators_with_divergence
        )
        print("   ✅ technical_indicators_service imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 2: Calculated Metrics Service
    print("\n2. Testing calculated_metrics_service imports...")
    try:
        from backend.app.services.calculated_metrics_service import (
            calculate_52week_distance,
            calculate_all_metrics
        )
        print("   ✅ calculated_metrics_service imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 3: YFinance Service
    print("\n3. Testing yfinance_service imports...")
    try:
        from backend.app.services.yfinance_service import (
            get_stock_info,
            get_chart_data,
            calculate_technical_indicators
        )
        print("   ✅ yfinance_service imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 4: Alert Service
    print("\n4. Testing alert_service imports...")
    try:
        from backend.app.services.alert_service import AlertService
        print("   ✅ alert_service imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 5: Stock Data Routes
    print("\n5. Testing stock_data routes imports...")
    try:
        from backend.app.routes.stock_data import router
        print("   ✅ stock_data routes imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 6: Calculate RSI via imported function
    print("\n6. Testing RSI calculation through calculated_metrics_service...")
    try:
        from backend.app.services.calculated_metrics_service import calculate_rsi
        import pandas as pd
        import numpy as np
        
        # Create sample data
        prices = pd.Series(np.random.randn(50).cumsum() + 100)
        result = calculate_rsi(prices)
        
        if result.get('value') is not None:
            print(f"   ✅ RSI calculation works: {result['value']:.2f}")
            tests_passed += 1
        else:
            print("   ❌ RSI calculation returned None")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 7: Calculate MACD via imported function
    print("\n7. Testing MACD calculation through calculated_metrics_service...")
    try:
        from backend.app.services.calculated_metrics_service import calculate_macd
        import pandas as pd
        import numpy as np
        
        # Create sample data
        prices = pd.Series(np.random.randn(100).cumsum() + 100)
        result = calculate_macd(prices)
        
        if result.get('macd_line') is not None:
            print(f"   ✅ MACD calculation works: {result['macd_line']:.4f}")
            tests_passed += 1
        else:
            print("   ❌ MACD calculation returned None")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED! Refactoring successful!")
        return True
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please review errors above.")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
