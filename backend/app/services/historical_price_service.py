"""
Historical Price Data Service
Handles loading, storing, and retrieving historical stock price data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from backend.app.models import Stock, StockPriceData

logger = logging.getLogger(__name__)


class HistoricalPriceService:
    """Service for managing historical price data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def load_and_save_historical_prices(
        self, 
        stock_id: int, 
        period: str = "max",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Load historical price data from yfinance and save to database
        
        Args:
            stock_id: Database ID of the stock
            period: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Data interval ("1d", "1wk", "1mo")
        
        Returns:
            Dict with status and count of records saved
        """
        try:
            # Get stock from database
            stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                return {"success": False, "error": "Stock not found", "count": 0}
            
            logger.info(f"Loading historical data for {stock.ticker_symbol} (period={period})")
            
            # Fetch data from yfinance
            ticker = yf.Ticker(stock.ticker_symbol)
            hist_data = ticker.history(period=period, interval=interval)
            
            if hist_data.empty:
                logger.warning(f"No historical data available for {stock.ticker_symbol}")
                return {"success": False, "error": "No data available", "count": 0}
            
            # Save data to database
            records_saved = self._save_price_data(stock_id, hist_data)
            
            logger.info(f"Saved {records_saved} price records for {stock.ticker_symbol}")
            
            return {
                "success": True,
                "count": records_saved,
                "date_range": {
                    "start": hist_data.index.min().strftime("%Y-%m-%d") if not hist_data.empty else None,
                    "end": hist_data.index.max().strftime("%Y-%m-%d") if not hist_data.empty else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading historical prices for stock {stock_id}: {e}")
            return {"success": False, "error": str(e), "count": 0}
    
    def _save_price_data(self, stock_id: int, df: pd.DataFrame) -> int:
        """
        Save price data from DataFrame to database
        Uses bulk insert for performance
        
        Args:
            stock_id: Database ID of the stock
            df: DataFrame with price data (from yfinance)
        
        Returns:
            Number of records saved
        """
        records_saved = 0
        
        try:
            # Prepare data for bulk insert
            price_records = []
            
            for date_idx, row in df.iterrows():
                # Convert timestamp to date
                price_date = date_idx.date() if hasattr(date_idx, 'date') else date_idx
                
                # Check if record already exists
                existing = self.db.query(StockPriceData).filter(
                    and_(
                        StockPriceData.stock_id == stock_id,
                        StockPriceData.date == price_date
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    existing.open = float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None
                    existing.high = float(row.get('High', 0)) if pd.notna(row.get('High')) else None
                    existing.low = float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None
                    existing.close = float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None
                    existing.volume = int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None
                    existing.adjusted_close = float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None
                    existing.dividends = float(row.get('Dividends', 0)) if pd.notna(row.get('Dividends')) else 0.0
                    existing.stock_splits = float(row.get('Stock Splits', 0)) if pd.notna(row.get('Stock Splits')) else None
                    records_saved += 1
                else:
                    # Create new record
                    price_record = StockPriceData(
                        stock_id=stock_id,
                        date=price_date,
                        open=float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                        high=float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                        low=float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                        close=float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                        volume=int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                        adjusted_close=float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                        dividends=float(row.get('Dividends', 0)) if pd.notna(row.get('Dividends')) else 0.0,
                        stock_splits=float(row.get('Stock Splits', 0)) if pd.notna(row.get('Stock Splits')) else None
                    )
                    price_records.append(price_record)
                    records_saved += 1
            
            # Bulk insert new records
            if price_records:
                self.db.bulk_save_objects(price_records)
            
            self.db.commit()
            
            return records_saved
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving price data: {e}")
            raise
    
    def get_historical_prices(
        self, 
        stock_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[StockPriceData]:
        """
        Retrieve historical price data from database
        
        Args:
            stock_id: Database ID of the stock
            start_date: Optional start date
            end_date: Optional end date
            limit: Optional limit on number of records
        
        Returns:
            List of StockPriceData objects
        """
        try:
            query = self.db.query(StockPriceData).filter(
                StockPriceData.stock_id == stock_id
            )
            
            if start_date:
                query = query.filter(StockPriceData.date >= start_date)
            
            if end_date:
                query = query.filter(StockPriceData.date <= end_date)
            
            # Order by date descending (newest first)
            query = query.order_by(desc(StockPriceData.date))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error retrieving historical prices: {e}")
            return []
    
    def get_latest_price(self, stock_id: int) -> Optional[StockPriceData]:
        """
        Get the most recent price data for a stock
        
        Args:
            stock_id: Database ID of the stock
        
        Returns:
            Latest StockPriceData or None
        """
        try:
            return self.db.query(StockPriceData).filter(
                StockPriceData.stock_id == stock_id
            ).order_by(desc(StockPriceData.date)).first()
            
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None
    
    def get_price_on_date(self, stock_id: int, target_date: date) -> Optional[StockPriceData]:
        """
        Get price data for a specific date
        
        Args:
            stock_id: Database ID of the stock
            target_date: The date to retrieve
        
        Returns:
            StockPriceData for that date or None
        """
        try:
            return self.db.query(StockPriceData).filter(
                and_(
                    StockPriceData.stock_id == stock_id,
                    StockPriceData.date == target_date
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting price on date: {e}")
            return None
    
    def update_recent_prices(self, stock_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Update only the most recent price data (for daily updates)
        
        Args:
            stock_id: Database ID of the stock
            days: Number of days to fetch (default 7 to catch weekends)
        
        Returns:
            Dict with status and count
        """
        try:
            # Get the most recent date we have
            latest = self.get_latest_price(stock_id)
            
            if latest:
                # Fetch only new data
                start_date = latest.date
                period = f"{days}d"
            else:
                # No data yet, fetch everything
                return self.load_and_save_historical_prices(stock_id, period="max")
            
            # Fetch recent data
            stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                return {"success": False, "error": "Stock not found", "count": 0}
            
            ticker = yf.Ticker(stock.ticker_symbol)
            hist_data = ticker.history(period=period, interval="1d")
            
            if hist_data.empty:
                return {"success": True, "count": 0, "message": "No new data"}
            
            # Save only new data
            records_saved = self._save_price_data(stock_id, hist_data)
            
            return {"success": True, "count": records_saved}
            
        except Exception as e:
            logger.error(f"Error updating recent prices: {e}")
            return {"success": False, "error": str(e), "count": 0}
    
    def get_price_dataframe(
        self, 
        stock_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get historical prices as a pandas DataFrame (useful for calculations)
        
        Args:
            stock_id: Database ID of the stock
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            DataFrame with date as index
        """
        try:
            prices = self.get_historical_prices(stock_id, start_date, end_date)
            
            if not prices:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for price in prices:
                data.append({
                    'date': price.date,
                    'open': price.open,
                    'high': price.high,
                    'low': price.low,
                    'close': price.close,
                    'volume': price.volume,
                    'adjusted_close': price.adjusted_close,
                    'dividends': price.dividends,
                    'stock_splits': price.stock_splits
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating price DataFrame: {e}")
            return pd.DataFrame()
    
    def get_data_quality_report(self, stock_id: int) -> Dict[str, Any]:
        """
        Get a report on the quality and completeness of historical data
        
        Returns:
            Dict with data quality metrics
        """
        try:
            prices = self.get_historical_prices(stock_id)
            
            if not prices:
                return {
                    "has_data": False,
                    "record_count": 0
                }
            
            dates = [p.date for p in prices]
            closes = [p.close for p in prices if p.close is not None]
            
            return {
                "has_data": True,
                "record_count": len(prices),
                "date_range": {
                    "start": min(dates).strftime("%Y-%m-%d"),
                    "end": max(dates).strftime("%Y-%m-%d")
                },
                "missing_closes": len(prices) - len(closes),
                "has_dividends": any(p.dividends and p.dividends > 0 for p in prices),
                "has_splits": any(p.stock_splits and p.stock_splits > 0 for p in prices),
                "completeness": len(closes) / len(prices) * 100 if prices else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating data quality report: {e}")
            return {"has_data": False, "error": str(e)}
