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
