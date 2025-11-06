from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    JSON,
    UniqueConstraint,
    Date,
    BigInteger,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base


class Watchlist(Base):
    """Watchlist model for organizing stocks"""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stocks = relationship("Stock", secondary="stocks_in_watchlist", back_populates="watchlists", viewonly=True)
    stock_watchlist_entries = relationship("StockInWatchlist", back_populates="watchlist", cascade="all, delete-orphan")


class Stock(Base):
    """Stock model for master stock data (Stammdaten)"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    isin = Column(String, nullable=True, index=True)
    wkn = Column(String, nullable=True, index=True)
    ticker_symbol = Column(String, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    business_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    watchlists = relationship("Watchlist", secondary="stocks_in_watchlist", back_populates="stocks", viewonly=True)
    watchlist_entries = relationship("StockInWatchlist", back_populates="stock", cascade="all, delete-orphan")
    price_data = relationship("StockPriceData", back_populates="stock", cascade="all, delete-orphan")
    fundamental_data = relationship("StockFundamentalData", back_populates="stock", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="stock", cascade="all, delete-orphan")
    extended_cache = relationship("ExtendedStockDataCache", back_populates="stock", uselist=False, cascade="all, delete-orphan")


class StockInWatchlist(Base):
    """Association table for stocks in watchlists (n:m relationship)"""
    __tablename__ = "stocks_in_watchlist"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "stock_id", name="uq_watchlist_stock"),
        Index("idx_watchlist_position", "watchlist_id", "position"),
    )

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    exchange = Column(String, nullable=True)  # e.g., "XETRA", "NASDAQ"
    currency = Column(String, nullable=True)  # e.g., "EUR", "USD"
    observation_reasons = Column(JSON, nullable=False, default=list)
    observation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="stock_watchlist_entries")
    stock = relationship("Stock", back_populates="watchlist_entries")


class StockPriceData(Base):
    """Historical daily price data for stocks"""
    __tablename__ = "stock_price_data"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stock_price_date"),
        Index("idx_stock_date", "stock_id", "date"),
        # Optimized index for "get latest price" queries (ORDER BY date DESC)
        Index("idx_stock_date_desc", "stock_id", "date", postgresql_ops={"date": "DESC"}),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=True)
    adjusted_close = Column(Float, nullable=True)
    dividends = Column(Float, nullable=True, default=0.0)  # Dividend amount on ex-div date
    stock_splits = Column(Float, nullable=True)  # Split ratio (e.g., 2.0 for 2:1 split)
    # Exchange and currency for price rows (nullable to support legacy rows)
    exchange = Column(String, nullable=True)  # e.g., "XETRA", "NASDAQ"
    currency = Column(String, nullable=True)  # e.g., "EUR", "USD"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="price_data")


class StockFundamentalData(Base):
    """Quarterly fundamental financial data for stocks"""
    __tablename__ = "stock_fundamental_data"
    __table_args__ = (
        UniqueConstraint("stock_id", "period", name="uq_stock_fundamental_period"),
        Index("idx_stock_period", "stock_id", "period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    period = Column(String, nullable=False, index=True)  # e.g., "FY2025Q3"
    period_end_date = Column(Date, nullable=True)
    
    # Income Statement
    revenue = Column(Float, nullable=True)
    earnings = Column(Float, nullable=True)  # Net Income
    eps_basic = Column(Float, nullable=True)
    eps_diluted = Column(Float, nullable=True)
    operating_income = Column(Float, nullable=True)
    gross_profit = Column(Float, nullable=True)
    ebitda = Column(Float, nullable=True)
    
    # Balance Sheet
    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)
    shareholders_equity = Column(Float, nullable=True)
    
    # Cash Flow
    operating_cashflow = Column(Float, nullable=True)
    free_cashflow = Column(Float, nullable=True)
    
    # Ratios (can be calculated or stored)
    profit_margin = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    return_on_equity = Column(Float, nullable=True)
    return_on_assets = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    current_ratio = Column(Float, nullable=True)
    quick_ratio = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="fundamental_data")


class Alert(Base):
    """Alert model for price and metric alerts"""
    __tablename__ = "alerts"
    __table_args__ = (
        # Optimized index for checking active alerts per stock
        Index("idx_stock_active", "stock_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    alert_type = Column(String, nullable=False)  # 'price', 'pe_ratio', 'rsi', 'volatility', 'price_change_percent', 'ma_cross', 'volume_spike', 'earnings', 'composite'
    condition = Column(String, nullable=False)  # 'above', 'below', 'equals', 'cross_above', 'cross_below', 'before'
    threshold_value = Column(Float, nullable=False)
    timeframe_days = Column(Integer, nullable=True)  # For percentage changes (e.g., 1 day, 7 days) or earnings days before
    composite_conditions = Column(JSON, nullable=True)  # For composite alerts: [{"type": "rsi", "condition": "below", "value": 30}, ...]
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)  # When alert was last triggered
    trigger_count = Column(Integer, default=0)  # How many times triggered
    expiry_date = Column(DateTime, nullable=True)  # Optional expiry date for auto-cleanup
    notes = Column(Text, nullable=True)  # Optional user notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="alerts")


class ExtendedStockDataCache(Base):
    """Cache model for extended yfinance stock data"""
    __tablename__ = "extended_stock_data_cache"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, unique=True)
    
    # Cached data as JSON
    extended_data = Column(JSON, nullable=True)  # Complete extended data from yfinance
    dividends_splits_data = Column(JSON, nullable=True)  # Historical dividends and splits
    calendar_data = Column(JSON, nullable=True)  # Earnings calendar data
    analyst_data = Column(JSON, nullable=True)  # Analyst recommendations and estimates
    holders_data = Column(JSON, nullable=True)  # Institutional and mutual fund holders
    
    # Cache metadata
    cache_type = Column(String, default="extended")  # Type of cached data
    last_updated = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # When cache expires
    fetch_success = Column(Boolean, default=True)  # Whether last fetch was successful
    error_message = Column(Text, nullable=True)  # Error message if fetch failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="extended_cache")
