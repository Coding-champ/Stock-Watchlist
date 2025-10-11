"""
Price data and chart functions
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from .client import _get_extended_period, _clean_for_json

logger = logging.getLogger(__name__)


def _calculate_period_cutoff_date(end_date: pd.Timestamp, period: str) -> pd.Timestamp:
    """
    Calculate the cutoff date for filtering data to the requested period.
    
    Args:
        end_date: The end date of the data
        period: The requested period (e.g., '1y', '3y', '5y')
        
    Returns:
        The cutoff date (start of the requested period)
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


def _filter_indicators_by_dates(indicators_result: Dict[str, Any], target_dates: List[str]) -> Dict[str, Any]:
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
            # Complex indicator with multiple series (e.g., macd, bollinger)
            filtered_dict = {}
            for key, values in indicator_data.items():
                if isinstance(values, list):
                    filtered_dict[key] = [
                        values[i] if i < len(values) else None
                        for i in matching_indices
                    ]
                else:
                    filtered_dict[key] = values
            filtered_indicators[indicator_name] = filtered_dict
        else:
            # Non-list data, keep as is
            filtered_indicators[indicator_name] = indicator_data
    
    return filtered_indicators


def get_fast_stock_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get fast stock data using fast_info (optimized for speed)
    Returns basic price, volume, and market data
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with fast stock data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        fast_info = ticker.fast_info
        
        return {
            # Price Data (from fast_info - much faster)
            'price_data': {
                'current_price': getattr(fast_info, 'last_price', None),
                'day_high': getattr(fast_info, 'day_high', None),
                'day_low': getattr(fast_info, 'day_low', None),
                'fifty_two_week_high': getattr(fast_info, 'year_high', None),
                'fifty_two_week_low': getattr(fast_info, 'year_low', None),
                'fifty_day_average': getattr(fast_info, 'fifty_day_average', None),
                'two_hundred_day_average': getattr(fast_info, 'two_hundred_day_average', None)
            },
            
            # Volume Data (from fast_info)
            'volume_data': {
                'volume': getattr(fast_info, 'last_volume', None),
                'average_volume': getattr(fast_info, 'average_volume', None),
                'average_volume_10days': getattr(fast_info, 'average_volume_10days', None)
            },
            
            # Basic Market Data (from fast_info)
            'market_data': {
                'market_cap': getattr(fast_info, 'market_cap', None),
                'currency': getattr(fast_info, 'currency', None),
                'timezone': getattr(fast_info, 'timezone', None)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching fast stock data for {ticker_symbol}: {e}")
        return None


def get_extended_stock_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get extended stock data including financial ratios, cashflow, dividends, and risk metrics
    Optimized: Uses fast_info for basic data, info only for detailed financials
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with extended stock data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get fast data first (much faster)
        fast_data = get_fast_stock_data(ticker_symbol)
        if not fast_data:
            return None
        
        # Get detailed info only for financial data (slower but necessary)
        info = ticker.info
        
        # Get historical data for volatility calculation
        hist = ticker.history(period="1y")
        volatility_30d = None
        if not hist.empty and len(hist) >= 30:
            # Calculate 30-day annualized volatility
            returns = hist['Close'].pct_change().dropna()
            if len(returns) >= 30:
                volatility_30d = returns.tail(30).std() * (252 ** 0.5)  # Annualized
        
        return {
            # Business Summary (info only)
            'business_summary': info.get('longBusinessSummary', ''),
            
            # Financial Ratios (info only - detailed financials)
            'financial_ratios': {
                'pe_ratio': info.get('trailingPE', info.get('forwardPE')),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'market_cap': fast_data['market_data']['market_cap']  # Use fast_info version
            },
            
            # Cashflow Data (info only)
            'cashflow_data': {
                'operating_cashflow': info.get('operatingCashflow'),
                'free_cashflow': info.get('freeCashflow'),
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),
                'debt_to_equity': info.get('debtToEquity')
            },
            
            # Dividend Info (info only)
            'dividend_info': {
                'dividend_rate': info.get('dividendRate'),
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield'),
                'ex_dividend_date': info.get('exDividendDate')
            },
            
            # Price Data (use fast_info version - much faster)
            'price_data': fast_data['price_data'],
            
            # Volume Data (use fast_info version - much faster)
            'volume_data': fast_data['volume_data'],
            
            # Volatility & Risk (mix of info and calculated)
            'risk_metrics': {
                'beta': info.get('beta'),
                'volatility_30d': volatility_30d,
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'held_percent_insiders': info.get('heldPercentInsiders'),
                'held_percent_institutions': info.get('heldPercentInstitutions')
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching extended stock data for {ticker_symbol}: {e}")
        return None


def get_historical_prices(ticker_symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Get historical price data for a stock.
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        DataFrame with historical price data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            logger.warning(f"No historical data found for {ticker_symbol}")
            return None
        
        return hist
        
    except Exception as e:
        logger.error(f"Error fetching historical prices for {ticker_symbol}: {str(e)}")
        return None


def get_chart_data(
    ticker_symbol: str,
    period: str = "1y",
    interval: str = "1d",
    indicators: List[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    include_dividends: bool = False,
    include_volume: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive chart data including price history and technical indicators.
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period for data (display period)
        interval: Data interval
        indicators: List of technical indicators to calculate
        start: Start date (overrides period)
        end: End date (overrides period)
        include_dividends: Whether to include dividend data
        include_volume: Whether to include volume data
        
    Returns:
        Dictionary with chart data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get historical data
        if start and end:
            # Use specific date range - no filtering needed
            hist = ticker.history(start=start, end=end, interval=interval)
            cutoff_date = None
        else:
            # Use extended period for better indicator calculations
            extended_period = _get_extended_period(period)
            hist = ticker.history(period=extended_period, interval=interval)
            
            # Calculate cutoff date to filter back to requested period
            # We load extra data for indicators but only return the requested period
            if not hist.empty and extended_period != period:
                cutoff_date = _calculate_period_cutoff_date(hist.index[-1], period)
            else:
                cutoff_date = None
        
        if hist.empty:
            logger.warning(f"No chart data found for {ticker_symbol}")
            return None
        
        # Calculate indicators on full dataset (with warmup period)
        indicators_result = None
        if indicators:
            from .indicators import calculate_technical_indicators
            indicators_result = calculate_technical_indicators(
                ticker_symbol=ticker_symbol,
                period=period,
                indicators=indicators,
                hist=hist  # Pass full historical data for accurate indicator calculation
            )
        
        # Filter data to requested period if we loaded extended data
        if cutoff_date:
            hist = hist[hist.index >= cutoff_date]
            logger.debug(f"Filtered data from {cutoff_date} to {hist.index[-1]} for period {period}")
        
        # Prepare chart data
        chart_data = []
        for date, row in hist.iterrows():
            data_point = {
                'date': date.isoformat(),
                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                'high': float(row['High']) if pd.notna(row['High']) else None,
                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                'close': float(row['Close']) if pd.notna(row['Close']) else None
            }
            
            # Handle Adj Close column (name can vary)
            adj_close_col = None
            for col_name in ['Adj Close', 'Adj_Close', 'AdjClose']:
                if col_name in row:
                    adj_close_col = col_name
                    break
            
            if adj_close_col:
                data_point['adj_close'] = float(row[adj_close_col]) if pd.notna(row[adj_close_col]) else None
            else:
                data_point['adj_close'] = None
            
            # Include volume if requested
            if include_volume and 'Volume' in row:
                data_point['volume'] = int(row['Volume']) if pd.notna(row['Volume']) else None
            
            chart_data.append(data_point)
        
        # Extract dates and separate arrays for frontend compatibility
        dates = [item['date'] for item in chart_data]
        opens = [item['open'] for item in chart_data]
        highs = [item['high'] for item in chart_data]
        lows = [item['low'] for item in chart_data]
        closes = [item['close'] for item in chart_data]
        volumes = [item['volume'] for item in chart_data]
        
        result = {
            'ticker': ticker_symbol,
            'period': period,
            'interval': interval,
            'dates': dates,  # Frontend expects this
            'open': opens,   # Frontend expects this
            'high': highs,   # Frontend expects this
            'low': lows,     # Frontend expects this
            'close': closes, # Frontend expects this
            'volume': volumes, # Frontend expects this
            'chart_data': chart_data,  # Keep for backward compatibility
            'data': chart_data,  # Keep for backward compatibility
            'indicators': {}
        }
        
        # Add filtered indicators to result
        if indicators_result and indicators_result.get('indicators'):
            # Filter indicators to match the filtered date range
            if cutoff_date and indicators_result.get('dates'):
                filtered_indicators = _filter_indicators_by_dates(
                    indicators_result, 
                    dates
                )
                result['indicators'] = filtered_indicators
            else:
                result['indicators'] = indicators_result.get('indicators', {})
        
        return _clean_for_json(result)
        
    except Exception as e:
        logger.error(f"Error fetching chart data for {ticker_symbol}: {str(e)}")
        return None


def get_intraday_chart_data(ticker_symbol: str, days: int = 1) -> Optional[Dict[str, Any]]:
    """
    Get intraday chart data for a stock.
    
    Args:
        ticker_symbol: Stock ticker symbol
        days: Number of days of intraday data (1, 2, 5, 15, 30, 60, 90)
        
    Returns:
        Dictionary with intraday chart data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Determine interval based on days
        if days <= 1:
            interval = "1m"
        elif days <= 2:
            interval = "2m"
        elif days <= 5:
            interval = "5m"
        elif days <= 15:
            interval = "15m"
        elif days <= 30:
            interval = "30m"
        elif days <= 60:
            interval = "60m"
        else:
            interval = "90m"
        
        # Get intraday data
        hist = ticker.history(period=f"{days}d", interval=interval)
        
        if hist.empty:
            logger.warning(f"No intraday data found for {ticker_symbol}")
            return None
        
        # Prepare intraday data
        intraday_data = []
        for date, row in hist.iterrows():
            data_point = {
                'datetime': date.isoformat(),
                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                'high': float(row['High']) if pd.notna(row['High']) else None,
                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                'close': float(row['Close']) if pd.notna(row['Close']) else None
            }
            
            # Include volume if available
            if 'Volume' in row:
                data_point['volume'] = int(row['Volume']) if pd.notna(row['Volume']) else None
            
            intraday_data.append(data_point)
        
        return {
            'ticker': ticker_symbol,
            'days': days,
            'interval': interval,
            'data': intraday_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching intraday chart data for {ticker_symbol}: {str(e)}")
        return None
