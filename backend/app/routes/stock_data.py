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
from backend.app.services.historical_price_service import HistoricalPriceService
from backend.app.services.fundamental_data_service import FundamentalDataService
from backend.app.services.volume_profile_service import VolumeProfileService
import pandas as pd
import logging
import math

router = APIRouter(prefix="/stock-data", tags=["stock-data"])
logger = logging.getLogger(__name__)


def clean_json_floats(obj):
    """
    Recursively clean NaN and Infinity values from nested dictionaries/lists
    for JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: clean_json_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_floats(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


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
        
        # Clean NaN/Infinity values before returning
        result = {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "lookback_days": lookback_days,
            "analyzed_at": datetime.utcnow().isoformat(),
            "analysis": clean_json_floats(analysis),
            "dates": chart_data.get('dates', []),
            "close_prices": clean_json_floats(chart_data.get('close', []))
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing divergences for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze divergences: {str(e)}"
        )


# ============================================================================
# HISTORICAL PRICE DATA ENDPOINTS
# ============================================================================

@router.get("/{stock_id}/price-history")
def get_price_history(
    stock_id: int,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Max number of records to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get historical price data from the database
    
    Returns stored OHLCV data for a stock
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        historical_service = HistoricalPriceService(db)
        
        # Get data as DataFrame
        df = historical_service.get_historical_data(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or df.empty:
            return {
                "stock_id": stock_id,
                "ticker_symbol": stock.ticker_symbol,
                "count": 0,
                "date_range": {"start": None, "end": None},
                "data": []
            }
        
        # Limit results
        if len(df) > limit:
            df = df.tail(limit)
        
        # Convert to list of dicts
        data = []
        for idx, row in df.iterrows():
            data.append({
                "date": idx.strftime("%Y-%m-%d") if isinstance(idx, pd.Timestamp) else str(idx),
                "open": float(row['open']) if pd.notna(row['open']) else None,
                "high": float(row['high']) if pd.notna(row['high']) else None,
                "low": float(row['low']) if pd.notna(row['low']) else None,
                "close": float(row['close']) if pd.notna(row['close']) else None,
                "volume": int(row['volume']) if pd.notna(row['volume']) else None,
                "dividends": float(row['dividends']) if 'dividends' in row and pd.notna(row['dividends']) else None,
                "stock_splits": float(row['stock_splits']) if 'stock_splits' in row and pd.notna(row['stock_splits']) else None
            })
        
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "count": len(data),
            "date_range": {
                "start": data[0]["date"] if data else None,
                "end": data[-1]["date"] if data else None
            },
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Error getting price history for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get price history: {str(e)}"
        )


@router.post("/{stock_id}/refresh-history", status_code=202)
def refresh_price_history(
    stock_id: int,
    period: str = Query("max", description="Period to fetch: 1mo, 3mo, 6mo, 1y, 5y, max"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Refresh historical price data from yfinance
    
    Updates the database with latest price data
    Returns number of records updated
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        historical_service = HistoricalPriceService(db)
        
        # Load and save historical data
        result = historical_service.load_and_save_historical_data(
            stock_id=stock_id,
            ticker_symbol=stock.ticker_symbol,
            period=period
        )
        
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "period": period,
            "records_saved": result.get("records_saved", 0),
            "date_range": result.get("date_range", {}),
            "success": result.get("success", False),
            "message": result.get("message", "Updated successfully")
        }
        
    except Exception as e:
        logger.error(f"Error refreshing price history for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh price history: {str(e)}"
        )


# ============================================================================
# FUNDAMENTAL DATA ENDPOINTS
# ============================================================================

@router.get("/{stock_id}/fundamentals")
def get_fundamentals(
    stock_id: int,
    latest_only: bool = Query(False, description="Return only latest quarter"),
    limit: int = Query(8, description="Max number of quarters to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get fundamental data (quarterly financials) from the database
    
    Returns income statement, balance sheet, and cash flow data
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        fundamental_service = FundamentalDataService(db)
        
        # Get quarterly data
        quarters = fundamental_service.get_quarterly_data(
            stock_id=stock_id,
            limit=limit if not latest_only else 1
        )
        
        if not quarters:
            return {
                "stock_id": stock_id,
                "ticker_symbol": stock.ticker_symbol,
                "count": 0,
                "quarters": []
            }
        
        # Convert to dict format
        quarters_data = []
        for quarter in quarters:
            quarters_data.append({
                "period": quarter.period,
                "period_end_date": quarter.period_end_date.strftime("%Y-%m-%d") if quarter.period_end_date else None,
                "revenue": quarter.revenue,
                "earnings": quarter.earnings,
                "eps_basic": quarter.eps_basic,
                "eps_diluted": quarter.eps_diluted,
                "operating_income": quarter.operating_income,
                "gross_profit": quarter.gross_profit,
                "ebitda": quarter.ebitda,
                "total_assets": quarter.total_assets,
                "total_liabilities": quarter.total_liabilities,
                "shareholders_equity": quarter.shareholders_equity,
                "operating_cashflow": quarter.operating_cashflow,
                "free_cashflow": quarter.free_cashflow,
                "profit_margin": quarter.profit_margin,
                "operating_margin": quarter.operating_margin,
                "return_on_equity": quarter.return_on_equity,
                "return_on_assets": quarter.return_on_assets,
                "debt_to_equity": quarter.debt_to_equity,
                "current_ratio": quarter.current_ratio,
                "quick_ratio": quarter.quick_ratio
            })
        
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "count": len(quarters_data),
            "quarters": quarters_data
        }
        
    except Exception as e:
        logger.error(f"Error getting fundamentals for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fundamentals: {str(e)}"
        )


@router.post("/{stock_id}/refresh-fundamentals", status_code=202)
def refresh_fundamentals(
    stock_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Refresh fundamental data from yfinance
    
    Updates the database with latest quarterly financial data
    Returns number of quarters updated
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        fundamental_service = FundamentalDataService(db)
        
        # Load and save fundamental data
        result = fundamental_service.load_and_save_fundamental_data(
            stock_id=stock_id,
            ticker_symbol=stock.ticker_symbol
        )
        
        return {
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "quarters_saved": result.get("quarters_saved", 0),
            "success": result.get("success", False),
            "message": result.get("message", "Updated successfully")
        }
        
    except Exception as e:
        logger.error(f"Error refreshing fundamentals for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh fundamentals: {str(e)}"
        )


# ============================================================================
# VOLUME PROFILE ENDPOINTS
# ============================================================================

@router.get("/{stock_id}/volume-profile")
def get_volume_profile(
    stock_id: int,
    period_days: int = Query(30, description="Number of days to analyze", ge=1, le=3650),  # Allow up to 10 years
    num_bins: int = Query(50, description="Number of price levels", ge=10, le=200),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Volume Profile analysis for a stock
    
    Volume Profile shows volume distribution across price levels:
    - Point of Control (POC): Price with highest volume
    - Value Area (VA): Price range with 70% of volume
    - High/Low Volume Nodes: Support/Resistance levels
    
    Parameters:
    - period_days: Days to analyze (used if start_date not provided)
    - num_bins: Number of price levels (more = finer detail)
    - start_date: Optional start date
    - end_date: Optional end date
    
    Returns:
    {
        "stock_id": 1,
        "ticker_symbol": "AAPL",
        "price_levels": [180.0, 180.3, ...],  # Price bins
        "volumes": [1000000, 1500000, ...],   # Volume per bin
        "poc": 182.50,                        # Point of Control
        "poc_volume": 2500000,                # Volume at POC
        "value_area": {
            "high": 185.00,                   # Value Area High
            "low": 180.00,                    # Value Area Low
            "volume_percent": 70.0
        },
        "hvn_levels": [182.50, 184.00],      # High Volume Nodes
        "lvn_levels": [181.00, 186.00],      # Low Volume Nodes
        "total_volume": 50000000,
        "period": {...},
        "price_range": {...}
    }
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        volume_profile_service = VolumeProfileService(db)
        
        result = volume_profile_service.calculate_volume_profile(
            stock_id=stock_id,
            period_days=period_days,
            num_bins=num_bins,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating volume profile for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate volume profile: {str(e)}"
        )


@router.get("/{stock_id}/volume-profile/summary")
def get_volume_profile_summary(
    stock_id: int,
    period_days: int = Query(30, description="Number of days to analyze", ge=1, le=3650),  # Allow up to 10 years
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get simplified Volume Profile summary
    
    Returns just the key levels:
    - POC (Point of Control)
    - Value Area High/Low
    
    This is faster than full volume profile and useful for quick checks.
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        volume_profile_service = VolumeProfileService(db)
        
        result = volume_profile_service.get_volume_profile_summary(
            stock_id=stock_id,
            period_days=period_days
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating volume profile summary for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate volume profile summary: {str(e)}"
        )
