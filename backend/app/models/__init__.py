from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
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
