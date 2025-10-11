"""
Technical indicators and calculations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
import logging

# Import technical indicators from dedicated service
from backend.app.services.technical_indicators_service import (
    calculate_rsi,
    calculate_rsi_series
)

from .client import _clean_for_json

logger = logging.getLogger(__name__)


def calculate_technical_indicators(
    ticker_symbol: str,
    period: str = "1y",
    indicators: Optional[List[str]] = None,
    hist: Optional[pd.DataFrame] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate technical indicators for historical data.
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period for context
        indicators: List of indicators to calculate
        hist: Optional historical data DataFrame (if not provided, will fetch)
        
    Returns:
        Dictionary with calculated indicators or None
    """
    try:
        # If no historical data provided, fetch it
        if hist is None:
            import yfinance as yf
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
        
        if hist.empty:
            return None
        
        # Set default indicators if none provided
        if indicators is None:
            indicators = ['sma_50', 'sma_200']
        
        close_prices = hist['Close']
        high_prices = hist['High']
        low_prices = hist['Low']
        volume = hist['Volume']
        
        result = {
            'dates': [date.isoformat() for date in hist.index],
            'close': close_prices.tolist(),
            'indicators': {}
        }
        
        # Calculate each requested indicator
        for indicator in indicators:
            try:
                if indicator == 'sma_20':
                    result['indicators']['sma_20'] = close_prices.rolling(window=20).mean().tolist()
                elif indicator == 'sma_50':
                    result['indicators']['sma_50'] = close_prices.rolling(window=50).mean().tolist()
                elif indicator == 'sma_200':
                    result['indicators']['sma_200'] = close_prices.rolling(window=200).mean().tolist()
                elif indicator == 'ema_12':
                    result['indicators']['ema_12'] = close_prices.ewm(span=12).mean().tolist()
                elif indicator == 'ema_26':
                    result['indicators']['ema_26'] = close_prices.ewm(span=26).mean().tolist()
                elif indicator == 'rsi':
                    rsi_data = calculate_rsi_series(close_prices, period=14)
                    if rsi_data is not None:
                        result['indicators']['rsi'] = rsi_data.tolist()
                elif indicator == 'macd':
                    ema_12 = close_prices.ewm(span=12).mean()
                    ema_26 = close_prices.ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()
                    histogram = macd_line - signal_line
                    
                    result['indicators']['macd'] = {
                        'macd': macd_line.tolist(),
                        'signal': signal_line.tolist(),
                        'histogram': histogram.tolist()
                    }
                elif indicator == 'bollinger':
                    sma_20 = close_prices.rolling(window=20).mean()
                    std_20 = close_prices.rolling(window=20).std()
                    upper_band = sma_20 + (std_20 * 2)
                    lower_band = sma_20 - (std_20 * 2)
                    
                    result['indicators']['bollinger'] = {
                        'upper': upper_band.tolist(),
                        'middle': sma_20.tolist(),
                        'lower': lower_band.tolist()
                    }
                elif indicator == 'atr':
                    atr_data = _calculate_atr_series(high_prices, low_prices, close_prices)
                    if atr_data is not None:
                        result['indicators']['atr'] = atr_data.tolist()
                elif indicator == 'vwap':
                    vwap_data = _calculate_vwap_rolling(high_prices, low_prices, close_prices, volume)
                    if vwap_data is not None:
                        result['indicators']['vwap'] = vwap_data.tolist()
                        
            except Exception as e:
                logger.warning(f"Error calculating indicator {indicator}: {str(e)}")
                result['indicators'][indicator] = None
        
        return _clean_for_json(result)
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators: {str(e)}")
        return None


def _calculate_atr_series(high_prices: pd.Series, low_prices: pd.Series, close_prices: pd.Series, period: int = 14) -> Optional[pd.Series]:
    """
    Calculate Average True Range (ATR) series.
    
    Args:
        high_prices: Series of high prices
        low_prices: Series of low prices
        close_prices: Series of close prices
        period: Period for ATR calculation
        
    Returns:
        ATR series or None
    """
    try:
        if len(high_prices) < period + 1:
            return None
        
        # Calculate True Range
        tr1 = high_prices - low_prices
        tr2 = abs(high_prices - close_prices.shift(1))
        tr3 = abs(low_prices - close_prices.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR using Wilder's smoothing
        atr = true_range.ewm(alpha=1/period, adjust=False).mean()
        
        return atr
        
    except Exception as e:
        logger.error(f"Error calculating ATR: {str(e)}")
        return None


def _calculate_vwap_rolling(high_prices: pd.Series, low_prices: pd.Series, close_prices: pd.Series, volume: pd.Series, period: int = 20) -> Optional[pd.Series]:
    """
    Calculate Volume Weighted Average Price (VWAP) using rolling window.
    
    Args:
        high_prices: Series of high prices
        low_prices: Series of low prices
        close_prices: Series of close prices
        volume: Series of volume
        period: Rolling window period
        
    Returns:
        VWAP series or None
    """
    try:
        if len(high_prices) < period:
            return None
        
        # Calculate typical price (HLC/3)
        typical_price = (high_prices + low_prices + close_prices) / 3
        
        # Calculate VWAP using rolling window
        vwap = (typical_price * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
        
        return vwap
        
    except Exception as e:
        logger.error(f"Error calculating VWAP: {str(e)}")
        return None
