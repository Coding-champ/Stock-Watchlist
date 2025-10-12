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
    # ...existing code from cache_service.py (persistent cache methods)...
