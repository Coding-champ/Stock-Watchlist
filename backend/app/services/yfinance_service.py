"""
yfinance service for fetching stock information
"""

import yfinance as yf
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class StockInfo:
    """Class to hold stock information from yfinance"""
    def __init__(self, ticker: str, data: Dict[str, Any]):
        self.ticker = ticker
        self.name = data.get('longName', data.get('shortName', ticker))
        self.sector = data.get('sector')
        self.industry = data.get('industry')
        self.country = data.get('country')
        self.current_price = data.get('currentPrice', data.get('regularMarketPrice'))
        self.pe_ratio = data.get('trailingPE', data.get('forwardPE'))
        self.market_cap = data.get('marketCap')
        self.isin = data.get('isin', '')


def get_stock_info(ticker_symbol: str) -> Optional[StockInfo]:
    """
    Fetch stock information using yfinance
    
    Args:
        ticker_symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        StockInfo object or None if not found
    """
    try:
        # Create ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Get stock info
        info = ticker.info
        
        # Check if the ticker is valid (has basic info)
        if not info.get('longName') and not info.get('shortName'):
            logger.warning(f"No information found for ticker: {ticker_symbol}")
            return None
            
        return StockInfo(ticker_symbol, info)
        
    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker_symbol}: {e}")
        return None


def get_current_stock_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get current stock market data
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with current market data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        return {
            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
            'pe_ratio': info.get('trailingPE', info.get('forwardPE')),
            'market_cap': info.get('marketCap'),
            'volume': info.get('volume'),
            'day_high': info.get('dayHigh'),
            'day_low': info.get('dayLow'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data for {ticker_symbol}: {e}")
        return None


def search_stocks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for stocks (basic implementation - yfinance doesn't have direct search)
    This is a placeholder for a more sophisticated search implementation
    """
    # For now, just try to validate if the query is a valid ticker
    stock_info = get_stock_info(query.upper())
    if stock_info:
        return [{
            'ticker': stock_info.ticker,
            'name': stock_info.name,
            'sector': stock_info.sector,
            'industry': stock_info.industry,
            'country': stock_info.country
        }]
    return []