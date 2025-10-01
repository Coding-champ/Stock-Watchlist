from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
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
    stocks = relationship("Stock", back_populates="watchlist", cascade="all, delete-orphan")


class Stock(Base):
    """Stock model for individual stocks in watchlists"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    isin = Column(String, nullable=False)
    ticker_symbol = Column(String, nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    position = Column(Integer, default=0)  # For ordering stocks in watchlist
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="stocks")
    stock_data = relationship("StockData", back_populates="stock", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="stock", cascade="all, delete-orphan")
    extended_cache = relationship("ExtendedStockDataCache", back_populates="stock", uselist=False, cascade="all, delete-orphan")


class StockData(Base):
    """Stock data model for current market data"""
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    current_price = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)  # KGV - Kurs-Gewinn-Verhältnis
    rsi = Column(Float, nullable=True)  # Relative Strength Index
    volatility = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="stock_data")


class Alert(Base):
    """Alert model for price and metric alerts"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    alert_type = Column(String, nullable=False)  # 'price', 'pe_ratio', 'rsi', 'volatility'
    condition = Column(String, nullable=False)  # 'above', 'below', 'equals'
    threshold_value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
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
