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
        from backend.app.services.chart_core import get_chart_with_indicators
        result = get_chart_with_indicators(
            ticker_symbol=ticker_symbol,
            period=period,
            indicators=indicators,
            include_volume=True
        )
        return _clean_for_json(result) if result else None
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
