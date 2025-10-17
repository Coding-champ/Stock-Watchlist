from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from threading import Lock
import logging
import pandas as pd
from backend.app.services.yfinance_service import get_historical_prices
from backend.app.services.seasonality_service import get_all_seasonalities
from backend.app.services.analyst_service import get_complete_analyst_overview
from backend.app import schemas
from backend.app.models import (
    Stock as StockModel,
    StockInWatchlist as StockInWatchlistModel,
    StockPriceData as StockPriceDataModel,
    StockFundamentalData as StockFundamentalDataModel,
    Watchlist as WatchlistModel,
    ExtendedStockDataCache as ExtendedStockDataCacheModel,
)
from backend.app.database import get_db, SessionLocal
from backend.app.services.yfinance_service import (
    get_stock_info, get_current_stock_data, get_fast_market_data, get_extended_stock_data,
    get_stock_dividends_and_splits, get_stock_calendar_and_earnings,
    get_analyst_data, get_institutional_holders,
    get_stock_info_by_identifier, get_ticker_from_isin,
    calculate_technical_indicators
)
from backend.app.services.cache_service import StockDataCacheService
from backend.app.services.stock_service import StockService
from backend.app.services.historical_price_service import HistoricalPriceService
from backend.app.services.fundamental_data_service import FundamentalDataService
from backend.app.services.stock_query_service import StockQueryService

router = APIRouter(prefix="/stocks", tags=["stocks"])

