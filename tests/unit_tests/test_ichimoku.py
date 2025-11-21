import pandas as pd
import numpy as np
from backend.app.services.indicators_core import calculate_ichimoku


def make_ohlc(length=100, start=100.0, step=0.5):
    # simple synthetic uptrend data for deterministic results
    closes = [start + i * step for i in range(length)]
    highs = [c + 0.2 for c in closes]
    lows = [c - 0.2 for c in closes]
    return pd.Series(highs), pd.Series(lows), pd.Series(closes)


def test_ichimoku_happy_path():
    high, low, close = make_ohlc(length=200)
    df = calculate_ichimoku(high, low, close)

    # Expect columns present
    assert set(['conversion', 'base', 'span_a', 'span_b', 'chikou']).issubset(df.columns)

    # conversion and base should be pandas Series with numeric values after their windows
    # Tenkan (conversion) requires 9 periods, Kijun (base) requires 26 periods
    # Therefore from index 25 (0-based) base should have at least some non-nan values
    assert not df['conversion'].iloc[-1:].isna().all()
    # span_a & span_b are shifted forward by displacement (26) so their last values may be NaN
    # but the unshifted middle values (before the shift) should exist earlier
    # chikou is close shifted backward by displacement: its first displacement values will be present
    assert df['chikou'].isna().sum() <= 26


def test_ichimoku_short_series_edge_case():
    # Very short series (less than span_b default 52)
    high, low, close = make_ohlc(length=20)
    df = calculate_ichimoku(high, low, close)

    # When data too short, many fields expected to be NaN but function should not crash
    assert set(['conversion', 'base', 'span_a', 'span_b', 'chikou']).issubset(df.columns)
    # conversion (9) may still be NaN if length < 9
    # Ensure the function returns a DataFrame of the same length
    assert len(df) == 20
    # All columns should be pandas Series of length 20
    for col in ['conversion', 'base', 'span_a', 'span_b', 'chikou']:
        assert isinstance(df[col], pd.Series)

