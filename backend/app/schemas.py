from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date


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
    """Base schema for stock master data (Stammdaten)"""
    isin: Optional[str] = None
    wkn: Optional[str] = None
    ticker_symbol: str
    name: str
    country: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    business_summary: Optional[str] = None


class StockCreate(StockBase):
    """Create stock with watchlist assignment"""
    watchlist_id: int
    observation_reasons: List[str] = Field(default_factory=list)
    observation_notes: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None


class StockCreateByTicker(BaseModel):
    """Schema für das Hinzufügen einer Aktie nur mit Ticker-Symbol"""
    ticker_symbol: str
    watchlist_id: int
    observation_reasons: List[str] = Field(default_factory=list)
    observation_notes: Optional[str] = None


class StockUpdate(BaseModel):
    isin: Optional[str] = None
    wkn: Optional[str] = None
    ticker_symbol: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    business_summary: Optional[str] = None


class StockMove(BaseModel):
    target_watchlist_id: int
    position: Optional[int] = None


class StockCopy(BaseModel):
    target_watchlist_id: int
    position: Optional[int] = None


# ============================================================================
# STOCKS IN WATCHLIST SCHEMAS (n:m Relation)
# ============================================================================

class StockInWatchlistBase(BaseModel):
    """Base schema for stock-watchlist association"""
    exchange: Optional[str] = None
    currency: Optional[str] = None
    observation_reasons: List[str] = Field(default_factory=list)
    observation_notes: Optional[str] = None
    position: int = 0


class StockInWatchlistCreate(StockInWatchlistBase):
    """Create stock-watchlist association"""
    watchlist_id: int
    stock_id: int


class StockInWatchlistUpdate(BaseModel):
    """Update stock-watchlist association"""
    exchange: Optional[str] = None
    currency: Optional[str] = None
    observation_reasons: Optional[List[str]] = None
    observation_notes: Optional[str] = None
    position: Optional[int] = None


class StockInWatchlist(StockInWatchlistBase):
    """Stock-watchlist association response"""
    id: int
    watchlist_id: int
    stock_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STOCK PRICE DATA SCHEMAS (Historical)
# ============================================================================

class StockPriceDataBase(BaseModel):
    """Base schema for historical stock price data"""
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float
    volume: Optional[int] = None
    adjusted_close: Optional[float] = None
    dividends: Optional[float] = 0.0
    stock_splits: Optional[float] = None


class StockPriceData(StockPriceDataBase):
    """Historical stock price data response"""
    id: int
    stock_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HistoricalPriceRequest(BaseModel):
    """Request schema for loading historical prices"""
    period: str = "max"  # "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    interval: str = "1d"  # "1d", "1wk", "1mo"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class HistoricalPriceResponse(BaseModel):
    """Response schema for historical prices"""
    stock_id: int
    ticker_symbol: str
    count: int
    date_range: Dict[str, Optional[str]]  # {"start": "2020-01-01", "end": "2024-12-31"}
    data: List[StockPriceData]


# ============================================================================
# STOCK FUNDAMENTAL DATA SCHEMAS (Quarterly)
# ============================================================================

class StockFundamentalDataBase(BaseModel):
    """Base schema for quarterly fundamental data"""
    period: str  # e.g., "FY2025Q3"
    period_end_date: Optional[date] = None
    
    # Income Statement
    revenue: Optional[float] = None
    earnings: Optional[float] = None
    eps_basic: Optional[float] = None
    eps_diluted: Optional[float] = None
    operating_income: Optional[float] = None
    gross_profit: Optional[float] = None
    ebitda: Optional[float] = None
    
    # Balance Sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    
    # Cash Flow
    operating_cashflow: Optional[float] = None
    free_cashflow: Optional[float] = None
    
    # Ratios
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None


class StockFundamentalData(StockFundamentalDataBase):
    """Quarterly fundamental data response"""
    id: int
    stock_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FundamentalDataResponse(BaseModel):
    """Response schema for fundamental data"""
    stock_id: int
    ticker_symbol: str
    count: int
    data: List[StockFundamentalData]


# ============================================================================
# LEGACY STOCK DATA SCHEMAS (will be deprecated)
# ============================================================================

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
    """Stock response schema - includes watchlist context for API compatibility"""
    id: int
    # These fields are populated from StockInWatchlist for API compatibility
    watchlist_id: Optional[int] = None  # Current watchlist context
    position: Optional[int] = None  # Position in current watchlist
    observation_reasons: List[str] = Field(default_factory=list)  # From StockInWatchlist
    observation_notes: Optional[str] = None  # From StockInWatchlist
    exchange: Optional[str] = None  # From StockInWatchlist
    currency: Optional[str] = None  # From StockInWatchlist
    created_at: datetime
    updated_at: datetime
    stock_data: Optional[List[StockData]] = []  # DEPRECATED - kept for backwards compatibility
    latest_data: Optional[StockData] = None  # Populated from stock_price_data and stock_fundamental_data

    class Config:
        from_attributes = True


