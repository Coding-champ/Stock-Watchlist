"""
Index Service
Service for managing market indices and their operations
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from backend.app.models import MarketIndex, AssetType
from backend.app.services.asset_price_service import AssetPriceService

logger = logging.getLogger(__name__)


class IndexService:
    """Service for managing market indices"""
    
    def __init__(self, db: Session):
        self.db = db
        self.asset_price_service = AssetPriceService(db)
    
    def create_index(
        self,
        ticker_symbol: str,
        name: str,
        region: Optional[str] = None,
        index_type: Optional[str] = None,
        calculation_method: Optional[str] = None,
        benchmark_index: Optional[str] = None,
        description: Optional[str] = None
    ) -> MarketIndex:
        """
        Create a new market index
        
        Args:
            ticker_symbol: Ticker symbol (e.g., "^GSPC", "^DJI")
            name: Index name (e.g., "S&P 500")
            region: Geographic region (e.g., "US", "Germany")
            index_type: Type of index (e.g., "broad_market", "sector", "style")
            calculation_method: Method (e.g., "market_cap_weighted", "price_weighted")
            benchmark_index: Parent benchmark ticker (e.g., "^GSPC" for sector indices)
            description: Description text
        
        Returns:
            Created MarketIndex
        """
        # Check if index already exists
        existing = self.db.query(MarketIndex).filter(
            MarketIndex.ticker_symbol == ticker_symbol
        ).first()
        
        if existing:
            logger.warning(f"Index {ticker_symbol} already exists")
            return existing
        
        index = MarketIndex(
            ticker_symbol=ticker_symbol,
            name=name,
            region=region,
            index_type=index_type,
            calculation_method=calculation_method,
            benchmark_index=benchmark_index,
            description=description
        )
        
        self.db.add(index)
        self.db.commit()
        self.db.refresh(index)
        
        logger.info(f"Created index: {name} ({ticker_symbol})")
        return index
    
    def get_index_by_symbol(self, ticker_symbol: str) -> Optional[MarketIndex]:
        """
        Get index by ticker symbol
        
        Args:
            ticker_symbol: Ticker symbol
        
        Returns:
            MarketIndex or None
        """
        return self.db.query(MarketIndex).filter(
            MarketIndex.ticker_symbol == ticker_symbol
        ).first()
    
    def get_index_by_id(self, index_id: int) -> Optional[MarketIndex]:
        """
        Get index by ID
        
        Args:
            index_id: Index ID
        
        Returns:
            MarketIndex or None
        """
        return self.db.query(MarketIndex).filter(
            MarketIndex.id == index_id
        ).first()
    
    def get_all_indices(
        self,
        region: Optional[str] = None,
        index_type: Optional[str] = None
    ) -> List[MarketIndex]:
        """
        Get all indices with optional filtering
        
        Args:
            region: Filter by region (optional)
            index_type: Filter by type (optional)
        
        Returns:
            List of MarketIndex
        """
        query = self.db.query(MarketIndex)
        
        if region:
            query = query.filter(MarketIndex.region == region)
        if index_type:
            query = query.filter(MarketIndex.index_type == index_type)
        
        return query.order_by(MarketIndex.name).all()
    
    def update_index(
        self,
        ticker_symbol: str,
        **kwargs
    ) -> Optional[MarketIndex]:
        """
        Update index metadata
        
        Args:
            ticker_symbol: Ticker symbol
            **kwargs: Fields to update
        
        Returns:
            Updated MarketIndex or None
        """
        index = self.get_index_by_symbol(ticker_symbol)
        if not index:
            return None
        
        for key, value in kwargs.items():
            if hasattr(index, key):
                setattr(index, key, value)
        
        index.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(index)
        
        logger.info(f"Updated index: {ticker_symbol}")
        return index
    
    def delete_index(self, ticker_symbol: str) -> bool:
        """
        Delete an index (cascades to constituents and price data)
        
        Args:
            ticker_symbol: Ticker symbol
        
        Returns:
            True if deleted, False if not found
        """
        index = self.get_index_by_symbol(ticker_symbol)
        if not index:
            return False
        
        # Delete price data
        self.asset_price_service.delete_price_data(
            ticker_symbol=ticker_symbol,
            asset_type=AssetType.INDEX
        )
        
        # Delete index (constituents cascade automatically)
        self.db.delete(index)
        self.db.commit()
        
        logger.info(f"Deleted index: {ticker_symbol}")
        return True
    
    def load_index_price_data(
        self,
        ticker_symbol: str,
        period: str = "max",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Load historical price data for an index
        
        Args:
            ticker_symbol: Index ticker symbol
            period: Time period
            interval: Data interval
        
        Returns:
            Result dict with status and count
        """
        # Check if index exists
        index = self.get_index_by_symbol(ticker_symbol)
        if not index:
            return {"success": False, "error": "Index not found", "count": 0}
        
        # Use AssetPriceService to load data
        return self.asset_price_service.load_and_save_price_data(
            ticker_symbol=ticker_symbol,
            asset_type=AssetType.INDEX,
            period=period,
            interval=interval
        )
    
    def get_index_latest_price(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest price for an index
        
        Args:
            ticker_symbol: Index ticker symbol
        
        Returns:
            Price data dict or None
        """
        price_data = self.asset_price_service.get_latest_price(
            ticker_symbol=ticker_symbol,
            asset_type=AssetType.INDEX
        )
        
        if not price_data:
            return None
        
        return {
            "ticker_symbol": price_data.ticker_symbol,
            "date": price_data.date.isoformat(),
            "open": price_data.open,
            "high": price_data.high,
            "low": price_data.low,
            "close": price_data.close,
            "volume": price_data.volume,
            "currency": price_data.currency
        }
    
    def get_index_price_history(
        self,
        ticker_symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get price history for an index
        
        Args:
            ticker_symbol: Index ticker symbol
            start_date: Start date (optional)
            end_date: End date (optional)
            limit: Max records (optional)
        
        Returns:
            List of price data dicts
        """
        price_data = self.asset_price_service.get_price_data(
            ticker_symbol=ticker_symbol,
            asset_type=AssetType.INDEX,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return [
            {
                "date": p.date.isoformat(),
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume
            }
            for p in price_data
        ]
