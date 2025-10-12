"""
chart_core.py: Centralized chart/visualization logic
Fetches price data, calculates overlays/indicators using indicators_core.py, returns unified chart data structure for API/frontend.
"""

import pandas as pd
from typing import Optional, Dict, Any, List
from backend.app.services.indicators_core import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_sma
)
from backend.app.services.yfinance.price_data import get_chart_data


def get_chart_with_indicators(
    ticker_symbol: str,
    period: str = "1y",
    interval: str = "1d",
    indicators: Optional[List[str]] = None,
    include_volume: bool = True,
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
    # Guarantee arrays for all OHLCV keys
    dates = df['date'].tolist() if 'date' in df else []
    open_ = df['open'].tolist() if 'open' in df else []
    high = df['high'].tolist() if 'high' in df else []
    low = df['low'].tolist() if 'low' in df else []
    close = df['close'].tolist() if 'close' in df else []
    volume = df['volume'].tolist() if 'volume' in df else []
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
        'indicators': {}
    }
    # Calculate requested indicators
    if indicators is None:
        indicators = ['sma_50', 'sma_200', 'rsi', 'macd', 'bollinger']
    close_prices = df['close'] if 'close' in df else pd.Series([])
    high_prices = df['high'] if 'high' in df else pd.Series([])
    low_prices = df['low'] if 'low' in df else pd.Series([])
    volume = df['volume'] if 'volume' in df else pd.Series([])
    for indicator in indicators:
        try:
            if indicator == 'sma_50':
                result['indicators']['sma_50'] = calculate_sma(close_prices, 50).tolist()
            elif indicator == 'sma_200':
                result['indicators']['sma_200'] = calculate_sma(close_prices, 200).tolist()
            elif indicator == 'rsi':
                result['indicators']['rsi'] = calculate_rsi(close_prices, 14).tolist()
            elif indicator == 'macd':
                macd_df = calculate_macd(close_prices)
                result['indicators']['macd'] = {
                    'macd': macd_df['macd'].tolist(),
                    'signal': macd_df['signal'].tolist(),
                    'hist': macd_df['hist'].tolist()
                }
            elif indicator == 'bollinger':
                bb_df = calculate_bollinger_bands(close_prices)
                result['indicators']['bollinger'] = {
                    'upper': bb_df['upper'].tolist(),
                    'middle': bb_df['sma'].tolist(),
                    'lower': bb_df['lower'].tolist()
                }
        except Exception as e:
            result['indicators'][indicator] = None
    return result
