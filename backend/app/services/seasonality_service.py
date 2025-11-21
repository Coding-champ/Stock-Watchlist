import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional

def calculate_monthly_returns(df: pd.DataFrame, price_col: str = 'Close') -> pd.Series:
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # If no data, return empty Series
    if df.empty:
        return pd.Series(dtype=float)

    # Determine the column to use for close prices. The dataframe coming from
    # HistoricalPriceService typically has lowercase column names ('close',
    # 'adjusted_close'), whereas other data sources may use 'Close'. Be robust
    # and accept common variants or fall back to the first numeric column.
    if price_col in df.columns:
        price_col_actual = price_col
    else:
        cols_lc = {c.lower(): c for c in df.columns}
        if price_col.lower() in cols_lc:
            price_col_actual = cols_lc[price_col.lower()]
        elif 'close' in cols_lc:
            price_col_actual = cols_lc['close']
        elif 'adjusted_close' in cols_lc:
            price_col_actual = cols_lc['adjusted_close']
        elif 'adj close' in cols_lc:
            price_col_actual = cols_lc['adj close']
        else:
            # Fallback: try to pick the first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                price_col_actual = numeric_cols[0]
            else:
                # No usable numeric column found
                return pd.Series(dtype=float)

    # Resample to month-end prices (last available price in each calendar month)
    try:
        monthly_prices = df[price_col_actual].resample('M').last()
    except Exception:
        # If resampling fails for any reason, return an empty series
        return pd.Series(dtype=float)

    # If the most recent month is incomplete (last row date before month end), drop it
    last_row_date = df.index.max()
    # Compute month end while preserving timezone info
    try:
        month_end = last_row_date + pd.offsets.MonthEnd(0)
    except Exception:
        # Fallback to period-based end_time (may drop tz)
        month_end = last_row_date.to_period('M').end_time

    if last_row_date < month_end:
        if len(monthly_prices) > 0 and monthly_prices.index.max().month == last_row_date.month and monthly_prices.index.max().year == last_row_date.year:
            monthly_prices = monthly_prices.iloc[:-1]

    monthly_returns = monthly_prices.pct_change() * 100
    return monthly_returns.dropna()

def calculate_seasonality(monthly_returns: pd.Series, years_back: Optional[int] = None) -> pd.DataFrame:
    if years_back is not None:
        cutoff_date = datetime.now() - timedelta(days=years_back*365)
        # Ensure cutoff_date is timezone-aware if monthly_returns.index is
        if hasattr(monthly_returns.index, 'tz') and monthly_returns.index.tz is not None:
            cutoff_date = pd.Timestamp(cutoff_date, tz=monthly_returns.index.tz)
        monthly_returns = monthly_returns[monthly_returns.index >= cutoff_date]
    else:
        # For "all" data: start with the first complete year
        if len(monthly_returns) > 0:
            first_date = monthly_returns.index.min()
            first_year = first_date.year
            # Check if the first year starts in January
            if first_date.month != 1:
                # Skip to the next year (first complete year)
                first_complete_year = first_year + 1
                cutoff_date = pd.Timestamp(f'{first_complete_year}-01-01')
                # Ensure timezone-awareness if needed
                if hasattr(monthly_returns.index, 'tz') and monthly_returns.index.tz is not None:
                    cutoff_date = cutoff_date.tz_localize(monthly_returns.index.tz)
                monthly_returns = monthly_returns[monthly_returns.index >= cutoff_date]
    
    df = pd.DataFrame({
        'return': monthly_returns.values,
        'month': monthly_returns.index.month,
        'year': monthly_returns.index.year
    })
    seasonality = df.groupby('month')['return'].agg([
        ('avg_return', 'mean'),
        ('median_return', 'median'),
        ('std_dev', 'std'),
        ('positive_count', lambda x: (x > 0).sum()),
        ('negative_count', lambda x: (x < 0).sum()),
        ('total_count', 'count')
    ]).reset_index()
    seasonality['win_rate'] = (seasonality['positive_count'] / seasonality['total_count'] * 100).round(2)
    month_names = {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    }
    seasonality['month_name'] = seasonality['month'].map(month_names)
    seasonality['avg_return'] = seasonality['avg_return'].round(2)
    seasonality['median_return'] = seasonality['median_return'].round(2)
    seasonality['std_dev'] = seasonality['std_dev'].round(2)
    return seasonality

def get_all_seasonalities(df: pd.DataFrame, price_col: str = 'Close') -> Dict[str, pd.DataFrame]:
    monthly_returns = calculate_monthly_returns(df, price_col)
    results = {
        '5y': calculate_seasonality(monthly_returns, years_back=5),
        '10y': calculate_seasonality(monthly_returns, years_back=10),
        '15y': calculate_seasonality(monthly_returns, years_back=15),
        'all': calculate_seasonality(monthly_returns, years_back=None)
    }
    return results
