"""
Persistent cache service for managing extended stock data cache
Implements intelligent caching with configurable expiration times
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models import Stock as StockModel, ExtendedStockDataCache
from backend.app.services.yfinance_service import (
    get_extended_stock_data,
    get_stock_dividends_and_splits,
    get_stock_calendar_and_earnings,
    get_analyst_data,
    get_institutional_holders
)
import logging

logger = logging.getLogger(__name__)

CACHE_DURATION_HOURS = {
    'extended_data': 12,
    'dividends_splits': 24,
    'calendar_data': 6,
    'analyst_data': 4,
    'holders_data': 12,
}

class StockDataCacheService:
    def __init__(self, db_session: Session):
        self.db = db_session
    def get_cached_extended_data(self, stock_id: int, force_refresh: bool = False) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Return a tuple (cached_record_dict, cache_hit)

        - If a valid, non-expired cache entry exists and force_refresh is False, return it with cache_hit=True
        - Otherwise, attempt to fetch fresh extended data via get_extended_stock_data, store/update the DB entry,
          and return the newly stored data with cache_hit=False (or True if an existing entry was reused).

        The returned cached_record_dict is a plain dict with keys matching the ExtendedStockDataCache model columns,
        e.g. {'extended_data': ..., 'dividends_splits_data': ..., 'calendar_data': ..., 'analyst_data': ..., 'holders_data': ..., 'last_updated': ..., 'expires_at': ..., 'fetch_success': ..., 'error_message': ...}
        """
        try:
            # Resolve stock and existing cache entry
            stock = self.db.query(StockModel).filter(StockModel.id == stock_id).first()
            if not stock:
                logger.debug(f"Stock not found (id={stock_id}) when fetching cached extended data")
                return None, False
        except Exception as e:
            logger.exception(f"Unexpected error in get_cached_extended_data for stock {stock_id}: {e}")
            return None, False

        # After successfully resolving the stock, continue with cache lookup
        cache_entry = self.db.query(ExtendedStockDataCache).filter(ExtendedStockDataCache.stock_id == stock_id).first()

        now = datetime.utcnow()

        # If we have a cache entry and it's not expired and no force_refresh requested, return it
        if cache_entry and not force_refresh:
            try:
                expires_at = cache_entry.expires_at
                if expires_at and expires_at > now:
                    logger.debug(f"Cache hit for stock_id={stock_id}")
                    # Return a plain dict
                    return {
                        'extended_data': cache_entry.extended_data,
                        'dividends_splits_data': cache_entry.dividends_splits_data,
                        'calendar_data': cache_entry.calendar_data,
                        'analyst_data': cache_entry.analyst_data,
                        'holders_data': cache_entry.holders_data,
                        'cache_type': cache_entry.cache_type,
                        'last_updated': cache_entry.last_updated,
                        'expires_at': cache_entry.expires_at,
                        'fetch_success': cache_entry.fetch_success,
                        'error_message': cache_entry.error_message,
                    }, True
            except Exception:
                # If any unexpected error reading the entry, fall through to refresh
                logger.exception(f"Error while checking cache expiry for stock {stock_id}, will refresh")

        # Need to fetch fresh data (either no entry, expired, or force_refresh)
        try:
            logger.debug(f"Fetching fresh extended data for stock {stock.ticker_symbol} (id={stock_id})")
            extended = get_extended_stock_data(stock.ticker_symbol)

            # Build new/updated cache record
            expires_at = datetime.utcnow() + timedelta(hours=CACHE_DURATION_HOURS.get('extended_data', 12))

            if cache_entry:
                cache_entry.extended_data = extended
                cache_entry.last_updated = datetime.utcnow()
                cache_entry.expires_at = expires_at
                cache_entry.fetch_success = True if extended else False
                cache_entry.error_message = None if extended else 'No data returned'
                self.db.add(cache_entry)
            else:
                cache_entry = ExtendedStockDataCache(
                    stock_id=stock_id,
                    extended_data=extended,
                    dividends_splits_data=None,
                    calendar_data=None,
                    analyst_data=None,
                    holders_data=None,
                    cache_type='extended',
                    last_updated=datetime.utcnow(),
                    expires_at=expires_at,
                    fetch_success=True if extended else False,
                    error_message=None if extended else 'No data returned'
                )
                self.db.add(cache_entry)

            # Commit DB changes
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception(f"Failed to commit cache entry for stock {stock_id}")

            result = {
                'extended_data': cache_entry.extended_data,
                'dividends_splits_data': cache_entry.dividends_splits_data,
                'calendar_data': cache_entry.calendar_data,
                'analyst_data': cache_entry.analyst_data,
                'holders_data': cache_entry.holders_data,
                'cache_type': cache_entry.cache_type,
                'last_updated': cache_entry.last_updated,
                'expires_at': cache_entry.expires_at,
                'fetch_success': cache_entry.fetch_success,
                'error_message': cache_entry.error_message,
            }

            return result, False

        except Exception as e:
            logger.exception(f"Failed to fetch or store extended data for stock {stock_id}: {e}")
            # If there is an existing cache entry (even expired), return it as a fallback
            if cache_entry:
                return {
                    'extended_data': cache_entry.extended_data,
                    'dividends_splits_data': cache_entry.dividends_splits_data,
                    'calendar_data': cache_entry.calendar_data,
                    'analyst_data': cache_entry.analyst_data,
                    'holders_data': cache_entry.holders_data,
                    'cache_type': cache_entry.cache_type,
                    'last_updated': cache_entry.last_updated,
                    'expires_at': cache_entry.expires_at,
                    'fetch_success': cache_entry.fetch_success,
                    'error_message': cache_entry.error_message,
                }, True
            return None, False

