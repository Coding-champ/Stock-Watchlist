from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Dict
from backend.app import schemas
from backend.app.models import (
    Watchlist as WatchlistModel,
    StockInWatchlist as StockInWatchlistModel,
    Stock as StockModel,
    StockPriceData as StockPriceDataModel,
    ExtendedStockDataCache as ExtendedStockDataCacheModel
)
from backend.app.database import get_db
from backend.app.services.stock_query_service import StockQueryService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("/", response_model=List[schemas.Watchlist])
def get_watchlists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all watchlists"""
    watchlists = db.query(WatchlistModel).offset(skip).limit(limit).all()
    return watchlists


@router.get("/{watchlist_id}", response_model=schemas.WatchlistWithStocks)
def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Get a specific watchlist with all its stocks and latest data"""
    logger.info(f"🔍 GET /watchlists/{watchlist_id} - Using optimized route with eager loading")
    
    watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # OPTIMIZATION: Use eager loading to fetch stocks in one query instead of N+1
    stocks_in_watchlist = db.query(StockInWatchlistModel)\
        .options(joinedload(StockInWatchlistModel.stock))\
        .filter(StockInWatchlistModel.watchlist_id == watchlist_id)\
        .order_by(StockInWatchlistModel.position)\
        .all()
    
    logger.info(f"Found {len(stocks_in_watchlist)} stocks in watchlist {watchlist_id}")
    
    # Extract stock IDs for batch queries
    stock_ids = [entry.stock.id for entry in stocks_in_watchlist]
    
    # OPTIMIZATION: Batch query for latest prices (1 query instead of N)
    latest_prices_query = db.query(StockPriceDataModel)\
        .filter(StockPriceDataModel.stock_id.in_(stock_ids))\
        .order_by(StockPriceDataModel.stock_id, desc(StockPriceDataModel.date))\
        .all()
    
    # Create a dict mapping stock_id to latest price (keep only the first/latest for each stock)
    latest_prices_map: Dict[int, StockPriceDataModel] = {}
    for price in latest_prices_query:
        if price.stock_id not in latest_prices_map:
            latest_prices_map[price.stock_id] = price
    
    # OPTIMIZATION: Batch query for cache entries (1 query instead of N)
    cache_entries_query = db.query(ExtendedStockDataCacheModel)\
        .filter(ExtendedStockDataCacheModel.stock_id.in_(stock_ids))\
        .all()
    
    # Create a dict mapping stock_id to cache entry
    cache_map: Dict[int, ExtendedStockDataCacheModel] = {
        entry.stock_id: entry for entry in cache_entries_query
    }
    
    stocks_with_data = []
    for entry in stocks_in_watchlist:
        stock = entry.stock
        
        # Get latest price from batch-loaded map
        latest_price = latest_prices_map.get(stock.id)
        
        # Get PE ratio from batch-loaded cache map
        pe_ratio = None
        cache_entry = cache_map.get(stock.id)
        if cache_entry and cache_entry.extended_data:
            try:
                financial_ratios = cache_entry.extended_data.get('financial_ratios', {})
                pe_ratio = financial_ratios.get('pe_ratio')
            except Exception as e:
                logger.warning(f"Could not load PE ratio from cache for stock_id={stock.id}: {e}")
        
        # Create latest_data if price data exists
        latest_data = None
        if latest_price:
            latest_data = {
                "id": latest_price.id,
                "stock_id": stock.id,
                "current_price": latest_price.close,
                "pe_ratio": pe_ratio,
                "rsi": None,
                "volatility": None,
                "timestamp": datetime.combine(latest_price.date, datetime.min.time())
            }
        
        # Build stock dict with all required fields
        stock_dict = {
            "id": stock.id,
            "isin": stock.isin,
            "wkn": stock.wkn,
            "ticker_symbol": stock.ticker_symbol,
            "name": stock.name,
            "country": stock.country,
            "industry": stock.industry,
            "sector": stock.sector,
            "business_summary": stock.business_summary,
            "created_at": stock.created_at,
            "updated_at": stock.updated_at,
            "watchlist_id": entry.watchlist_id,
            "position": entry.position,
            "observation_reasons": entry.observation_reasons or [],
            "observation_notes": entry.observation_notes,
            "exchange": entry.exchange,
            "currency": entry.currency,
            "stock_data": [],  # Deprecated field
            "latest_data": latest_data
        }
        
        stocks_with_data.append(schemas.Stock(**stock_dict))
    
    # Return watchlist with stocks
    return schemas.WatchlistWithStocks(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
        stocks=stocks_with_data
    )


@router.post("/", response_model=schemas.Watchlist, status_code=201)
def create_watchlist(watchlist: schemas.WatchlistCreate, db: Session = Depends(get_db)):
    """Create a new watchlist"""
    # Check if watchlist with same name exists
    existing = db.query(WatchlistModel).filter(WatchlistModel.name == watchlist.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Watchlist with this name already exists")
    
    db_watchlist = WatchlistModel(**watchlist.model_dump())
    db.add(db_watchlist)
    db.commit()
    db.refresh(db_watchlist)
    return db_watchlist


@router.put("/{watchlist_id}", response_model=schemas.Watchlist)
def update_watchlist(
    watchlist_id: int,
    watchlist: schemas.WatchlistUpdate,
    db: Session = Depends(get_db)
):
    """Update a watchlist"""
    db_watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == watchlist_id).first()
    if not db_watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    update_data = watchlist.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_watchlist, field, value)
    
    db.commit()
    db.refresh(db_watchlist)
    return db_watchlist


@router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Delete a watchlist"""
    db_watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == watchlist_id).first()
    if not db_watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    db.delete(db_watchlist)
    db.commit()
    return None
