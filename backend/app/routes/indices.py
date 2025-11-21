"""
Indices API Routes
Endpoints for market indices operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date
import logging
import tempfile
import os

from backend.app.database import get_db
from backend.app.services.index_service import IndexService
from backend.app.services.index_constituent_service import IndexConstituentService
from backend.app.services.statistics_service import StatisticsService
from backend.app.services.chart_core import get_chart_with_indicators
from backend.app.models import MarketIndex, IndexConstituent
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.market_breadth_service import MarketBreadthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indices", tags=["indices"])


# ==================== Index Management ====================

@router.get("", response_model=List[Dict[str, Any]])
def get_all_indices(
    region: Optional[str] = Query(None, description="Filter by region (e.g., US, Germany)"),
    index_type: Optional[str] = Query(None, description="Filter by type (e.g., broad_market, sector)"),
    db: Session = Depends(get_db)
):
    """
    Get all market indices with optional filtering
    """
    try:
        service = IndexService(db)
        indices = service.get_all_indices(region=region, index_type=index_type)
        
        # Get latest prices for each index
        result = []
        for index in indices:
            latest_price = service.get_index_latest_price(index.ticker_symbol)
            result.append({
                "id": index.id,
                "ticker_symbol": index.ticker_symbol,
                "name": index.name,
                "region": index.region,
                "index_type": index.index_type,
                "calculation_method": index.calculation_method,
                "benchmark_index": index.benchmark_index,
                "description": index.description,
                "latest_price": latest_price
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=201)
def create_index(
    ticker_symbol: str,
    name: str,
    region: Optional[str] = None,
    index_type: Optional[str] = None,
    calculation_method: Optional[str] = None,
    benchmark_index: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new market index
    """
    try:
        service = IndexService(db)
        index = service.create_index(
            ticker_symbol=ticker_symbol,
            name=name,
            region=region,
            index_type=index_type,
            calculation_method=calculation_method,
            benchmark_index=benchmark_index,
            description=description
        )
        
        return {
            "id": index.id,
            "ticker_symbol": index.ticker_symbol,
            "name": index.name,
            "region": index.region,
            "index_type": index.index_type,
            "calculation_method": index.calculation_method,
            "benchmark_index": index.benchmark_index,
            "description": index.description
        }
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Correlation Matrix ====================

