"""
Cache service for managing extended stock data cache
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

# Cache configuration
CACHE_DURATION_HOURS = {
    'extended_data': 1,           # Extended financial data - 1 hour
    'dividends_splits': 24,       # Historical dividends/splits - 24 hours
    'calendar_data': 6,           # Earnings calendar - 6 hours
    'analyst_data': 4,            # Analyst data - 4 hours
    'holders_data': 12,           # Institutional holders - 12 hours
}

class StockDataCacheService:
    """Service for managing cached stock data"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_cached_extended_data(self, stock_id: int, force_refresh: bool = False) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Get cached extended data for a stock
        
        Args:
            stock_id: Stock ID
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            Tuple of (data_dict, cache_hit)
            cache_hit is True if data came from cache, False if fetched fresh
        """
        cache_entry = self.db.query(ExtendedStockDataCache).filter(
            ExtendedStockDataCache.stock_id == stock_id
        ).first()
        
        # Check if we need to refresh cache
        needs_refresh = (
            force_refresh or 
            not cache_entry or 
            not cache_entry.fetch_success or
            datetime.utcnow() > cache_entry.expires_at
        )
        
        if not needs_refresh and cache_entry:
            logger.info(f"Cache HIT for stock_id {stock_id}")
            return self._build_combined_data(cache_entry), True
        
        # Fetch fresh data
        logger.info(f"Cache MISS for stock_id {stock_id} - fetching fresh data")
        return self._fetch_and_cache_data(stock_id, cache_entry), False
    
    def _fetch_and_cache_data(self, stock_id: int, existing_cache: Optional[ExtendedStockDataCache]) -> Optional[Dict[str, Any]]:
        """Fetch fresh data from yfinance and update cache"""
        
        # Get stock ticker
        stock = self.db.query(StockModel).filter(StockModel.id == stock_id).first()
        if not stock:
            logger.error(f"Stock with ID {stock_id} not found")
            return None
        
        ticker = stock.ticker_symbol
        logger.info(f"Fetching fresh data for {ticker}")
        
        # Fetch all data types
        try:
            extended_data = get_extended_stock_data(ticker)
            dividends_splits_data = get_stock_dividends_and_splits(ticker)
            calendar_data = get_stock_calendar_and_earnings(ticker)
            analyst_data = get_analyst_data(ticker)
            holders_data = get_institutional_holders(ticker)
            
            # Calculate expiration time (use shortest cache duration)
            min_cache_hours = min(CACHE_DURATION_HOURS.values())
            expires_at = datetime.utcnow() + timedelta(hours=min_cache_hours)
            
            # Update or create cache entry
            if existing_cache:
                existing_cache.extended_data = extended_data
                existing_cache.dividends_splits_data = dividends_splits_data
                existing_cache.calendar_data = calendar_data
                existing_cache.analyst_data = analyst_data
                existing_cache.holders_data = holders_data
                existing_cache.last_updated = datetime.utcnow()
                existing_cache.expires_at = expires_at
                existing_cache.fetch_success = True
                existing_cache.error_message = None
                cache_entry = existing_cache
            else:
                cache_entry = ExtendedStockDataCache(
                    stock_id=stock_id,
                    extended_data=extended_data,
                    dividends_splits_data=dividends_splits_data,
                    calendar_data=calendar_data,
                    analyst_data=analyst_data,
                    holders_data=holders_data,
                    last_updated=datetime.utcnow(),
                    expires_at=expires_at,
                    fetch_success=True
                )
                self.db.add(cache_entry)
            
            self.db.commit()
            self.db.refresh(cache_entry)
            
            logger.info(f"Successfully cached data for {ticker}")
            return self._build_combined_data(cache_entry)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            
            # Update cache with error info
            if existing_cache:
                existing_cache.fetch_success = False
                existing_cache.error_message = str(e)
                existing_cache.last_updated = datetime.utcnow()
                # Set short expiration for failed fetches to retry sooner
                existing_cache.expires_at = datetime.utcnow() + timedelta(minutes=15)
                self.db.commit()
                
                # Return old data if available
                if existing_cache.extended_data:
                    logger.info(f"Returning stale cached data for {ticker} due to fetch error")
                    return self._build_combined_data(existing_cache)
            
            return None
    
    def _build_combined_data(self, cache_entry: ExtendedStockDataCache) -> Dict[str, Any]:
        """Build combined data dictionary from cache entry"""
        return {
            'extended_data': cache_entry.extended_data,
            'dividends_splits_data': cache_entry.dividends_splits_data,
            'calendar_data': cache_entry.calendar_data,
            'analyst_data': cache_entry.analyst_data,
            'holders_data': cache_entry.holders_data,
            'cache_info': {
                'last_updated': cache_entry.last_updated,
                'expires_at': cache_entry.expires_at,
                'fetch_success': cache_entry.fetch_success,
                'error_message': cache_entry.error_message
            }
        }
    
    def invalidate_cache(self, stock_id: int) -> bool:
        """Invalidate cache for a specific stock"""
        try:
            cache_entry = self.db.query(ExtendedStockDataCache).filter(
                ExtendedStockDataCache.stock_id == stock_id
            ).first()
            
            if cache_entry:
                # Set expiration to past to force refresh
                cache_entry.expires_at = datetime.utcnow() - timedelta(hours=1)
                self.db.commit()
                logger.info(f"Invalidated cache for stock_id {stock_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating cache for stock_id {stock_id}: {str(e)}")
            return False
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        try:
            # Delete entries that are older than 7 days and expired
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            deleted_count = self.db.query(ExtendedStockDataCache).filter(
                ExtendedStockDataCache.expires_at < datetime.utcnow(),
                ExtendedStockDataCache.last_updated < cutoff_date
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_entries = self.db.query(ExtendedStockDataCache).count()
            
            successful_entries = self.db.query(ExtendedStockDataCache).filter(
                ExtendedStockDataCache.fetch_success == True
            ).count()
            
            expired_entries = self.db.query(ExtendedStockDataCache).filter(
                ExtendedStockDataCache.expires_at < datetime.utcnow()
            ).count()
            
            recent_entries = self.db.query(ExtendedStockDataCache).filter(
                ExtendedStockDataCache.last_updated > datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            return {
                'total_entries': total_entries,
                'successful_entries': successful_entries,
                'failed_entries': total_entries - successful_entries,
                'expired_entries': expired_entries,
                'recent_updates': recent_entries,
                'cache_hit_rate': f"{(successful_entries / total_entries * 100):.1f}%" if total_entries > 0 else "0%"
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {'error': str(e)}