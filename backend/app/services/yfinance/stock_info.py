"""
Stock information and resolution functions
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from .client import StockInfo, _is_probable_isin, get_ticker_from_isin

logger = logging.getLogger(__name__)


def get_stock_info_by_identifier(identifier: str) -> Optional[StockInfo]:
    """
    Try to resolve stock information using either a ticker symbol or an ISIN.
    """
    if not identifier:
        return None

    normalized = identifier.strip().upper()
    if not normalized:
        return None

    stock_info = get_stock_info(normalized)
    if stock_info:
        return stock_info

    if _is_probable_isin(normalized):
        ticker = get_ticker_from_isin(normalized)
        if ticker:
            return get_stock_info(ticker)

    return None


def get_stock_info(ticker_symbol: str) -> Optional[StockInfo]:
    """
    Get comprehensive stock information for a given ticker symbol.
    
    Args:
        ticker_symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        StockInfo object with comprehensive stock data or None if not found
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or 'symbol' not in info:
            logger.warning(f"No data found for ticker: {ticker_symbol}")
            return None
        
        return StockInfo(ticker_symbol, info)
        
    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker_symbol}: {str(e)}")
        return None


def get_fast_market_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get fast market data using fast_info (optimized for speed)
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with fast market data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        fast = ticker.fast_info
        
        return {
            'ticker': ticker_symbol,
            'last_price': getattr(fast, 'last_price', None),
            'last_volume': getattr(fast, 'last_volume', None),
            'day_high': getattr(fast, 'day_high', None),
            'day_low': getattr(fast, 'day_low', None),
            'year_high': getattr(fast, 'year_high', None),
            'year_low': getattr(fast, 'year_low', None),
            'fifty_day_average': getattr(fast, 'fifty_day_average', None),
            'two_hundred_day_average': getattr(fast, 'two_hundred_day_average', None),
            'average_volume': getattr(fast, 'average_volume', None),
            'average_volume_10days': getattr(fast, 'average_volume_10days', None),
            'market_cap': getattr(fast, 'market_cap', None),
            'currency': getattr(fast, 'currency', None),
            'timezone': getattr(fast, 'timezone', None),
            'exchange': getattr(fast, 'exchange', None),
            'quote_type': getattr(fast, 'quote_type', None),
            'shares_outstanding': getattr(fast, 'shares_outstanding', None),
            'float_shares': getattr(fast, 'float_shares', None),
            'last_updated': getattr(fast, 'last_updated', None)
        }
    
    except Exception as e:
        logger.error(f"Error fetching fast market data for {ticker_symbol}: {str(e)}")
        return None


def _convert_epoch_to_iso(epoch_val):
    try:
        if epoch_val is None:
            return None
        # some yfinance fields may be strings
        if isinstance(epoch_val, str) and epoch_val.isdigit():
            epoch_val = int(epoch_val)
        if isinstance(epoch_val, (int, float)):
            return datetime.utcfromtimestamp(int(epoch_val)).isoformat() + 'Z'
        return None
    except Exception:
        return None


def get_fast_market_data_with_timestamp(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Wrapper around get_fast_market_data that also tries to provide a normalized
    ISO 8601 `timestamp` field. Preference order:
      1. fast_info.last_updated
      2. info.regularMarketTime (epoch seconds)
      3. info.lastUpdated (ISO / str) if present
    """
    try:
        data = get_fast_market_data(ticker_symbol)
        if not data:
            return None

        # Try fast_info.last_updated first
        ts = data.get('last_updated')
        if ts:
            # last_updated from fast_info may already be an ISO string or datetime
            if isinstance(ts, (int, float)):
                ts_iso = datetime.utcfromtimestamp(int(ts)).isoformat() + 'Z'
            else:
                try:
                    # Try to coerce to ISO string
                    ts_iso = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
                except Exception:
                    ts_iso = str(ts)
            data['timestamp'] = ts_iso
            return data

        # Fallback: check ticker.info for regularMarketTime
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info or {}
            reg_time = info.get('regularMarketTime')
            if reg_time:
                ts_iso = _convert_epoch_to_iso(reg_time) or (str(reg_time) if reg_time else None)
                if ts_iso:
                    data['timestamp'] = ts_iso
                    return data

            # lastUpdated may be present as ISO string
            last_up = info.get('lastUpdated')
            if last_up:
                data['timestamp'] = last_up if isinstance(last_up, str) else str(last_up)
                return data
        except Exception:
            # don't fail the whole call if info isn't available
            pass

        # Additional fallback: use get_current_stock_data which may expose other lastUpdated fields
        try:
            curr = get_current_stock_data(ticker_symbol)
            if curr and isinstance(curr, dict):
                lu = curr.get('last_updated') or curr.get('lastUpdated')
                if lu:
                    # normalize numeric epoch values
                    if isinstance(lu, (int, float)):
                        data['timestamp'] = datetime.utcfromtimestamp(int(lu)).isoformat() + 'Z'
                    else:
                        data['timestamp'] = lu if isinstance(lu, str) else str(lu)
                    return data
        except Exception:
            pass

        # No timestamp found
        return data
    except Exception as e:
        logger.error(f"Error fetching fast market data with timestamp for {ticker_symbol}: {e}")
        return None


def get_current_stock_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get current stock data including price, volume, and basic metrics.
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with current stock data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info:
            return None
        
        return {
            'ticker': ticker_symbol,
            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
            'previous_close': info.get('previousClose'),
            'day_high': info.get('dayHigh'),
            'day_low': info.get('dayLow'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'fifty_day_average': info.get('fiftyDayAverage'),
            'two_hundred_day_average': info.get('twoHundredDayAverage'),
            'volume': info.get('volume', info.get('regularMarketVolume')),
            'average_volume': info.get('averageVolume'),
            'average_volume_10days': info.get('averageVolume10days'),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency'),
            'exchange': info.get('exchange'),
            'market_state': info.get('marketState'),
            'last_updated': info.get('lastUpdated')
        }
        
    except Exception as e:
        logger.error(f"Error fetching current stock data for {ticker_symbol}: {str(e)}")
        return None


def search_stocks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for stocks by ticker symbol or company name.
    
    Args:
        query: Search query (ticker symbol or company name)
        limit: Maximum number of results to return
        
    Returns:
        List of stock information dictionaries
    """
    try:
        # Use yfinance search functionality
        search_results = yf.search(query)
        
        if search_results is None or search_results.empty:
            return []
        
        # Convert to list of dictionaries
        results = []
        for _, row in search_results.head(limit).iterrows():
            results.append({
                'ticker': row.get('symbol', ''),
                'name': row.get('longname', row.get('shortname', '')),
                'exchange': row.get('exchange', ''),
                'type': row.get('type', ''),
                'sector': row.get('sector', ''),
                'industry': row.get('industry', '')
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching stocks for query '{query}': {str(e)}")
        return []
