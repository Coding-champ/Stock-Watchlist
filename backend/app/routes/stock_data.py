from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from backend.app import schemas
from backend.app.models import (
    Stock as StockModel,
    StockPriceData as StockPriceDataModel
)
from backend.app.database import get_db
from backend.app.services.yfinance_service import get_chart_data, calculate_technical_indicators
from backend.app.services.cache_service import get_cached_chart_data, cache_chart_data
from backend.app.services.technical_indicators_service import (
    analyze_technical_indicators_with_divergence
)
import pandas as pd
import logging

router = APIRouter(prefix="/stock-data", tags=["stock-data"])
logger = logging.getLogger(__name__)


@router.get("/{stock_id}", response_model=List[schemas.StockData])
def get_stock_data(
    stock_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get historical price data for a stock from the database"""
    # Get stock to retrieve ticker
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get historical data from stock_price_data table
    price_data = db.query(StockPriceDataModel).filter(
        StockPriceDataModel.stock_id == stock_id
    ).order_by(desc(StockPriceDataModel.date)).offset(skip).limit(limit).all()
    
    # Convert to StockData schema
    stock_data_list = []
    for price in price_data:
        stock_data_list.append(schemas.StockData(
            id=price.id,
            stock_id=stock_id,
            current_price=price.close,
            pe_ratio=None,  # Not available in price data
            rsi=None,
            volatility=None,
            timestamp=datetime.combine(price.date, datetime.min.time())
        ))
    
    return stock_data_list


@router.get("/{stock_id}/chart")
def get_stock_chart_data(
    stock_id: int,
    period: str = Query("1y", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 3y, 5y, max"),
    interval: str = Query("1d", description="Data interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"),
    include_volume: bool = Query(True, description="Include volume data"),
    start: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get chart data for a stock
    Returns OHLCV data formatted for frontend chart components
    """
    # Get stock to retrieve ticker
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    ticker = stock.ticker_symbol
    
    # Try to get from cache first
    try:
        cached_data = get_cached_chart_data(ticker, period, interval)
        if cached_data and not (start or end):  # Don't use cache for custom date ranges
            logger.debug(f"Using cached chart data for {ticker} ({period}/{interval})")
            return cached_data
    except Exception as e:
        logger.warning(f"Failed to retrieve cached chart data: {e}")
    
    # Fetch from yfinance
    try:
        chart_data = get_chart_data(
            ticker_symbol=ticker,
            period=period if not (start or end) else None,
            interval=interval,
            start=start,
            end=end,
            include_dividends=True,
            include_volume=include_volume
        )
        
        if not chart_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No chart data found for {ticker}"
            )
        
        # Cache the data (only for non-custom date ranges)
        if not (start or end):
            try:
                # Cache for 30 minutes for intraday, 1 hour for daily+
                ttl = 1800 if interval in ['1m', '5m', '15m', '30m'] else 3600
                cache_chart_data(ticker, period, interval, chart_data, ttl=ttl)
            except Exception as e:
                logger.warning(f"Failed to cache chart data: {e}")
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error fetching chart data for {ticker}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch chart data: {str(e)}"
        )


@router.get("/{stock_id}/chart/intraday")
def get_intraday_chart(
    stock_id: int,
    days: int = Query(1, description="Number of days (1-5)", ge=1, le=5),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get intraday chart data (5-minute intervals)
    Optimized endpoint for recent trading data
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Map days to period and interval
    period_map = {
        1: ("1d", "5m"),
        2: ("2d", "5m"),
        5: ("5d", "5m")
    }
    
    period, interval = period_map.get(days, ("1d", "5m"))
    
    try:
        chart_data = get_chart_data(
            ticker_symbol=stock.ticker_symbol,
            period=period,
            interval=interval,
            include_dividends=False,
            include_volume=True
        )
        
        if not chart_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No intraday data found for {stock.ticker_symbol}"
            )
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error fetching intraday data for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch intraday data: {str(e)}"
        )


