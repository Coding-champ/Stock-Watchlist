"""
yfinance service for fetching stock information
"""

import yfinance as yf
import pandas as pd
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
        
        # Business Summary
        self.business_summary = data.get('longBusinessSummary', '')
        
        # Financial Ratios
        self.peg_ratio = data.get('pegRatio')
        self.price_to_book = data.get('priceToBook')
        self.price_to_sales = data.get('priceToSalesTrailing12Months')
        self.profit_margins = data.get('profitMargins')
        self.operating_margins = data.get('operatingMargins')
        self.return_on_equity = data.get('returnOnEquity')
        self.return_on_assets = data.get('returnOnAssets')
        
        # Cashflow Data
        self.operating_cashflow = data.get('operatingCashflow')
        self.free_cashflow = data.get('freeCashflow')
        self.total_cash = data.get('totalCash')
        self.total_debt = data.get('totalDebt')
        self.debt_to_equity = data.get('debtToEquity')
        
        # Dividend Info
        self.dividend_rate = data.get('dividendRate')
        self.dividend_yield = data.get('dividendYield')
        self.payout_ratio = data.get('payoutRatio')
        self.five_year_avg_dividend_yield = data.get('fiveYearAvgDividendYield')
        self.ex_dividend_date = data.get('exDividendDate')
        
        # Price Data
        self.day_high = data.get('dayHigh')
        self.day_low = data.get('dayLow')
        self.fifty_two_week_high = data.get('fiftyTwoWeekHigh')
        self.fifty_two_week_low = data.get('fiftyTwoWeekLow')
        self.fifty_day_average = data.get('fiftyDayAverage')
        self.two_hundred_day_average = data.get('twoHundredDayAverage')
        
        # Volume Data
        self.volume = data.get('volume', data.get('regularMarketVolume'))
        self.average_volume = data.get('averageVolume')
        self.average_volume_10days = data.get('averageVolume10days')
        
        # Volatility & Risk
        self.beta = data.get('beta')
        self.shares_outstanding = data.get('sharesOutstanding')
        self.float_shares = data.get('floatShares')
        self.held_percent_insiders = data.get('heldPercentInsiders')
        self.held_percent_institutions = data.get('heldPercentInstitutions')


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
            'volume': info.get('volume', info.get('regularMarketVolume')),
            'day_high': info.get('dayHigh'),
            'day_low': info.get('dayLow'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data for {ticker_symbol}: {e}")
        return None


def get_extended_stock_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get extended stock data including financial ratios, cashflow, dividends, and risk metrics
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with extended stock data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
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
            # Business Summary
            'business_summary': info.get('longBusinessSummary', ''),
            
            # Financial Ratios
            'financial_ratios': {
                'pe_ratio': info.get('trailingPE', info.get('forwardPE')),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'market_cap': info.get('marketCap')
            },
            
            # Cashflow Data
            'cashflow_data': {
                'operating_cashflow': info.get('operatingCashflow'),
                'free_cashflow': info.get('freeCashflow'),
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),
                'debt_to_equity': info.get('debtToEquity')
            },
            
            # Dividend Info
            'dividend_info': {
                'dividend_rate': info.get('dividendRate'),
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield'),
                'ex_dividend_date': info.get('exDividendDate')
            },
            
            # Price Data
            'price_data': {
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'fifty_day_average': info.get('fiftyDayAverage'),
                'two_hundred_day_average': info.get('twoHundredDayAverage')
            },
            
            # Volume Data
            'volume_data': {
                'volume': info.get('volume', info.get('regularMarketVolume')),
                'average_volume': info.get('averageVolume'),
                'average_volume_10days': info.get('averageVolume10days')
            },
            
            # Volatility & Risk
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


def get_stock_dividends_and_splits(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get dividend and split history for a stock
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with dividend and split data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get dividends and splits
        dividends = ticker.dividends
        splits = ticker.splits
        
        # Convert to lists for JSON serialization
        dividend_history = []
        if not dividends.empty:
            for date, amount in dividends.items():
                dividend_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'amount': float(amount)
                })
        
        split_history = []
        if not splits.empty:
            for date, ratio in splits.items():
                split_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'ratio': float(ratio)
                })
        
        return {
            'dividends': dividend_history,
            'splits': split_history
        }
        
    except Exception as e:
        logger.error(f"Error fetching dividend/split data for {ticker_symbol}: {e}")
        return None


