#!/usr/bin/env python3
"""
Test für die behobenen Funktionssignaturen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_fixed_functions():
    """Testet die behobenen Funktionssignaturen"""
    
    print("🔧 Test: Behobene Funktionssignaturen")
    print("=" * 40)
    
    try:
        # Test 1: calculate_technical_indicators mit neuen Parametern
        print("📊 Teste calculate_technical_indicators...")
        from backend.app.services.yfinance import calculate_technical_indicators
        
        result = calculate_technical_indicators(
            ticker_symbol="AAPL",
            period="1y",
            indicators=["sma_50", "vwap"]
        )
        
        if result:
            print("✅ calculate_technical_indicators funktioniert")
            print(f"   - Dates: {len(result.get('dates', []))}")
            print(f"   - Indicators: {list(result.get('indicators', {}).keys())}")
        else:
            print("⚠️ calculate_technical_indicators: Keine Daten")
        
        # Test 2: get_chart_data mit neuen Parametern
        print("\n📈 Teste get_chart_data...")
        from backend.app.services.yfinance import get_chart_data
        
        chart_result = get_chart_data(
            ticker_symbol="AAPL",
            period="1mo",
            interval="1d",
            include_volume=True
        )
        
        if chart_result:
            print("✅ get_chart_data funktioniert")
            print(f"   - Data points: {len(chart_result.get('data', []))}")
            print(f"   - Ticker: {chart_result.get('ticker')}")
        else:
            print("⚠️ get_chart_data: Keine Daten")
        
        print("\n🎉 Alle Tests erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fixed_functions()
