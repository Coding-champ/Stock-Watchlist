"""
Time Series Utilities
Provides unified functions for time series data manipulation, date calculations, and filtering
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def calculate_period_cutoff_date(end_date: pd.Timestamp, period: str) -> Optional[pd.Timestamp]:
    """
    Calculate the cutoff date for filtering data to the requested period.
    
    Args:
        end_date: The end date of the data
        period: The requested period (e.g., '1y', '3y', '5y')
        
    Returns:
        The cutoff date (start of the requested period), or None if period is 'max' or unknown
    """
    period_map = {
        '1d': timedelta(days=1),
        '5d': timedelta(days=5),
        '1mo': timedelta(days=30),
        '2mo': timedelta(days=60),
        '3mo': timedelta(days=90),
        '6mo': timedelta(days=180),
        '1y': timedelta(days=365),
        '2y': timedelta(days=730),
        '3y': timedelta(days=1095),
        '5y': timedelta(days=1825),
        '10y': timedelta(days=3650),
    }
    
    delta = period_map.get(period)
    if delta:
        cutoff = end_date - delta
        return cutoff
    
    # For 'ytd', calculate from start of current year
    if period == 'ytd':
        return pd.Timestamp(datetime(end_date.year, 1, 1))
    
    # For 'max' or unknown periods, return None (no filtering)
    return None


def filter_indicators_by_dates(
    indicators_result: Dict[str, Any], 
    target_dates: List[str]
) -> Dict[str, Any]:
    """
    Filter indicator data to match the target date range.
    
    Args:
        indicators_result: Dictionary with 'dates' and 'indicators' keys
        target_dates: List of target dates to filter to (ISO format strings)
        
    Returns:
        Filtered indicators dictionary
    """
    if not indicators_result or not indicators_result.get('dates'):
        return {}
    
    source_dates = indicators_result['dates']
    indicators = indicators_result.get('indicators', {})
    
    # Convert target dates to set for faster lookup
    target_dates_set = set(target_dates)
    
    # Find matching indices
    matching_indices = [
        i for i, date in enumerate(source_dates)
        if date in target_dates_set
    ]
    
    if not matching_indices:
        return indicators  # Return all if no matches (safety fallback)
    
    # Filter each indicator
    filtered_indicators = {}
    for indicator_name, indicator_data in indicators.items():
        if isinstance(indicator_data, list):
            # Simple list indicator (e.g., sma_50, sma_200, rsi)
            filtered_indicators[indicator_name] = [
                indicator_data[i] if i < len(indicator_data) else None
                for i in matching_indices
            ]
        elif isinstance(indicator_data, dict):
            # Complex indicator with multiple series (e.g., macd, bollinger_bands)
            filtered_sub_indicator = {}
            for sub_key, sub_values in indicator_data.items():
                if isinstance(sub_values, list):
                    filtered_sub_indicator[sub_key] = [
                        sub_values[i] if i < len(sub_values) else None
                        for i in matching_indices
                    ]
                else:
                    # Non-list value, keep as-is
                    filtered_sub_indicator[sub_key] = sub_values
            filtered_indicators[indicator_name] = filtered_sub_indicator
        else:
            # Scalar or other type, keep as-is
            filtered_indicators[indicator_name] = indicator_data
    
    return filtered_indicators


def format_period_string(period_date) -> str:
    """
    Format period date to string like "FY2025Q3"
    
    Args:
        period_date: Pandas Timestamp or datetime
    
    Returns:
        Formatted period string (e.g., "FY2025Q3")
    """
    try:
        if hasattr(period_date, 'year'):
            year = period_date.year
            month = period_date.month
            quarter = (month - 1) // 3 + 1
            return f"FY{year}Q{quarter}"
        return str(period_date)
    except:
        return str(period_date)


def estimate_required_warmup_bars(indicators: Optional[List[str]]) -> Optional[int]:
    """
    Estimate the number of additional bars needed for accurate indicator calculation
    
    Args:
        indicators: List of indicator names to calculate
        
    Returns:
        Number of warmup bars needed, or None if no indicators specified
    """
    if not indicators:
        return None
    
    # Mapping of indicators to their warmup requirements
    warmup_requirements = {
        'sma_50': 50,
        'sma_200': 200,
        'sma_20': 20,
        'ema_12': 26,  # Use slow period for MACD
        'ema_26': 26,
        'rsi': 14,
        'macd': 26,  # slow period
        'bollinger_bands': 20,
        'atr': 14,
        'stochastic': 14,
        'vwap': 20,  # Typical period for VWAP calculation
        'obv': 0,  # OBV doesn't need warmup
    }
    
    # Find maximum warmup needed
    max_warmup = 0
    for indicator in indicators:
        # Handle both exact matches and prefixes (e.g., 'sma_50' or 'sma')
        for key, warmup in warmup_requirements.items():
            if indicator.startswith(key.split('_')[0]):
                max_warmup = max(max_warmup, warmup)
                break
    
    # Add some buffer (20%) to ensure clean calculations
    if max_warmup > 0:
        return int(max_warmup * 1.2)
    
    return None