def get_stock_calendar_and_earnings(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get earnings dates and calendar information
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with calendar and earnings data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get earnings dates and calendar
        earnings_dates = ticker.earnings_dates
        calendar = ticker.calendar
        
        # Convert earnings dates
        earnings_list = []
        if earnings_dates is not None and not earnings_dates.empty:
            for idx, row in earnings_dates.head(10).iterrows():  # Last 10 earnings dates
                date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
                earnings_list.append({
                    'date': date_str,
                    'eps_estimate': float(row.get('EPS Estimate', 0)) if pd.notna(row.get('EPS Estimate')) else None,
                    'reported_eps': float(row.get('Reported EPS', 0)) if pd.notna(row.get('Reported EPS')) else None,
                    'surprise': float(row.get('Surprise(%)', 0)) if pd.notna(row.get('Surprise(%)')) else None
                })
        
        # Convert calendar
        calendar_data = {}
        if calendar is not None and not calendar.empty:
            for col in calendar.columns:
                calendar_data[col] = calendar[col].iloc[0] if len(calendar) > 0 else None
        
        return {
            'earnings_dates': earnings_list,
            'calendar': calendar_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching calendar/earnings data for {ticker_symbol}: {e}")
        return None


def get_analyst_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get analyst recommendations and price targets
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with analyst data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get analyst data
        recommendations = ticker.recommendations
        analyst_price_targets = ticker.analyst_price_targets
        earnings_estimate = ticker.earnings_estimate
        revenue_estimate = ticker.revenue_estimate
        
        # Process recommendations
        recommendations_list = []
        if recommendations is not None and not recommendations.empty:
            for idx, row in recommendations.head(10).iterrows():
                date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
                recommendations_list.append({
                    'date': date_str,
                    'firm': str(row.get('Firm', '')),
                    'to_grade': str(row.get('To Grade', '')),
                    'from_grade': str(row.get('From Grade', '')),
                    'action': str(row.get('Action', ''))
                })
        
        # Process price targets
        price_targets = {}
        if analyst_price_targets is not None and not analyst_price_targets.empty:
            latest_targets = analyst_price_targets.iloc[0]
            price_targets = {
                'current': float(latest_targets.get('current', 0)) if pd.notna(latest_targets.get('current')) else None,
                'low': float(latest_targets.get('low', 0)) if pd.notna(latest_targets.get('low')) else None,
                'high': float(latest_targets.get('high', 0)) if pd.notna(latest_targets.get('high')) else None,
                'mean': float(latest_targets.get('mean', 0)) if pd.notna(latest_targets.get('mean')) else None,
                'median': float(latest_targets.get('median', 0)) if pd.notna(latest_targets.get('median')) else None
            }
        
        # Process earnings estimates
        earnings_est = {}
        if earnings_estimate is not None and not earnings_estimate.empty:
            for period in earnings_estimate.columns:
                if period in earnings_estimate.columns:
                    earnings_est[period] = {
                        'avg': float(earnings_estimate.loc['Avg. Estimate', period]) if 'Avg. Estimate' in earnings_estimate.index and pd.notna(earnings_estimate.loc['Avg. Estimate', period]) else None,
                        'low': float(earnings_estimate.loc['Low Estimate', period]) if 'Low Estimate' in earnings_estimate.index and pd.notna(earnings_estimate.loc['Low Estimate', period]) else None,
                        'high': float(earnings_estimate.loc['High Estimate', period]) if 'High Estimate' in earnings_estimate.index and pd.notna(earnings_estimate.loc['High Estimate', period]) else None,
                        'num_analysts': int(earnings_estimate.loc['No. of Analysts', period]) if 'No. of Analysts' in earnings_estimate.index and pd.notna(earnings_estimate.loc['No. of Analysts', period]) else None
                    }
        
        return {
            'recommendations': recommendations_list,
            'price_targets': price_targets,
            'earnings_estimates': earnings_est
        }
        
    except Exception as e:
        logger.error(f"Error fetching analyst data for {ticker_symbol}: {e}")
        return None


def get_institutional_holders(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get institutional and major holders information
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with holder information or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get holder data
        major_holders = ticker.major_holders
        institutional_holders = ticker.institutional_holders
        mutualfund_holders = ticker.mutualfund_holders
        
        # Process major holders
        major_holders_data = {}
        if major_holders is not None and not major_holders.empty:
            for idx, row in major_holders.iterrows():
                if len(row) >= 2:
                    key = str(row.iloc[1]).lower().replace(' ', '_').replace('%', 'percent')
                    value = str(row.iloc[0])
                    major_holders_data[key] = value
        
        # Process institutional holders
        institutional_list = []
        if institutional_holders is not None and not institutional_holders.empty:
            for idx, row in institutional_holders.head(15).iterrows():
                institutional_list.append({
                    'holder': str(row.get('Holder', '')),
                    'shares': int(row.get('Shares', 0)) if pd.notna(row.get('Shares')) else 0,
                    'date_reported': str(row.get('Date Reported', '')),
                    'percent_out': float(row.get('% Out', 0)) if pd.notna(row.get('% Out')) else 0,
                    'value': int(row.get('Value', 0)) if pd.notna(row.get('Value')) else 0
                })
        
        # Process mutual fund holders
        mutualfund_list = []
        if mutualfund_holders is not None and not mutualfund_holders.empty:
            for idx, row in mutualfund_holders.head(15).iterrows():
                mutualfund_list.append({
                    'holder': str(row.get('Holder', '')),
                    'shares': int(row.get('Shares', 0)) if pd.notna(row.get('Shares')) else 0,
                    'date_reported': str(row.get('Date Reported', '')),
                    'percent_out': float(row.get('% Out', 0)) if pd.notna(row.get('% Out')) else 0,
                    'value': int(row.get('Value', 0)) if pd.notna(row.get('Value')) else 0
                })
        
        return {
            'major_holders': major_holders_data,
            'institutional_holders': institutional_list,
            'mutualfund_holders': mutualfund_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching holder data for {ticker_symbol}: {e}")
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