"""
yfinance service for fetching stock information
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
import logging


logger = logging.getLogger(__name__)


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


def get_stock_info_by_identifier(identifier: str) -> Optional["StockInfo"]:
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


def _calculate_rsi(close_prices: pd.Series, period: int = 14) -> Optional[float]:
    """Calculate RSI using Wilder's smoothing."""
    if close_prices is None or close_prices.empty or len(close_prices) < period + 1:
        return None

    delta = close_prices.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    if average_loss.iloc[-1] == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    rsi_series = 100 - (100 / (1 + relative_strength))
    rsi_value = rsi_series.iloc[-1]

    if pd.isna(rsi_value):
        return None

    return float(rsi_value)


def _calculate_annualized_volatility(close_prices: pd.Series, window: int = 30, trading_days: int = 252) -> Optional[float]:
    """Calculate annualized volatility over the given window."""
    if close_prices is None or close_prices.empty:
        return None

    returns = close_prices.pct_change().dropna()
    if returns.empty:
        return None

    window_returns = returns.tail(window) if len(returns) >= window else returns
    std_dev = window_returns.std()

    if pd.isna(std_dev):
        return None

    annualized = std_dev * (trading_days ** 0.5)
    return float(annualized * 100)  # convert to percentage


def get_stock_indicators(ticker_symbol: str, rsi_period: int = 14, volatility_window: int = 30) -> Dict[str, Optional[float]]:
    """Fetch historical data to compute RSI and volatility."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(period="6mo")

        if history is None or history.empty or "Close" not in history.columns:
            return {"rsi": None, "volatility": None}

        close_prices = history["Close"].dropna()
        rsi_value = _calculate_rsi(close_prices, period=rsi_period)
        volatility_value = _calculate_annualized_volatility(close_prices, window=volatility_window)

        return {"rsi": rsi_value, "volatility": volatility_value}
    except Exception as exc:
        logger.error(f"Error calculating indicators for {ticker_symbol}: {exc}")
        return {"rsi": None, "volatility": None}


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


def get_historical_prices(ticker_symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Get historical price data for technical analysis
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        
    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            logger.warning(f"No historical data found for {ticker_symbol}")
            return None
        
        # Return only OHLCV columns
        return hist[['Open', 'High', 'Low', 'Close', 'Volume']]
        
    except Exception as e:
        logger.error(f"Error fetching historical prices for {ticker_symbol}: {e}")
        return None


def get_chart_data(
    ticker_symbol: str,
    period: str = "1y",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    include_dividends: bool = True,
    include_volume: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive historical chart data for a stock
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period - Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,3y,5y,10y,ytd,max
        interval: Data interval - Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                  Note: Intraday data (1m-90m) is only available for periods up to 60 days
        start: Start date in format 'YYYY-MM-DD' (overrides period if provided with end)
        end: End date in format 'YYYY-MM-DD' (overrides period if provided with start)
        include_dividends: Include dividend data
        include_volume: Include volume data
        
    Returns:
        Dictionary with chart data in format suitable for frontend:
        {
            'dates': [...],          # List of timestamps
            'open': [...],           # Opening prices
            'high': [...],           # High prices
            'low': [...],            # Low prices
            'close': [...],          # Closing prices
            'volume': [...],         # Trading volume (if include_volume=True)
            'dividends': [...],      # Dividend payments (if include_dividends=True)
            'splits': [...],         # Stock splits (if include_dividends=True)
            'metadata': {
                'symbol': str,
                'period': str,
                'interval': str,
                'first_date': str,
                'last_date': str,
                'data_points': int
            }
        }
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Use start/end dates if provided, otherwise use period
        if start and end:
            hist = ticker.history(start=start, end=end, interval=interval)
        else:
            hist = ticker.history(period=period, interval=interval)
        
        if hist is None or hist.empty:
            logger.warning(f"No chart data found for {ticker_symbol} (period={period}, interval={interval})")
            return None
        
        # Convert index to string format for JSON serialization
        dates = [date.isoformat() for date in hist.index]
        
        # Prepare base chart data
        chart_data = {
            'dates': dates,
            'open': hist['Open'].tolist(),
            'high': hist['High'].tolist(),
            'low': hist['Low'].tolist(),
            'close': hist['Close'].tolist(),
        }
        
        # Add volume if requested
        if include_volume and 'Volume' in hist.columns:
            chart_data['volume'] = hist['Volume'].tolist()
        
        # Add dividends and splits if requested
        if include_dividends:
            if 'Dividends' in hist.columns:
                # Filter out zero dividends and convert to list of events
                dividends_series = hist['Dividends']
                dividend_events = [
                    {
                        'date': dates[i],
                        'amount': float(dividends_series.iloc[i])
                    }
                    for i in range(len(dividends_series))
                    if dividends_series.iloc[i] > 0
                ]
                chart_data['dividends'] = dividend_events
            else:
                chart_data['dividends'] = []
            
            if 'Stock Splits' in hist.columns:
                # Filter out 0 splits and convert to list of events
                splits_series = hist['Stock Splits']
                split_events = [
                    {
                        'date': dates[i],
                        'ratio': float(splits_series.iloc[i])
                    }
                    for i in range(len(splits_series))
                    if splits_series.iloc[i] > 0
                ]
                chart_data['splits'] = split_events
            else:
                chart_data['splits'] = []
        
        # Add metadata
        chart_data['metadata'] = {
            'symbol': ticker_symbol.upper(),
            'period': period,
            'interval': interval,
            'first_date': dates[0] if dates else None,
            'last_date': dates[-1] if dates else None,
            'data_points': len(dates)
        }
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error fetching chart data for {ticker_symbol}: {e}")
        return None


def get_intraday_chart_data(ticker_symbol: str, days: int = 1) -> Optional[Dict[str, Any]]:
    """
    Get intraday chart data with appropriate interval
    
    Args:
        ticker_symbol: Stock ticker symbol
        days: Number of days (1-60)
        
    Returns:
        Dictionary with intraday chart data
    """
    # Determine appropriate period and interval
    if days <= 1:
        period = "1d"
        interval = "5m"  # 5-minute intervals for 1 day
    elif days <= 5:
        period = "5d"
        interval = "15m"  # 15-minute intervals for up to 5 days
    elif days <= 30:
        period = f"{days}d"
        interval = "30m"  # 30-minute intervals for up to 30 days
    else:
        period = "60d"
        interval = "1h"  # Hourly intervals for up to 60 days
    
    return get_chart_data(
        ticker_symbol=ticker_symbol,
        period=period,
        interval=interval,
        include_dividends=False,  # Usually not needed for intraday
        include_volume=True
    )


def _clean_for_json(data):
    """
    Replace NaN, Inf, and -Inf values with None for JSON serialization
    """
    if isinstance(data, list):
        return [None if pd.isna(x) or np.isinf(x) else x for x in data]
    elif isinstance(data, dict):
        return {k: _clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, (pd.Series, np.ndarray)):
        return _clean_for_json(data.tolist())
    elif pd.isna(data) or (isinstance(data, float) and np.isinf(data)):
        return None
    return data


def calculate_technical_indicators(
    ticker_symbol: str,
    period: str = "1y",
    indicators: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate technical indicators from historical data
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period for historical data
        indicators: List of indicators to calculate. Available:
                   - 'sma_20': 20-day Simple Moving Average
                   - 'sma_50': 50-day Simple Moving Average
                   - 'sma_200': 200-day Simple Moving Average
                   - 'ema_12': 12-day Exponential Moving Average
                   - 'ema_26': 26-day Exponential Moving Average
                   - 'rsi': Relative Strength Index (14-day)
                   - 'macd': Moving Average Convergence Divergence
                   - 'bollinger': Bollinger Bands (20-day)
                   - 'atr' or 'atr_14': Average True Range (14-day)
                   - 'vwap' or 'vwap_20': Volume Weighted Average Price (Rolling 20-day)
                   - 'volatility': Historical Volatility (30-day)
                   
    Returns:
        Dictionary with calculated indicators
    """
    if indicators is None:
        indicators = ['sma_20', 'sma_50', 'rsi']
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        
        if hist is None or hist.empty:
            return None
        
        close_prices = hist['Close']
        dates = [date.isoformat() for date in hist.index]
        
        result = {
            'dates': dates,
            'close': _clean_for_json(close_prices),
            'indicators': {}
        }
        
        # Simple Moving Averages
        if 'sma_20' in indicators:
            result['indicators']['sma_20'] = _clean_for_json(close_prices.rolling(window=20).mean())
        if 'sma_50' in indicators:
            result['indicators']['sma_50'] = _clean_for_json(close_prices.rolling(window=50).mean())
        if 'sma_200' in indicators:
            result['indicators']['sma_200'] = _clean_for_json(close_prices.rolling(window=200).mean())
        
        # Exponential Moving Averages
        if 'ema_12' in indicators:
            result['indicators']['ema_12'] = _clean_for_json(close_prices.ewm(span=12, adjust=False).mean())
        if 'ema_26' in indicators:
            result['indicators']['ema_26'] = _clean_for_json(close_prices.ewm(span=26, adjust=False).mean())
        
        # RSI
        if 'rsi' in indicators:
            rsi_values = _calculate_rsi_series(close_prices, period=14)
            if rsi_values is not None:
                result['indicators']['rsi'] = _clean_for_json(rsi_values)
        
        # MACD
        if 'macd' in indicators:
            ema_12 = close_prices.ewm(span=12, adjust=False).mean()
            ema_26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line
            
            result['indicators']['macd'] = {
                'macd': _clean_for_json(macd_line),
                'signal': _clean_for_json(signal_line),
                'histogram': _clean_for_json(histogram)
            }
        
        # Bollinger Bands
        if 'bollinger' in indicators:
            sma_20 = close_prices.rolling(window=20).mean()
            std_20 = close_prices.rolling(window=20).std()
            upper_band = sma_20 + (std_20 * 2)
            lower_band = sma_20 - (std_20 * 2)
            
            result['indicators']['bollinger'] = {
                'middle': _clean_for_json(sma_20),
                'upper': _clean_for_json(upper_band),
                'lower': _clean_for_json(lower_band)
            }
        
        # Historical Volatility
        if 'volatility' in indicators:
            returns = close_prices.pct_change()
            volatility = returns.rolling(window=30).std() * (252 ** 0.5) * 100
            result['indicators']['volatility'] = _clean_for_json(volatility)
        
        # ATR (Average True Range)
        if 'atr' in indicators or 'atr_14' in indicators:
            # Check if required columns exist
            if all(col in hist.columns for col in ['High', 'Low', 'Close']):
                atr_values = _calculate_atr_series(hist['High'], hist['Low'], hist['Close'], period=14)
                if atr_values is not None:
                    result['indicators']['atr'] = _clean_for_json(atr_values)
        
        # VWAP (Volume Weighted Average Price) - Rolling
        if 'vwap' in indicators or 'vwap_20' in indicators:
            # Check if required columns exist
            if all(col in hist.columns for col in ['High', 'Low', 'Close', 'Volume']):
                vwap_period = 20  # Rolling 20-period VWAP
                vwap_values = _calculate_vwap_rolling(
                    hist['High'], 
                    hist['Low'], 
                    hist['Close'], 
                    hist['Volume'], 
                    period=vwap_period
                )
                if vwap_values is not None:
                    result['indicators']['vwap'] = _clean_for_json(vwap_values)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {ticker_symbol}: {e}")
        return None