class StockWithExtendedData(Stock):
    extended_data: Optional[ExtendedStockData] = None

    class Config:
        from_attributes = True


class BulkStockAddRequest(BaseModel):
    watchlist_id: int
    identifiers: List[str]
    identifier_type: Literal["auto", "ticker", "isin"] = "auto"


class BulkStockAddItem(BaseModel):
    identifier: str
    resolved_ticker: Optional[str] = None
    status: Literal["created", "exists", "not_found", "invalid", "error"]
    message: Optional[str] = None
    stock: Optional[Stock] = None


class BulkStockAddResponse(BaseModel):
    watchlist_id: int
    results: List[BulkStockAddItem]
    created_count: int
    failed_count: int


# Watchlist with stocks
class WatchlistWithStocks(Watchlist):
    stocks: List[Stock] = []

    class Config:
        from_attributes = True


# Alert schemas
class AlertBase(BaseModel):
    alert_type: str  # 'price', 'pe_ratio', 'rsi', 'volatility', 'price_change_percent', 'ma_cross', 'volume_spike', 'earnings', 'composite'
    condition: str  # 'above', 'below', 'equals', 'cross_above', 'cross_below', 'before'
    threshold_value: Optional[float] = None
    timeframe_days: Optional[int] = None  # For percentage changes, earnings days before
    composite_conditions: Optional[List[Dict[str, Any]]] = None  # For composite alerts
    is_active: bool = True
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class AlertCreate(BaseModel):
    stock_id: Optional[int] = None
    stock_symbol: Optional[str] = None
    alert_type: str
    condition: str
    threshold_value: Optional[float] = None
    threshold: Optional[float] = None  # Alternative field name
    timeframe_days: Optional[int] = None
    composite_conditions: Optional[List[Dict[str, Any]]] = None
    is_active: bool = True
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class AlertUpdate(BaseModel):
    alert_type: Optional[str] = None
    condition: Optional[str] = None
    threshold_value: Optional[float] = None
    timeframe_days: Optional[int] = None
    composite_conditions: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class Alert(AlertBase):
    id: int
    stock_id: int
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CALCULATED METRICS SCHEMAS
# ============================================================================

# Phase 1: Basic Indicators
class Week52Metrics(BaseModel):
    distance_from_52w_high: Optional[float] = None
    distance_from_52w_low: Optional[float] = None
    position_in_52w_range: Optional[float] = None


class SMAMetrics(BaseModel):
    distance_from_sma50: Optional[float] = None
    distance_from_sma200: Optional[float] = None
    golden_cross: Optional[bool] = None
    death_cross: Optional[bool] = None
    trend: Optional[Literal['bullish', 'bearish', 'neutral']] = None
    price_above_sma50: Optional[bool] = None
    price_above_sma200: Optional[bool] = None


class VolumeMetrics(BaseModel):
    relative_volume: Optional[float] = None
    volume_ratio: Optional[float] = None
    volume_category: Optional[Literal['very_low', 'low', 'normal', 'high', 'very_high']] = None


class CrossoverEvent(BaseModel):
    type: Literal['golden_cross', 'death_cross']
    date: str
    price: float
    sma_short: float
    sma_long: float


class SMACrossovers(BaseModel):
    last_crossover_type: Optional[Literal['golden_cross', 'death_cross']] = None
    last_crossover_date: Optional[str] = None
    days_since_crossover: Optional[int] = None
    price_at_crossover: Optional[float] = None
    current_price: Optional[float] = None
    price_change_since_crossover: Optional[float] = None
    all_crossovers: list[CrossoverEvent] = []


class FibonacciLevels(BaseModel):
    swing_high: float
    swing_low: float
    range: float
    retracement: Dict[str, float]  # "0.0", "23.6", "38.2", "50.0", "61.8", "78.6", "100.0"
    extension: Dict[str, float]    # "0.0", "100.0", "127.2", "161.8", "200.0", "261.8"


class SupportResistanceLevel(BaseModel):
    price: float
    type: Literal['support', 'resistance']
    strength: int  # Wie oft getestet
    relevance: float  # Nähe zum aktuellen Preis
    score: float  # Gesamtscore


class SupportResistance(BaseModel):
    support: list[SupportResistanceLevel] = []
    resistance: list[SupportResistanceLevel] = []
    current_price: float


