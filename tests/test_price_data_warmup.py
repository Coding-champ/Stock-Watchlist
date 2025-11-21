import pytest

from backend.app.services.yfinance import price_data


def test_estimate_required_warmup_bars_basic():
    assert price_data._estimate_required_warmup_bars(['sma_50']) == 50
    assert price_data._estimate_required_warmup_bars(['sma_200']) == 200
    assert price_data._estimate_required_warmup_bars(['rsi']) == 14
    assert price_data._estimate_required_warmup_bars(['macd']) == 35


def test_estimate_required_warmup_bars_mixed():
    # mixed indicators should return the maximum required window
    assert price_data._estimate_required_warmup_bars(['sma_50', 'rsi']) == 50
    assert price_data._estimate_required_warmup_bars(['sma_50', 'sma_200']) == 200


def test_period_mappings():
    assert price_data._period_to_days('1y') == 365
    assert price_data._period_to_days('6mo') == 180
    # period_for_days should map ranges appropriately
    assert price_data._period_for_days(30) == '1mo'
    assert price_data._period_for_days(365) == '1y'
