"""Market Breadth Service
Calculates advance/decline style breadth metrics for an index and its constituents.

Implementation notes:
 - Uses stock_price_data for constituent stocks (HistoricalPriceService logic inline for performance).
 - SMA 200 and 52w High/Low derived from recent closing prices (approx 252 trading days).
 - For history requests we pull (days + 200) closes per stock and compute a daily boolean close > SMA200.
 - Designed for moderate index sizes (e.g., 40 for DAX, 100 for NASDAQ100). For very large indices (e.g., S&P 500)
   future optimization could batch queries or add caching (Redis layer).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging
import pandas as pd

from backend.app.models import IndexConstituent, StockPriceData, MarketIndex
from backend.app.services.index_constituent_service import IndexConstituentService

logger = logging.getLogger(__name__)


class MarketBreadthService:
    def __init__(self, db: Session):
        self.db = db
        self.constituent_service = IndexConstituentService(db)

    # -------------------- Core data helpers --------------------
    def _get_active_stock_ids(self, index_id: int) -> List[int]:
        return [c.stock_id for c in self.constituent_service.get_active_constituents(index_id)]

    def _get_recent_closes(self, stock_id: int, limit: int) -> List[StockPriceData]:
        return self.db.query(StockPriceData).filter(
            StockPriceData.stock_id == stock_id
        ).order_by(desc(StockPriceData.date)).limit(limit).all()

    # -------------------- Point-in-time breadth --------------------
    def calculate_advance_decline(self, index_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        if target_date is None:
            target_date = date.today()
        stock_ids = self._get_active_stock_ids(index_id)
        advancing = declining = unchanged = 0
        details = []
        for sid in stock_ids:
            # Latest close (on or before target_date)
            latest = self.db.query(StockPriceData).filter(
                and_(
                    StockPriceData.stock_id == sid,
                    StockPriceData.date <= target_date
                )
            ).order_by(desc(StockPriceData.date)).first()
            if not latest:
                continue
            # Last 200 closes up to latest date (including)
            closes = self.db.query(StockPriceData).filter(
                and_(
                    StockPriceData.stock_id == sid,
                    StockPriceData.date <= latest.date
                )
            ).order_by(desc(StockPriceData.date)).limit(200).all()
            if len(closes) < 5:  # insufficient data
                continue
            sma200 = sum(p.close for p in closes) / len(closes)
            if latest.close > sma200:
                advancing += 1
                state = 'advancing'
            elif latest.close < sma200:
                declining += 1
                state = 'declining'
            else:
                unchanged += 1
                state = 'unchanged'
            details.append({
                'stock_id': sid,
                'date': latest.date.isoformat(),
                'close': latest.close,
                'sma200': round(sma200, 4),
                'state': state
            })
        total = advancing + declining + unchanged
        pct_adv = (advancing / total * 100.0) if total else 0.0
        return {
            'index_id': index_id,
            'date': target_date.isoformat(),
            'advancing': advancing,
            'declining': declining,
            'unchanged': unchanged,
            'percentage_advancing': round(pct_adv, 2),
            'total_count': total,
            'method': 'close_vs_sma200',
            'details_sample': details[:25]  # sample to keep payload bounded
        }

    def get_new_highs_lows(self, index_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        if target_date is None:
            target_date = date.today()
        stock_ids = self._get_active_stock_ids(index_id)
        new_highs = new_lows = 0
        considered = 0
        for sid in stock_ids:
            latest = self.db.query(StockPriceData).filter(
                and_(
                    StockPriceData.stock_id == sid,
                    StockPriceData.date <= target_date
                )
            ).order_by(desc(StockPriceData.date)).first()
            if not latest:
                continue
            # Last ~252 trading days for 52w range
            window = self.db.query(StockPriceData).filter(
                and_(
                    StockPriceData.stock_id == sid,
                    StockPriceData.date <= latest.date
                )
            ).order_by(desc(StockPriceData.date)).limit(252).all()
            if len(window) < 30:  # need minimum data
                continue
            closes = [p.close for p in window]
            hi = max(closes)
            lo = min(closes)
            considered += 1
            if latest.close >= hi:
                new_highs += 1
            if latest.close <= lo:
                new_lows += 1
        return {
            'index_id': index_id,
            'date': target_date.isoformat(),
            'new_highs': new_highs,
            'new_lows': new_lows,
            'considered': considered,
            'percentage_new_highs': round((new_highs / considered * 100.0) if considered else 0.0, 2),
            'percentage_new_lows': round((new_lows / considered * 100.0) if considered else 0.0, 2)
        }

    # -------------------- Historical breadth --------------------
    def calculate_advance_decline_history(self, index_id: int, days: int = 30) -> Dict[str, Any]:
        days = max(1, min(days, 90))  # clamp
        stock_ids = self._get_active_stock_ids(index_id)
        if not stock_ids:
            return {'error': 'No constituents'}
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 220)  # fetch sufficient backfill
        # Build per-stock DataFrame of closes
        series_map: Dict[int, pd.DataFrame] = {}
        for sid in stock_ids:
            rows = self.db.query(StockPriceData).filter(
                and_(
                    StockPriceData.stock_id == sid,
                    StockPriceData.date >= start_date,
                    StockPriceData.date <= end_date
                )
            ).order_by(StockPriceData.date).all()
            if len(rows) < 30:
                continue
            df = pd.DataFrame({'date': [r.date for r in rows], 'close': [r.close for r in rows]})
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            # Rolling SMA 200
            df['sma200'] = df['close'].rolling(window=200, min_periods=50).mean()
            # Rolling 52w high/low approximation (252 trading days)
            df['rolling_high_252'] = df['close'].rolling(window=252, min_periods=30).max()
            df['rolling_low_252'] = df['close'].rolling(window=252, min_periods=30).min()
            series_map[sid] = df
        if not series_map:
            return {'error': 'Insufficient data for constituents'}
        # Aggregate by date
        all_dates = sorted(set().union(*[df.index for df in series_map.values()]))
        recent_dates = [d for d in all_dates if d.date() >= (end_date - timedelta(days=days))]
        records = []
        for d in recent_dates:
            adv = dec = unch = 0
            new_highs = new_lows = 0
            for df in series_map.values():
                if d not in df.index:
                    continue
                row = df.loc[d]
                if pd.isna(row['sma200']):
                    continue
                if row['close'] > row['sma200']:
                    adv += 1
                elif row['close'] < row['sma200']:
                    dec += 1
                else:
                    unch += 1
                # High / Low checks (require rolling window values)
                rh = row.get('rolling_high_252')
                rl = row.get('rolling_low_252')
                if not pd.isna(rh) and row['close'] >= rh:
                    new_highs += 1
                if not pd.isna(rl) and row['close'] <= rl:
                    new_lows += 1
            total = adv + dec + unch
            pct_adv = (adv / total * 100.0) if total else 0.0
            records.append({
                'date': d.date().isoformat(),
                'advancing': adv,
                'declining': dec,
                'unchanged': unch,
                'percentage_advancing': round(pct_adv, 2),
                'total_count': total,
                'new_highs': new_highs,
                'new_lows': new_lows
            })
        return {
            'index_id': index_id,
            'days': days,
            'records': records
        }

    def calculate_mcclellan_oscillator(self, index_id: int, days: int = 90) -> Dict[str, Any]:
        # Build history first
        hist = self.calculate_advance_decline_history(index_id, days=days)
        if 'records' not in hist:
            return {'error': hist.get('error', 'No history')}
        df = pd.DataFrame(hist['records'])
        if df.empty:
            return {'error': 'Empty history'}
        df['adv_dec_diff'] = df['advancing'] - df['declining']
        # Exponential moving averages (19, 39) typical parameters
        df['ema19'] = df['adv_dec_diff'].ewm(span=19, adjust=False).mean()
        df['ema39'] = df['adv_dec_diff'].ewm(span=39, adjust=False).mean()
        df['oscillator'] = df['ema19'] - df['ema39']
        payload = [
            {
                'date': r['date'],
                'adv_dec_diff': int(r['adv_dec_diff']),
                'ema19': round(float(r['ema19']), 3),
                'ema39': round(float(r['ema39']), 3),
                'oscillator': round(float(r['oscillator']), 3)
            }
            for r in df.to_dict(orient='records')
        ]
        return {
            'index_id': index_id,
            'days': days,
            'mcclellan': payload
        }
