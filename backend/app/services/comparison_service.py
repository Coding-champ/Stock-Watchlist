"""Comparison Service
Provides cross-asset comparison metrics (beta, correlation, relative strength).

Focus: Stock vs. Benchmark Index comparisons and generic correlation helpers.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import Stock, MarketIndex, AssetType
from backend.app.services.asset_price_service import AssetPriceService

logger = logging.getLogger(__name__)


PERIOD_DAY_MAP = {
    "1mo": 21,
    "3mo": 63,
    "6mo": 126,
    "1y": 252,
    "2y": 504,
    "5y": 1260,
}


class ComparisonService:
    """Service providing comparative analytics between assets."""

    def __init__(self, db: Session):
        self.db = db
        self.asset_price_service = AssetPriceService(db)

    # ------------------------ Data Helpers ------------------------
    def _load_price_dataframe(
        self,
        ticker_symbol: str,
        asset_type: AssetType,
        period_days: Optional[int] = None,
    ) -> pd.DataFrame:
        """Load price data from unified asset_price_data and return DataFrame.

        Args:
            ticker_symbol: Asset ticker
            asset_type: AssetType enum
            period_days: Limit to last N trading days (approx). If None -> all.
        """
        try:
            records = self.asset_price_service.get_price_data(
                ticker_symbol=ticker_symbol,
                asset_type=asset_type,
                start_date=None,
                end_date=None,
                limit=None,
            )
            if not records:
                return pd.DataFrame()
            data = [
                {"date": r.date, "close": r.close}
                for r in records
                if r.close is not None
            ]
            df = pd.DataFrame(data)
            if df.empty:
                return df
            df["date"] = pd.to_datetime(df["date"])
            df.sort_values("date", inplace=True)
            if period_days and len(df) > period_days:
                df = df.tail(period_days)
            df.set_index("date", inplace=True)
            return df
        except Exception as e:
            logger.error(f"Failed loading dataframe for {ticker_symbol}: {e}")
            return pd.DataFrame()

    def _compute_returns(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "close" not in df.columns:
            return pd.Series(dtype=float)
        return df["close"].pct_change().dropna()

    # ------------------------ Core Metrics ------------------------
    def calculate_beta(
        self,
        stock_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> Optional[float]:
        """Calculate beta of stock vs. benchmark using covariance/variance."""
        try:
            if stock_returns.empty or benchmark_returns.empty:
                return None
            # Align index intersection
            common_index = stock_returns.index.intersection(benchmark_returns.index)
            if len(common_index) < 10:  # need enough data points
                return None
            s = stock_returns.loc[common_index]
            b = benchmark_returns.loc[common_index]
            cov_matrix = np.cov(s, b)
            var_b = np.var(b)
            if var_b == 0:
                return None
            beta = cov_matrix[0, 1] / var_b
            return float(beta)
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return None

    def calculate_correlation(
        self,
        asset1_returns: pd.Series,
        asset2_returns: pd.Series,
    ) -> Optional[float]:
        try:
            if asset1_returns.empty or asset2_returns.empty:
                return None
            common = asset1_returns.index.intersection(asset2_returns.index)
            if len(common) < 10:
                return None
            c = asset1_returns.loc[common].corr(asset2_returns.loc[common])
            return float(c) if not pd.isna(c) else None
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return None

    def calculate_relative_strength(
        self,
        stock_prices: pd.DataFrame,
        benchmark_prices: pd.DataFrame,
    ) -> pd.DataFrame:
        """Normalize both price series to 100 at the first common date."""
        if stock_prices.empty or benchmark_prices.empty:
            return pd.DataFrame()
        common = stock_prices.index.intersection(benchmark_prices.index)
        if common.empty:
            return pd.DataFrame()
        s = stock_prices.loc[common]["close"]
        b = benchmark_prices.loc[common]["close"]
        base_s = s.iloc[0]
        base_b = b.iloc[0]
        if base_s == 0 or base_b == 0:
            return pd.DataFrame()
        norm_s = s / base_s * 100.0
        norm_b = b / base_b * 100.0
        rel = norm_s - norm_b
        return pd.DataFrame(
            {
                "stock": norm_s.round(2),
                "benchmark": norm_b.round(2),
                "relative": rel.round(2),
            },
            index=common,
        )

    def _max_drawdown(self, series: pd.Series) -> Optional[float]:
        if series.empty:
            return None
        roll_max = series.cummax()
        drawdowns = (series / roll_max) - 1.0
        return float(drawdowns.min()) if not drawdowns.empty else None

    # ------------------------ Public Composite ------------------------
    def benchmark_comparison(
        self,
        stock_id: int,
        index_symbol: str,
        period: str = "1y",
    ) -> Dict[str, Any]:
        """Return benchmark comparison metrics for stock vs index."""
        # Resolve period_days
        period_days = PERIOD_DAY_MAP.get(period)

        stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"error": "Stock not found"}
        index = self.db.query(MarketIndex).filter(MarketIndex.ticker_symbol == index_symbol).first()
        if not index:
            return {"error": "Index not found"}

        stock_df = self._load_price_dataframe(stock.ticker_symbol, AssetType.STOCK, period_days)
        index_df = self._load_price_dataframe(index_symbol, AssetType.INDEX, period_days)

        if stock_df.empty or index_df.empty:
            return {"error": "Insufficient price data"}

        stock_ret = self._compute_returns(stock_df)
        index_ret = self._compute_returns(index_df)

        beta = self.calculate_beta(stock_ret, index_ret)
        corr = self.calculate_correlation(stock_ret, index_ret)
        rel_df = self.calculate_relative_strength(stock_df, index_df)
        max_dd_stock = self._max_drawdown(rel_df["stock"]) if not rel_df.empty else None
        max_dd_index = self._max_drawdown(rel_df["benchmark"]) if not rel_df.empty else None
        outperformance = None
        if not rel_df.empty:
            outperformance = float(rel_df["relative"].iloc[-1])

        rel_payload = [
            {
                "date": idx.date().isoformat(),
                "stock": float(row.stock),
                "benchmark": float(row.benchmark),
                "relative": float(row.relative),
            }
            for idx, row in rel_df.iterrows()
        ] if not rel_df.empty else []

        def _classify_beta(val: Optional[float]) -> Optional[str]:
            if val is None:
                return None
            if val < 0.8:
                return "low"
            if val <= 1.2:
                return "market"
            return "high"

        def _classify_corr(val: Optional[float]) -> Optional[str]:
            if val is None:
                return None
            if val > 0.7:
                return "strong"
            if val >= 0.3:
                return "moderate"
            return "weak"

        return {
            "stock_id": stock_id,
            "stock_symbol": stock.ticker_symbol,
            "benchmark_symbol": index_symbol,
            "period": period,
            "beta": beta,
            "beta_class": _classify_beta(beta),
            "correlation": corr,
            "correlation_class": _classify_corr(corr),
            "relative_performance_series": rel_payload,
            "outperformance": outperformance,  # final relative difference
            "drawdown_comparison": {
                "stock_max_drawdown": max_dd_stock,
                "benchmark_max_drawdown": max_dd_index,
            },
            "data_points": len(rel_payload),
        }

    # ------------------------ Correlation Matrix ------------------------
    def get_correlation_matrix(
        self,
        index_symbols: List[str],
        period: str = "1y",
    ) -> Dict[str, Any]:
        """Build correlation matrix for given index symbols.

        Returns JSON friendly payload:
        {
            symbols: [...],
            period: "1y",
            matrix: [[1.0, ...], [...]],  # symmetric
            pairs: [{"a":"^GSPC","b":"^IXIC","correlation":0.87}, ...]
        }
        """
        if not index_symbols or len(index_symbols) < 2:
            return {"error": "At least two symbols required"}
        period_days = PERIOD_DAY_MAP.get(period)
        returns_map: Dict[str, pd.Series] = {}

        for sym in index_symbols:
            df = self._load_price_dataframe(sym, AssetType.INDEX, period_days)
            ret = self._compute_returns(df)
            if ret.empty:
                logger.warning(f"No returns data for {sym}")
            returns_map[sym] = ret

        # Build aligned DataFrame
        valid = [s for s, ser in returns_map.items() if not ser.empty]
        if len(valid) < 2:
            return {"error": "Insufficient data for correlation matrix"}

        # Align on common index intersection across all series
        common_index = None
        for sym in valid:
            ser = returns_map[sym]
            common_index = ser.index if common_index is None else common_index.intersection(ser.index)
        if common_index is None or len(common_index) < 10:
            return {"error": "Not enough overlapping data points"}

        aligned_df = pd.DataFrame({sym: returns_map[sym].loc[common_index] for sym in valid})
        corr_df = aligned_df.corr()
        symbols_order = list(corr_df.columns)
        matrix = corr_df.values.round(4).tolist()
        pairs: List[Dict[str, Any]] = []
        for i, a in enumerate(symbols_order):
            for j, b in enumerate(symbols_order):
                if j <= i:
                    continue
                val = matrix[i][j]
                pairs.append({"a": a, "b": b, "correlation": float(val)})

        return {
            "symbols": symbols_order,
            "period": period,
            "data_points": int(len(common_index)),
            "matrix": matrix,
            "pairs": pairs,
        }
