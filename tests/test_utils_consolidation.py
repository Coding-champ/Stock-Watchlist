"""
Quick validation script for consolidated helper functions
Tests that all new utils work correctly and old deprecated functions still work
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

import numpy as np
import pandas as pd
from datetime import datetime


def test_signal_interpretation():
    """Test signal interpretation utilities"""
    print("🎯 Testing Signal Interpretation...")
    
    from backend.app.utils.signal_interpretation import interpret_rsi, interpret_macd
    
    # Test RSI interpretation
    assert interpret_rsi(75) == 'overbought', "RSI 75 should be overbought"
    assert interpret_rsi(25) == 'oversold', "RSI 25 should be oversold"
    assert interpret_rsi(65) == 'bullish', "RSI 65 should be bullish"
    assert interpret_rsi(35) == 'bearish', "RSI 35 should be bearish"
    assert interpret_rsi(50) == 'neutral', "RSI 50 should be neutral"
    
    # Test MACD interpretation
    assert interpret_macd(1.5) == 'bullish', "MACD histogram > 0 should be bullish"
    assert interpret_macd(-1.5) == 'bearish', "MACD histogram < 0 should be bearish"
    assert interpret_macd(0) == 'neutral', "MACD histogram = 0 should be neutral"
    
    print("✅ Signal Interpretation: All tests passed!")
    return True


def test_json_serialization():
    """Test JSON serialization utilities"""
    print("🧹 Testing JSON Serialization...")
    
    from backend.app.utils.json_serialization import clean_for_json, clean_json_floats
    
    # Test clean_for_json with numpy types
    data = {
        'int': np.int64(42),
        'float': np.float64(3.14),
        'array': np.array([1, 2, 3]),
        'nan': np.nan,
        'nested': {
            'value': np.int32(100)
        }
    }
    
    cleaned = clean_for_json(data)
    assert isinstance(cleaned['int'], int), "numpy int64 should become Python int"
    assert isinstance(cleaned['float'], float), "numpy float64 should become Python float"
    assert isinstance(cleaned['array'], list), "numpy array should become list"
    assert cleaned['nan'] is None, "numpy.nan should become None"
    assert isinstance(cleaned['nested']['value'], int), "Nested numpy types should be cleaned"
    
    # Test clean_json_floats
    float_data = {
        'nan': float('nan'),
        'inf': float('inf'),
        'normal': 42.5,
        'nested': {
            'bad': float('-inf')
        }
    }
    
    cleaned_floats = clean_json_floats(float_data)
    assert cleaned_floats['nan'] is None, "NaN should become None"
    assert cleaned_floats['inf'] is None, "Infinity should become None"
    assert cleaned_floats['normal'] == 42.5, "Normal floats should stay unchanged"
    assert cleaned_floats['nested']['bad'] is None, "Nested infinity should become None"
    
    print("✅ JSON Serialization: All tests passed!")
    return True


def test_time_series_utils():
    """Test time series utilities"""
    print("📅 Testing Time Series Utils...")
    
    from backend.app.utils.time_series_utils import (
        calculate_period_cutoff_date,
        filter_indicators_by_dates,
        format_period_string,
        estimate_required_warmup_bars
    )
    
    # Test calculate_period_cutoff_date
    end_date = pd.Timestamp('2025-01-01')
    cutoff_1y = calculate_period_cutoff_date(end_date, '1y')
    assert cutoff_1y.year == 2024, "1y cutoff should be 1 year before"
    
    cutoff_ytd = calculate_period_cutoff_date(end_date, 'ytd')
    assert cutoff_ytd.month == 1 and cutoff_ytd.day == 1, "YTD should start at Jan 1"
    
    cutoff_max = calculate_period_cutoff_date(end_date, 'max')
    assert cutoff_max is None, "Max period should return None"
    
    # Test filter_indicators_by_dates
    indicators_result = {
        'dates': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'indicators': {
            'rsi': [70, 65, 60],
            'macd': {
                'line': [1.0, 1.5, 2.0],
                'signal': [0.5, 1.0, 1.5]
            }
        }
    }
    
    filtered = filter_indicators_by_dates(indicators_result, ['2025-01-01', '2025-01-03'])
    assert len(filtered['rsi']) == 2, "Filtered RSI should have 2 values"
    assert filtered['rsi'] == [70, 60], "Filtered values should match target dates"
    
    # Test format_period_string
    period = pd.Timestamp('2025-09-30')
    formatted = format_period_string(period)
    assert formatted == 'FY2025Q3', "Should format as FY2025Q3"
    
    # Test estimate_required_warmup_bars
    indicators = ['sma_200', 'rsi']
    warmup = estimate_required_warmup_bars(indicators)
    assert warmup is not None and warmup > 0, f"Warmup should be > 0, got {warmup}"
    print(f"  ℹ️  Warmup calculation returned {warmup} bars for {indicators}")
    
    warmup_none = estimate_required_warmup_bars(None)
    assert warmup_none is None, "No indicators should return None"
    
    print("✅ Time Series Utils: All tests passed!")
    return True


def test_indicator_interpretation_stable():
    """Ensure public interpretation utilities remain stable after wrapper removal"""
    print("🔄 Testing Indicator Interpretation Stability...")
    from backend.app.utils.signal_interpretation import interpret_rsi, interpret_macd
    assert interpret_rsi(75) == 'overbought'
    assert interpret_macd(1.5) == 'bullish'
    print("✅ Indicator Interpretation Stability: All tests passed!")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 HELPER FUNCTIONS CONSOLIDATION - VALIDATION TESTS")
    print("=" * 60)
    print()
    
    try:
        results = []
        results.append(test_signal_interpretation())
        results.append(test_json_serialization())
        results.append(test_time_series_utils())
        results.append(test_indicator_interpretation_stable())
        
        print()
        print("=" * 60)
        if all(results):
            print("🎉 ALL TESTS PASSED! Consolidation successful!")
        else:
            print("❌ SOME TESTS FAILED! Please review.")
        print("=" * 60)
        
        return 0 if all(results) else 1
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