class Phase1BasicIndicators(BaseModel):
    week_52_metrics: Week52Metrics
    sma_metrics: SMAMetrics
    volume_metrics: VolumeMetrics
    fcf_yield: Optional[float] = None
    sma_crossovers: Optional[SMACrossovers] = None
    fibonacci_levels: Optional[FibonacciLevels] = None
    support_resistance: Optional[SupportResistance] = None


# Phase 2: Valuation Scores
class ValueMetrics(BaseModel):
    value_score: Optional[float] = None
    pe_score: Optional[float] = None
    pb_score: Optional[float] = None
    ps_score: Optional[float] = None
    value_category: Optional[Literal['undervalued', 'fair', 'overvalued']] = None


class QualityMetrics(BaseModel):
    quality_score: Optional[float] = None
    roe_score: Optional[float] = None
    roa_score: Optional[float] = None
    profitability_score: Optional[float] = None
    financial_health_score: Optional[float] = None
    quality_category: Optional[Literal['excellent', 'good', 'average', 'poor']] = None


class DividendMetrics(BaseModel):
    dividend_safety_score: Optional[float] = None
    payout_sustainability: Optional[float] = None
    yield_sustainability: Optional[float] = None
    dividend_growth_potential: Optional[float] = None
    safety_category: Optional[Literal['very_safe', 'safe', 'moderate', 'risky', 'very_risky']] = None


class Phase2ValuationScores(BaseModel):
    peg_ratio: Optional[float] = None
    value_metrics: ValueMetrics
    quality_metrics: QualityMetrics
    dividend_metrics: DividendMetrics


# Phase 3: Advanced Analysis
class MACDMetrics(BaseModel):
    macd_line: Optional[float] = None
    signal_line: Optional[float] = None
    histogram: Optional[float] = None
    trend: Optional[Literal['bullish', 'bearish', 'neutral']] = None


class StochasticMetrics(BaseModel):
    k_percent: Optional[float] = None
    d_percent: Optional[float] = None
    signal: Optional[Literal['overbought', 'oversold', 'neutral']] = None
    is_overbought: bool = False
    is_oversold: bool = False


class VolatilityMetrics(BaseModel):
    volatility_30d: Optional[float] = None
    volatility_90d: Optional[float] = None
    volatility_1y: Optional[float] = None
    volatility_category: Optional[Literal['very_low', 'low', 'moderate', 'high', 'very_high']] = None


class DrawdownMetrics(BaseModel):
    max_drawdown: Optional[float] = None
    max_drawdown_duration: Optional[int] = None
    current_drawdown: Optional[float] = None


class AnalystMetrics(BaseModel):
    upside_potential: Optional[float] = None
    target_mean: Optional[float] = None
    target_high: Optional[float] = None
    target_low: Optional[float] = None
    consensus_strength: Optional[Literal['strong', 'moderate', 'weak']] = None
    recommendation_score: Optional[float] = None
    number_of_analysts: Optional[int] = None


class BetaAdjustedMetrics(BaseModel):
    sharpe_ratio: Optional[float] = None
    alpha: Optional[float] = None
    treynor_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    beta_adjusted_return: Optional[float] = None
    information_ratio: Optional[float] = None
    downside_deviation: Optional[float] = None
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    risk_rating: Optional[Literal['low', 'moderate', 'high', 'very_high']] = None


class RiskAdjustedPerformance(BaseModel):
    overall_score: Optional[float] = None
    rating: Optional[Literal['excellent', 'good', 'average', 'poor']] = None
    sharpe_contribution: Optional[float] = None
    alpha_contribution: Optional[float] = None
    sortino_contribution: Optional[float] = None
    information_contribution: Optional[float] = None


class Phase3AdvancedAnalysis(BaseModel):
    macd: Optional[MACDMetrics] = None
    stochastic: Optional[StochasticMetrics] = None
    volatility: Optional[VolatilityMetrics] = None
    drawdown: Optional[DrawdownMetrics] = None
    beta_adjusted_metrics: Optional[BetaAdjustedMetrics] = None
    risk_adjusted_performance: Optional[RiskAdjustedPerformance] = None
    analyst_metrics: AnalystMetrics


# Complete Calculated Metrics
class CalculatedMetrics(BaseModel):
    basic_indicators: Phase1BasicIndicators
    valuation_scores: Phase2ValuationScores
    advanced_analysis: Phase3AdvancedAnalysis
    calculation_timestamp: str


# Extended Stock Data with Calculated Metrics
class StockWithCalculatedMetrics(StockWithExtendedData):
    calculated_metrics: Optional[CalculatedMetrics] = None

    class Config:
        from_attributes = True
