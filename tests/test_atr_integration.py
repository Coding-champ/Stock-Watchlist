import pytest

from backend.app.services.yfinance.price_data import get_chart_data


def test_atr_integration_includes_atr_series():
    """Integration test: requesting ATR should return indicators['atr'] and per-point 'atr' in chart_data."""
    # call with default include_volume (True) to match typical API usage
    d = get_chart_data('AAPL', period='1y', indicators=['atr'])
    assert d is not None, "get_chart_data returned None"
    assert 'indicators' in d, "indicators key missing in result"
    atr = d['indicators'].get('atr')
    assert isinstance(atr, list), "indicators['atr'] is not a list"
    # At least one non-null value expected in the ATR series
    assert any(v is not None for v in atr), "ATR series appears empty or all None"

    # Chart data should contain per-point 'atr' where available
    chart_data = d.get('chart_data') or d.get('data')
    assert isinstance(chart_data, list) and len(chart_data) > 0, "chart_data is empty"
    assert any(('atr' in p and p['atr'] is not None) for p in chart_data), "No per-point 'atr' values found in chart_data"
