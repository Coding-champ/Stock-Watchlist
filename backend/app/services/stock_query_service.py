"""
StockQueryService: Centralized stock lookup and 404 handling for services/routes.
"""

from sqlalchemy.orm import Session
from backend.app.models import Stock as StockModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class StockQueryService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_stock_by_id(self, stock_id: int) -> Optional[StockModel]:
        stock = self.db.query(StockModel).filter(StockModel.id == stock_id).first()
        if not stock:
            logger.warning(f"Stock with ID {stock_id} not found.")
        return stock

    def get_stock_by_ticker(self, ticker: str) -> Optional[StockModel]:
        stock = self.db.query(StockModel).filter(StockModel.ticker_symbol == ticker).first()
        if not stock:
            logger.warning(f"Stock with ticker '{ticker}' not found.")
        return stock

    def get_stock_or_404(self, ticker: str) -> StockModel:
        stock = self.get_stock_by_ticker(ticker)
        if not stock:
            logger.error(f"Stock with ticker '{ticker}' not found. Raising 404.")
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found.")
        return stock

    def get_stock_id_or_404(self, stock_id: int) -> StockModel:
        stock = self.get_stock_by_id(stock_id)
        if not stock:
            logger.error(f"Stock with ID {stock_id} not found. Raising 404.")
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Stock ID '{stock_id}' not found.")
        return stock
