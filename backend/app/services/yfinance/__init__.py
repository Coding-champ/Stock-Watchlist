"""
yfinance service package - modularized version
Maintains backward compatibility by re-exporting all functions
"""

# Re-export all functions to maintain backward compatibility
# This ensures existing imports continue to work without changes

from .client import (
    _get_extended_period,
    _is_probable_isin,
    get_ticker_from_isin,
    StockInfo,
    _clean_for_json
)

from .stock_info import (
    get_stock_info_by_identifier,
    get_stock_info,
    get_fast_market_data,
    get_fast_market_data_with_timestamp,
    get_current_stock_data,
    search_stocks
)

from .price_data import (
    get_fast_stock_data,
    get_extended_stock_data,
    get_historical_prices,
    get_chart_data,
    get_intraday_chart_data
)

from .financial_data import (
    get_stock_dividends_and_splits,
    get_stock_calendar_and_earnings,
    get_analyst_data,
    get_institutional_holders
)

from .indicators import (
    calculate_technical_indicators,
    _calculate_atr_series,
    _calculate_vwap_rolling
)

# Maintain the same module interface
__all__ = [
    # Client utilities
    '_get_extended_period',
    '_is_probable_isin', 
    'get_ticker_from_isin',
    'StockInfo',
    '_clean_for_json',
    
    # Stock info
    'get_stock_info_by_identifier',
    'get_stock_info',
    'get_fast_market_data',
    'get_fast_market_data_with_timestamp',
    'get_current_stock_data',
    'search_stocks',
    
    # Price data
    'get_fast_stock_data',
    'get_extended_stock_data',
    'get_historical_prices',
    'get_chart_data',
    'get_intraday_chart_data',
    
    # Financial data
    'get_stock_dividends_and_splits',
    'get_stock_calendar_and_earnings',
    'get_analyst_data',
    'get_institutional_holders',
    
    # Technical indicators
    'calculate_technical_indicators',
    '_calculate_atr_series',
    '_calculate_vwap_rolling'
]
