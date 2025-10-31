"""
Financial data functions (dividends, earnings, analyst data, etc.)
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any, List
import logging

from .client import _clean_for_json

logger = logging.getLogger(__name__)


def get_stock_dividends_and_splits(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get dividend and split history for a stock.
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with dividend and split data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get dividend history
        dividends = ticker.dividends
        splits = ticker.splits
        
        # Convert to lists
        dividend_data = []
        if not dividends.empty:
            for date, amount in dividends.items():
                dividend_data.append({
                    'date': date.isoformat(),
                    'amount': float(amount)
                })
        
        split_data = []
        if not splits.empty:
            for date, ratio in splits.items():
                split_data.append({
                    'date': date.isoformat(),
                    'ratio': float(ratio)
                })
        
        return {
            'ticker': ticker_symbol,
            'dividends': dividend_data,
            'splits': split_data,
            'total_dividends': len(dividend_data),
            'total_splits': len(split_data)
        }
        
    except Exception as e:
        logger.error(f"Error fetching dividends and splits for {ticker_symbol}: {str(e)}")
        return None


def get_stock_calendar_and_earnings(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get earnings calendar and upcoming events for a stock.
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with calendar and earnings data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info:
            return None
        
        # Extract earnings-related data
        # Determine next_earnings_date from multiple possible yfinance sources
        def _extract_next_earnings_date(ticker_obj, info_dict):
            # Try info fields first
            candidates = []
            if info_dict:
                candidates.append(info_dict.get('earningsDate'))
                candidates.append(info_dict.get('nextEarningsDate'))
                candidates.append(info_dict.get('next_earnings_date'))

            # Try ticker.calendar (pandas DataFrame) if available
            try:
                cal = getattr(ticker_obj, 'calendar', None)
                if cal is not None:
                    # calendar may be a DataFrame or a dict with values containing datetimes
                    try:
                        # If it's a pandas DataFrame, grab the first cell
                        if hasattr(cal, 'iat') and getattr(cal, 'shape', (0, 0))[1] >= 1:
                            val = cal.iat[0, 0]
                            candidates.append(val)
                        # If it's a dict (some yfinance versions), look for 'Earnings Date' key
                        elif isinstance(cal, dict):
                            # 'Earnings Date' may be a list of dates
                            ed = cal.get('Earnings Date') or cal.get('earningsDate')
                            if ed:
                                # if list-like, take first element
                                try:
                                    if isinstance(ed, (list, tuple)) and len(ed) > 0:
                                        candidates.append(ed[0])
                                    else:
                                        candidates.append(ed)
                                except Exception:
                                    candidates.append(ed)
                    except Exception:
                        pass
            except Exception:
                pass

            # Try get_earnings_dates if available (recent yfinance)
            try:
                if hasattr(ticker_obj, 'get_earnings_dates'):
                    ed_df = ticker_obj.get_earnings_dates(limit=5)
                    # ed_df may be a DataFrame with 'Earnings Date' column or index
                    try:
                        if hasattr(ed_df, 'iloc') and len(ed_df) > 0:
                            # attempt to get first datetime-like value
                            first_row = ed_df.iloc[0]
                            # try known column names
                            for col in ['Earnings Date', 'earningsDate', 'date']:
                                if col in ed_df.columns:
                                    candidates.append(first_row[col])
                                    break
                            else:
                                # fallback: use first value in the row
                                for v in first_row.values:
                                    candidates.append(v)
                                    break
                    except Exception:
                        pass
            except Exception:
                pass

            # Normalize candidate to epoch seconds if possible
            for c in candidates:
                if c is None:
                    continue
                # If pandas Timestamp
                try:
                    import pandas as pd
                    if isinstance(c, pd.Timestamp):
                        return int(c.to_datetime64().astype('int64') // 10**9)
                except Exception:
                    pass

                # If datetime
                try:
                    from datetime import datetime, date
                    if isinstance(c, datetime):
                        return int(c.timestamp())
                    if isinstance(c, date):
                        return int(datetime(c.year, c.month, c.day).timestamp())
                except Exception:
                    pass

                # If numeric epoch
                try:
                    n = float(c)
                    if n > 0:
                        # normalize milliseconds -> seconds
                        if n > 1e12:
                            n = n / 1000.0
                        return int(n)
                except Exception:
                    pass

                # If string parseable
                try:
                    from dateutil import parser as _p
                    dt = _p.parse(str(c))
                    return int(dt.timestamp())
                except Exception:
                    pass

            return None

        next_ed = _extract_next_earnings_date(ticker, info)

        # Plausibility checks for the extracted next_earnings_date
        from datetime import datetime, timedelta
        now_ts = int(datetime.utcnow().timestamp())
        last_earnings_date = None
        # If the extracted date equals the ex-dividend date, prefer calendar earnings when available
        try:
            ex_div = info.get('exDividendDate')
            if ex_div:
                try:
                    ex_div_n = float(ex_div)
                    if ex_div_n > 1e12:
                        ex_div_n = int(ex_div_n / 1000.0)
                    else:
                        ex_div_n = int(ex_div_n)
                except Exception:
                    ex_div_n = None
            else:
                ex_div_n = None
        except Exception:
            ex_div_n = None

        # If next_ed is in the distant past, treat it as last_earnings_date
        if next_ed is not None:
            # Normalize large ms->s already handled in extractor; assume seconds here
            if next_ed < (now_ts - 7 * 24 * 3600):
                last_earnings_date = next_ed
                next_ed = None
            # If the date is unreasonably far in the future (>1 year), drop it
            elif next_ed > (now_ts + 365 * 24 * 3600):
                next_ed = None
            # If it exactly matches ex-dividend date and calendar contained explicit Earnings Date, prefer calendar
            elif ex_div_n is not None and next_ed == ex_div_n:
                # try to prefer calendar's earnings date if present
                try:
                    cal = getattr(ticker, 'calendar', None)
                    if isinstance(cal, dict):
                        ed = cal.get('Earnings Date') or cal.get('earningsDate')
                        if ed:
                            if isinstance(ed, (list, tuple)) and len(ed) > 0:
                                # convert date to epoch
                                import pandas as pd
                                v = ed[0]
                                if isinstance(v, pd.Timestamp):
                                    next_ed = int(v.to_datetime64().astype('int64') // 10**9)
                                else:
                                    try:
                                        from dateutil import parser as _p
                                        next_ed = int(_p.parse(str(v)).timestamp())
                                    except Exception:
                                        pass
                except Exception:
                    pass

        earnings_data = {
            'ticker': ticker_symbol,
            'next_earnings_date': next_ed,
            'last_earnings_date': last_earnings_date,
            'earnings_growth': info.get('earningsGrowth'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),
            'revenue_quarterly_growth': info.get('revenueQuarterlyGrowth'),
            'trailing_eps': info.get('trailingEps'),
            'forward_eps': info.get('forwardEps'),
            'trailing_pe': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_sales_trailing_12_months': info.get('priceToSalesTrailing12Months'),
            'price_to_book': info.get('priceToBook'),
            'enterprise_to_revenue': info.get('enterpriseToRevenue'),
            'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
            'profit_margins': info.get('profitMargins'),
            'operating_margins': info.get('operatingMargins'),
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets'),
            'gross_profits': info.get('grossProfits'),
            'total_revenue': info.get('totalRevenue'),
            'net_income_to_common': info.get('netIncomeToCommon'),
            'operating_cashflow': info.get('operatingCashflow'),
            'free_cashflow': info.get('freeCashflow'),
            'total_cash': info.get('totalCash'),
            'total_debt': info.get('totalDebt'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'quick_ratio': info.get('quickRatio'),
            'total_cash_per_share': info.get('totalCashPerShare'),
            'book_value': info.get('bookValue'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
            'held_percent_insiders': info.get('heldPercentInsiders'),
            'held_percent_institutions': info.get('heldPercentInstitutions'),
            'last_updated': info.get('lastUpdated')
        }
        
        return _clean_for_json(earnings_data)
    
    except Exception as e:
        logger.error(f"Error fetching calendar and earnings for {ticker_symbol}: {str(e)}")
        return None


def get_analyst_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get analyst recommendations and price targets for a stock.
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with analyst data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info:
            return None
        
        # Extract analyst-related data
        analyst_data = {
            'ticker': ticker_symbol,
            'recommendation_mean': info.get('recommendationMean'),
            'recommendation_key': info.get('recommendationKey'),
            'target_mean_price': info.get('targetMeanPrice'),
            'target_high_price': info.get('targetHighPrice'),
            'target_low_price': info.get('targetLowPrice'),
            'number_of_analyst_opinions': info.get('numberOfAnalystOpinions'),
            'strong_buy': info.get('strongBuy'),
            'buy': info.get('buy'),
            'hold': info.get('hold'),
            'sell': info.get('sell'),
            'strong_sell': info.get('strongSell'),
            'last_updated': info.get('lastUpdated')
        }
        
        return _clean_for_json(analyst_data)
        
    except Exception as e:
        logger.error(f"Error fetching analyst data for {ticker_symbol}: {str(e)}")
        return None


def get_institutional_holders(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get institutional holders information for a stock.
    
    Args:
        ticker_symbol: Stock ticker symbol
        
    Returns:
        Dictionary with institutional holders data or None
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info:
            return None
        
        # Extract institutional holder data
        holders_data = {
            'ticker': ticker_symbol,
            'held_percent_insiders': info.get('heldPercentInsiders'),
            'held_percent_institutions': info.get('heldPercentInstitutions'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
            'implied_shares_outstanding': info.get('impliedSharesOutstanding'),
            'last_updated': info.get('lastUpdated')
        }
        
        # Try to get detailed institutional holders if available
        try:
            institutional_holders = ticker.institutional_holders
            if not institutional_holders.empty:
                holders_list = []
                for _, holder in institutional_holders.iterrows():
                    holders_list.append({
                        'holder': holder.get('Holder', ''),
                        'shares': int(holder.get('Shares', 0)) if pd.notna(holder.get('Shares')) else 0,
                        'date_reported': holder.get('Date Reported', ''),
                        'percent_out': float(holder.get('% Out', 0)) if pd.notna(holder.get('% Out')) else 0,
                        'value': float(holder.get('Value', 0)) if pd.notna(holder.get('Value')) else 0
                    })
                holders_data['institutional_holders'] = holders_list
        except Exception as e:
            logger.warning(f"Could not fetch detailed institutional holders for {ticker_symbol}: {str(e)}")
        
        # Try to get major holders if available
        try:
            major_holders = ticker.major_holders
            if not major_holders.empty:
                major_holders_list = []
                for _, holder in major_holders.iterrows():
                    major_holders_list.append({
                        'holder': holder.get('Holder', ''),
                        'shares': int(holder.get('Shares', 0)) if pd.notna(holder.get('Shares')) else 0,
                        'date_reported': holder.get('Date Reported', ''),
                        'percent_out': float(holder.get('% Out', 0)) if pd.notna(holder.get('% Out')) else 0,
                        'value': float(holder.get('Value', 0)) if pd.notna(holder.get('Value')) else 0
                    })
                holders_data['major_holders'] = major_holders_list
        except Exception as e:
            logger.warning(f"Could not fetch major holders for {ticker_symbol}: {str(e)}")
        
        return _clean_for_json(holders_data)
        
    except Exception as e:
        logger.error(f"Error fetching institutional holders for {ticker_symbol}: {str(e)}")
        return None
