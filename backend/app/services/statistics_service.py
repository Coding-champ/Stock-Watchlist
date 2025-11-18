"""
Statistics Service
Calculates advanced performance metrics for indices and stocks
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.models import AssetPriceData, AssetType
from backend.app.services.asset_price_service import AssetPriceService


class StatisticsService:
    """Service for calculating financial statistics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.asset_price_service = AssetPriceService(db)
    
    def calculate_index_statistics(
        self,
        ticker_symbol: str,
        risk_free_rate: float = 0.04  # 4% annual risk-free rate (US Treasury)
    ) -> Dict:
        """
        Calculate comprehensive statistics for an index
        
        Returns:
            - volatility_annual: Annualized volatility (standard deviation)
            - sharpe_ratio: Risk-adjusted return (Sharpe ratio)
            - max_drawdown: Maximum peak-to-trough decline
            - max_drawdown_period: Start and end dates of max drawdown
            - ytd_return: Year-to-date return percentage
            - return_1y: 1-year return percentage
            - return_3y: 3-year annualized return percentage
            - return_5y: 5-year annualized return percentage
            - return_10y: 10-year annualized return percentage
            - best_day: Best single-day return
            - worst_day: Worst single-day return
            - positive_days_pct: Percentage of positive return days
            - current_drawdown: Current drawdown from all-time high
        """
        
        # Fetch price data (all available)
        price_data = (
            self.db.query(AssetPriceData)
            .filter(
                AssetPriceData.asset_type == AssetType.INDEX,
                AssetPriceData.ticker_symbol == ticker_symbol
            )
            .order_by(AssetPriceData.date.asc())
            .all()
        )

        # Fallback: if no (or too little) stored data, fetch and persist once
        if not price_data or len(price_data) < 2:
            try:
                fetch_result = self.asset_price_service.load_and_save_price_data(
                    ticker_symbol=ticker_symbol,
                    asset_type=AssetType.INDEX,
                    period="max",
                    interval="1d"
                )
                if fetch_result.get("success"):
                    price_data = (
                        self.db.query(AssetPriceData)
                        .filter(
                            AssetPriceData.asset_type == AssetType.INDEX,
                            AssetPriceData.ticker_symbol == ticker_symbol
                        )
                        .order_by(AssetPriceData.date.asc())
                        .all()
                    )
            except Exception:
                pass

        if not price_data or len(price_data) < 2:
            return {"error": "Insufficient data for statistics calculation", "ticker": ticker_symbol}
        
        # Convert to pandas DataFrame for easier calculation
        df = pd.DataFrame([
            {
                'date': p.date,
                'close': p.close,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'volume': p.volume
            }
            for p in price_data
        ])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').set_index('date')
        
        # Calculate daily returns
        df['daily_return'] = df['close'].pct_change()
        
        # Current date and key reference dates
        today = datetime.now().date()
        start_of_year = datetime(today.year, 1, 1).date()
        
        # Initialize results
        stats = {
            "ticker": ticker_symbol,
            "data_start_date": df.index[0].date().isoformat(),
            "data_end_date": df.index[-1].date().isoformat(),
            "total_trading_days": len(df)
        }
        
        # --- Volatility (Annualized) ---
        # Daily volatility * sqrt(252 trading days)
        daily_vol = df['daily_return'].std()
        stats['volatility_annual'] = round(daily_vol * np.sqrt(252) * 100, 2)  # as percentage
        
        # --- Returns over different periods ---
        latest_close = df['close'].iloc[-1]
        
        # YTD Return
        ytd_data = df[df.index >= pd.Timestamp(start_of_year)]
        if len(ytd_data) > 0:
            ytd_start_price = ytd_data['close'].iloc[0]
            stats['ytd_return'] = round(((latest_close / ytd_start_price) - 1) * 100, 2)
        else:
            stats['ytd_return'] = None
        
        # 1-Year Return
        one_year_ago = today - timedelta(days=365)
        one_year_data = df[df.index >= pd.Timestamp(one_year_ago)]
        if len(one_year_data) > 0:
            one_year_start_price = one_year_data['close'].iloc[0]
            stats['return_1y'] = round(((latest_close / one_year_start_price) - 1) * 100, 2)
        else:
            stats['return_1y'] = None
        
        # 3-Year Annualized Return
        three_years_ago = today - timedelta(days=3*365)
        three_year_data = df[df.index >= pd.Timestamp(three_years_ago)]
        if len(three_year_data) > 0:
            three_year_start_price = three_year_data['close'].iloc[0]
            total_return_3y = (latest_close / three_year_start_price) - 1
            stats['return_3y'] = round(((1 + total_return_3y) ** (1/3) - 1) * 100, 2)
        else:
            stats['return_3y'] = None
        
        # 5-Year Annualized Return
        five_years_ago = today - timedelta(days=5*365)
        five_year_data = df[df.index >= pd.Timestamp(five_years_ago)]
        if len(five_year_data) > 0:
            five_year_start_price = five_year_data['close'].iloc[0]
            total_return_5y = (latest_close / five_year_start_price) - 1
            stats['return_5y'] = round(((1 + total_return_5y) ** (1/5) - 1) * 100, 2)
        else:
            stats['return_5y'] = None
        
        # 10-Year Annualized Return
        ten_years_ago = today - timedelta(days=10*365)
        ten_year_data = df[df.index >= pd.Timestamp(ten_years_ago)]
        if len(ten_year_data) > 0:
            ten_year_start_price = ten_year_data['close'].iloc[0]
            total_return_10y = (latest_close / ten_year_start_price) - 1
            stats['return_10y'] = round(((1 + total_return_10y) ** (1/10) - 1) * 100, 2)
        else:
            stats['return_10y'] = None
        
        # --- Sharpe Ratio (using 1-year data if available, else all data) ---
        sharpe_data = one_year_data if len(one_year_data) > 20 else df
        if len(sharpe_data) > 20:
            avg_daily_return = sharpe_data['daily_return'].mean()
            daily_std = sharpe_data['daily_return'].std()
            
            # Annualize
            annual_return = avg_daily_return * 252
            annual_std = daily_std * np.sqrt(252)
            
            # Sharpe = (Return - RiskFreeRate) / Volatility
            sharpe = (annual_return - risk_free_rate) / annual_std if annual_std > 0 else 0
            stats['sharpe_ratio'] = round(sharpe, 2)
        else:
            stats['sharpe_ratio'] = None
        
        # --- Maximum Drawdown ---
        df['cummax'] = df['close'].cummax()
        df['drawdown'] = (df['close'] / df['cummax']) - 1
        
        max_dd = df['drawdown'].min()
        stats['max_drawdown'] = round(max_dd * 100, 2)  # as percentage
        
        # Find the period of max drawdown
        max_dd_idx = df['drawdown'].idxmin()
        peak_before_dd = df.loc[:max_dd_idx, 'cummax'].idxmax()
        stats['max_drawdown_period'] = {
            "peak_date": peak_before_dd.date().isoformat(),
            "trough_date": max_dd_idx.date().isoformat()
        }
        
        # --- Current Drawdown from ATH ---
        current_dd = df['drawdown'].iloc[-1]
        stats['current_drawdown'] = round(current_dd * 100, 2)
        # Determine start of current drawdown (last ATH date before today)
        try:
            if current_dd < 0:
                # All-time high value at end
                ath_value = df['cummax'].iloc[-1]
                # Filter rows where close equals cumulative max (ATH points)
                ath_points = df[df['close'] == df['cummax']]
                # Last ATH before today (could be today if at high)
                last_ath_date = ath_points.index[-1]
                stats['current_drawdown_period'] = {
                    'start_date': last_ath_date.date().isoformat(),
                    'end_date': df.index[-1].date().isoformat()
                }
                # Duration of current drawdown in days
                stats['current_drawdown_duration_days'] = (df.index[-1].date() - last_ath_date.date()).days
            else:
                # No drawdown; start=end=today
                today_date = df.index[-1].date().isoformat()
                stats['current_drawdown_period'] = {
                    'start_date': today_date,
                    'end_date': today_date
                }
                stats['current_drawdown_duration_days'] = 0
        except Exception:
            stats['current_drawdown_period'] = None
            stats['current_drawdown_duration_days'] = None

        # --- Recovery Duration After Max Drawdown ---
        try:
            peak_date = pd.to_datetime(stats['max_drawdown_period']['peak_date']) if stats.get('max_drawdown_period') else None
            trough_date = pd.to_datetime(stats['max_drawdown_period']['trough_date']) if stats.get('max_drawdown_period') else None
            if peak_date is not None and trough_date is not None:
                peak_price = df.loc[peak_date, 'close'] if peak_date in df.index else None
                # Find first date after trough where close >= peak_price
                after_trough = df[df.index > trough_date]
                recovery_rows = after_trough[after_trough['close'] >= peak_price] if peak_price is not None else pd.DataFrame()
                if not recovery_rows.empty:
                    recovery_date = recovery_rows.index[0]
                    stats['max_drawdown_recovery_days'] = (recovery_date.date() - trough_date.date()).days
                    stats['max_drawdown_recovery_date'] = recovery_date.date().isoformat()
                else:
                    stats['max_drawdown_recovery_days'] = None  # Not yet recovered
                    stats['max_drawdown_recovery_date'] = None
            else:
                stats['max_drawdown_recovery_days'] = None
                stats['max_drawdown_recovery_date'] = None
        except Exception:
            stats['max_drawdown_recovery_days'] = None
            stats['max_drawdown_recovery_date'] = None

        # --- Count of New ATHs in Current Year ---
        try:
            year_start = pd.Timestamp(datetime(today.year, 1, 1))
            prior_high = df[df.index < year_start]['close'].max() if any(df.index < year_start) else -np.inf
            ath_count = 0
            for ts, row in df[df.index >= year_start].iterrows():
                if row['close'] > prior_high:
                    ath_count += 1
                    prior_high = row['close']
            stats['new_aths_ytd'] = ath_count
        except Exception:
            stats['new_aths_ytd'] = None
        
        # --- Best and Worst Days ---
        valid_returns = df['daily_return'].dropna()
        stats['best_day'] = round(valid_returns.max() * 100, 2)
        stats['worst_day'] = round(valid_returns.min() * 100, 2)
        # Dates for best/worst day
        try:
            best_idx = valid_returns.idxmax()
            worst_idx = valid_returns.idxmin()
            stats['best_day_date'] = best_idx.date().isoformat()
            stats['worst_day_date'] = worst_idx.date().isoformat()
        except Exception:
            stats['best_day_date'] = None
            stats['worst_day_date'] = None
        
        # --- Positive Days Percentage ---
        positive_days = (df['daily_return'] > 0).sum()
        total_days_with_return = df['daily_return'].notna().sum()
        stats['positive_days_pct'] = round((positive_days / total_days_with_return) * 100, 2) if total_days_with_return > 0 else None
        
        # --- Up/Down Ratio ---
        negative_days = (df['daily_return'] < 0).sum()
        stats['up_down_ratio'] = round(positive_days / negative_days, 2) if negative_days > 0 else None
        
        # --- Additional Metrics ---
        stats['average_volume'] = int(df['volume'].mean()) if 'volume' in df.columns else None
        stats['current_price'] = round(latest_close, 2)
        stats['all_time_high'] = round(df['close'].max(), 2)
        stats['all_time_low'] = round(df['close'].min(), 2)
        
        return stats
    
    def calculate_correlation(
        self,
        ticker1: str,
        ticker2: str,
        period_days: int = 252  # 1 year default
    ) -> Optional[float]:
        """
        Calculate correlation between two indices/assets
        """
        
        cutoff_date = datetime.now().date() - timedelta(days=period_days)
        
        # Fetch data for both assets
        data1 = (
            self.db.query(AssetPriceData)
            .filter(
                AssetPriceData.ticker_symbol == ticker1,
                AssetPriceData.date >= cutoff_date
            )
            .order_by(AssetPriceData.date.asc())
            .all()
        )
        
        data2 = (
            self.db.query(AssetPriceData)
            .filter(
                AssetPriceData.ticker_symbol == ticker2,
                AssetPriceData.date >= cutoff_date
            )
            .order_by(AssetPriceData.date.asc())
            .all()
        )
        
        if not data1 or not data2:
            return None
        
        # Convert to DataFrames
        df1 = pd.DataFrame([{'date': p.date, 'close': p.close} for p in data1])
        df2 = pd.DataFrame([{'date': p.date, 'close': p.close} for p in data2])
        
        df1['date'] = pd.to_datetime(df1['date'])
        df2['date'] = pd.to_datetime(df2['date'])
        
        # Merge on date
        merged = pd.merge(df1, df2, on='date', suffixes=('_1', '_2'))
        
        if len(merged) < 10:
            return None
        
        # Calculate correlation
        correlation = merged['close_1'].corr(merged['close_2'])
        
        return round(correlation, 3)
