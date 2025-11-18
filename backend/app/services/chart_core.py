"""
chart_core.py: Centralized chart/visualization logic
Fetches price data, calculates overlays/indicators using indicators_core.py, returns unified chart data structure for API/frontend.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from backend.app.services.indicators_core import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_sma
)
from backend.app.services.yfinance.price_data import get_chart_data


def _sanitize_for_json(value):
    """Convert NaN/Infinity to None for JSON compliance."""
    if isinstance(value, (list, tuple)):
        return [_sanitize_for_json(v) for v in value]
    elif isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    elif isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    return value


def get_chart_with_indicators(
    ticker_symbol: str,
    period: str = "1y",
    interval: str = "1d",
    indicators: Optional[List[str]] = None,
    include_volume: bool = True,
    include_earnings: bool = False,
    start: Optional[str] = None,
    end: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch chart price data and calculate overlays/indicators.
    Returns unified chart data structure for API/frontend.
    """
    # Fetch price data
    chart_data = get_chart_data(
        ticker_symbol=ticker_symbol,
        period=period,
        interval=interval,
        start=start,
        end=end,
        include_dividends=True,
        include_volume=include_volume,
        include_earnings=include_earnings,
        indicators=indicators,
    )
    # Accept multiple possible keys for price data
    prices = None
    for key in ['prices', 'data', 'chart_data']:
        if chart_data and key in chart_data:
            prices = chart_data[key]
            break
    if not prices:
        return None
    df = pd.DataFrame(prices)
    # Guarantee arrays for all OHLCV keys and sanitize for JSON
    dates = _sanitize_for_json(df['date'].tolist()) if 'date' in df else []
    open_ = _sanitize_for_json(df['open'].tolist()) if 'open' in df else []
    high = _sanitize_for_json(df['high'].tolist()) if 'high' in df else []
    low = _sanitize_for_json(df['low'].tolist()) if 'low' in df else []
    close = _sanitize_for_json(df['close'].tolist()) if 'close' in df else []
    volume = _sanitize_for_json(df['volume'].tolist()) if 'volume' in df else []
    # Guarantee arrays, never undefined
    for arr in [dates, open_, high, low, close, volume]:
        if not isinstance(arr, list):
            arr = []
    result = {
        'dates': dates,
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'indicators': {},
        # pass through volume summary if backend provided it
        'volume_data': chart_data.get('volume_data') if chart_data and isinstance(chart_data, dict) and chart_data.get('volume_data') else None,
        # pass through dividends, splits, earnings if provided
        'dividends': chart_data.get('dividends', []) if chart_data and isinstance(chart_data, dict) else [],
        'dividends_annual': chart_data.get('dividends_annual', []) if chart_data and isinstance(chart_data, dict) else [],
        'splits': chart_data.get('splits', []) if chart_data and isinstance(chart_data, dict) else [],
        'earnings': chart_data.get('earnings', []) if chart_data and isinstance(chart_data, dict) else [],
        'metadata': chart_data.get('metadata', {}) if chart_data and isinstance(chart_data, dict) else {}
    }
    # If the fetched chart_data already contains precomputed indicators (with warmup), use them
    if chart_data and chart_data.get('indicators'):
        try:
            result['indicators'] = _sanitize_for_json(chart_data.get('indicators', {}))
            # Ensure indicator lists align with dates length; fallback to recompute if mismatch
            for name, series in list(result['indicators'].items()):
                if isinstance(series, list) and len(series) != len(dates):
                    # mismatch detected; drop indicators to allow local computation below
                    result['indicators'] = {}
                    break
        except Exception:
            # on any issue, fall back to local computation
            result['indicators'] = {}

    # Calculate requested indicators locally if not provided by chart_data
    if not result['indicators']:
        if indicators is None:
            indicators = ['sma_50', 'sma_200', 'rsi', 'macd', 'bollinger']
        close_prices = df['close'] if 'close' in df else pd.Series([])
        high_prices = df['high'] if 'high' in df else pd.Series([])
        low_prices = df['low'] if 'low' in df else pd.Series([])
        volume = df['volume'] if 'volume' in df else pd.Series([])
        for indicator in indicators:
            try:
                if indicator == 'sma_50':
                    result['indicators']['sma_50'] = _sanitize_for_json(calculate_sma(close_prices, 50).tolist())
                elif indicator == 'sma_200':
                    result['indicators']['sma_200'] = _sanitize_for_json(calculate_sma(close_prices, 200).tolist())
                elif indicator == 'rsi':
                    result['indicators']['rsi'] = _sanitize_for_json(calculate_rsi(close_prices, 14).tolist())
                elif indicator == 'macd':
                    macd_df = calculate_macd(close_prices)
                    result['indicators']['macd'] = {
                        'macd': _sanitize_for_json(macd_df['macd'].tolist()),
                        'signal': _sanitize_for_json(macd_df['signal'].tolist()),
                        'hist': _sanitize_for_json(macd_df['hist'].tolist())
                    }
                elif indicator == 'bollinger':
                    bb_df = calculate_bollinger_bands(close_prices)
                    result['indicators']['bollinger'] = {
                        'upper': _sanitize_for_json(bb_df['upper'].tolist()),
                        'middle': _sanitize_for_json(bb_df['sma'].tolist()),
                        'lower': _sanitize_for_json(bb_df['lower'].tolist())
                    }
            except Exception as e:
                result['indicators'][indicator] = None
        # also compute volume moving averages locally if volume series available
        try:
            if 'volume' in df and df['volume'].notna().any():
                vol_series = df['volume']
                # 10-day and 20-day moving averages using centralized calculation
                result['indicators']['volumeMA10'] = _sanitize_for_json(calculate_sma(vol_series, 10).fillna(value=np.nan).tolist())
                result['indicators']['volumeMA20'] = _sanitize_for_json(calculate_sma(vol_series, 20).fillna(value=np.nan).tolist())
        except Exception:
            # non-fatal
            pass
    return result
