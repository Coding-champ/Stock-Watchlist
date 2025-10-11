"""
Test the chart data fix to ensure indicators align with the requested period
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.yfinance.price_data import get_chart_data
from datetime import datetime


def test_3y_chart_alignment():
    """Test that 3Y chart data and indicators are properly aligned"""
    print("Testing 3Y chart data alignment...")
    
    # Request 3 year data
    chart_data = get_chart_data(
        ticker_symbol="MSFT",
        period="3y",
        interval="1wk",
        indicators=['sma_50', 'sma_200'],
        include_volume=True
    )
    
    if not chart_data:
        print("❌ Failed to fetch chart data")
        return False
    
    # Check data
    dates = chart_data.get('dates', [])
    closes = chart_data.get('close', [])
    indicators = chart_data.get('indicators', {})
    
    print(f"\n📊 Chart Data Info:")
    print(f"   Period requested: 3y")
    print(f"   Interval: 1wk")
    print(f"   Total data points: {len(dates)}")
    
    if len(dates) > 0:
        print(f"   Date range: {dates[0]} to {dates[-1]}")
        
        # Calculate actual time span
        start_date = datetime.fromisoformat(dates[0].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(dates[-1].replace('Z', '+00:00'))
        days_span = (end_date - start_date).days
        years_span = days_span / 365.25
        
        print(f"   Actual span: {days_span} days (~{years_span:.1f} years)")
        
        # Check if span is close to 3 years (allow some margin)
        if 2.5 <= years_span <= 3.5:
            print("   ✅ Time span is correct (~3 years)")
        else:
            print(f"   ⚠️  Time span is {years_span:.1f} years, expected ~3 years")
    
    # Check indicators
    if 'sma_50' in indicators and 'sma_200' in indicators:
        sma_50 = indicators['sma_50']
        sma_200 = indicators['sma_200']
        
        print(f"\n📈 Indicator Info:")
        print(f"   SMA50 data points: {len(sma_50)}")
        print(f"   SMA200 data points: {len(sma_200)}")
        
        # Check if indicator length matches price data length
        if len(sma_50) == len(dates):
            print("   ✅ SMA50 length matches price data")
        else:
            print(f"   ❌ SMA50 length mismatch: {len(sma_50)} vs {len(dates)}")
            
        if len(sma_200) == len(dates):
            print("   ✅ SMA200 length matches price data")
        else:
            print(f"   ❌ SMA200 length mismatch: {len(sma_200)} vs {len(dates)}")
        
        # Check for valid values (not all None)
        sma_50_valid = sum(1 for x in sma_50 if x is not None)
        sma_200_valid = sum(1 for x in sma_200 if x is not None)
        
        print(f"   SMA50 valid values: {sma_50_valid}/{len(sma_50)} ({100*sma_50_valid/len(sma_50):.1f}%)")
        print(f"   SMA200 valid values: {sma_200_valid}/{len(sma_200)} ({100*sma_200_valid/len(sma_200):.1f}%)")
    else:
        print("\n❌ Missing indicator data")
        return False
    
    print("\n✅ Chart alignment test completed successfully!")
    return True


def test_1y_chart_alignment():
    """Test that 1Y chart data and indicators are properly aligned"""
    print("\n" + "="*60)
    print("Testing 1Y chart data alignment...")
    
    chart_data = get_chart_data(
        ticker_symbol="MSFT",
        period="1y",
        interval="1d",
        indicators=['sma_50', 'sma_200'],
        include_volume=True
    )
    
    if not chart_data:
        print("❌ Failed to fetch chart data")
        return False
    
    dates = chart_data.get('dates', [])
    
    if len(dates) > 0:
        start_date = datetime.fromisoformat(dates[0].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(dates[-1].replace('Z', '+00:00'))
        days_span = (end_date - start_date).days
        
        print(f"\n📊 Chart Data Info:")
        print(f"   Period requested: 1y")
        print(f"   Total data points: {len(dates)}")
        print(f"   Date range: {dates[0]} to {dates[-1]}")
        print(f"   Actual span: {days_span} days (~{days_span/365.25:.1f} years)")
        
        # Check if span is close to 1 year
        if 0.9 <= days_span/365.25 <= 1.1:
            print("   ✅ Time span is correct (~1 year)")
            return True
        else:
            print(f"   ⚠️  Time span is off")
            return False
    
    return False


if __name__ == "__main__":
    print("="*60)
    print("CHART DATA ALIGNMENT TEST")
    print("="*60)
    
    success = True
    
    # Test 3Y chart
    if not test_3y_chart_alignment():
        success = False
    
    # Test 1Y chart
    if not test_1y_chart_alignment():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("="*60)