def _calculate_atr_series(high_prices: pd.Series, 
                          low_prices: pd.Series, 
                          close_prices: pd.Series, 
                          period: int = 14) -> Optional[pd.Series]:
    """Calculate ATR as a series (for technical analysis)"""
    try:
        if len(close_prices) < period + 1:
            logger.warning(f"Not enough data for ATR calculation. Need {period + 1}, have {len(close_prices)}")
            return None
        
        # True Range berechnen
        high_low = high_prices - low_prices
        high_close = abs(high_prices - close_prices.shift())
        low_close = abs(low_prices - close_prices.shift())
        
        # Maximum der drei Werte
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR = Exponential Moving Average von True Range
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    except Exception as e:
        logger.error(f"Error calculating ATR series: {e}", exc_info=True)
        return None


def _calculate_vwap_rolling(high_prices: pd.Series,
                            low_prices: pd.Series,
                            close_prices: pd.Series,
                            volume: pd.Series,
                            period: int = 20) -> Optional[pd.Series]:
    """
    Calculate Rolling VWAP (Volume Weighted Average Price)
    
    VWAP Formula:
    VWAP = Σ(Typical Price × Volume) / Σ(Volume)
    
    Where Typical Price = (High + Low + Close) / 3
    
    Args:
        high_prices: Series of high prices
        low_prices: Series of low prices
        close_prices: Series of close prices
        volume: Series of volume data
        period: Rolling window period (default: 20)
        
    Returns:
        Series with rolling VWAP values
    """
    try:
        # Check if we have enough data
        if len(close_prices) < period:
            logger.warning(f"Not enough data for VWAP calculation. Need {period}, have {len(close_prices)}")
            return None
        
        # Calculate Typical Price (HLC/3)
        typical_price = (high_prices + low_prices + close_prices) / 3
        
        # Calculate Price × Volume
        pv = typical_price * volume
        
        # Rolling sum of (Price × Volume) and Volume
        rolling_pv = pv.rolling(window=period).sum()
        rolling_volume = volume.rolling(window=period).sum()
        
        # VWAP = Σ(Price × Volume) / Σ(Volume)
        vwap = rolling_pv / rolling_volume
        
        return vwap
    except Exception as e:
        logger.error(f"Error calculating VWAP series: {e}", exc_info=True)
        return None


def _calculate_rsi_series(prices: pd.Series, period: int = 14) -> Optional[pd.Series]:
    """Calculate RSI as a series (for technical analysis)"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception:
        return None