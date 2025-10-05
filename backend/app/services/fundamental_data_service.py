"""
Fundamental Data Service
Handles loading, storing, and retrieving quarterly fundamental financial data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from backend.app.models import Stock, StockFundamentalData

logger = logging.getLogger(__name__)


class FundamentalDataService:
    """Service for managing fundamental financial data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def load_and_save_fundamental_data(self, stock_id: int) -> Dict[str, Any]:
        """
        Load quarterly fundamental data from yfinance and save to database
        
        Args:
            stock_id: Database ID of the stock
        
        Returns:
            Dict with status and count of records saved
        """
        try:
            # Get stock from database
            stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                return {"success": False, "error": "Stock not found", "count": 0}
            
            logger.info(f"Loading fundamental data for {stock.ticker_symbol}")
            
            # Fetch data from yfinance
            ticker = yf.Ticker(stock.ticker_symbol)
            
            # Get quarterly financials
            quarterly_income = ticker.quarterly_income_stmt
            quarterly_balance = ticker.quarterly_balance_sheet
            quarterly_cashflow = ticker.quarterly_cashflow
            
            if quarterly_income.empty and quarterly_balance.empty and quarterly_cashflow.empty:
                logger.warning(f"No fundamental data available for {stock.ticker_symbol}")
                return {"success": False, "error": "No data available", "count": 0}
            
            # Save data to database
            records_saved = self._save_fundamental_data(
                stock_id, 
                quarterly_income, 
                quarterly_balance, 
                quarterly_cashflow
            )
            
            logger.info(f"Saved {records_saved} fundamental records for {stock.ticker_symbol}")
            
            return {
                "success": True,
                "count": records_saved
            }
            
        except Exception as e:
            logger.error(f"Error loading fundamental data for stock {stock_id}: {e}")
            return {"success": False, "error": str(e), "count": 0}
    
    def _save_fundamental_data(
        self, 
        stock_id: int, 
        income_df: pd.DataFrame,
        balance_df: pd.DataFrame,
        cashflow_df: pd.DataFrame
    ) -> int:
        """
        Save fundamental data from DataFrames to database
        
        Args:
            stock_id: Database ID of the stock
            income_df: Income statement DataFrame
            balance_df: Balance sheet DataFrame
            cashflow_df: Cash flow DataFrame
        
        Returns:
            Number of records saved
        """
        records_saved = 0
        
        try:
            # Get all unique periods (column headers are dates)
            all_periods = set()
            
            if not income_df.empty:
                all_periods.update(income_df.columns)
            if not balance_df.empty:
                all_periods.update(balance_df.columns)
            if not cashflow_df.empty:
                all_periods.update(cashflow_df.columns)
            
            # Process each period
            for period_date in sorted(all_periods, reverse=True):
                try:
                    # Extract data for this period
                    period_str = self._format_period_string(period_date)
                    period_end = period_date.date() if hasattr(period_date, 'date') else period_date
                    
                    # Check if record already exists
                    existing = self.db.query(StockFundamentalData).filter(
                        and_(
                            StockFundamentalData.stock_id == stock_id,
                            StockFundamentalData.period == period_str
                        )
                    ).first()
                    
                    # Extract values from dataframes
                    fundamental_data = self._extract_fundamental_values(
                        period_date, income_df, balance_df, cashflow_df
                    )
                    
                    if existing:
                        # Update existing record
                        self._update_fundamental_record(existing, fundamental_data, period_end)
                    else:
                        # Create new record
                        new_record = StockFundamentalData(
                            stock_id=stock_id,
                            period=period_str,
                            period_end_date=period_end,
                            **fundamental_data
                        )
                        self.db.add(new_record)
                    
                    records_saved += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing period {period_date}: {e}")
                    continue
            
            self.db.commit()
            return records_saved
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving fundamental data: {e}")
            raise
    
    def _extract_fundamental_values(
        self,
        period_date,
        income_df: pd.DataFrame,
        balance_df: pd.DataFrame,
        cashflow_df: pd.DataFrame
    ) -> Dict[str, Optional[float]]:
        """Extract fundamental values for a specific period"""
        
        def safe_get(df: pd.DataFrame, key: str, period) -> Optional[float]:
            """Safely get a value from DataFrame"""
            try:
                if df.empty or period not in df.columns:
                    return None
                if key in df.index:
                    value = df.loc[key, period]
                    if pd.notna(value):
                        return float(value)
            except:
                pass
            return None
        
        # Income Statement data
        revenue = safe_get(income_df, 'Total Revenue', period_date)
        earnings = safe_get(income_df, 'Net Income', period_date)
        operating_income = safe_get(income_df, 'Operating Income', period_date)
        gross_profit = safe_get(income_df, 'Gross Profit', period_date)
        ebitda = safe_get(income_df, 'EBITDA', period_date)
        
        # Balance Sheet data
        total_assets = safe_get(balance_df, 'Total Assets', period_date)
        total_liabilities = safe_get(balance_df, 'Total Liabilities Net Minority Interest', period_date)
        shareholders_equity = safe_get(balance_df, 'Stockholders Equity', period_date)
        
        # Cash Flow data
        operating_cashflow = safe_get(cashflow_df, 'Operating Cash Flow', period_date)
        free_cashflow = safe_get(cashflow_df, 'Free Cash Flow', period_date)
        
        # Calculate ratios
        profit_margin = None
        if revenue and revenue != 0 and earnings:
            profit_margin = earnings / revenue
        
        operating_margin = None
        if revenue and revenue != 0 and operating_income:
            operating_margin = operating_income / revenue
        
        return_on_equity = None
        if shareholders_equity and shareholders_equity != 0 and earnings:
            return_on_equity = earnings / shareholders_equity
        
        return_on_assets = None
        if total_assets and total_assets != 0 and earnings:
            return_on_assets = earnings / total_assets
        
        debt_to_equity = None
        if shareholders_equity and shareholders_equity != 0 and total_liabilities:
            debt_to_equity = total_liabilities / shareholders_equity
        
        return {
            'revenue': revenue,
            'earnings': earnings,
            'operating_income': operating_income,
            'gross_profit': gross_profit,
            'ebitda': ebitda,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'shareholders_equity': shareholders_equity,
            'operating_cashflow': operating_cashflow,
            'free_cashflow': free_cashflow,
            'profit_margin': profit_margin,
            'operating_margin': operating_margin,
            'return_on_equity': return_on_equity,
            'return_on_assets': return_on_assets,
            'debt_to_equity': debt_to_equity
        }
    
    def _update_fundamental_record(
        self, 
        record: StockFundamentalData, 
        data: Dict[str, Optional[float]],
        period_end: date
    ):
        """Update an existing fundamental data record"""
        record.period_end_date = period_end
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.updated_at = datetime.utcnow()
    
    def _format_period_string(self, period_date) -> str:
        """
        Format period date to string like "FY2025Q3"
        
        Args:
            period_date: Pandas Timestamp or datetime
        
        Returns:
            Formatted period string
        """
        try:
            if hasattr(period_date, 'year'):
                year = period_date.year
                month = period_date.month
                quarter = (month - 1) // 3 + 1
                return f"FY{year}Q{quarter}"
            return str(period_date)
        except:
            return str(period_date)
    
    def get_fundamental_data(
        self, 
        stock_id: int,
        periods: Optional[int] = None
    ) -> List[StockFundamentalData]:
        """
        Retrieve fundamental data from database
        
        Args:
            stock_id: Database ID of the stock
            periods: Number of periods to retrieve (None = all)
        
        Returns:
            List of StockFundamentalData objects (newest first)
        """
        try:
            query = self.db.query(StockFundamentalData).filter(
                StockFundamentalData.stock_id == stock_id
            ).order_by(desc(StockFundamentalData.period_end_date))
            
            if periods:
                query = query.limit(periods)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error retrieving fundamental data: {e}")
            return []
    
    def get_latest_fundamental_data(self, stock_id: int) -> Optional[StockFundamentalData]:
        """
        Get the most recent fundamental data for a stock
        
        Args:
            stock_id: Database ID of the stock
        
        Returns:
            Latest StockFundamentalData or None
        """
        try:
            return self.db.query(StockFundamentalData).filter(
                StockFundamentalData.stock_id == stock_id
            ).order_by(desc(StockFundamentalData.period_end_date)).first()
            
        except Exception as e:
            logger.error(f"Error getting latest fundamental data: {e}")
            return None
    
    def get_fundamental_dataframe(self, stock_id: int, periods: Optional[int] = None) -> pd.DataFrame:
        """
        Get fundamental data as pandas DataFrame
        
        Args:
            stock_id: Database ID of the stock
            periods: Number of periods to retrieve
        
        Returns:
            DataFrame with period as index
        """
        try:
            data_list = self.get_fundamental_data(stock_id, periods)
            
            if not data_list:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for item in data_list:
                data.append({
                    'period': item.period,
                    'period_end_date': item.period_end_date,
                    'revenue': item.revenue,
                    'earnings': item.earnings,
                    'eps_basic': item.eps_basic,
                    'eps_diluted': item.eps_diluted,
                    'operating_income': item.operating_income,
                    'gross_profit': item.gross_profit,
                    'ebitda': item.ebitda,
                    'total_assets': item.total_assets,
                    'total_liabilities': item.total_liabilities,
                    'shareholders_equity': item.shareholders_equity,
                    'operating_cashflow': item.operating_cashflow,
                    'free_cashflow': item.free_cashflow,
                    'profit_margin': item.profit_margin,
                    'operating_margin': item.operating_margin,
                    'return_on_equity': item.return_on_equity,
                    'return_on_assets': item.return_on_assets,
                    'debt_to_equity': item.debt_to_equity
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('period', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating fundamental DataFrame: {e}")
            return pd.DataFrame()
    
    def get_data_summary(self, stock_id: int) -> Dict[str, Any]:
        """
        Get a summary of available fundamental data
        
        Returns:
            Dict with summary information
        """
        try:
            data_list = self.get_fundamental_data(stock_id)
            
            if not data_list:
                return {
                    "has_data": False,
                    "record_count": 0
                }
            
            latest = data_list[0] if data_list else None
            
            return {
                "has_data": True,
                "record_count": len(data_list),
                "periods": [d.period for d in data_list],
                "latest_period": latest.period if latest else None,
                "latest_date": latest.period_end_date.strftime("%Y-%m-%d") if latest and latest.period_end_date else None,
                "has_revenue": any(d.revenue for d in data_list),
                "has_earnings": any(d.earnings for d in data_list),
                "has_cashflow": any(d.operating_cashflow for d in data_list)
            }
            
        except Exception as e:
            logger.error(f"Error generating fundamental data summary: {e}")
            return {"has_data": False, "error": str(e)}
