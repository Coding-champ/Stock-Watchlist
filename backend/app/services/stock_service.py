"""
Stock Service
Handles CRUD operations for stocks with the new n:m watchlist relationship
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional, List, Dict, Any
import logging

from backend.app.models import Stock, StockInWatchlist, Watchlist
from backend.app.services.yfinance_service import get_stock_info, get_stock_info_by_identifier
from backend.app.services.historical_price_service import HistoricalPriceService
from backend.app.services.fundamental_data_service import FundamentalDataService

logger = logging.getLogger(__name__)


class StockService:
    """Service for managing stocks and their watchlist associations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.historical_service = HistoricalPriceService(db)
        self.fundamental_service = FundamentalDataService(db)
    
    def create_stock(
        self,
        ticker_symbol: str,
        name: Optional[str] = None,
        isin: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        sector: Optional[str] = None,
        business_summary: Optional[str] = None,
        exchange: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Stock:
        """
        Create a new stock (simple version without watchlist association)
        
        Args:
            ticker_symbol: Stock ticker symbol
            name: Stock name
            isin: ISIN code
            country: Country
            industry: Industry
            sector: Sector
            business_summary: Business description
            exchange: Exchange
            currency: Currency
        
        Returns:
            Created Stock object
        """
        # Check if stock already exists
        existing = self.db.query(Stock).filter(Stock.ticker_symbol == ticker_symbol).first()
        if existing:
            logger.warning(f"Stock {ticker_symbol} already exists")
            return existing
        
        stock = Stock(
            ticker_symbol=ticker_symbol.upper(),
            name=name or ticker_symbol,
            isin=isin,
            country=country,
            industry=industry,
            sector=sector,
            business_summary=business_summary
        )
        
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)
        
        logger.info(f"Created stock: {ticker_symbol} (ID: {stock.id})")
        return stock
    
    def create_stock_with_watchlist(
        self,
        ticker_symbol: str,
        watchlist_id: int,
        observation_reasons: List[str] = None,
        observation_notes: Optional[str] = None,
        exchange: Optional[str] = None,
        currency: Optional[str] = None,
        load_historical: bool = True,
        load_fundamentals: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new stock or get existing, and add to watchlist
        Also loads historical and fundamental data
        
        Args:
            ticker_symbol: Stock ticker symbol
            watchlist_id: ID of watchlist to add stock to
            observation_reasons: List of observation reasons
            observation_notes: Optional notes
            exchange: Exchange (e.g., "XETRA", "NASDAQ")
            currency: Currency (e.g., "EUR", "USD")
            load_historical: Whether to load historical price data
            load_fundamentals: Whether to load fundamental data
        
        Returns:
            Dict with stock, watchlist entry, and load status
        """
        try:
            # Check if watchlist exists
            watchlist = self.db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
            if not watchlist:
                return {"success": False, "error": "Watchlist not found"}
            
            # Get or create stock
            stock = self.db.query(Stock).filter(Stock.ticker_symbol == ticker_symbol).first()
            
            if not stock:
                # Fetch stock info from yfinance
                stock_info = get_stock_info(ticker_symbol)
                if not stock_info:
                    return {"success": False, "error": f"Stock {ticker_symbol} not found"}
                
                # Create new stock entry
                stock = Stock(
                    ticker_symbol=ticker_symbol.upper(),
                    name=stock_info.name,
                    isin=stock_info.isin if stock_info.isin else None,
                    country=stock_info.country,
                    industry=stock_info.industry,
                    sector=stock_info.sector,
                    business_summary=stock_info.business_summary
                )
                self.db.add(stock)
                self.db.flush()  # Get the stock ID
                
                logger.info(f"Created new stock: {ticker_symbol} (ID: {stock.id})")
                
                # Load historical data in background
                if load_historical:
                    try:
                        hist_result = self.historical_service.load_and_save_historical_prices(
                            stock.id, period="max"
                        )
                        logger.info(f"Loaded {hist_result.get('count', 0)} historical records for {ticker_symbol}")
                    except Exception as e:
                        logger.error(f"Error loading historical data: {e}")
                
                # Load fundamental data
                if load_fundamentals:
                    try:
                        fund_result = self.fundamental_service.load_and_save_fundamental_data(stock.id)
                        logger.info(f"Loaded {fund_result.get('count', 0)} fundamental records for {ticker_symbol}")
                    except Exception as e:
                        logger.error(f"Error loading fundamental data: {e}")
            
            # Check if stock is already in this watchlist
            existing_entry = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == watchlist_id,
                    StockInWatchlist.stock_id == stock.id
                )
            ).first()
            
            if existing_entry:
                return {
                    "success": False,
                    "error": "Stock already in this watchlist",
                    "stock": stock,
                    "entry": existing_entry
                }
            
            # Get max position in watchlist
            max_position = self.db.query(StockInWatchlist).filter(
                StockInWatchlist.watchlist_id == watchlist_id
            ).count()
            
            # Create watchlist entry
            watchlist_entry = StockInWatchlist(
                watchlist_id=watchlist_id,
                stock_id=stock.id,
                position=max_position,
                exchange=exchange,
                currency=currency,
                observation_reasons=observation_reasons or [],
                observation_notes=observation_notes
            )
            self.db.add(watchlist_entry)
            self.db.commit()
            
            logger.info(f"Added {ticker_symbol} to watchlist {watchlist_id}")
            
            return {
                "success": True,
                "stock": stock,
                "entry": watchlist_entry,
                "created_new": True
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating stock with watchlist: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stocks_in_watchlist(self, watchlist_id: int) -> List[Dict[str, Any]]:
        """
        Get all stocks in a watchlist with their association data
        Returns API-compatible format
        
        Args:
            watchlist_id: ID of the watchlist
        
        Returns:
            List of stock dictionaries with watchlist context
        """
        try:
            # Query with join
            entries = self.db.query(StockInWatchlist).filter(
                StockInWatchlist.watchlist_id == watchlist_id
            ).options(
                joinedload(StockInWatchlist.stock)
            ).order_by(StockInWatchlist.position).all()
            
            # Format for API compatibility
            stocks = []
            for entry in entries:
                stock = entry.stock
                stock_dict = {
                    "id": stock.id,
                    "ticker_symbol": stock.ticker_symbol,
                    "name": stock.name,
                    "isin": stock.isin,
                    "wkn": stock.wkn,
                    "country": stock.country,
                    "industry": stock.industry,
                    "sector": stock.sector,
                    "business_summary": stock.business_summary,
                    # Watchlist context from StockInWatchlist
                    "watchlist_id": entry.watchlist_id,
                    "position": entry.position,
                    "exchange": entry.exchange,
                    "currency": entry.currency,
                    "observation_reasons": entry.observation_reasons,
                    "observation_notes": entry.observation_notes,
                    "created_at": stock.created_at,
                    "updated_at": stock.updated_at
                }
                stocks.append(stock_dict)
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting stocks in watchlist: {e}")
            return []
    
    def update_stock_master_data(self, stock_id: int, update_data: Dict[str, Any]) -> Optional[Stock]:
        """
        Update stock master data (Stammdaten)
        
        Args:
            stock_id: Stock ID
            update_data: Dict with fields to update
        
        Returns:
            Updated stock or None
        """
        try:
            stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                return None
            
            # Update allowed fields
            allowed_fields = ['name', 'isin', 'wkn', 'country', 'industry', 'sector', 'business_summary']
            for field in allowed_fields:
                if field in update_data:
                    setattr(stock, field, update_data[field])
            
            self.db.commit()
            return stock
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating stock master data: {e}")
            return None
    
    def update_watchlist_entry(
        self, 
        watchlist_id: int, 
        stock_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[StockInWatchlist]:
        """
        Update stock-watchlist association data
        
        Args:
            watchlist_id: Watchlist ID
            stock_id: Stock ID
            update_data: Dict with fields to update
        
        Returns:
            Updated entry or None
        """
        try:
            entry = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == watchlist_id,
                    StockInWatchlist.stock_id == stock_id
                )
            ).first()
            
            if not entry:
                return None
            
            # Update allowed fields
            allowed_fields = ['position', 'exchange', 'currency', 'observation_reasons', 'observation_notes']
            for field in allowed_fields:
                if field in update_data:
                    setattr(entry, field, update_data[field])
            
            self.db.commit()
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating watchlist entry: {e}")
            return None
    
    def move_stock_in_watchlist(
        self, 
        watchlist_id: int, 
        stock_id: int, 
        new_position: int
    ) -> bool:
        """
        Move a stock to a new position within the same watchlist
        
        Args:
            watchlist_id: Watchlist ID
            stock_id: Stock ID
            new_position: New position index
        
        Returns:
            True if successful
        """
        try:
            entry = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == watchlist_id,
                    StockInWatchlist.stock_id == stock_id
                )
            ).first()
            
            if not entry:
                return False
            
            old_position = entry.position
            
            # Update positions of other stocks
            if new_position < old_position:
                # Moving up - shift others down
                self.db.query(StockInWatchlist).filter(
                    and_(
                        StockInWatchlist.watchlist_id == watchlist_id,
                        StockInWatchlist.position >= new_position,
                        StockInWatchlist.position < old_position
                    )
                ).update({StockInWatchlist.position: StockInWatchlist.position + 1})
            elif new_position > old_position:
                # Moving down - shift others up
                self.db.query(StockInWatchlist).filter(
                    and_(
                        StockInWatchlist.watchlist_id == watchlist_id,
                        StockInWatchlist.position > old_position,
                        StockInWatchlist.position <= new_position
                    )
                ).update({StockInWatchlist.position: StockInWatchlist.position - 1})
            
            # Update target position
            entry.position = new_position
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error moving stock: {e}")
            return False
    
    def copy_stock_to_watchlist(
        self,
        source_watchlist_id: int,
        stock_id: int,
        target_watchlist_id: int,
        position: Optional[int] = None
    ) -> Optional[StockInWatchlist]:
        """
        Copy a stock to another watchlist
        
        Args:
            source_watchlist_id: Source watchlist ID
            stock_id: Stock ID
            target_watchlist_id: Target watchlist ID
            position: Optional position in target watchlist
        
        Returns:
            New watchlist entry or None
        """
        try:
            # Get source entry
            source_entry = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == source_watchlist_id,
                    StockInWatchlist.stock_id == stock_id
                )
            ).first()
            
            if not source_entry:
                return None
            
            # Check if already in target
            existing = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == target_watchlist_id,
                    StockInWatchlist.stock_id == stock_id
                )
            ).first()
            
            if existing:
                logger.warning(f"Stock {stock_id} already in target watchlist {target_watchlist_id}")
                return existing
            
            # Determine position
            if position is None:
                position = self.db.query(StockInWatchlist).filter(
                    StockInWatchlist.watchlist_id == target_watchlist_id
                ).count()
            
            # Create new entry
            new_entry = StockInWatchlist(
                watchlist_id=target_watchlist_id,
                stock_id=stock_id,
                position=position,
                exchange=source_entry.exchange,
                currency=source_entry.currency,
                observation_reasons=source_entry.observation_reasons,
                observation_notes=source_entry.observation_notes
            )
            self.db.add(new_entry)
            self.db.commit()
            
            return new_entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error copying stock to watchlist: {e}")
            return None
    
    def remove_stock_from_watchlist(self, watchlist_id: int, stock_id: int) -> bool:
        """
        Remove a stock from a watchlist
        
        Args:
            watchlist_id: Watchlist ID
            stock_id: Stock ID
        
        Returns:
            True if successful
        """
        try:
            entry = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == watchlist_id,
                    StockInWatchlist.stock_id == stock_id
                )
            ).first()
            
            if not entry:
                return False
            
            self.db.delete(entry)
            
            # Re-index remaining stocks
            remaining = self.db.query(StockInWatchlist).filter(
                and_(
                    StockInWatchlist.watchlist_id == watchlist_id,
                    StockInWatchlist.position > entry.position
                )
            ).all()
            
            for item in remaining:
                item.position -= 1
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing stock from watchlist: {e}")
            return False
    
    def delete_stock_completely(self, stock_id: int) -> bool:
        """
        Delete a stock completely from the database
        This will cascade delete all related data
        
        Args:
            stock_id: Stock ID
        
        Returns:
            True if successful
        """
        try:
            stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                return False
            
            self.db.delete(stock)
            self.db.commit()
            
            logger.info(f"Deleted stock {stock_id} completely")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting stock: {e}")
            return False
