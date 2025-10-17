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

    # Resample to month-end prices (last available price in each calendar month)
    monthly_prices = df[price_col].resample('M').last()

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
        'all': calculate_seasonality(monthly_returns, years_back=None),
        '5y': calculate_seasonality(monthly_returns, years_back=5),
        '10y': calculate_seasonality(monthly_returns, years_back=10),
        '15y': calculate_seasonality(monthly_returns, years_back=15)
    }
    return results
