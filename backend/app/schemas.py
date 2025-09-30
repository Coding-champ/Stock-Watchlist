from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Watchlist schemas
class WatchlistBase(BaseModel):
    name: str
    description: Optional[str] = None


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Watchlist(WatchlistBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Stock schemas
class StockBase(BaseModel):
    isin: str
    ticker_symbol: str
    name: str
    country: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None


class StockCreate(StockBase):
    watchlist_id: int


class StockUpdate(BaseModel):
    isin: Optional[str] = None
    ticker_symbol: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None


class StockMove(BaseModel):
    target_watchlist_id: int
    position: Optional[int] = None


# StockData schemas
class StockDataBase(BaseModel):
    current_price: Optional[float] = None
    pe_ratio: Optional[float] = None
    rsi: Optional[float] = None
    volatility: Optional[float] = None


class StockDataCreate(StockDataBase):
    stock_id: int


class StockData(StockDataBase):
    id: int
    stock_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Stock with data (for detailed view)
class Stock(StockBase):
    id: int
    watchlist_id: int
    position: int
    created_at: datetime
    updated_at: datetime
    stock_data: Optional[List[StockData]] = []
    latest_data: Optional[StockData] = None

    class Config:
        from_attributes = True


# Watchlist with stocks
class WatchlistWithStocks(Watchlist):
    stocks: List[Stock] = []

    class Config:
        from_attributes = True


# Alert schemas
class AlertBase(BaseModel):
    alert_type: str  # 'price', 'pe_ratio', 'rsi', 'volatility'
    condition: str  # 'above', 'below', 'equals'
    threshold_value: float
    is_active: bool = True


class AlertCreate(AlertBase):
    stock_id: int


class AlertUpdate(BaseModel):
    alert_type: Optional[str] = None
    condition: Optional[str] = None
    threshold_value: Optional[float] = None
    is_active: Optional[bool] = None


class Alert(AlertBase):
    id: int
    stock_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
