"""
Indicators Core: Zentrale Berechnungsfunktionen für technische Indikatoren (RSI, MACD, SMA, Bollinger Bands)
Alle Funktionen sind pure Python und nutzen pandas.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union

def calculate_sma(series: Union[pd.Series, list], window: int) -> pd.Series:
    return pd.Series(series).rolling(window=window, min_periods=window).mean()

def calculate_rsi(series: Union[pd.Series, list], period: int = 14) -> pd.Series:
    series = pd.Series(series)
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series: Union[pd.Series, list], fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    series = pd.Series(series)
    ema_fast = series.ewm(span=fast, min_periods=fast).mean()
    ema_slow = series.ewm(span=slow, min_periods=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, min_periods=signal).mean()
    hist = macd - signal_line
    return pd.DataFrame({
        'macd': macd,
        'signal': signal_line,
        'hist': hist
    })

def calculate_bollinger_bands(series: Union[pd.Series, list], window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    series = pd.Series(series)
    sma = series.rolling(window=window, min_periods=window).mean()
    std = series.rolling(window=window, min_periods=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return pd.DataFrame({
        'sma': sma,
        'upper': upper_band,
        'lower': lower_band
    })


def calculate_stochastic(
    high: Union[pd.Series, list],
    low: Union[pd.Series, list],
    close: Union[pd.Series, list],
    period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3
) -> pd.DataFrame:
    """
    Berechnet Stochastic Oscillator (%K und %D).
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Lookback period for %K (default: 14)
        smooth_k: Smoothing period for %K (default: 3)
        smooth_d: Smoothing period for %D (default: 3)
        
    Returns:
        DataFrame with columns 'k_percent' and 'd_percent'
    """
    high_s = pd.Series(high)
    low_s = pd.Series(low)
    close_s = pd.Series(close)
    
    # Calculate raw %K
    lowest_low = low_s.rolling(window=period, min_periods=period).min()
    highest_high = high_s.rolling(window=period, min_periods=period).max()
    k_raw = 100 * ((close_s - lowest_low) / (highest_high - lowest_low))
    
    # Apply smoothing to %K
    if smooth_k > 1:
        k_percent = calculate_sma(k_raw, smooth_k)
    else:
        k_percent = k_raw
    
    # Calculate %D (signal line)
    d_percent = calculate_sma(k_percent, smooth_d)
    
    return pd.DataFrame({
        'k_percent': k_percent,
        'd_percent': d_percent
    })


def calculate_ichimoku(
    high: Union[pd.Series, list],
    low: Union[pd.Series, list],
    close: Union[pd.Series, list],
    conversion: int = 9,
    base: int = 26,
    span_b: int = 52,
    displacement: int = 26
) -> pd.DataFrame:
    """
    Berechnet die Ichimoku-Komponenten.

    Returns DataFrame with columns:
      - conversion (Tenkan-sen)
      - base (Kijun-sen)
      - span_a (Senkou Span A) -- shifted forward by `displacement`
      - span_b (Senkou Span B) -- shifted forward by `displacement`
      - chikou (Chikou Span)  -- close shifted backward by `displacement`

    All series are aligned to the original index (NaN where not available).
    """
    high_s = pd.Series(high)
    low_s = pd.Series(low)
    close_s = pd.Series(close)

    # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    conv_high = high_s.rolling(window=conversion, min_periods=conversion).max()
    conv_low = low_s.rolling(window=conversion, min_periods=conversion).min()
    conversion_line = (conv_high + conv_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    base_high = high_s.rolling(window=base, min_periods=base).max()
    base_low = low_s.rolling(window=base, min_periods=base).min()
    base_line = (base_high + base_low) / 2

    # Senkou Span A: (Conversion + Base) / 2 -> shifted forward by displacement
    span_a = ((conversion_line + base_line) / 2).shift(periods=displacement)

    # Senkou Span B: (52-period high + 52-period low) / 2 -> shifted forward
    spanb_high = high_s.rolling(window=span_b, min_periods=span_b).max()
    spanb_low = low_s.rolling(window=span_b, min_periods=span_b).min()
    span_b_line = ((spanb_high + spanb_low) / 2).shift(periods=displacement)

    # Chikou Span: close shifted backward by displacement (plotted to the left)
    chikou = close_s.shift(periods=-displacement)

    return pd.DataFrame({
        'conversion': conversion_line,
        'base': base_line,
        'span_a': span_a,
        'span_b': span_b_line,
        'chikou': chikou
    })
