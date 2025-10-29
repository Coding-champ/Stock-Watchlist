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


def _estimate_required_warmup_bars(indicators: Optional[List[str]]) -> Optional[int]:
    """
    Estimate required warmup bars (history) given a list of indicators.
    Returns the maximum window length needed by the requested indicators.
    """
    if not indicators:
        return None

    # Base mapping of indicator -> required bars
    mapping = {
        'sma_50': 50,
        'sma_200': 200,
        'sma': 200,  # generic fallback
        'rsi': 14,
        'macd': 35,  # slow (26) + signal (9)
        'bollinger': 20,
        'stochastic': 20,
        'vwap': 20,
        'atr': 14
    }

    required = 0
    for ind in indicators:
        name = ind.lower() if isinstance(ind, str) else ''
        if not name:
            continue
        if name in mapping:
            required = max(required, mapping[name])
            continue
        # handle names like 'sma_50' or 'sma_200'
        if 'sma' in name:
            if '200' in name:
                required = max(required, 200)
            elif '50' in name:
                required = max(required, 50)
            else:
                required = max(required, 50)
            continue
        if 'macd' in name:
            required = max(required, mapping['macd'])
            continue
        if 'rsi' in name:
            required = max(required, mapping['rsi'])
            continue
        if 'stochastic' in name or 'stoch' in name:
            required = max(required, mapping['stochastic'])
            continue
        if 'bollinger' in name:
            required = max(required, mapping['bollinger'])

    return required if required > 0 else None


def _period_to_days(period: str) -> int:
    """Approximate number of days for a period string."""
    map_days = {
        '1d': 1,
        '5d': 5,
        '1mo': 30,
        '2mo': 60,
        '3mo': 90,
        '6mo': 180,
        '1y': 365,
        '2y': 730,
        '3y': 1095,
        '5y': 1825,
        '10y': 3650,
        'ytd': 365,
        'max': 3650
    }
    return map_days.get(period, 365)