@router.get("/correlation-matrix")
def get_index_correlation_matrix(
    symbols: str = Query(..., description="Comma-separated index ticker symbols (e.g. ^GSPC,^IXIC,^GDAXI)"),
    period: str = Query("1y", description="Period window (1mo,3mo,6mo,1y,2y,5y)"),
    db: Session = Depends(get_db)
):
    """Return correlation matrix for provided indices.

    Uses daily returns over the specified period approximation. Requires at least two symbols and sufficient overlapping data.
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        service = ComparisonService(db)
        result = service.get_correlation_matrix(symbol_list, period=period)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail="Internal error generating correlation matrix")


@router.get("/{ticker_symbol}")
def get_index_details(
    ticker_symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific index
    """
    try:
        service = IndexService(db)
        index = service.get_index_by_symbol(ticker_symbol)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        # Get latest price
        latest_price = service.get_index_latest_price(ticker_symbol)
        
        # Get active constituents count
        constituent_service = IndexConstituentService(db)
        constituents = constituent_service.get_active_constituents(index.id)
        
        return {
            "id": index.id,
            "ticker_symbol": index.ticker_symbol,
            "name": index.name,
            "region": index.region,
            "index_type": index.index_type,
            "calculation_method": index.calculation_method,
            "benchmark_index": index.benchmark_index,
            "description": index.description,
            "latest_price": latest_price,
            "constituent_count": len(constituents)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching index {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{ticker_symbol}")
def update_index(
    ticker_symbol: str,
    name: Optional[str] = None,
    region: Optional[str] = None,
    index_type: Optional[str] = None,
    calculation_method: Optional[str] = None,
    benchmark_index: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update index metadata
    """
    try:
        service = IndexService(db)
        
        # Build update dict
        updates = {}
        if name is not None:
            updates['name'] = name
        if region is not None:
            updates['region'] = region
        if index_type is not None:
            updates['index_type'] = index_type
        if calculation_method is not None:
            updates['calculation_method'] = calculation_method
        if benchmark_index is not None:
            updates['benchmark_index'] = benchmark_index
        if description is not None:
            updates['description'] = description
        
        index = service.update_index(ticker_symbol, **updates)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        return {
            "id": index.id,
            "ticker_symbol": index.ticker_symbol,
            "name": index.name,
            "region": index.region,
            "index_type": index.index_type,
            "calculation_method": index.calculation_method,
            "benchmark_index": index.benchmark_index,
            "description": index.description
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating index {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{ticker_symbol}")
def delete_index(
    ticker_symbol: str,
    db: Session = Depends(get_db)
):
    """
    Delete an index (cascades to constituents and price data)
    """
    try:
        service = IndexService(db)
        success = service.delete_index(ticker_symbol)
        
        if not success:
            raise HTTPException(status_code=404, detail="Index not found")
        
        return {"success": True, "message": f"Index {ticker_symbol} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting index {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Price Data ====================

@router.post("/{ticker_symbol}/load-prices")
def load_index_prices(
    ticker_symbol: str,
    period: str = Query("max", description="Time period (1mo, 3mo, 6mo, 1y, 2y, 5y, max)"),
    interval: str = Query("1d", description="Data interval (1d, 1wk, 1mo)"),
    db: Session = Depends(get_db)
):
    """
    Load historical price data for an index from yfinance
    """
    try:
        service = IndexService(db)
        result = service.load_index_price_data(
            ticker_symbol=ticker_symbol,
            period=period,
            interval=interval
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to load prices"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading prices for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker_symbol}/chart")
def get_index_chart(
    ticker_symbol: str,
    period: str = Query("1y", description="Time period (e.g. 1mo,3mo,6mo,1y,3y,5y,max)"),
    interval: str = Query("1d", description="Data interval (1d,1wk,1mo)"),
    indicators: Optional[str] = Query(
        None,
        description=(
            "Comma-separated indicators. Supported canonical keys: "
            "sma_50,sma_200,rsi,macd,bollinger. Synonyms: sma50,sma200,bb -> bollinger."
        )
    ),
    db: Session = Depends(get_db)
):
    """Return chart OHLCV arrays plus optional technical indicators for an index.

    Indicator key mapping performed so callers may use shorthand:
    - sma50 -> sma_50
    - sma200 -> sma_200
    - bb -> bollinger
    - bollinger -> bollinger (canonical)
    Other values are passed through; unsupported indicators will be ignored upstream.
    """
    try:
        # Parse + normalize indicators
        indicator_list: List[str] = []
        if indicators:
            raw = [ind.strip().lower() for ind in indicators.split(',') if ind.strip()]
            canonical: List[str] = []
            for ind in raw:
                if ind in ("sma50", "sma_50"):
                    mapped = "sma_50"
                elif ind in ("sma200", "sma_200"):
                    mapped = "sma_200"
                elif ind in ("bb", "bollinger"):
                    mapped = "bollinger"
                else:
                    mapped = ind  # pass through unknown; chart_core may ignore
                if mapped not in canonical:
                    canonical.append(mapped)
            indicator_list = canonical

        # Use existing chart_core (works for indices via yfinance)
        chart_data = get_chart_with_indicators(
            ticker_symbol=ticker_symbol,
            period=period,
            interval=interval,
            indicators=indicator_list or None
        )
        
        if not chart_data:
            raise HTTPException(status_code=404, detail="Chart data not available")
        
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chart for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker_symbol}/price-history")
def get_index_price_history(
    ticker_symbol: str,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """
    Get historical price data for an index
    """
    try:
        service = IndexService(db)
        price_history = service.get_index_price_history(
            ticker_symbol=ticker_symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "ticker_symbol": ticker_symbol,
            "count": len(price_history),
            "data": price_history
        }
    except Exception as e:
        logger.error(f"Error fetching price history for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Constituents Management ====================

@router.get("/{ticker_symbol}/constituents")
def get_index_constituents(
    ticker_symbol: str,
    include_removed: bool = Query(False, description="Include removed constituents"),
    db: Session = Depends(get_db)
):
    """
    Get all constituents of an index
    """
    try:
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        constituent_service = IndexConstituentService(db)
        constituents = constituent_service.get_all_constituents(index.id, include_removed)
        
        result = []
        for constituent in constituents:
            result.append({
                "stock_id": constituent.stock_id,
                "ticker_symbol": constituent.stock.ticker_symbol,
                "name": constituent.stock.name,
                "weight": constituent.weight,
                "status": constituent.status,
                "date_added": constituent.date_added.isoformat(),
                "date_removed": constituent.date_removed.isoformat() if constituent.date_removed else None
            })
        
        return {
            "index": ticker_symbol,
            "count": len(result),
            "constituents": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching constituents for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticker_symbol}/constituents/import")
async def import_constituents_from_csv(
    ticker_symbol: str,
    file: UploadFile = File(...),
    replace_existing: bool = Query(False, description="Replace all existing constituents"),
    auto_calculate_weights: bool = Query(True, description="Automatically calculate weights after import"),
    weight_method: str = Query("market_cap", description="Weight calculation method: market_cap or equal"),
    db: Session = Depends(get_db)
):
    """
    Import constituents from CSV file
    Expected columns: ticker_symbol, weight (optional if auto_calculate_weights=True), date_added (optional)
    """
    try:
        # Get index
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Import constituents
            constituent_service = IndexConstituentService(db)
            result = constituent_service.import_constituents_from_csv(
                index_id=index.id,
                csv_file_path=tmp_file_path,
                replace_existing=replace_existing,
                auto_calculate_weights=auto_calculate_weights,
                weight_method=weight_method
            )
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
            
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing constituents for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticker_symbol}/constituents/recalculate-weights")
def recalculate_weights(
    ticker_symbol: str,
    method: str = Query("market_cap", description="Weight calculation method: market_cap or equal"),
    refresh_market_caps: bool = Query(True, description="Refresh market cap data from yfinance"),
    db: Session = Depends(get_db)
):
    """
    Recalculate constituent weights for an index
    
    Methods:
    - market_cap: Weight based on market capitalization (default)
    - equal: Equal weight for all constituents
    """
    try:
        from backend.app.services.index_weight_calculator import IndexWeightCalculator
        
        # Get index
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        # Calculate weights
        calculator = IndexWeightCalculator(db)
        
        if method == "market_cap":
            result = calculator.calculate_market_cap_weights(
                index_id=index.id,
                refresh_market_caps=refresh_market_caps
            )
        elif method == "equal":
            result = calculator.calculate_equal_weights(index_id=index.id)
        else:
            raise HTTPException(status_code=400, detail="Invalid method. Use 'market_cap' or 'equal'")
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Weight calculation failed"))
        
        return {
            "success": True,
            "index": index.name,
            "method": method,
            "updated_count": result.get("updated_count", 0),
            "total_market_cap": result.get("total_market_cap"),
            "weights": result.get("weights", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating weights for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticker_symbol}/constituents/add")
def add_constituent(
    ticker_symbol: str,
    stock_id: int,
    weight: Optional[float] = None,
    date_added: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Add a stock to an index
    """
    try:
        # Get index
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        # Add constituent
        constituent_service = IndexConstituentService(db)
        constituent = constituent_service.add_constituent(
            index_id=index.id,
            stock_id=stock_id,
            weight=weight,
            date_added=date_added
        )
        
        return {
            "success": True,
            "constituent": {
                "stock_id": constituent.stock_id,
                "ticker_symbol": constituent.stock.ticker_symbol,
                "weight": constituent.weight,
                "date_added": constituent.date_added.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding constituent to {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{ticker_symbol}/constituents/{stock_id}")
def remove_constituent(
    ticker_symbol: str,
    stock_id: int,
    date_removed: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Remove a stock from an index
    """
    try:
        # Get index
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        
        # Remove constituent
        constituent_service = IndexConstituentService(db)
        success = constituent_service.remove_constituent(
            index_id=index.id,
            stock_id=stock_id,
            date_removed=date_removed
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Constituent not found")
        
        return {"success": True, "message": "Constituent removed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing constituent from {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Index Statistics ====================

@router.get("/{ticker_symbol}/statistics")
def get_index_statistics(
    ticker_symbol: str,
    risk_free_rate: float = Query(0.04, description="Annual risk-free rate (default 4%)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for an index including:
    - Volatility (annualized)
    - Sharpe ratio
    - Maximum drawdown
    - Returns (YTD, 1Y, 3Y, 5Y, 10Y)
    - Best/worst days
    - Current drawdown from ATH
    """
    try:
        # Verify index exists
        service = IndexService(db)
        index = service.get_index_by_symbol(ticker_symbol)
        if not index:
            raise HTTPException(status_code=404, detail=f"Index {ticker_symbol} not found")
        
        # Calculate statistics
        stats_service = StatisticsService(db)
        stats = stats_service.calculate_index_statistics(
            ticker_symbol=ticker_symbol,
            risk_free_rate=risk_free_rate
        )
        
        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating statistics for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ==================== Top/Flops ====================

@router.get("/{ticker_symbol}/top-flops")
def get_index_top_flops(
    ticker_symbol: str,
    limit: int = Query(5, ge=1, le=20, description="Number of items for top/flops each"),
    db: Session = Depends(get_db)
):
    """Return top and flop movers for the given index using daily percent change."""
    try:
        index_service = IndexService(db)
        result = index_service.get_index_top_flops(ticker_symbol, limit=limit)
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing top/flops for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal error computing top/flops")


@router.get("/{ticker_symbol}/sector-breakdown")
def get_index_sector_breakdown(
    ticker_symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get sector breakdown for an index showing:
    - Number of stocks per sector
    - Total weight per sector
    - Sector distribution
    """
    try:
        # Verify index exists
        service = IndexService(db)
        index = service.get_index_by_symbol(ticker_symbol)
        if not index:
            raise HTTPException(status_code=404, detail=f"Index {ticker_symbol} not found")
        
        # Get constituents with stock details
        constituent_service = IndexConstituentService(db)
        constituents = constituent_service.get_active_constituents(index.id)
        
        # Aggregate by sector
        sector_data = {}
        total_weight = 0
        
        for constituent in constituents:
            stock = constituent.stock
            sector = stock.sector or "Unknown"
            weight = constituent.weight or 0
            
            if sector not in sector_data:
                sector_data[sector] = {
                    "sector": sector,
                    "count": 0,
                    "total_weight": 0,
                    "stocks": []
                }
            
            sector_data[sector]["count"] += 1
            sector_data[sector]["total_weight"] += weight
            sector_data[sector]["stocks"].append({
                "ticker_symbol": stock.ticker_symbol,
                "name": stock.name,
                "weight": weight
            })
            total_weight += weight
        
        # Calculate percentages and sort
        sectors = []
        for sector_info in sector_data.values():
            percentage = (sector_info["total_weight"] / total_weight * 100) if total_weight > 0 else 0
            sectors.append({
                "sector": sector_info["sector"],
                "count": sector_info["count"],
                "weight": round(sector_info["total_weight"], 2),
                "percentage": round(percentage, 2),
                "top_stocks": sorted(sector_info["stocks"], key=lambda x: x["weight"], reverse=True)[:5]
            })
        
        # Sort by weight descending
        sectors.sort(key=lambda x: x["weight"], reverse=True)
        
        return {
            "ticker_symbol": ticker_symbol,
            "total_constituents": len(constituents),
            "total_weight": round(total_weight, 2),
            "sectors": sectors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating sector breakdown for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Market Breadth ====================

@router.get("/{ticker_symbol}/breadth")
def get_index_breadth(
    ticker_symbol: str,
    date_param: Optional[str] = Query(None, description="Date (YYYY-MM-DD) for point-in-time breadth; defaults to today"),
    db: Session = Depends(get_db)
):
    """Return advance/decline and new highs/lows snapshot for an index."""
    try:
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        target_date = None
        if date_param:
            from datetime import datetime as _dt
            try:
                target_date = _dt.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format; expected YYYY-MM-DD")
        service = MarketBreadthService(db)
        adv_dec = service.calculate_advance_decline(index.id, target_date)
        highs_lows = service.get_new_highs_lows(index.id, target_date)
        return {
            "index": ticker_symbol,
            "advance_decline": adv_dec,
            "new_highs_lows": highs_lows
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating breadth for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal error calculating breadth")


@router.get("/{ticker_symbol}/breadth/history")
def get_index_breadth_history(
    ticker_symbol: str,
    days: int = Query(30, description="Number of days for breadth history (max 90)"),
    include_mcclellan: bool = Query(False, description="Include McClellan oscillator data"),
    db: Session = Depends(get_db)
):
    """Return historical breadth (advancing vs declining) counts for the index."""
    try:
        index_service = IndexService(db)
        index = index_service.get_index_by_symbol(ticker_symbol)
        if not index:
            raise HTTPException(status_code=404, detail="Index not found")
        service = MarketBreadthService(db)
        history = service.calculate_advance_decline_history(index.id, days=days)
        if history.get("error"):
            raise HTTPException(status_code=400, detail=history["error"])
        if include_mcclellan:
            osc = service.calculate_mcclellan_oscillator(index.id, days=min(days, 90))
            if "mcclellan" in osc:
                history["mcclellan_oscillator"] = osc["mcclellan"]
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating breadth history for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal error calculating breadth history")

