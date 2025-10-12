"""
Cache service for managing extended stock data cache
Implements intelligent caching with configurable expiration times
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
"""
Cache service split: persistent cache and in-memory cache are now in separate modules.
Import persistent cache via persistent_cache_service and in-memory cache via in_memory_cache.
"""

from backend.app.services.persistent_cache_service import StockDataCacheService
from backend.app.services.in_memory_cache import (
    SimpleCache,
    cache_service,
    get_chart_cache_key,
    get_indicators_cache_key,
    get_comparison_cache_key,
    cache_chart_data,
    get_cached_chart_data,
    cache_indicators,
    get_cached_indicators,
    cache_comparison_data,
    get_cached_comparison_data,
    invalidate_chart_cache
)