def _period_for_days(days: int) -> str:
    """Return an appropriate yfinance period string approximating the given days."""
    if days <= 5:
        return '5d'
    if days <= 30:
        return '1mo'
    if days <= 90:
        return '3mo'
    if days <= 180:
        return '6mo'
    if days <= 365:
        return '1y'
    if days <= 730:
        return '2y'
    if days <= 1095:
        return '3y'
    if days <= 1825:
        return '5y'
    if days <= 3650:
        return '10y'
    return 'max'


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
                #'fifty_day_average': getattr(fast_info, 'fifty_day_average', None),
                #'two_hundred_day_average': getattr(fast_info, 'two_hundred_day_average', None)
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
            # Determine dynamic warmup based on requested indicators
            # Default: rely on conservative extended_period mapping
            warmup_bars = None
            if indicators:
                warmup_bars = _estimate_required_warmup_bars(indicators)

            # If explicit warmup not available, fall back to configured mapping
            # Also ensure volume MA warmup (20 bars) if volume will be returned
            # We prefer a 20-bar warmup to support both 10-day and 20-day volume averages
            if include_volume:
                warmup_bars = max(warmup_bars or 0, 20)

            if warmup_bars is None:
                extended_period = _get_extended_period(period)
            else:
                # Estimate display days for requested period
                display_days = _period_to_days(period)

                # Map interval to approximate trading bars per calendar day.
                bars_per_day_map = {
                    '1m': 390,
                    '5m': 78,
                    '15m': 26,
                    '30m': 13,
                    '60m': 6,
                    '1h': 6,
                    '1d': 1,
                    '1wk': 1.0 / 5.0,   # one weekly bar per 5 trading days
                    '1mo': 1.0 / 21.0,  # one monthly bar per ~21 trading days
                }

                # Determine bars per calendar day for the requested interval (default 1)
                bars_per_day = bars_per_day_map.get(interval, 1)

                # Compute approximate number of display bars requested
                display_bars = max(1, int(display_days * bars_per_day))

                # Total bars needed = display bars + indicator warmup bars + safety margin
                safety_margin_bars = max(10, int(0.05 * (display_bars + warmup_bars))) if warmup_bars else 10
                total_bars_needed = display_bars + (warmup_bars or 0) + safety_margin_bars

                # Convert required bars back to conservative calendar days
                # Avoid division by very small bars_per_day by ensuring a minimum
                effective_bars_per_day = bars_per_day if bars_per_day >= 0.05 else 0.05
                weekend_holiday_factor = 1.15  # account for weekends/holidays
                required_days = int((total_bars_needed / effective_bars_per_day) * weekend_holiday_factor) + 1

                # Ensure at least the display days are requested
                total_days = max(required_days, display_days)
                extended_period = _period_for_days(total_days)

                # compute extended_period above; now fetch hist for whichever branch
                pass

            # Fetch historical data for the computed extended_period
            hist = ticker.history(period=extended_period, interval=interval)
            # Debug info
            logger.debug(f"extended_period={extended_period}, interval={interval}, indicators={indicators}")

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
            # Compute indicators directly using low-level indicator implementations to avoid recursion
            from backend.app.services.indicators_core import (
                calculate_sma,
                calculate_rsi,
                calculate_macd,
                calculate_bollinger_bands,
            )
            import re

            indicators_result = {
                'dates': [d.isoformat() for d in hist.index],
                'indicators': {}
            }

            for ind in indicators:
                name = ind.lower() if isinstance(ind, str) else ''
                try:
                    if name.startswith('sma'):
                        # try to extract window from name, e.g. 'sma_50'
                        m = re.search(r"(\d+)", name)
                        window = int(m.group(1)) if m else 50
                        indicators_result['indicators'][f'sma_{window}'] = calculate_sma(hist['Close'], window).tolist()
                    elif name == 'rsi':
                        indicators_result['indicators']['rsi'] = calculate_rsi(hist['Close'], 14).tolist()
                    elif name == 'macd':
                        macd_df = calculate_macd(hist['Close'])
                        indicators_result['indicators']['macd'] = {
                            'macd': macd_df['macd'].tolist(),
                            'signal': macd_df['signal'].tolist(),
                            'hist': macd_df['hist'].tolist()
                        }
                    elif 'bollinger' in name:
                        bb = calculate_bollinger_bands(hist['Close'])
                        indicators_result['indicators']['bollinger'] = {
                            'upper': bb['upper'].tolist(),
                            'middle': bb['sma'].tolist(),
                            'lower': bb['lower'].tolist()
                        }
                    elif name in ('atr', 'atr_14'):
                        # Calculate ATR series (14) using High/Low/Close
                        try:
                            from backend.app.services.yfinance.indicators import _calculate_atr_series
                            atr_series = _calculate_atr_series(hist['High'], hist['Low'], hist['Close'], 14)
                            if atr_series is None:
                                indicators_result['indicators']['atr'] = None
                            else:
                                # convert NaN to None and ensure floats
                                indicators_result['indicators']['atr'] = [None if pd.isna(v) else float(v) for v in atr_series.tolist()]
                        except Exception:
                            indicators_result['indicators']['atr'] = None
                    else:
                        # fallback: try sma default 50
                        m = re.search(r"(\d+)", name)
                        if m:
                            window = int(m.group(1))
                            indicators_result['indicators'][name] = calculate_sma(hist['Close'], window).tolist()
                except Exception:
                    # If indicator calculation fails, set None to indicate unavailability
                    indicators_result['indicators'][name] = None

        # Compute volume moving averages if volume requested
        if include_volume and 'Volume' in hist.columns:
            try:
                # 10-day and 20-day volume moving averages (align with frontend expectations)
                vol_ma10 = hist['Volume'].rolling(window=10).mean()
                vol_ma20 = hist['Volume'].rolling(window=20).mean()
                # Ensure it's serializable (convert NaN to None)
                indicators_result = indicators_result or {'dates': [d.isoformat() for d in hist.index], 'indicators': {}}
                indicators_result['indicators']['volumeMA10'] = [None if pd.isna(v) else float(v) for v in vol_ma10.tolist()]
                indicators_result['indicators']['volumeMA20'] = [None if pd.isna(v) else float(v) for v in vol_ma20.tolist()]
            except Exception:
                # Non-fatal: skip volume MA if calculation fails
                logger.debug("volumeMA10 calculation failed, skipping")
        
        # Filter data to requested period if we loaded extended data
        if cutoff_date:
            # Ensure the filtered (visible) start has enough prior warmup bars
            # so that indicators (SMA/RSI/etc.) are numeric at the first visible index.
            try:
                required_warmup = _estimate_required_warmup_bars(indicators) or 0
            except Exception:
                required_warmup = 0
            # Ensure volume MA warmup is accounted for when volume is included
            if include_volume:
                required_warmup = max(required_warmup, 10)
            logger.debug(f"required_warmup={required_warmup}")

            # Find the first index in hist that is >= cutoff_date
            idx_positions = [i for i, d in enumerate(hist.index) if d >= cutoff_date]
            if idx_positions:
                first_pos = idx_positions[0]
            else:
                first_pos = 0
            logger.debug(f"first_pos={first_pos}, hist_len={len(hist)}")

            # If we don't have enough prior bars before first_pos, shift the visible
            # start forward (later) to the earliest position that does have enough prior bars.
            if required_warmup and len(hist) > required_warmup and first_pos < required_warmup:
                new_start_pos = required_warmup
                logger.debug(f"shifting start from pos {first_pos} to {new_start_pos}")
                if new_start_pos < len(hist):
                    cutoff_date = hist.index[new_start_pos]

            hist = hist[hist.index >= cutoff_date]
            logger.debug(f"Filtered data from {cutoff_date} to {hist.index[-1]} for period {period}")
        
        # Prepare chart data
        chart_data = []
        # Precompute filtered volume moving averages (10 & 20) for per-point inclusion
        try:
            filtered_volumes = [int(row['Volume']) if pd.notna(row['Volume']) else None for _, row in hist.iterrows()]
            vol_series = pd.Series([v if v is not None else np.nan for v in filtered_volumes])
            vol_ma10_filtered = vol_series.rolling(window=10).mean().tolist()
            vol_ma20_filtered = vol_series.rolling(window=20).mean().tolist()
        except Exception:
            vol_ma10_filtered = [None] * len(hist)
            vol_ma20_filtered = [None] * len(hist)

        for i, (date, row) in enumerate(hist.iterrows()):
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
                # include precomputed 10-day volume moving average per point
                try:
                    ma_val = vol_ma10_filtered[i]
                    data_point['volumeMA10'] = None if (ma_val is None or (isinstance(ma_val, float) and pd.isna(ma_val))) else float(ma_val)
                except Exception:
                    data_point['volumeMA10'] = None
                # include precomputed 20-day volume moving average per point
                try:
                    ma20 = vol_ma20_filtered[i]
                    data_point['volumeMA20'] = None if (ma20 is None or (isinstance(ma20, float) and pd.isna(ma20))) else float(ma20)
                except Exception:
                    data_point['volumeMA20'] = None
            
            chart_data.append(data_point)
        
        # Extract dates and separate arrays for frontend compatibility
        dates = [item['date'] for item in chart_data]
        opens = [item['open'] for item in chart_data]
        highs = [item['high'] for item in chart_data]
        lows = [item['low'] for item in chart_data]
        closes = [item['close'] for item in chart_data]
        volumes = [item['volume'] for item in chart_data]
        # Compute aggregate average volume stats from the filtered data
        try:
            avg_volume = int(pd.Series([v for v in volumes if v is not None]).mean()) if any(v is not None for v in volumes) else None
        except Exception:
            avg_volume = None
        try:
            avg_volume_10days = int(pd.Series([v for v in volumes if v is not None]).tail(10).mean()) if any(v is not None for v in volumes) else None
        except Exception:
            avg_volume_10days = None
        
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
            'indicators': {},
            'volume_data': {
                'average_volume': avg_volume,
                'average_volume_10days': avg_volume_10days
            }
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

        # Inject per-point ATR into chart_data items so frontend can map d.atr
        try:
            atr_list = result.get('indicators', {}).get('atr')
            if isinstance(atr_list, list) and len(atr_list) == len(chart_data):
                for idx, item in enumerate(chart_data):
                    try:
                        val = atr_list[idx]
                        item['atr'] = None if (val is None or (isinstance(val, float) and pd.isna(val))) else float(val)
                    except Exception:
                        item['atr'] = None
            elif isinstance(atr_list, list) and len(atr_list) > 0:
                # If lengths differ, still try to align by index where possible
                for idx, item in enumerate(chart_data):
                    try:
                        val = atr_list[idx] if idx < len(atr_list) else None
                        item['atr'] = None if (val is None or (isinstance(val, float) and pd.isna(val))) else float(val)
                    except Exception:
                        item['atr'] = None
        except Exception:
            # non-fatal: leave chart_data without atr entries
            pass
        
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