# Analysten-Endpunkt mit Fehlerbehandlung
@router.get("/{stock_id}/analyst-ratings")
def get_stock_analyst_ratings(stock_id: int, db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger("analyst_debug")
    try:
        stock = get_stock(stock_id=stock_id, db=db)
        if not stock:
            logger.error(f"Stock not found for id {stock_id}")
            return {"error": "Stock not found", "price_targets": {}, "recommendations": {}}
        ticker_symbol = stock.ticker_symbol
        logger.info(f"Fetching analyst data for ticker: {ticker_symbol}")
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        recommendations = ticker.recommendations
        analyst_price_targets = getattr(ticker, 'analyst_price_targets', None)
        logger.info(f"yfinance.info: {info}")
        logger.info(f"yfinance.recommendations: {recommendations}")
        logger.info(f"yfinance.analyst_price_targets: {analyst_price_targets}")
        overview = get_complete_analyst_overview(ticker_symbol)
        logger.info(f"Overview returned: {overview}")
        return overview
    except Exception as e:
        import traceback
        logger.error(f"Exception in analyst endpoint: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "trace": traceback.format_exc(), "price_targets": {}, "recommendations": {}}


# Saisonalität-Endpunkt mit Fehlerbehandlung
@router.get("/{stock_id}/seasonality")
def get_stock_seasonality(stock_id: int, years_back: int = None, include_series: bool = Query(False), db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger("seasonality_debug")
    try:
        # Get ticker_symbol from stock_id
        stock = StockQueryService(db).get_stock_id_or_404(stock_id)
        ticker_symbol = stock.ticker_symbol
        logger.info(f"Resolved ticker_symbol for stock_id {stock_id}: {ticker_symbol}")
        prices_df = get_historical_prices(ticker_symbol, period="max")
        logger.info(f"Historical prices for ticker {ticker_symbol}: {prices_df}")
        if prices_df is None or prices_df.empty:
            logger.warning(f"No historical prices found for ticker {ticker_symbol}")
            return []
        df = prices_df
        logger.info(f"DataFrame head: {df.head()}")
        seasonality = get_all_seasonalities(df)
        logger.info(f"Seasonality result keys: {list(seasonality.keys())}")
        if years_back:
            key = f"{years_back}y"
            result_df = seasonality.get(key, seasonality['all'])
            logger.info(f"Seasonality for {key}: {result_df}")
        else:
            result_df = seasonality['all']
            logger.info(f"Seasonality for all: {result_df}")

        # If requested, build per-year monthly closes series (up to 10 years)
        if include_series:
            try:
                # monthly_prices: last close per month (month-end)
                monthly_prices = prices_df['Close'].resample('M').last()
                # Determine available years (descending recent first)
                available_years = sorted(set(monthly_prices.index.year), reverse=True)
                # Decide how many years to include: prefer years_back if provided, else up to 10
                max_years = min(10, int(years_back) if years_back else 10)
                years_to_use = available_years[:max_years]

                series_list = []
                # We'll compute per-month OHLC for each year (open, high, low, close)
                # Resample to monthly OHLC from the full prices DataFrame
                monthly_ohlc = prices_df.resample('M').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
                for y in years_to_use:
                    monthly_data = []
                    monthly_closes = []
                    for m in range(1, 13):
                        matches = monthly_ohlc[(monthly_ohlc.index.year == y) & (monthly_ohlc.index.month == m)]
                        if not matches.empty:
                            row = matches.iloc[-1]
                            o = None if pd.isna(row['Open']) else float(row['Open'])
                            h = None if pd.isna(row['High']) else float(row['High'])
                            l = None if pd.isna(row['Low']) else float(row['Low'])
                            c = None if pd.isna(row['Close']) else float(row['Close'])
                            monthly_data.append({"open": o, "high": h, "low": l, "close": c})
                            monthly_closes.append(c)
                        else:
                            monthly_data.append({"open": None, "high": None, "low": None, "close": None})
                            monthly_closes.append(None)
                    series_list.append({"year": int(y), "monthly_ohlc": monthly_data, "monthly_closes": monthly_closes})
                # Additionally, provide daily OHLC for the current year for detailed charts
                try:
                    current_year = datetime.now().year
                    daily = prices_df[(prices_df.index.year == current_year)][['Open', 'High', 'Low', 'Close']]
                    daily_list = []
                    if not daily.empty:
                        for idx, row in daily.iterrows():
                            daily_list.append({
                                'date': str(idx.date()),
                                'open': None if pd.isna(row['Open']) else float(row['Open']),
                                'high': None if pd.isna(row['High']) else float(row['High']),
                                'low': None if pd.isna(row['Low']) else float(row['Low']),
                                'close': None if pd.isna(row['Close']) else float(row['Close'])
                            })
                    else:
                        daily_list = []
                except Exception as e:
                    logger.warning(f"Failed to build daily series for current year: {e}")
                    daily_list = []
            except Exception as e:
                logger.warning(f"Failed to build series for seasonality: {e}")
                series_list = []

            return {"seasonality": result_df.to_dict(orient="records"), "series": series_list, "current_year_daily_ohlc": daily_list}

        return result_df.to_dict(orient="records")
    except Exception as e:
        import traceback
        logger.error(f"Exception in seasonality endpoint: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "trace": traceback.format_exc(), "data": []}

logger = logging.getLogger(__name__)

ALLOWED_OBSERVATION_REASONS = {
    "chart_technical",
    "fundamentals",
    "industry",
    "economics",
}


INDICATOR_REFRESH_DEBOUNCE = timedelta(minutes=1)
INDICATOR_REFRESH_SUCCESS_INTERVAL = timedelta(hours=6)
INDICATOR_REFRESH_FAILURE_INTERVAL = timedelta(minutes=30)

_indicator_refresh_tracker: Dict[int, datetime] = {}
_indicator_refresh_lock = Lock()


def _mark_refresh_window(stock_id: int, window: timedelta) -> None:
    with _indicator_refresh_lock:
        _indicator_refresh_tracker[stock_id] = datetime.utcnow() + window


def _can_schedule_indicator_refresh(stock_id: int) -> bool:
    now = datetime.utcnow()
    with _indicator_refresh_lock:
        next_allowed = _indicator_refresh_tracker.get(stock_id)
        if next_allowed and next_allowed > now:
            return False
        _indicator_refresh_tracker[stock_id] = now + INDICATOR_REFRESH_DEBOUNCE
        return True


def _mark_refresh_success(stock_id: int) -> None:
    _mark_refresh_window(stock_id, INDICATOR_REFRESH_SUCCESS_INTERVAL)


def _mark_refresh_failure(stock_id: int) -> None:
    _mark_refresh_window(stock_id, INDICATOR_REFRESH_FAILURE_INTERVAL)


def _get_latest_stock_data(db: Session, stock_id: int) -> Optional[schemas.StockData]:
    """
    Get the latest price and fundamental data for a stock
    
    Returns a StockData schema object compatible with the frontend
    """
    logger.debug(f"Getting latest data for stock_id={stock_id}")
    
    # Get latest price data
    latest_price = db.query(StockPriceDataModel).filter(
        StockPriceDataModel.stock_id == stock_id
    ).order_by(desc(StockPriceDataModel.date)).first()
    
    if not latest_price:
        logger.warning(f"No price data found for stock_id={stock_id}")
        return None
    
    logger.debug(f"Found price data: date={latest_price.date}, close={latest_price.close}")
    
    # Get PE ratio from extended data cache (if available)
    pe_ratio = None
    try:
        cache_entry = db.query(ExtendedStockDataCacheModel).filter(
            ExtendedStockDataCacheModel.stock_id == stock_id
        ).first()
        
        if cache_entry and cache_entry.extended_data:
            financial_ratios = cache_entry.extended_data.get('financial_ratios', {})
            pe_ratio = financial_ratios.get('pe_ratio')
            logger.debug(f"Found PE ratio from cache: {pe_ratio}")
    except Exception as e:
        logger.warning(f"Could not load PE ratio from cache for stock_id={stock_id}: {e}")
    
    # Create StockData schema object
    result = schemas.StockData(
        id=latest_price.id,
        stock_id=stock_id,
        current_price=latest_price.close,
        pe_ratio=pe_ratio,
        rsi=None,  # Will be calculated on demand
        volatility=None,  # Will be calculated on demand
        timestamp=datetime.combine(latest_price.date, datetime.min.time())
    )
    
    logger.debug(f"Created StockData object: current_price={result.current_price}")
    return result



def _normalize_observation_reasons(reasons: Optional[List[str]]) -> List[str]:
    if not reasons:
        return []

    normalized: List[str] = []
    for raw_reason in reasons:
        if raw_reason is None:
            continue
        reason = raw_reason.strip()
        if not reason:
            continue
        if reason not in ALLOWED_OBSERVATION_REASONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid observation reason '{raw_reason}'.",
            )
        if reason not in normalized:
            normalized.append(reason)
    return normalized


def _normalize_observation_notes(note: Optional[str]) -> Optional[str]:
    if note is None:
        return None
    trimmed = note.strip()
    return trimmed or None


@router.get("/", response_model=List[schemas.Stock])
def get_stocks(
    watchlist_id: Optional[int] = None,
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    skip: int = 0,
    limit: int = 100,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Get stocks with optional filtering and sorting"""
    
    if watchlist_id:
        # Use new StockService for watchlist-specific queries
        stock_service = StockService(db)
        stocks_data = stock_service.get_stocks_in_watchlist(watchlist_id)
        
        # Convert to Stock objects for response
        stocks = []
        for stock_dict in stocks_data:
            stock = StockModel(**{k: v for k, v in stock_dict.items() if k not in ['watchlist_id', 'position', 'observation_reasons', 'observation_notes', 'exchange', 'currency']})
            # Attach watchlist context for API compatibility
            stock.watchlist_id = stock_dict.get('watchlist_id')
            stock.position = stock_dict.get('position')
            stock.observation_reasons = stock_dict.get('observation_reasons', [])
            stock.observation_notes = stock_dict.get('observation_notes')
            stock.exchange = stock_dict.get('exchange')
            stock.currency = stock_dict.get('currency')
            
            # Get latest stock data from new price_data table
            latest_data = _get_latest_stock_data(db, stock.id)
                
            stock.latest_data = latest_data
            stocks.append(stock)
        
        return stocks[skip:skip+limit]
    else:
        # Get all stocks (no watchlist filter)
        query = db.query(StockModel)
        
        # Apply sorting
        if sort_by:
            order_func = desc if sort_order.lower() == "desc" else asc
            if hasattr(StockModel, sort_by):
                query = query.order_by(order_func(getattr(StockModel, sort_by)))
        
        stocks = query.offset(skip).limit(limit).all()
        
        # Attach latest stock data to each stock
        for stock in stocks:
            latest_data = _get_latest_stock_data(db, stock.id)

            stock.latest_data = latest_data
        
        return stocks


@router.get("/{stock_id}", response_model=schemas.Stock)
def get_stock(
        stock_id: int,
        watchlist_id: Optional[int] = None,
        background_tasks: BackgroundTasks = None,
        db: Session = Depends(get_db)
    ):
    """Get a specific stock with its latest data"""
    stock = StockQueryService(db).get_stock_id_or_404(stock_id)
    
    # If watchlist_id provided, get watchlist context
    if watchlist_id:
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.watchlist_id == watchlist_id,
            StockInWatchlistModel.stock_id == stock_id
        ).first()
        
        if watchlist_entry:
            stock.watchlist_id = watchlist_entry.watchlist_id
            stock.position = watchlist_entry.position
            stock.observation_reasons = watchlist_entry.observation_reasons
            stock.observation_notes = watchlist_entry.observation_notes
            stock.exchange = watchlist_entry.exchange
            stock.currency = watchlist_entry.currency
    
    # Get latest stock data from new price_data table
    latest_data = _get_latest_stock_data(db, stock_id)
    
    stock.latest_data = latest_data
    
    return stock


@router.post("/", response_model=schemas.Stock, status_code=201)
def create_stock(
    stock: schemas.StockCreate, 
    load_historical: bool = Query(True, description="Load historical price data"),
    load_fundamentals: bool = Query(True, description="Load fundamental data"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Add a stock to a watchlist
    Automatically loads historical price data and fundamental data
    """
    ticker_symbol = stock.ticker_symbol.strip().upper()
    observation_reasons = _normalize_observation_reasons(stock.observation_reasons)
    observation_notes = _normalize_observation_notes(stock.observation_notes)

    if not ticker_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    # Use new StockService
    stock_service = StockService(db)
    
    result = stock_service.create_stock_with_watchlist(
        ticker_symbol=ticker_symbol,
        watchlist_id=stock.watchlist_id,
        observation_reasons=observation_reasons,
        observation_notes=observation_notes,
        exchange=stock.exchange if hasattr(stock, 'exchange') else None,
        currency=stock.currency if hasattr(stock, 'currency') else None,
        load_historical=load_historical,
        load_fundamentals=load_fundamentals
    )
    
    if not result.get("success"):
        error_msg = result.get("error", "Unknown error")
        if "already in" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        elif "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    # Get the created stock with watchlist context
    created_stock = result["stock"]
    watchlist_entry = result["entry"]
    
    # Attach watchlist context for API compatibility
    created_stock.watchlist_id = watchlist_entry.watchlist_id
    created_stock.position = watchlist_entry.position
    created_stock.observation_reasons = watchlist_entry.observation_reasons
    created_stock.observation_notes = watchlist_entry.observation_notes
    created_stock.exchange = watchlist_entry.exchange
    created_stock.currency = watchlist_entry.currency
    
    # Get latest stock data from new tables
    created_stock.latest_data = _get_latest_stock_data(db, created_stock.id)
    
    return created_stock


@router.put("/{stock_id}", response_model=schemas.Stock)
def update_stock(
    stock_id: int,
    stock: schemas.StockUpdate,
    watchlist_id: Optional[int] = Query(None, description="Watchlist context for observation data"),
    db: Session = Depends(get_db)
):
    """
    Update a stock's master data and/or watchlist-specific data
    """
    stock_service = StockService(db)
    
    update_data = stock.model_dump(exclude_unset=True)
    
    # Separate master data from watchlist-specific data
    master_data = {}
    watchlist_data = {}
    
    master_fields = ['name', 'isin', 'wkn', 'country', 'industry', 'sector', 'business_summary']
    watchlist_fields = ['observation_reasons', 'observation_notes', 'exchange', 'currency', 'position']
    
    for field, value in update_data.items():
        if field in master_fields:
            master_data[field] = value
        elif field in watchlist_fields:
            if field == "observation_reasons":
                watchlist_data[field] = _normalize_observation_reasons(value)
            elif field == "observation_notes":
                watchlist_data[field] = _normalize_observation_notes(value)
            else:
                watchlist_data[field] = value
    
    # Update master data if provided
    if master_data:
        updated_stock = stock_service.update_stock_master_data(stock_id, master_data)
        if not updated_stock:
            raise HTTPException(status_code=404, detail="Stock not found")
    
    # Update watchlist-specific data if provided and watchlist_id given
    if watchlist_data and watchlist_id:
        updated_entry = stock_service.update_watchlist_entry(watchlist_id, stock_id, watchlist_data)
        if not updated_entry:
            raise HTTPException(status_code=404, detail="Stock not in this watchlist")
    
    # Return updated stock with watchlist context
    db_stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    
    if watchlist_id:
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.watchlist_id == watchlist_id,
            StockInWatchlistModel.stock_id == stock_id
        ).first()
        
        if watchlist_entry:
            db_stock.watchlist_id = watchlist_entry.watchlist_id
            db_stock.position = watchlist_entry.position
            db_stock.observation_reasons = watchlist_entry.observation_reasons
            db_stock.observation_notes = watchlist_entry.observation_notes
            db_stock.exchange = watchlist_entry.exchange
            db_stock.currency = watchlist_entry.currency
    
    return db_stock


@router.put("/{stock_id}/move", response_model=schemas.Stock)
def move_stock(
    stock_id: int,
    move_data: schemas.StockMove,
    source_watchlist_id: int = Query(..., description="Source watchlist ID"),
    db: Session = Depends(get_db)
):
    """Move a stock to another watchlist"""
    stock_service = StockService(db)
    
    # Check if target is same as source
    if source_watchlist_id == move_data.target_watchlist_id:
        raise HTTPException(status_code=400, detail="Aktie befindet sich bereits in dieser Watchlist.")
    
    # Try to copy to target watchlist
    new_entry = stock_service.copy_stock_to_watchlist(
        source_watchlist_id=source_watchlist_id,
        stock_id=stock_id,
        target_watchlist_id=move_data.target_watchlist_id,
        position=move_data.position
    )
    
    if not new_entry:
        raise HTTPException(status_code=404, detail="Stock or watchlist not found")
    
    # Remove from source watchlist
    removed = stock_service.remove_stock_from_watchlist(source_watchlist_id, stock_id)
    if not removed:
        # Rollback the copy
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove from source watchlist")
    
    # Return stock with new watchlist context
    db_stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    db_stock.watchlist_id = new_entry.watchlist_id
    db_stock.position = new_entry.position
    db_stock.observation_reasons = new_entry.observation_reasons
    db_stock.observation_notes = new_entry.observation_notes
    db_stock.exchange = new_entry.exchange
    db_stock.currency = new_entry.currency
    
    return db_stock


@router.post("/{stock_id}/copy", response_model=schemas.Stock, status_code=201)
def copy_stock(
    stock_id: int,
    copy_data: schemas.StockCopy,
    source_watchlist_id: int = Query(..., description="Source watchlist ID"),
    db: Session = Depends(get_db)
):
    """Copy a stock to another watchlist"""
    stock_service = StockService(db)
    
    # Check if target is same as source
    if source_watchlist_id == copy_data.target_watchlist_id:
        raise HTTPException(status_code=400, detail="Aktie befindet sich bereits in dieser Watchlist.")
    
    # Copy to target watchlist
    new_entry = stock_service.copy_stock_to_watchlist(
        source_watchlist_id=source_watchlist_id,
        stock_id=stock_id,
        target_watchlist_id=copy_data.target_watchlist_id,
        position=copy_data.position
    )
    
    if not new_entry:
        raise HTTPException(status_code=409, detail="Aktie ist schon in der Ziel-Watchlist vorhanden!")
    
    # Return stock with new watchlist context
    db_stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    db_stock.watchlist_id = new_entry.watchlist_id
    db_stock.position = new_entry.position
    db_stock.observation_reasons = new_entry.observation_reasons
    db_stock.observation_notes = new_entry.observation_notes
    db_stock.exchange = new_entry.exchange
    db_stock.currency = new_entry.currency
    
    return db_stock

    original_cache = db.query(ExtendedStockDataCacheModel).filter(
        ExtendedStockDataCacheModel.stock_id == stock_id
    ).first()

    if original_cache:
        db.add(ExtendedStockDataCacheModel(
            stock_id=new_stock.id,
            extended_data=original_cache.extended_data,
            dividends_splits_data=original_cache.dividends_splits_data,
            calendar_data=original_cache.calendar_data,
            analyst_data=original_cache.analyst_data,
            holders_data=original_cache.holders_data,
            cache_type=original_cache.cache_type,
            last_updated=original_cache.last_updated,
            expires_at=original_cache.expires_at,
            fetch_success=original_cache.fetch_success,
            error_message=original_cache.error_message
        ))

    db.commit()
    db.refresh(new_stock)
    return new_stock


@router.delete("/{stock_id}", status_code=204)
def delete_stock(
    stock_id: int, 
    watchlist_id: Optional[int] = Query(None, description="If provided, only remove from this watchlist"),
    delete_completely: bool = Query(False, description="Delete stock completely from database"),
    db: Session = Depends(get_db)
):
    """
    Delete a stock from a watchlist or completely from the database
    
    - If watchlist_id provided: Remove from that specific watchlist
    - If delete_completely=true: Delete stock master data (removes from all watchlists)
    """
    stock_service = StockService(db)
    
    if delete_completely:
        # Delete stock completely (all watchlists and all data)
        success = stock_service.delete_stock_completely(stock_id)
        if not success:
            raise HTTPException(status_code=404, detail="Stock not found")
    elif watchlist_id:
        # Remove from specific watchlist
        success = stock_service.remove_stock_from_watchlist(watchlist_id, stock_id)
        if not success:
            raise HTTPException(status_code=404, detail="Stock not in this watchlist")
    else:
        raise HTTPException(
            status_code=400, 
            detail="Must provide either watchlist_id or set delete_completely=true"
        )
    
    return None


@router.post("/add-by-ticker", response_model=schemas.Stock, status_code=201)
def add_stock_by_ticker(
    stock_data: schemas.StockCreateByTicker, 
    load_historical: bool = Query(True, description="Load historical data"),
    load_fundamentals: bool = Query(True, description="Load fundamental data"),
    db: Session = Depends(get_db)
):
    """
    Add a stock to a watchlist by ticker symbol only
    The rest of the information is fetched from yfinance
    """
    # Check if watchlist exists
    watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == stock_data.watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    ticker_symbol = stock_data.ticker_symbol.strip().upper()
    observation_reasons = _normalize_observation_reasons(stock_data.observation_reasons)
    observation_notes = _normalize_observation_notes(stock_data.observation_notes)

    if not ticker_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")
    
    # Use new StockService
    stock_service = StockService(db)
    
    result = stock_service.create_stock_with_watchlist(
        ticker_symbol=ticker_symbol,
        watchlist_id=stock_data.watchlist_id,
        observation_reasons=observation_reasons,
        observation_notes=observation_notes,
        load_historical=load_historical,
        load_fundamentals=load_fundamentals
    )
    
    if not result.get("success"):
        error_msg = result.get("error", "Unknown error")
        if "already in" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        elif "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    # Get the created stock with watchlist context
    created_stock = result["stock"]
    watchlist_entry = result["entry"]
    
    # Attach watchlist context for API compatibility
    created_stock.watchlist_id = watchlist_entry.watchlist_id
    created_stock.position = watchlist_entry.position
    created_stock.observation_reasons = watchlist_entry.observation_reasons
    created_stock.observation_notes = watchlist_entry.observation_notes
    created_stock.exchange = watchlist_entry.exchange
    created_stock.currency = watchlist_entry.currency
    
    # Get latest stock data from new tables
    created_stock.latest_data = _get_latest_stock_data(db, created_stock.id)
    
    return created_stock


@router.post("/bulk-add", response_model=schemas.BulkStockAddResponse, status_code=status.HTTP_200_OK)
def bulk_add_stocks(
    payload: schemas.BulkStockAddRequest, 
    load_historical: bool = Query(False, description="Load historical data for each stock"),
    load_fundamentals: bool = Query(False, description="Load fundamental data for each stock"),
    db: Session = Depends(get_db)
):
    """Add multiple stocks to a watchlist by ticker symbols or ISINs."""
    identifiers = payload.identifiers or []
    if len(identifiers) == 0:
        raise HTTPException(status_code=400, detail="No identifiers provided")

    watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == payload.watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Use new StockService
    stock_service = StockService(db)
    
    # Get existing stocks in watchlist
    existing_entries = stock_service.get_stocks_in_watchlist(payload.watchlist_id)
    existing_tickers = {stock.ticker_symbol.upper() for stock in existing_entries}
    existing_isins = {stock.isin.upper() for stock in existing_entries if stock.isin}

    batch_tickers = set()
    batch_isins = set()
    results: List[Dict[str, Any]] = []

    for raw_identifier in identifiers:
        identifier = (raw_identifier or "").strip()
        normalized_identifier = identifier.upper()
        if not normalized_identifier:
            results.append({
                "identifier": identifier,
                "resolved_ticker": None,
                "status": "invalid",
                "message": "Identifier is empty",
                "stock": None
            })
            continue

        try:
            stock_info = None
            resolved_ticker = None

            # Resolve identifier to ticker symbol
            if payload.identifier_type == "ticker":
                resolved_ticker = normalized_identifier
                stock_info = get_stock_info(resolved_ticker)
            elif payload.identifier_type == "isin":
                resolved_ticker = get_ticker_from_isin(normalized_identifier)
                if resolved_ticker:
                    stock_info = get_stock_info(resolved_ticker)
            else:  # auto-detect
                stock_info = get_stock_info_by_identifier(normalized_identifier)
                if stock_info:
                    resolved_ticker = stock_info.ticker
                else:
                    # Fallback: if it looks like an ISIN try to resolve manually
                    if len(normalized_identifier) == 12 and normalized_identifier[:2].isalpha():
                        resolved_ticker = get_ticker_from_isin(normalized_identifier)
                        if resolved_ticker:
                            stock_info = get_stock_info(resolved_ticker)

            if not stock_info or not resolved_ticker:
                results.append({
                    "identifier": identifier,
                    "resolved_ticker": resolved_ticker,
                    "status": "not_found",
                    "message": "No stock information found",
                    "stock": None
                })
                continue

            resolved_ticker_upper = resolved_ticker.upper()
            candidate_isin_upper = None
            if stock_info.isin:
                candidate_isin_upper = stock_info.isin.upper()
            elif len(normalized_identifier) == 12 and normalized_identifier[:2].isalpha():
                candidate_isin_upper = normalized_identifier

            # Check for duplicates
            if resolved_ticker_upper in existing_tickers or resolved_ticker_upper in batch_tickers or (
                candidate_isin_upper and (
                    candidate_isin_upper in existing_isins or candidate_isin_upper in batch_isins
                )
            ):
                results.append({
                    "identifier": identifier,
                    "resolved_ticker": resolved_ticker_upper,
                    "status": "exists",
                    "message": "Stock already exists in this watchlist",
                    "stock": None
                })
                continue

            # Create stock using StockService
            result = stock_service.create_stock_with_watchlist(
                ticker_symbol=resolved_ticker_upper,
                watchlist_id=payload.watchlist_id,
                observation_reasons=[],
                observation_notes=None,
                load_historical=load_historical,
                load_fundamentals=load_fundamentals
            )

            if not result.get("success"):
                error_msg = result.get("error", "Unknown error")
                results.append({
                    "identifier": identifier,
                    "resolved_ticker": resolved_ticker_upper,
                    "status": "error",
                    "message": f"Failed to create stock: {error_msg}",
                    "stock": None
                })
                continue

            # Success - get created stock
            created_stock = result["stock"]
            watchlist_entry = result["entry"]
            
            # Attach watchlist context for API compatibility
            created_stock.watchlist_id = watchlist_entry.watchlist_id
            created_stock.position = watchlist_entry.position
            created_stock.observation_reasons = watchlist_entry.observation_reasons
            created_stock.observation_notes = watchlist_entry.observation_notes
            created_stock.exchange = watchlist_entry.exchange
            created_stock.currency = watchlist_entry.currency
            
            # Get latest stock data
            created_stock.latest_data = _get_latest_stock_data(db, created_stock.id)
            # Track added stocks
            batch_tickers.add(resolved_ticker_upper)
            existing_tickers.add(resolved_ticker_upper)
            if candidate_isin_upper:
                batch_isins.add(candidate_isin_upper)
                existing_isins.add(candidate_isin_upper)

            results.append({
                "identifier": identifier,
                "resolved_ticker": resolved_ticker_upper,
                "status": "created",
                "message": "Stock added successfully",
                "stock": created_stock
            })

        except Exception as exc:
            logger.error(f"Unexpected error while processing identifier {identifier}: {exc}")
            results.append({
                "identifier": identifier,
                "resolved_ticker": None,
                "status": "error",
                "message": "Unexpected error during processing",
                "stock": None
            })

    created_count = sum(1 for result in results if result["status"] == "created")
    failed_count = len(results) - created_count

    return {
        "watchlist_id": payload.watchlist_id,
        "results": results,
        "created_count": created_count,
        "failed_count": failed_count
    }


@router.get("/search/{query}")
def search_stocks(query: str) -> Dict[str, Any]:
    """
    Suche nach Aktien anhand eines Ticker-Symbols oder Namens
    """
    stock_info = get_stock_info(query.upper())
    if stock_info:
        return {
            "found": True,
            "stock": {
                "ticker": stock_info.ticker,
                "name": stock_info.name,
                "sector": stock_info.sector,
                "industry": stock_info.industry,
                "country": stock_info.country,
                "current_price": stock_info.current_price,
                "pe_ratio": stock_info.pe_ratio,
                "isin": stock_info.isin
            }
        }
    else:
        return {"found": False, "message": f"No stock found for '{query}'"}


@router.get("/{stock_id}/fast-data")
def get_stock_fast_data(
    stock_id: int,
    db: Session = Depends(get_db)
):
    """
    Get fast stock data using fast_info (optimized for speed)
    Returns basic price, volume, and market data without detailed financials
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get fast data directly (no caching needed for basic price data)
    from backend.app.services.yfinance_service import get_fast_stock_data
    fast_data = get_fast_stock_data(stock.ticker_symbol)
    
    if not fast_data:
        raise HTTPException(
            status_code=400, 
            detail="Could not fetch fast data for this stock"
        )
    
    return fast_data


@router.get("/{stock_id}/extended-data", response_model=schemas.ExtendedStockData)
def get_stock_extended_data(
    stock_id: int, 
    force_refresh: bool = Query(False, description="Force refresh cache"),
    db: Session = Depends(get_db)
):
    """
    Get extended stock data including financial ratios, cashflow, dividends, and risk metrics
    Uses intelligent caching to improve performance
    Optimized: Uses fast_info for basic data, info only for detailed financials
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Use cache service to get data
    cache_service = StockDataCacheService(db)
    cached_data, cache_hit = cache_service.get_cached_extended_data(stock_id, force_refresh)
    
    if not cached_data or not cached_data.get('extended_data'):
        raise HTTPException(
            status_code=400, 
            detail="Could not fetch extended data for this stock"
        )
    
    extended_data = cached_data['extended_data']
    
    return schemas.ExtendedStockData(
        business_summary=extended_data.get('business_summary'),
        financial_ratios=schemas.FinancialRatios(**extended_data.get('financial_ratios', {})),
        cashflow_data=schemas.CashflowData(**extended_data.get('cashflow_data', {})),
        dividend_info=schemas.DividendInfo(**extended_data.get('dividend_info', {})),
        price_data=schemas.PriceData(**extended_data.get('price_data', {})),
        volume_data=schemas.VolumeData(**extended_data.get('volume_data', {})),
        risk_metrics=schemas.RiskMetrics(**extended_data.get('risk_metrics', {}))
    )


@router.get("/{stock_id}/detailed", response_model=schemas.StockWithExtendedData)
def get_stock_detailed(
    stock_id: int, 
    watchlist_id: Optional[int] = Query(None, description="Optional watchlist context"),
    force_refresh: bool = Query(False, description="Force refresh cache"),
    db: Session = Depends(get_db)
):
    """
    Get stock with all extended data for the overview page
    Uses intelligent caching for improved performance
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get watchlist context from StockInWatchlist table
    watchlist_entry = None
    if watchlist_id:
        # Use provided watchlist_id
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.watchlist_id == watchlist_id,
            StockInWatchlistModel.stock_id == stock_id
        ).first()
    else:
        # Fallback: use first watchlist where stock is present
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.stock_id == stock_id
        ).first()
    
    # Set watchlist context attributes on stock object for compatibility
    if watchlist_entry:
        stock.watchlist_id = watchlist_entry.watchlist_id
        stock.position = watchlist_entry.position
        stock.observation_reasons = watchlist_entry.observation_reasons or []
        stock.observation_notes = watchlist_entry.observation_notes
        stock.exchange = watchlist_entry.exchange
        stock.currency = watchlist_entry.currency
    else:
        # Stock exists but not in any watchlist (shouldn't happen normally)
        stock.watchlist_id = None
        stock.position = None
        stock.observation_reasons = []
        stock.observation_notes = None
        stock.exchange = None
        stock.currency = None
    
    # Attach latest stock data
    # Latest data loaded via _get_latest_stock_data in get_stocks route
    # Use intelligent cache service for performance optimization
    try:
        cache_service = StockDataCacheService(db)
        cached_data, cache_hit = cache_service.get_cached_extended_data(stock_id, force_refresh)
        extended_data = cached_data.get('extended_data') if cached_data else None
        
        if not extended_data:
            # Fallback to direct API call if cache fails
            extended_data = get_extended_stock_data(stock.ticker_symbol)
    except Exception as e:
        # If cache fails, fallback to direct yfinance call
        import logging
        logging.warning(f"Cache service failed for stock {stock_id}: {str(e)}")
        extended_data = get_extended_stock_data(stock.ticker_symbol)
    
    if not extended_data:
        # Return basic stock data without extended info if all fetch methods fail
        stock_dict = {
            "id": stock.id,
            "isin": stock.isin,
            "ticker_symbol": stock.ticker_symbol,
            "name": stock.name,
            "country": stock.country,
            "industry": stock.industry,
            "sector": stock.sector,
            "watchlist_id": stock.watchlist_id,
            "position": stock.position,
            "observation_reasons": stock.observation_reasons,
            "observation_notes": stock.observation_notes,
            "exchange": stock.exchange,
            "currency": stock.currency,
            "created_at": stock.created_at,
            "updated_at": stock.updated_at,
            "stock_data": [],
            "latest_data": _get_latest_stock_data(db, stock.id),
            "extended_data": None
        }
        return schemas.StockWithExtendedData(**stock_dict)
    
    # Create extended data object if available
    extended_data_obj = None
    if extended_data:
        extended_data_obj = schemas.ExtendedStockData(
            business_summary=extended_data.get('business_summary'),
            financial_ratios=schemas.FinancialRatios(**extended_data.get('financial_ratios', {})),
            cashflow_data=schemas.CashflowData(**extended_data.get('cashflow_data', {})),
            dividend_info=schemas.DividendInfo(**extended_data.get('dividend_info', {})),
            price_data=schemas.PriceData(**extended_data.get('price_data', {})),
            volume_data=schemas.VolumeData(**extended_data.get('volume_data', {})),
            risk_metrics=schemas.RiskMetrics(**extended_data.get('risk_metrics', {}))
        )
    
    # Create response object
    stock_dict = {
        "id": stock.id,
        "isin": stock.isin,
        "ticker_symbol": stock.ticker_symbol,
        "name": stock.name,
        "country": stock.country,
        "industry": stock.industry,
        "sector": stock.sector,
        "watchlist_id": stock.watchlist_id,
        "position": stock.position,
        "observation_reasons": stock.observation_reasons,
        "observation_notes": stock.observation_notes,
        "exchange": stock.exchange,
        "currency": stock.currency,
        "created_at": stock.created_at,
        "updated_at": stock.updated_at,
        "stock_data": [],
        "latest_data": _get_latest_stock_data(db, stock.id),
        "extended_data": extended_data_obj
    }
    
    return schemas.StockWithExtendedData(**stock_dict)


@router.get(
    "/{stock_id}/with-calculated-metrics", 
    response_model=schemas.StockWithCalculatedMetrics,
    summary="Get Stock with Calculated Metrics",
    description="""
    Retrieve complete stock information including:
    - Basic stock details (ticker, name, sector, industry)
    - Latest price data
    - Extended financial data (ratios, cashflow, dividends)
    - **Comprehensive calculated metrics** (all 3 phases)
    
    This is a convenience endpoint that combines `/api/stocks/{stock_id}` 
    and `/api/stock-data/{stock_id}/calculated-metrics` into a single response.
    
    **Use Cases:**
    - Stock detail pages requiring complete analysis
    - Dashboard widgets with all metrics
    - Portfolio analysis tools
    
    **Performance:** Cached for 1 hour, typically responds in < 500ms.
    """,
    response_description="Complete stock information with calculated metrics",
    responses={
        200: {
            "description": "Successfully retrieved stock with metrics",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "ticker_symbol": "AAPL",
                        "name": "Apple Inc.",
                        "sector": "Technology",
                        "industry": "Consumer Electronics",
                        "extended_data": {
                            "business_summary": "Apple Inc. designs, manufactures...",
                            "financial_ratios": {
                                "pe_ratio": 28.5,
                                "peg_ratio": 2.1
                            }
                        },
                        "calculated_metrics": {
                            "basic_indicators": {"...": "..."},
                            "valuation_scores": {"...": "..."},
                            "advanced_analysis": {"...": "..."}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Stock not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock not found"}
                }
            }
        }
    },
    tags=["Stock Analysis", "Stocks"]
)
def get_stock_with_calculated_metrics(
    stock_id: int, 
    watchlist_id: Optional[int] = Query(None, description="Optional watchlist context"),
    period: str = Query("1y", description="Historical data period: '1mo', '3mo', '6mo', '1y', '2y'"),
    force_refresh: bool = Query(False, description="Force cache refresh"),
    db: Session = Depends(get_db)
):
    """
    Get complete stock information including all calculated metrics.
    
    Combines basic stock data, extended financial information, and 
    comprehensive calculated metrics in a single API call.
    """
    from backend.app.services import calculated_metrics_service
    
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get watchlist context from StockInWatchlist table
    watchlist_entry = None
    if watchlist_id:
        # Use provided watchlist_id
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.watchlist_id == watchlist_id,
            StockInWatchlistModel.stock_id == stock_id
        ).first()
    else:
        # Fallback: use first watchlist where stock is present
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.stock_id == stock_id
        ).first()
    
    # Set watchlist context attributes on stock object for compatibility
    if watchlist_entry:
        stock.watchlist_id = watchlist_entry.watchlist_id
        stock.position = watchlist_entry.position
        stock.observation_reasons = watchlist_entry.observation_reasons or []
        stock.observation_notes = watchlist_entry.observation_notes
        stock.exchange = watchlist_entry.exchange
        stock.currency = watchlist_entry.currency
    else:
        # Stock exists but not in any watchlist (shouldn't happen normally)
        stock.watchlist_id = None
        stock.position = None
        stock.observation_reasons = []
        stock.observation_notes = None
        stock.exchange = None
        stock.currency = None
    
    # Attach latest stock data
    # Latest data loaded via _get_latest_stock_data in get_stocks route
    # Get extended data (with caching)
    try:
        cache_service = StockDataCacheService(db)
        cached_data, cache_hit = cache_service.get_cached_extended_data(stock_id, force_refresh)
        extended_data = cached_data.get('extended_data') if cached_data else None
        
        if not extended_data:
            extended_data = get_extended_stock_data(stock.ticker_symbol)
    except Exception as e:
        logger.warning(f"Cache service failed for stock {stock_id}: {str(e)}")
        extended_data = get_extended_stock_data(stock.ticker_symbol)
    
    # Create extended data object
    extended_data_obj = None
    if extended_data:
        extended_data_obj = schemas.ExtendedStockData(
            business_summary=extended_data.get('business_summary'),
            financial_ratios=schemas.FinancialRatios(**extended_data.get('financial_ratios', {})),
            cashflow_data=schemas.CashflowData(**extended_data.get('cashflow_data', {})),
            dividend_info=schemas.DividendInfo(**extended_data.get('dividend_info', {})),
            price_data=schemas.PriceData(**extended_data.get('price_data', {})),
            volume_data=schemas.VolumeData(**extended_data.get('volume_data', {})),
            risk_metrics=schemas.RiskMetrics(**extended_data.get('risk_metrics', {}))
        )
    
    # Calculate metrics
    calculated_metrics = None
    if extended_data:
        try:
            # Flatten extended_data for metrics calculation
            stock_data = {}
            for key, value in extended_data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        stock_data[sub_key] = sub_value
                else:
                    stock_data[key] = value
            
            # Get historical prices
            from backend.app.services.yfinance_service import get_historical_prices, get_analyst_data
            historical_prices = get_historical_prices(stock.ticker_symbol, period)
            
            # Get analyst data if available
            try:
                analyst_data = get_analyst_data(stock.ticker_symbol)
                if analyst_data:
                    stock_data['price_targets'] = analyst_data.get('price_targets')
                    stock_data['recommendations'] = analyst_data.get('recommendations', [])
            except Exception as e:
                logger.warning(f"Could not fetch analyst data for {stock.ticker_symbol}: {e}")
                stock_data['price_targets'] = None
                stock_data['recommendations'] = []
            
            # Calculate all metrics
            metrics_dict = calculated_metrics_service.calculate_all_metrics(
                stock_data,
                historical_prices
            )
            
            # Convert to schema
            calculated_metrics = schemas.CalculatedMetrics(**metrics_dict)
            
        except Exception as e:
            logger.error(f"Error calculating metrics for stock {stock_id}: {str(e)}")
            # Return without calculated metrics if calculation fails
    
    # Create response object
    stock_dict = {
        "id": stock.id,
        "isin": stock.isin,
        "ticker_symbol": stock.ticker_symbol,
        "name": stock.name,
        "country": stock.country,
        "industry": stock.industry,
        "sector": stock.sector,
        "watchlist_id": stock.watchlist_id,
        "position": stock.position,
        "observation_reasons": stock.observation_reasons,
        "observation_notes": stock.observation_notes,
        "exchange": stock.exchange,
        "currency": stock.currency,
        "created_at": stock.created_at,
        "updated_at": stock.updated_at,
        "stock_data": [],
        "latest_data": _get_latest_stock_data(db, stock.id),
        "extended_data": extended_data_obj,
        "calculated_metrics": calculated_metrics
    }
    
    return schemas.StockWithCalculatedMetrics(**stock_dict)


# ============================================================================
# NEW ENDPOINTS FOR HISTORICAL DATA
# ============================================================================

@router.get("/{stock_id}/price-history", response_model=schemas.HistoricalPriceResponse)
def get_stock_price_history(
    stock_id: int,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Limit number of records"),
    db: Session = Depends(get_db)
):
    """
    Get historical price data for a stock
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    historical_service = HistoricalPriceService(db)
    prices = historical_service.get_historical_prices(
        stock_id, 
        start_date=start_date, 
        end_date=end_date,
        limit=limit
    )
    
    if not prices:
        return schemas.HistoricalPriceResponse(
            stock_id=stock_id,
            ticker_symbol=stock.ticker_symbol,
            count=0,
            date_range={"start": None, "end": None},
            data=[]
        )
    
    dates = [p.date for p in prices]
    return schemas.HistoricalPriceResponse(
        stock_id=stock_id,
        ticker_symbol=stock.ticker_symbol,
        count=len(prices),
        date_range={
            "start": min(dates).strftime("%Y-%m-%d"),
            "end": max(dates).strftime("%Y-%m-%d")
        },
        data=prices
    )


@router.post("/{stock_id}/price-history/refresh", response_model=Dict[str, Any])
def refresh_stock_price_history(
    stock_id: int,
    period: str = Query("7d", description="Period to refresh (7d, 1mo, 3mo, 6mo, 1y, max)"),
    db: Session = Depends(get_db)
):
    """
    Refresh historical price data for a stock
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    historical_service = HistoricalPriceService(db)
    
    # For short periods, use update_recent_prices
    if period in ["7d", "1d", "5d"]:
        days = int(period.replace("d", ""))
        result = historical_service.update_recent_prices(stock_id, days=days)
    else:
        # For longer periods, reload all data
        result = historical_service.load_and_save_historical_prices(
            stock_id, 
            period=period
        )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to refresh data: {result.get('error')}"
        )
    
    return {
        "success": True,
        "stock_id": stock_id,
        "ticker_symbol": stock.ticker_symbol,
        "records_updated": result.get("count", 0),
        "message": f"Successfully refreshed {result.get('count', 0)} price records"
    }


@router.get("/{stock_id}/fundamentals", response_model=schemas.FundamentalDataResponse)
def get_stock_fundamentals(
    stock_id: int,
    periods: Optional[int] = Query(None, description="Number of periods to return (default: all)"),
    db: Session = Depends(get_db)
):
    """
    Get quarterly fundamental data for a stock
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    fundamental_service = FundamentalDataService(db)
    fundamentals = fundamental_service.get_fundamental_data(stock_id, periods=periods)
    
    return schemas.FundamentalDataResponse(
        stock_id=stock_id,
        ticker_symbol=stock.ticker_symbol,
        count=len(fundamentals),
        data=fundamentals
    )


@router.post("/{stock_id}/fundamentals/refresh", response_model=Dict[str, Any])
def refresh_stock_fundamentals(
    stock_id: int,
    db: Session = Depends(get_db)
):
    """
    Refresh fundamental data for a stock
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    fundamental_service = FundamentalDataService(db)
    result = fundamental_service.load_and_save_fundamental_data(stock_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to refresh fundamentals: {result.get('error')}"
        )
    
    return {
        "success": True,
        "stock_id": stock_id,
        "ticker_symbol": stock.ticker_symbol,
        "records_updated": result.get("count", 0),
        "message": f"Successfully refreshed {result.get('count', 0)} fundamental records"
    }


@router.post("/{stock_id}/update-market-data", response_model=Dict[str, Any])
def update_market_data(
    stock_id: int,
    db: Session = Depends(get_db)
):
    """
    Update market data (current price, volumes, etc.) for a stock
    Fetches latest data from yfinance using fast_info (optimized)
    
    Note: PE ratio and extended data are updated via cache service
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        # Get current stock data from yfinance using fast_info (0.3s instead of 2-3s)
        current_data = get_fast_market_data(stock.ticker_symbol)
        
        if not current_data:
            raise HTTPException(
                status_code=400,
                detail=f"Could not fetch market data for {stock.ticker_symbol}"
            )
        
        # Update historical price service with latest price
        historical_service = HistoricalPriceService(db)
        
        # Try to refresh recent price data - use 1mo to ensure we get the latest data
        try:
            result = historical_service.load_and_save_historical_prices(
                stock_id=stock_id,
                period="1mo",  # Get last month to ensure latest data
                interval="1d"
            )
            if result.get("success"):
                logger.info(f"Successfully refreshed historical data for {stock.ticker_symbol}: {result.get('count')} records")
            else:
                logger.warning(f"Historical data refresh returned: {result}")
        except Exception as e:
            logger.warning(f"Could not refresh historical data for {stock.ticker_symbol}: {e}")
        
        # Ensure all changes are committed before reading
        db.commit()
        
        # Refresh the session to get the latest data
        db.expire_all()
        
        # Get the latest price data from the database
        latest_price = historical_service.get_latest_price(stock_id)
        
        # Calculate change if we have previous data
        change = None
        change_percent = None
        if latest_price and latest_price.close:
            # Try to get previous day's close
            prev_price = db.query(StockPriceDataModel).filter(
                StockPriceDataModel.stock_id == stock_id,
                StockPriceDataModel.date < latest_price.date
            ).order_by(desc(StockPriceDataModel.date)).first()
            
            if prev_price and prev_price.close:
                change = latest_price.close - prev_price.close
                change_percent = (change / prev_price.close) * 100
        
        # Use current_data for change if not calculated from historical
        if change is None and current_data.get('change') is not None:
            change = current_data.get('change')
            change_percent = current_data.get('change_percent')
        
        # Get PE ratio from cache (extended data updated via daily job or on add)
        pe_ratio = None
        try:
            cache_service = StockDataCacheService(db)
            # Force refresh extended data to get latest PE ratio and fundamentals (uses .info internally)
            extended_data_result, _ = cache_service.get_cached_extended_data(stock_id, force_refresh=True)
            if extended_data_result and extended_data_result.get('extended_data'):
                financial_ratios = extended_data_result['extended_data'].get('financial_ratios', {})
                pe_ratio = financial_ratios.get('pe_ratio')
            db.commit()
        except Exception as e:
            logger.warning(f"Could not update extended data cache for {stock.ticker_symbol}: {e}")
        
        # Build response
        current_price = latest_price.close if latest_price else current_data.get('current_price')
        volume = latest_price.volume if latest_price else current_data.get('volume')
        price_date = latest_price.date if latest_price else datetime.now().date()
        
        return {
            "success": True,
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "data": {
                "current_price": current_price,
                "pe_ratio": pe_ratio,
                "change": change,
                "change_percent": change_percent,
                "volume": volume,
                "date": price_date.isoformat() if isinstance(price_date, date) else str(price_date)
            },
            "message": "Market data updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating market data for {stock.ticker_symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update market data: {str(e)}"
        )


@router.get("/{stock_id}/data-quality", response_model=Dict[str, Any])
def get_stock_data_quality(
    stock_id: int,
    db: Session = Depends(get_db)
):
    """
    Get data quality report for a stock
    Shows completeness of historical and fundamental data
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    historical_service = HistoricalPriceService(db)
    fundamental_service = FundamentalDataService(db)
    
    price_quality = historical_service.get_data_quality_report(stock_id)
    fundamental_summary = fundamental_service.get_data_summary(stock_id)
    
    return {
        "stock_id": stock_id,
        "ticker_symbol": stock.ticker_symbol,
        "price_data": price_quality,
        "fundamental_data": fundamental_summary,
        "overall_status": "complete" if price_quality.get("has_data") and fundamental_summary.get("has_data") else "incomplete"
    }