@router.get("/{stock_id}/technical-indicators")
def get_technical_indicators(
    stock_id: int,
    period: str = Query("1y", description="Time period for calculation"),
    indicators: List[str] = Query([], description="Indicators to calculate: sma_50, sma_200, rsi, macd"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get technical indicators for a stock
    Available indicators: sma_50, sma_200, rsi, macd, bollinger_bands
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    if not indicators:
        # Default indicators if none specified
        indicators = ['sma_50', 'sma_200']
    
    try:
        indicators_data = calculate_technical_indicators(
            ticker_symbol=stock.ticker_symbol,
            period=period,
            indicators=indicators
        )
        
        if not indicators_data:
            logger.warning(f"No indicators data returned for {stock.ticker_symbol}")
            return {
                "stock_id": stock_id,
                "ticker_symbol": stock.ticker_symbol,
                "period": period,
                "dates": [],
                "close": [],
                "indicators": {}
            }
        
        # Return with flattened structure: the frontend expects direct access to indicators
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "period": period,
            "dates": indicators_data.get('dates', []),
            "close": indicators_data.get('close', []),
            "indicators": indicators_data.get('indicators', {})
        }
        
    except Exception as e:
        logger.error(f"Error calculating indicators for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to calculate indicators: {str(e)}"
        )


@router.get("/{stock_id}/calculated-metrics")
def get_calculated_metrics(
    stock_id: int,
    period: str = Query("1y", description="Period for calculations: 1mo, 3mo, 6mo, 1y, 2y"),
    use_cache: bool = Query(True, description="Use cached results if available"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive calculated metrics for a stock
    
    This endpoint provides:
    - Phase 1: Basic technical indicators (RSI, MACD, Moving Averages)
    - Phase 2: Valuation scores (P/E, P/B, PEG ratios)
    - Phase 3: Advanced analysis (Beta, Sharpe ratio, etc.)
    """
    from backend.app.services import calculated_metrics_service
    from backend.app.services.yfinance_service import get_extended_stock_data, get_historical_prices
    
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        # Get extended data (financial ratios, etc.)
        extended_data = get_extended_stock_data(stock.ticker_symbol)
        if not extended_data:
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for {stock.ticker_symbol}"
            )
        
        # Flatten extended_data for metrics calculation
        stock_data = {}
        for key, value in extended_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    stock_data[sub_key] = sub_value
            else:
                stock_data[key] = value
        
        # Get historical prices
        historical_prices = get_historical_prices(stock.ticker_symbol, period)
        
        # Calculate all metrics
        metrics_dict = calculated_metrics_service.calculate_all_metrics(
            stock_data,
            historical_prices
        )
        
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "period": period,
            "calculated_at": datetime.utcnow().isoformat(),
            "metrics": metrics_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metrics for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate metrics: {str(e)}"
        )


@router.get("/{stock_id}/divergence-analysis")
def get_divergence_analysis(
    stock_id: int,
    lookback_days: int = Query(60, description="Days to look back for divergence detection"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze technical indicators with divergence detection for RSI and MACD.
    
    This endpoint detects:
    - Bullish/Bearish RSI Divergences
    - Bullish/Bearish MACD Divergences
    - Overall trading signals
    
    Returns detailed divergence points for chart visualization.
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        # Get chart data for the lookback period + buffer
        period_days = lookback_days + 30  # Add buffer for calculations
        period = f"{period_days}d" if period_days < 365 else "1y"
        
        chart_data = get_chart_data(stock.ticker_symbol, period=period, interval="1d")
        
        if not chart_data or not chart_data.get('close'):
            raise HTTPException(
                status_code=404,
                detail=f"No chart data available for {stock.ticker_symbol}"
            )
        
        # Convert to pandas Series
        close_prices = pd.Series(chart_data['close'])
        high_prices = pd.Series(chart_data.get('high', [])) if chart_data.get('high') else None
        low_prices = pd.Series(chart_data.get('low', [])) if chart_data.get('low') else None
        
        # Perform comprehensive analysis with divergence detection
        analysis = analyze_technical_indicators_with_divergence(
            close_prices=close_prices,
            high_prices=high_prices,
            low_prices=low_prices,
            lookback_days=lookback_days
        )
        
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "lookback_days": lookback_days,
            "analyzed_at": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "dates": chart_data.get('dates', []),
            "close_prices": chart_data.get('close', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing divergences for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze divergences: {str(e)}"
        )
