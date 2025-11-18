"""
Asset Price Data Service
Base service for managing universal asset price data (stocks, indices, ETFs, bonds, crypto)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from backend.app.models import AssetPriceData, AssetType

logger = logging.getLogger(__name__)


class AssetPriceService:
    """Base service for managing asset price data across all asset types"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def load_and_save_price_data(
        self, 
        ticker_symbol: str,
        asset_type: AssetType,
        period: str = "max",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Load price data from yfinance and save to asset_price_data table
        
        Args:
            ticker_symbol: Ticker symbol (e.g., "AAPL", "^GSPC", "BTC-USD")
            asset_type: AssetType enum (STOCK, INDEX, ETF, BOND, CRYPTO)
            period: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Data interval ("1d", "1wk", "1mo")
        
        Returns:
            Dict with status and count of records saved
        """
        try:
            logger.info(f"Loading price data for {ticker_symbol} ({asset_type.value}, period={period})")
            
            # Fetch data from yfinance
            ticker = yf.Ticker(ticker_symbol)
            hist_data = ticker.history(period=period, interval=interval)
            
            # Try to get exchange and currency metadata
            info = {}
            try:
                info = ticker.info or {}
            except Exception:
                info = {}
            exchange = info.get('exchange') or info.get('market') or None
            currency = info.get('currency') or None
            
            if hist_data.empty:
                logger.warning(f"No price data available for {ticker_symbol}")
                return {"success": False, "error": "No data available", "count": 0}
            
            # Save data to database
            records_saved = self._save_price_data(
                ticker_symbol=ticker_symbol,
                asset_type=asset_type,
                hist_data=hist_data,
                exchange=exchange,
                currency=currency
            )
            
            logger.info(f"Saved {records_saved} price records for {ticker_symbol}")
            
            return {
                "success": True,
                "count": records_saved,
                "date_range": {
                    "start": hist_data.index.min().strftime("%Y-%m-%d") if not hist_data.empty else None,
                    "end": hist_data.index.max().strftime("%Y-%m-%d") if not hist_data.empty else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading price data for {ticker_symbol}: {e}")
            return {"success": False, "error": str(e), "count": 0}
    
    def _save_price_data(
        self,
        ticker_symbol: str,
        asset_type: AssetType,
        hist_data: pd.DataFrame,
        exchange: Optional[str] = None,
        currency: Optional[str] = None
    ) -> int:
        """
        Save price data to asset_price_data table (batch upsert)
        
        Args:
            ticker_symbol: Ticker symbol
            asset_type: AssetType enum
            hist_data: DataFrame from yfinance with OHLCV data
            exchange: Exchange name (optional)
            currency: Currency code (optional)
        
        Returns:
            Number of records saved
        """
        records_saved = 0
        
        for date_val, row in hist_data.iterrows():
            # Convert date
            if isinstance(date_val, pd.Timestamp):
                date_obj = date_val.date()
            else:
                date_obj = date_val
            
            # Check if record exists
            existing = self.db.query(AssetPriceData).filter(
                and_(
                    AssetPriceData.asset_type == asset_type,
                    AssetPriceData.ticker_symbol == ticker_symbol,
                    AssetPriceData.date == date_obj
                )
            ).first()
            
            # Prepare data (handle NaN values)
            open_val = None if pd.isna(row.get('Open')) else float(row['Open'])
            high_val = None if pd.isna(row.get('High')) else float(row['High'])
            low_val = None if pd.isna(row.get('Low')) else float(row['Low'])
            close_val = float(row['Close']) if not pd.isna(row['Close']) else None
            volume_val = None if pd.isna(row.get('Volume')) else int(row['Volume'])
            adj_close_val = None if pd.isna(row.get('Adj Close')) else float(row['Adj Close'])
            dividends_val = None if pd.isna(row.get('Dividends')) else float(row['Dividends'])
            splits_val = None if pd.isna(row.get('Stock Splits')) else float(row['Stock Splits'])
            
            if close_val is None:
                continue  # Skip rows without close price
            
            if existing:
                # Update existing record
                existing.open = open_val
                existing.high = high_val
                existing.low = low_val
                existing.close = close_val
                existing.volume = volume_val
                existing.adjusted_close = adj_close_val
                existing.dividends = dividends_val or 0.0
                existing.stock_splits = splits_val
                existing.exchange = exchange
                existing.currency = currency
            else:
                # Create new record
                price_record = AssetPriceData(
                    asset_type=asset_type,
                    ticker_symbol=ticker_symbol,
                    date=date_obj,
                    open=open_val,
                    high=high_val,
                    low=low_val,
                    close=close_val,
                    volume=volume_val,
                    adjusted_close=adj_close_val,
                    dividends=dividends_val or 0.0,
                    stock_splits=splits_val,
                    exchange=exchange,
                    currency=currency
                )
                self.db.add(price_record)
            
            records_saved += 1
        
        self.db.commit()
        return records_saved
    
    def get_price_data(
        self,
        ticker_symbol: str,
        asset_type: AssetType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[AssetPriceData]:
        """
        Retrieve price data from database
        
        Args:
            ticker_symbol: Ticker symbol
            asset_type: AssetType enum
            start_date: Start date (optional)
            end_date: End date (optional)
            limit: Maximum number of records (optional)
        
        Returns:
            List of AssetPriceData records
        """
        query = self.db.query(AssetPriceData).filter(
            and_(
                AssetPriceData.asset_type == asset_type,
                AssetPriceData.ticker_symbol == ticker_symbol
            )
        )
        
        if start_date:
            query = query.filter(AssetPriceData.date >= start_date)
        if end_date:
            query = query.filter(AssetPriceData.date <= end_date)
        
        query = query.order_by(desc(AssetPriceData.date))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_latest_price(
        self,
        ticker_symbol: str,
        asset_type: AssetType
    ) -> Optional[AssetPriceData]:
        """
        Get the most recent price record
        
        Args:
            ticker_symbol: Ticker symbol
            asset_type: AssetType enum
        
        Returns:
            Most recent AssetPriceData record or None
        """
        return self.db.query(AssetPriceData).filter(
            and_(
                AssetPriceData.asset_type == asset_type,
                AssetPriceData.ticker_symbol == ticker_symbol
            )
        ).order_by(desc(AssetPriceData.date)).first()
    
    def get_price_on_date(
        self,
        ticker_symbol: str,
        asset_type: AssetType,
        target_date: date
    ) -> Optional[AssetPriceData]:
        """
        Get price data for a specific date
        
        Args:
            ticker_symbol: Ticker symbol
            asset_type: AssetType enum
            target_date: Target date
        
        Returns:
            AssetPriceData record or None
        """
        return self.db.query(AssetPriceData).filter(
            and_(
                AssetPriceData.asset_type == asset_type,
                AssetPriceData.ticker_symbol == ticker_symbol,
                AssetPriceData.date == target_date
            )
        ).first()
    
    def delete_price_data(
        self,
        ticker_symbol: str,
        asset_type: AssetType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        Delete price data for a ticker symbol
        
        Args:
            ticker_symbol: Ticker symbol
            asset_type: AssetType enum
            start_date: Start date (optional, deletes all if not specified)
            end_date: End date (optional)
        
        Returns:
            Number of records deleted
        """
        query = self.db.query(AssetPriceData).filter(
            and_(
                AssetPriceData.asset_type == asset_type,
                AssetPriceData.ticker_symbol == ticker_symbol
            )
        )
        
        if start_date:
            query = query.filter(AssetPriceData.date >= start_date)
        if end_date:
            query = query.filter(AssetPriceData.date <= end_date)
        
        count = query.count()
        query.delete(synchronize_session=False)
        self.db.commit()
        
        return count
