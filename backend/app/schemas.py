from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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


class StockCreateByTicker(BaseModel):
    """Schema für das Hinzufügen einer Aktie nur mit Ticker-Symbol"""
    ticker_symbol: str
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
# Extended Stock Data schemas
class FinancialRatios(BaseModel):
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    profit_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    market_cap: Optional[float] = None


class CashflowData(BaseModel):
    operating_cashflow: Optional[float] = None
    free_cashflow: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    debt_to_equity: Optional[float] = None


class DividendInfo(BaseModel):
    dividend_rate: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    five_year_avg_dividend_yield: Optional[float] = None
    ex_dividend_date: Optional[int] = None


class PriceData(BaseModel):
    current_price: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    fifty_day_average: Optional[float] = None
    two_hundred_day_average: Optional[float] = None


class VolumeData(BaseModel):
    volume: Optional[int] = None
    average_volume: Optional[int] = None
    average_volume_10days: Optional[int] = None


class RiskMetrics(BaseModel):
    beta: Optional[float] = None
    volatility_30d: Optional[float] = None
    shares_outstanding: Optional[int] = None
    float_shares: Optional[int] = None
    held_percent_insiders: Optional[float] = None
    held_percent_institutions: Optional[float] = None


# New schemas for additional yfinance data
class DividendHistory(BaseModel):
    date: str
    amount: float


class SplitHistory(BaseModel):
    date: str
    ratio: float


class EarningsDate(BaseModel):
    date: str
    eps_estimate: Optional[float] = None
    reported_eps: Optional[float] = None
    surprise: Optional[float] = None


class AnalystRecommendation(BaseModel):
    date: str
    firm: str
    to_grade: str
    from_grade: str
    action: str


class PriceTargets(BaseModel):
    current: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None


class EarningsEstimate(BaseModel):
    avg: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    num_analysts: Optional[int] = None


class InstitutionalHolder(BaseModel):
    holder: str
    shares: int
    date_reported: str
    percent_out: float
    value: int


class MutualFundHolder(BaseModel):
    holder: str
    shares: int
    date_reported: str
    percent_out: float
    value: int


class HistoricalData(BaseModel):
    dividends: List[DividendHistory] = []
    splits: List[SplitHistory] = []


class CalendarData(BaseModel):
    earnings_dates: List[EarningsDate] = []
    calendar: Dict[str, Any] = {}


class AnalystData(BaseModel):
    recommendations: List[AnalystRecommendation] = []
    price_targets: Optional[PriceTargets] = None
    earnings_estimates: Dict[str, EarningsEstimate] = {}


class HoldersData(BaseModel):
    major_holders: Dict[str, str] = {}
    institutional_holders: List[InstitutionalHolder] = []
    mutualfund_holders: List[MutualFundHolder] = []


class ExtendedStockData(BaseModel):
    business_summary: Optional[str] = None
    financial_ratios: Optional[FinancialRatios] = None
    cashflow_data: Optional[CashflowData] = None
    dividend_info: Optional[DividendInfo] = None
    price_data: Optional[PriceData] = None
    volume_data: Optional[VolumeData] = None
    risk_metrics: Optional[RiskMetrics] = None
    historical_data: Optional[HistoricalData] = None
    calendar_data: Optional[CalendarData] = None
    analyst_data: Optional[AnalystData] = None
    holders_data: Optional[HoldersData] = None


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


class StockWithExtendedData(Stock):
    extended_data: Optional[ExtendedStockData] = None

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
