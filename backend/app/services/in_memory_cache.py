"""
Simple in-memory cache for calculated metrics, chart data, indicators, and comparisons
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}

    def set(self, key: str, value: Any, ttl: int = 1800):
        expire_time = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = (value, expire_time)

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry:
            value, expire_time = entry
            if datetime.utcnow() < expire_time:
                return value
            else:
                # Expired
                del self._cache[key]
        return None

cache_service = SimpleCache()

# Chart/Indicator/Comparison cache helpers

def get_chart_cache_key(ticker: str, period: str, interval: str) -> str:
    return f"chart:{ticker}:{period}:{interval}"

def get_indicators_cache_key(ticker: str, period: str, indicators: str) -> str:
    return f"indicators:{ticker}:{period}:{indicators}"

def get_comparison_cache_key(tickers: list, period: str) -> str:
    tickers_str = ",".join(sorted(tickers))
    return f"comparison:{tickers_str}:{period}"

def cache_chart_data(ticker: str, period: str, interval: str, data: Any, ttl: int = 1800):
    cache_key = get_chart_cache_key(ticker, period, interval)
    cache_service.set(cache_key, data, ttl=ttl)

def get_cached_chart_data(ticker: str, period: str, interval: str) -> Optional[Any]:
    cache_key = get_chart_cache_key(ticker, period, interval)
    return cache_service.get(cache_key)

def cache_indicators(ticker: str, period: str, indicators: list, data: Any, ttl: int = 1800):
    indicators_str = ",".join(sorted(indicators))
    cache_key = get_indicators_cache_key(ticker, period, indicators_str)
    cache_service.set(cache_key, data, ttl=ttl)

def get_cached_indicators(ticker: str, period: str, indicators: list) -> Optional[Any]:
    indicators_str = ",".join(sorted(indicators))
    cache_key = get_indicators_cache_key(ticker, period, indicators_str)
    return cache_service.get(cache_key)

def cache_comparison_data(tickers: list, period: str, data: Any, ttl: int = 1800):
    cache_key = get_comparison_cache_key(tickers, period)
    cache_service.set(cache_key, data, ttl=ttl)

def get_cached_comparison_data(tickers: list, period: str) -> Optional[Any]:
    cache_key = get_comparison_cache_key(tickers, period)
    return cache_service.get(cache_key)

def invalidate_chart_cache(ticker: str):
    # This is a simple implementation - in production you might want to track all keys for a ticker and delete them specifically
    logger.info(f"Chart cache invalidation requested for {ticker}")
    # For now, users can force refresh by not using cache
