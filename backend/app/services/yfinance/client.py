"""
Core yfinance client utilities and base classes
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def _get_extended_period(period: str) -> str:
    """
    Get an extended period to load more historical data for indicator calculations.
    This ensures indicators like SMA200 (needs ~200 days warmup) have enough 
    historical data to be calculated accurately from the beginning of the chart.
    
    The extension is moderate to avoid loading too much unnecessary data.
    
    Args:
        period: The requested display period
        
    Returns:
        Extended period string for data loading
    """
    period_extensions = {
        '1d': '5d',      # Load 5 days for 1 day display (enough for short-term indicators)
        '5d': '1mo',     # Load 1 month for 5 days display (20 trading days buffer)
        '1mo': '2mo',    # Load 2 months for 1 month display (1 month buffer)
        '3mo': '1y',     # Load 1 year for 3 months display (SMA200 needs ~200 days)
        '6mo': '2y',     # Load 2 years for 6 months display (1.5 year buffer for SMA200)
        '1y': '3y',      # Load 3 years for 1 year display (2 year buffer for SMA200)
        '2y': '4y',      # Load 4 years for 2 years display (2 year buffer)
        '3y': '7y',      # Load 7 years for 3 years display (4 year buffer for SMA200 on weekly)
        '5y': '8y',      # Load 8 years for 5 years display (3 year buffer)
        '10y': 'max',    # Load max for 10 years display
        'ytd': '2y',     # Load 2 years for YTD display (enough for SMA200)
        'max': 'max',    # Already max
    }
    
    return period_extensions.get(period, period)  # Default: use original period if not in map


def _is_probable_isin(identifier: str) -> bool:
    """Rough validation to check if a string looks like an ISIN."""
    if len(identifier) != 12:
        return False
    country_code = identifier[:2]
    if not country_code.isalpha():
        return False
    return identifier.isalnum()


def get_ticker_from_isin(isin: str) -> Optional[str]:
    """Resolve an ISIN to a ticker symbol using yfinance utilities."""
    try:
        ticker = yf.utils.get_ticker_by_isin(isin)
        if ticker:
            return ticker.upper()
    except Exception as exc:
        logger.error(f"Error resolving ISIN {isin} to ticker: {exc}")
    return None


class StockInfo:
    """Class to hold stock information from yfinance"""
    def __init__(self, ticker: str, data: Dict[str, Any]):
        self.ticker = ticker
        self.name = data.get('longName', data.get('shortName', ticker))
        self.sector = data.get('sector')
        self.industry = data.get('industry')
        self.country = data.get('country')
        self.exchange = data.get('exchange')
        self.currency = data.get('currency')
        self.market_cap = data.get('marketCap')
        self.current_price = data.get('currentPrice', data.get('regularMarketPrice'))
        self.previous_close = data.get('previousClose')
        self.day_high = data.get('dayHigh')
        self.day_low = data.get('dayLow')
        self.fifty_two_week_high = data.get('fiftyTwoWeekHigh')
        self.fifty_two_week_low = data.get('fiftyTwoWeekLow')
        self.volume = data.get('volume', data.get('regularMarketVolume'))
        self.average_volume = data.get('averageVolume')
        self.pe_ratio = data.get('trailingPE', data.get('forwardPE'))
        self.eps = data.get('trailingEps', data.get('forwardEps'))
        self.dividend_yield = data.get('dividendYield')
        self.beta = data.get('beta')
        self.shares_outstanding = data.get('sharesOutstanding')
        self.float_shares = data.get('floatShares')
        self.held_percent_insiders = data.get('heldPercentInsiders')
        self.held_percent_institutions = data.get('heldPercentInstitutions')
        self.book_value = data.get('bookValue')
        self.price_to_book = data.get('priceToBook')
        self.price_to_sales = data.get('priceToSalesTrailing12Months')
        self.profit_margins = data.get('profitMargins')
        self.operating_margins = data.get('operatingMargins')
        self.return_on_equity = data.get('returnOnEquity')
        self.return_on_assets = data.get('returnOnAssets')
        self.debt_to_equity = data.get('debtToEquity')
        self.current_ratio = data.get('currentRatio')
        self.quick_ratio = data.get('quickRatio')
        self.cash_per_share = data.get('totalCashPerShare')
        self.total_cash = data.get('totalCash')
        self.total_debt = data.get('totalDebt')
        self.operating_cashflow = data.get('operatingCashflow')
        self.free_cashflow = data.get('freeCashflow')
        self.revenue = data.get('totalRevenue')
        self.gross_profit = data.get('grossProfits')
        self.net_income = data.get('netIncomeToCommon')
        self.earnings_growth = data.get('earningsGrowth')
        self.revenue_growth = data.get('revenueGrowth')
        self.target_price = data.get('targetMeanPrice')
        self.recommendation = data.get('recommendationMean')
        self.number_of_analysts = data.get('numberOfAnalystOpinions')
        self.last_dividend_date = data.get('lastDividendDate')
        self.ex_dividend_date = data.get('exDividendDate')
        self.dividend_rate = data.get('dividendRate')
        self.payout_ratio = data.get('payoutRatio')
        self.five_year_avg_dividend_yield = data.get('fiveYearAvgDividendYield')
        self.business_summary = data.get('longBusinessSummary', '')
        
        # Additional calculated fields
        self.isin = data.get('isin')
        self.cusip = data.get('cusip')
        self.sedol = data.get('sedol')
        self.lei = data.get('lei')
        
        # Market data
        self.market_state = data.get('marketState')
        self.quote_type = data.get('quoteType')
        self.symbol = data.get('symbol')
        self.short_name = data.get('shortName')
        self.long_name = data.get('longName')
        self.timezone = data.get('timezone')
        self.timezone_name = data.get('timezoneName')
        
        # Financial ratios
        self.peg_ratio = data.get('pegRatio')
        self.price_to_sales_trailing_12_months = data.get('priceToSalesTrailing12Months')
        self.price_to_book = data.get('priceToBook')
        self.enterprise_to_revenue = data.get('enterpriseToRevenue')
        self.enterprise_to_ebitda = data.get('enterpriseToEbitda')
        
        # Growth metrics
        self.earnings_quarterly_growth = data.get('earningsQuarterlyGrowth')
        self.revenue_quarterly_growth = data.get('revenueQuarterlyGrowth')
        
        # Risk metrics
        self.beta = data.get('beta')
        self.volatility_30d = None  # Will be calculated separately
        self.volatility_90d = None  # Will be calculated separately
        
        # Technical indicators (will be calculated separately)
        self.rsi = None
        self.macd = None
        self.bollinger_bands = None
        
        # Additional metadata
        self.last_updated = data.get('lastUpdated')
        self.data_source = 'yfinance'
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert StockInfo to dictionary"""
        return {
            'ticker': self.ticker,
            'name': self.name,
            'sector': self.sector,
            'industry': self.industry,
            'country': self.country,
            'exchange': self.exchange,
            'currency': self.currency,
            'market_cap': self.market_cap,
            'current_price': self.current_price,
            'previous_close': self.previous_close,
            'day_high': self.day_high,
            'day_low': self.day_low,
            'fifty_two_week_high': self.fifty_two_week_high,
            'fifty_two_week_low': self.fifty_two_week_low,
            'volume': self.volume,
            'average_volume': self.average_volume,
            'pe_ratio': self.pe_ratio,
            'eps': self.eps,
            'dividend_yield': self.dividend_yield,
            'beta': self.beta,
            'shares_outstanding': self.shares_outstanding,
            'float_shares': self.float_shares,
            'held_percent_insiders': self.held_percent_insiders,
            'held_percent_institutions': self.held_percent_institutions,
            'book_value': self.book_value,
            'price_to_book': self.price_to_book,
            'price_to_sales': self.price_to_sales,
            'profit_margins': self.profit_margins,
            'operating_margins': self.operating_margins,
            'return_on_equity': self.return_on_equity,
            'return_on_assets': self.return_on_assets,
            'debt_to_equity': self.debt_to_equity,
            'current_ratio': self.current_ratio,
            'quick_ratio': self.quick_ratio,
            'cash_per_share': self.cash_per_share,
            'total_cash': self.total_cash,
            'total_debt': self.total_debt,
            'operating_cashflow': self.operating_cashflow,
            'free_cashflow': self.free_cashflow,
            'revenue': self.revenue,
            'gross_profit': self.gross_profit,
            'net_income': self.net_income,
            'earnings_growth': self.earnings_growth,
            'revenue_growth': self.revenue_growth,
            'target_price': self.target_price,
            'recommendation': self.recommendation,
            'number_of_analysts': self.number_of_analysts,
            'last_dividend_date': self.last_dividend_date,
            'ex_dividend_date': self.ex_dividend_date,
            'dividend_rate': self.dividend_rate,
            'payout_ratio': self.payout_ratio,
            'five_year_avg_dividend_yield': self.five_year_avg_dividend_yield,
            'business_summary': self.business_summary,
            'isin': self.isin,
            'cusip': self.cusip,
            'sedol': self.sedol,
            'lei': self.lei,
            'market_state': self.market_state,
            'quote_type': self.quote_type,
            'symbol': self.symbol,
            'short_name': self.short_name,
            'long_name': self.long_name,
            'timezone': self.timezone,
            'timezone_name': self.timezone_name,
            'peg_ratio': self.peg_ratio,
            'price_to_sales_trailing_12_months': self.price_to_sales_trailing_12_months,
            'enterprise_to_revenue': self.enterprise_to_revenue,
            'enterprise_to_ebitda': self.enterprise_to_ebitda,
            'earnings_quarterly_growth': self.earnings_quarterly_growth,
            'revenue_quarterly_growth': self.revenue_quarterly_growth,
            'volatility_30d': self.volatility_30d,
            'volatility_90d': self.volatility_90d,
            'rsi': self.rsi,
            'macd': self.macd,
            'bollinger_bands': self.bollinger_bands,
            'last_updated': self.last_updated,
            'data_source': self.data_source
        }


def _clean_for_json(data):
    """
    Clean data for JSON serialization by converting numpy types to Python types
    """
    if isinstance(data, dict):
        return {key: _clean_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_clean_for_json(item) for item in data]
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif pd.isna(data):
        return None
    else:
        return data
