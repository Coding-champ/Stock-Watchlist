from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from threading import Lock
import logging
import pandas as pd
from backend.app.services.yfinance_service import get_historical_prices
from backend.app.services.seasonality_service import get_all_seasonalities, calculate_monthly_returns, calculate_seasonality
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
    get_fast_market_data_with_timestamp,
    get_stock_dividends_and_splits, get_stock_calendar_and_earnings,
    get_analyst_data, get_institutional_holders,
    get_stock_info_by_identifier, get_ticker_from_isin,
    calculate_technical_indicators
)
from backend.app.services.cache_service import StockDataCacheService
from backend.app.services.stock_service import StockService
from backend.app.services.historical_price_service import HistoricalPriceService
from backend.app.services.fundamental_data_service import FundamentalDataService
from backend.app.services.technical_indicators_service import calculate_rsi as ta_calculate_rsi, calculate_macd as ta_calculate_macd
from backend.app.utils.signal_interpretation import interpret_rsi as ta_interpret_rsi, interpret_macd as ta_interpret_macd
from backend.app.services.stock_query_service import StockQueryService
from backend.app.utils.url_utils import normalize_website_url

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/{stock_id}/analyst-ratings")
def get_stock_analyst_ratings(stock_id: int, db: Session = Depends(get_db)):
    """Return analyst overview/ratings for the given stock."""
    logger = logging.getLogger("analyst_debug")
    try:
        stock = StockQueryService(db).get_stock_id_or_404(stock_id)
        # Delegate to service which may aggregate multiple sources
        overview = get_complete_analyst_overview(stock.ticker_symbol)
        return overview or {"ticker": stock.ticker_symbol, "analyst_overview": {}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analyst ratings for stock_id={stock_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal error fetching analyst ratings")

logger = logging.getLogger(__name__)

ALLOWED_OBSERVATION_REASONS = {
    "chart_technical",
    "earnings",
    "fundamentals",
    "company",
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

    # If the latest price is from today, try to enrich the timestamp using fast yfinance data
    try:
        if isinstance(latest_price.date, date) and latest_price.date == date.today():
            try:
                # Resolve ticker symbol
                stock_row = db.query(StockModel).filter(StockModel.id == stock_id).first()
                if stock_row and getattr(stock_row, 'ticker_symbol', None):
                    fast = get_fast_market_data_with_timestamp(stock_row.ticker_symbol)
                    if fast and isinstance(fast, dict):
                        ts_val = fast.get('timestamp') or fast.get('last_updated')
                        if ts_val:
                            parsed = None
                            # ts_val may be int/float epoch, ISO string with Z, or datetime
                            if isinstance(ts_val, (int, float)):
                                parsed = datetime.utcfromtimestamp(int(ts_val))
                            elif isinstance(ts_val, str):
                                try:
                                    # handle trailing Z
                                    if ts_val.endswith('Z'):
                                        parsed = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                                    else:
                                        parsed = datetime.fromisoformat(ts_val)
                                except Exception:
                                    try:
                                        parsed = datetime.utcfromtimestamp(int(float(ts_val)))
                                    except Exception:
                                        parsed = None
                            elif isinstance(ts_val, datetime):
                                parsed = ts_val

                            if isinstance(parsed, datetime):
                                result.timestamp = parsed
            except Exception:
                # do not break on failures to enrich timestamp
                pass
    except Exception:
        pass
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
        for s in stocks:
            s.latest_data = _get_latest_stock_data(db, s.id)

        # Batch-fetch cache entries to avoid N+1 queries
        try:
            stock_ids = [s.id for s in stocks]
            cache_map = {}
            if stock_ids:
                cache_entries = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id.in_(stock_ids)).all()
                # Map stock_id -> extended_data dict (if present)
                for c in cache_entries:
                    try:
                        if c and getattr(c, 'extended_data', None):
                            cache_map[c.stock_id] = c.extended_data
                    except Exception:
                        continue

            for s in stocks:
                try:
                    ext = cache_map.get(s.id)
                    if ext:
                        ir = ext.get('irWebsite') or ext.get('ir_website') or ext.get('website') or (ext.get('info_full') or {}).get('website')
                        ir = normalize_website_url(ir)
                        if ir:
                            setattr(s, 'ir_website', ir)
                except Exception:
                    # don't fail the whole list if one entry is bad
                    continue
        except Exception:
            # best-effort: if batching fails, fall back to per-stock logic (kept minimal)
            try:
                for s in stocks:
                    try:
                        cache_entry = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id == s.id).first()
                        if cache_entry and cache_entry.extended_data:
                            ext = cache_entry.extended_data
                            ir = ext.get('irWebsite') or ext.get('ir_website') or ext.get('website') or (ext.get('info_full') or {}).get('website')
                            ir = normalize_website_url(ir)
                            if ir:
                                setattr(s, 'ir_website', ir)
                    except Exception:
                        continue
            except Exception:
                pass

        return stocks


# ------------------------------------------------------------------
# ALL STOCKS: Performance list (with optional RSI/MACD signals)
# Moved above generic /{stock_id} route to avoid path-param shadowing
# ------------------------------------------------------------------
@router.get("/performance", response_model=schemas.PerformanceListResponse)
def list_stocks_performance(
    period: str = Query("6m", description="Period: e.g. 6m, 1y, 3y"),
    points: int = Query(24, ge=2, le=180, description="Number of sparkline points"),
    sort: str = Query("desc", description="Sort order by performance: asc|desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=200),
    includeSignals: bool = Query(True, description="Include latest RSI/MACD signals"),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of stocks with performance over the given period,
    a compact price series (sparkline), and optionally lightweight RSI/MACD signals.

    Response format:
    {
      "items": [
        {
          "id": 1,
          "ticker": "AAPL",
          "name": "Apple Inc.",
          "performance_pct": 12.34,
          "price_series": [{"date": "YYYY-MM-DD", "close": 123.45}, ...],
          "signals": {
             "rsi": {"value": 52.1, "signal": "neutral"},
             "macd": {"histogram": 0.12, "trend": "bullish"}
          }
        }
      ],
      "total": 123,
      "page": 1,
      "limit": 24
    }
    """
    from dateutil.relativedelta import relativedelta
    from datetime import datetime
    import pandas as pd

    now = datetime.utcnow().date()
    p = (period or "6m").lower()
    if p.endswith("y") and p[:-1].isdigit():
        start_date = now - relativedelta(years=int(p[:-1]))
    elif p.endswith("m") and p[:-1].isdigit():
        start_date = now - relativedelta(months=int(p[:-1]))
    else:
        start_date = now - relativedelta(months=6)

    # Load candidates (all stocks); simple approach first
    stocks = db.query(StockModel).all()

    items = []
    for s in stocks:
        try:
            latest_row = db.query(StockPriceDataModel).filter(StockPriceDataModel.stock_id == s.id).order_by(desc(StockPriceDataModel.date)).first()
            if not latest_row:
                continue

            # find start reference price
            start_row = db.query(StockPriceDataModel).filter(
                StockPriceDataModel.stock_id == s.id,
                StockPriceDataModel.date >= start_date
            ).order_by(asc(StockPriceDataModel.date)).first()
            if not start_row:
                start_row = db.query(StockPriceDataModel).filter(
                    StockPriceDataModel.stock_id == s.id,
                    StockPriceDataModel.date <= start_date
                ).order_by(desc(StockPriceDataModel.date)).first()

            perf_pct = None
            if start_row and start_row.close not in (None, 0) and latest_row.close is not None:
                try:
                    perf_pct = (float(latest_row.close) - float(start_row.close)) / float(start_row.close) * 100.0
                    perf_pct = round(perf_pct, 2)
                except Exception:
                    perf_pct = None

            # Collect price rows to build sparkline and (optionally) compute signals
            price_rows = db.query(StockPriceDataModel).filter(
                StockPriceDataModel.stock_id == s.id,
                StockPriceDataModel.date >= start_date,
                StockPriceDataModel.date <= latest_row.date
            ).order_by(asc(StockPriceDataModel.date)).all()

            points_list = []
            closes_for_ind = []
            for pr in price_rows:
                if pr.close is None:
                    continue
                d = pr.date.strftime("%Y-%m-%d")
                c = float(pr.close)
                points_list.append({"date": d, "close": c})
                closes_for_ind.append(c)

            # Downsample to requested number of points (similar strategy as peers)
            price_series = None
            if points_list:
                try:
                    # Aggregate by month for longer periods (>=3 months)
                    months = None
                    if p.endswith('y') and p[:-1].isdigit():
                        months = int(p[:-1]) * 12
                    elif p.endswith('m') and p[:-1].isdigit():
                        months = int(p[:-1])
                    else:
                        months = 6

                    if months >= 3:
                        grouped = {}
                        for pt in points_list:
                            y, m, _ = pt['date'].split('-')
                            key = (int(y), int(m))
                            grouped[key] = pt  # keep last occurrence in month
                        sorted_months = sorted(grouped.keys())
                        month_points = [grouped[k] for k in sorted_months]
                        if len(month_points) > points and points > 1:
                            step = max(1, int(len(month_points) / points))
                            sampled = [month_points[i] for i in range(0, len(month_points), step)]
                            price_series = sampled[:points]
                        else:
                            price_series = month_points
                    else:
                        if len(points_list) > points and points > 1:
                            step = max(1, int(len(points_list) / points))
                            sampled = [points_list[i] for i in range(0, len(points_list), step)]
                            price_series = sampled[:points]
                        else:
                            price_series = points_list
                except Exception:
                    # simple fallback
                    if len(points_list) > points and points > 1:
                        step = max(1, int(len(points_list) / points))
                        sampled = [points_list[i] for i in range(0, len(points_list), step)]
                        price_series = sampled[:points]
                    else:
                        price_series = points_list

            signals = None
            if includeSignals and closes_for_ind and len(closes_for_ind) >= 30:  # ensure minimum data length
                try:
                    close_series = pd.Series(closes_for_ind)
                    rsi_res = ta_calculate_rsi(close_series)
                    macd_res = ta_calculate_macd(close_series)
                    signals = {
                        "rsi": {
                            "value": float(rsi_res.get('value')) if rsi_res.get('value') is not None else None,
                            "signal": rsi_res.get('signal') or (ta_interpret_rsi(rsi_res.get('value')) if rsi_res.get('value') is not None else None)
                        },
                        "macd": {
                            "histogram": float(macd_res.get('histogram')) if macd_res.get('histogram') is not None else None,
                            "trend": macd_res.get('trend') or (ta_interpret_macd(macd_res.get('histogram')) if macd_res.get('histogram') is not None else None)
                        }
                    }
                except Exception:
                    signals = None

            items.append({
                "id": s.id,
                "ticker": s.ticker_symbol,
                "name": s.name,
                "performance_pct": perf_pct,
                "price_series": price_series or [],
                "signals": signals
            })
        except Exception:
            continue

    # Sort and paginate
    def sort_key(x):
        v = x.get("performance_pct")
        return (v is None, v if sort == "asc" else -(v or 0))

    items_sorted = sorted(items, key=sort_key)
    total = len(items_sorted)
    start = (page - 1) * limit
    end = start + limit
    page_items = items_sorted[start:end]

    return {"items": page_items, "total": total, "page": page, "limit": limit}


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
    # Try to attach investor-relations / website link from extended cache if present
    try:
        cache_entry = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id == stock_id).first()
        if cache_entry and cache_entry.extended_data:
            ext = cache_entry.extended_data
            ir_website = ext.get('irWebsite') or ext.get('ir_website') or ext.get('website') or (ext.get('info_full') or {}).get('website')
            ir_website = normalize_website_url(ir_website)
            if ir_website:
                setattr(stock, 'ir_website', ir_website)
    except Exception:
        pass

    return stock


# ------------------------------------------------------------------
# Fundamentals time-series endpoint (supports mock fallback)
# ------------------------------------------------------------------
@router.get("/{stock_id}/fundamentals/timeseries")
def get_fundamentals_timeseries(
    stock_id: int,
    metric: str = Query("pe_ratio", description="Metric to return: pe_ratio, price_to_sales, ev_ebit, price_to_book"),
    period: str = Query("3y", description="Period to return: 1y,3y,5y"),
    db: Session = Depends(get_db)
):
    """
    Returns a time-series for a requested fundamental metric for the given stock.
    If reliable fundamental or price data is not available, returns a mocked series.
    """
    import random
    from dateutil.relativedelta import relativedelta
    from datetime import datetime

    stock = StockQueryService(db).get_stock_id_or_404(stock_id)
    fund_service = FundamentalDataService(db)

    try:
        df = fund_service.get_fundamental_dataframe(stock_id)
    except Exception as e:
        df = None

    series = []
    used_mock = False

    # Helper to create mocked monthly series
    def _mock_series(base, months=36):
        out = []
        today = datetime.utcnow().date()
        for i in range(months, 0, -1):
            d = (today - relativedelta(months=i-1)).replace(day=1)
            # add some smooth noise
            val = round(base * (1 + (random.random() - 0.5) * 0.2), 2)
            out.append({"date": d.strftime("%Y-%m-%d"), "value": val})
        return out

    # Try to compute real series for selected metrics using stored fundamentals and price data
    if df is not None and not df.empty:
        try:
            rows = df.reset_index().to_dict(orient='records')
            # We'll attempt to compute for each supported metric
            for rec in sorted(rows, key=lambda r: r.get('period_end_date') or datetime.min):
                period_end = rec.get('period_end_date')
                if not period_end:
                    continue

                # Find latest price on or before period_end
                price_rec = db.query(StockPriceDataModel).filter(
                    StockPriceDataModel.stock_id == stock_id,
                    StockPriceDataModel.date <= period_end
                ).order_by(desc(StockPriceDataModel.date)).first()
                if not price_rec:
                    continue

                price = float(price_rec.close) if price_rec.close is not None else None

                # EPS (basic or diluted)
                eps = rec.get('eps_basic') or rec.get('eps_diluted') or None
                # Revenue and operating income
                revenue = rec.get('revenue')
                operating_income = rec.get('operating_income')

                # Try to obtain shares outstanding (from extended cache)
                shares_outstanding = None
                try:
                    cache = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id == stock_id).first()
                    if cache and cache.extended_data:
                        shares_outstanding = cache.extended_data.get('sharesOutstanding') or cache.extended_data.get('shares_outstanding')
                except Exception:
                    shares_outstanding = None

                # Compute requested metric value if possible
                computed = None
                if metric == 'pe_ratio' and eps and eps != 0 and price:
                    try:
                        computed = price / float(eps)
                    except Exception:
                        computed = None
                elif metric == 'price_to_sales' and revenue and shares_outstanding and price:
                    try:
                        market_cap = price * float(shares_outstanding)
                        computed = market_cap / float(revenue) if revenue else None
                    except Exception:
                        computed = None
                elif metric == 'price_to_book' and rec.get('shareholders_equity') and shares_outstanding and price:
                    try:
                        market_cap = price * float(shares_outstanding)
                        book_value = float(rec.get('shareholders_equity'))
                        computed = market_cap / book_value if book_value else None
                    except Exception:
                        computed = None
                elif metric == 'ev_ebit' and operating_income:
                    try:
                        # Try to get enterprise value from cache or compute: EV = market_cap + total_debt - total_cash
                        ev = None
                        cache = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id == stock_id).first()
                        if cache and cache.extended_data:
                            ev = cache.extended_data.get('enterpriseValue') or cache.extended_data.get('enterprise_value')
                        if ev is None and shares_outstanding and price:
                            market_cap = price * float(shares_outstanding)
                            total_debt = rec.get('total_liabilities') or 0
                            # Try to get cash if present in cache
                            total_cash = None
                            if cache and cache.extended_data:
                                total_cash = cache.extended_data.get('totalCash') or cache.extended_data.get('total_cash')
                            if total_debt is not None:
                                try:
                                    ev = market_cap + float(total_debt) - (float(total_cash) if total_cash is not None else 0)
                                except Exception:
                                    ev = None
                        if ev and operating_income and float(operating_income) != 0:
                            computed = float(ev) / float(operating_income)
                    except Exception:
                        computed = None

                if computed is not None and not (computed != computed):
                    series.append({"date": period_end.strftime("%Y-%m-%d"), "value": round(computed, 2)})
        except Exception:
            series = []

    # If we couldn't build a reliable series, return mock data
    if not series:
        used_mock = True
        months = 12 if period == '1y' else (36 if period == '3y' else 60)
        # Choose plausible bases per metric
        base_map = {
            'pe_ratio': 20.0,
            'price_to_sales': 3.5,
            'ev_ebit': 15.0,
            'price_to_book': 4.0
        }
        base = base_map.get(metric, 10.0)
        series = _mock_series(base=base, months=months)

    return {"stock_id": stock_id, "ticker": stock.ticker_symbol, "metric": metric, "period": period, "used_mock": used_mock, "series": series}


# ------------------------------------------------------------------
# Sector/Industry peers endpoint (with mock fallback values)
# ------------------------------------------------------------------
@router.get("/{stock_id}/peers")
def get_stock_peers(
    stock_id: int,
    metric: str = Query("market_cap", description="Metric to compare: market_cap, pe_ratio, price_to_sales"),
    by: str = Query("sector", description="Group peers by 'sector' or 'industry'"),
    limit: int = Query(10, description="Max number of peers to return"),
    perf_period: str = Query("1y", description="Performance period to compute (e.g. 1y,3m,6m,1m)"),
    perf_points: int = Query(12, description="Number of points to include in returned price series (sparkline)"),
    db: Session = Depends(get_db)
):
    """
    Returns a list of peer stocks for the same sector or industry with a metric value.
    If no reliable values are available, returns mocked values for the peers.
    """
    import random
    stock = StockQueryService(db).get_stock_id_or_404(stock_id)

    key_field = 'sector' if by != 'industry' else 'industry'
    key_value = getattr(stock, key_field, None)
    if not key_value:
        return {"stock_id": stock_id, "ticker": stock.ticker_symbol, "peers": []}

    # Query peers in same sector/industry
    peers_q = db.query(StockModel).filter(getattr(StockModel, key_field) == key_value, StockModel.id != stock_id).limit(limit).all()
    used_mock = False

    # If no peers found in the same group, broaden the candidate set to all other stocks
    if not peers_q:
        # We'll try to compute metric values for all other stocks and pick the top 'limit' ones
        candidates = db.query(StockModel).filter(StockModel.id != stock_id).all()
        peers_candidates = candidates
    else:
        peers_candidates = peers_q

    peers = []

    for p in peers_candidates:
        val = None
        perf_pct = None
        try:
            # Try to compute using latest price and cache
            cache = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id == p.id).first()

            # Get latest price
            latest_price = db.query(StockPriceDataModel).filter(StockPriceDataModel.stock_id == p.id).order_by(desc(StockPriceDataModel.date)).first()
            price = float(latest_price.close) if latest_price and latest_price.close is not None else None

            shares_outstanding = None
            if cache and cache.extended_data:
                shares_outstanding = cache.extended_data.get('sharesOutstanding') or cache.extended_data.get('shares_outstanding')

            if metric == 'market_cap':
                # Prefer explicit market cap from cache (try multiple common keys)
                if cache and cache.extended_data:
                    ext = cache.extended_data
                    val = ext.get('market_cap') if ext.get('market_cap') is not None else (
                        ext.get('marketCap') if ext.get('marketCap') is not None else (
                          ext.get('financial_ratios', {}).get('market_cap') if isinstance(ext.get('financial_ratios'), dict) else None
                        )
                    )
                    # If the cached value is a numeric string, try to convert
                    if isinstance(val, str):
                        try:
                            val = float(val)
                        except Exception:
                            pass
                # Fallback to calculating from latest price and shares outstanding
                if val is None and price and shares_outstanding:
                    try:
                        val = price * float(shares_outstanding)
                    except Exception:
                        val = None
            elif metric == 'pe_ratio':
                # Prefer cached financial ratios
                if cache and cache.extended_data and cache.extended_data.get('financial_ratios') and cache.extended_data['financial_ratios'].get('pe_ratio'):
                    val = cache.extended_data['financial_ratios'].get('pe_ratio')
                else:
                    # try compute from latest eps in fundamental table
                    fund_service = FundamentalDataService(db)
                    fund_df = fund_service.get_fundamental_dataframe(p.id)
                    if fund_df is not None and not fund_df.empty and price:
                        # use most recent EPS
                        try:
                            latest_rec = fund_df.reset_index().iloc[0]
                            eps = latest_rec.get('eps_basic') or latest_rec.get('eps_diluted')
                            if eps and float(eps) != 0:
                                val = price / float(eps)
                        except Exception:
                            val = None
            elif metric == 'price_to_sales':
                if cache and cache.extended_data and cache.extended_data.get('financial_ratios') and cache.extended_data['financial_ratios'].get('price_to_sales'):
                    val = cache.extended_data['financial_ratios'].get('price_to_sales')
                elif price and shares_outstanding:
                    # attempt market_cap / revenue
                    fund_service = FundamentalDataService(db)
                    fund_df = fund_service.get_fundamental_dataframe(p.id)
                    if fund_df is not None and not fund_df.empty:
                        try:
                            latest_rec = fund_df.reset_index().iloc[0]
                            revenue = latest_rec.get('revenue')
                            if revenue and shares_outstanding:
                                market_cap = price * float(shares_outstanding)
                                val = market_cap / float(revenue)
                        except Exception:
                            val = None

        except Exception:
            val = None

        if val is None:
            # skip entries where we couldn't compute a value
            continue

        # Compute performance percentage for the requested perf_period (if possible)
        try:
            # interpret perf_period into a start date
            from dateutil.relativedelta import relativedelta
            from datetime import datetime
            now = datetime.utcnow().date()
            period = perf_period.lower()
            if period.endswith('y'):
                years = int(period[:-1]) if period[:-1].isdigit() else 1
                start_date = now - relativedelta(years=years)
            elif period.endswith('m'):
                months = int(period[:-1]) if period[:-1].isdigit() else 1
                start_date = now - relativedelta(months=months)
            else:
                # default fallback 1 year
                start_date = now - relativedelta(years=1)

            # find price at or just after start_date, fallback to just before
            start_price_rec = db.query(StockPriceDataModel).filter(
                StockPriceDataModel.stock_id == p.id,
                StockPriceDataModel.date >= start_date
            ).order_by(asc(StockPriceDataModel.date)).first()
            if not start_price_rec:
                start_price_rec = db.query(StockPriceDataModel).filter(
                    StockPriceDataModel.stock_id == p.id,
                    StockPriceDataModel.date <= start_date
                ).order_by(desc(StockPriceDataModel.date)).first()

            if start_price_rec and latest_price and start_price_rec.close not in (None, 0):
                try:
                    perf_pct = (float(latest_price.close) - float(start_price_rec.close)) / float(start_price_rec.close) * 100.0
                    perf_pct = round(perf_pct, 2)
                except Exception:
                    perf_pct = None
        except Exception:
            perf_pct = None

        # Build a compact price series (sparkline) of up to perf_points between start_date and latest
        price_series = None
        try:
            if 'start_date' in locals() and latest_price:
                price_rows = db.query(StockPriceDataModel).filter(
                    StockPriceDataModel.stock_id == p.id,
                    StockPriceDataModel.date >= start_date,
                    StockPriceDataModel.date <= latest_price.date
                ).order_by(asc(StockPriceDataModel.date)).all()

                points = []
                for pr in price_rows:
                    if pr.close is None:
                        continue
                    points.append({"date": pr.date.strftime("%Y-%m-%d"), "close": float(pr.close)})

                if points:
                    # Decide sampling strategy: monthly closes for longer periods (>=3 months),
                    # otherwise downsample daily points. Compute requested months from perf_period.
                    try:
                        months = None
                        pp = perf_period.lower()
                        if pp.endswith('y') and pp[:-1].isdigit():
                            months = int(pp[:-1]) * 12
                        elif pp.endswith('m') and pp[:-1].isdigit():
                            months = int(pp[:-1])
                        else:
                            # default to 12 months
                            months = 12

                        if months >= 3:
                            # Aggregate by month: pick last available price per month
                            grouped = {}
                            for pt in points:
                                d = pt['date']
                                # date in YYYY-MM-DD format
                                y, m, _ = d.split('-')
                                key = (int(y), int(m))
                                # keep last occurrence (points are ordered asc)
                                grouped[key] = pt
                            # sort by year/month ascending
                            sorted_months = sorted(grouped.keys())
                            month_points = [grouped[k] for k in sorted_months]
                            # Downsample months to perf_points if necessary
                            if len(month_points) > perf_points and perf_points > 1:
                                step = max(1, int(len(month_points) / perf_points))
                                sampled = [month_points[i] for i in range(0, len(month_points), step)]
                                price_series = sampled[:perf_points]
                            else:
                                price_series = month_points
                        else:
                            # short period: downsample daily points to perf_points
                            if len(points) > perf_points and perf_points > 1:
                                step = max(1, int(len(points) / perf_points))
                                sampled = [points[i] for i in range(0, len(points), step)]
                                price_series = sampled[:perf_points]
                            else:
                                price_series = points
                    except Exception:
                        # fallback to simple downsample
                        if len(points) > perf_points and perf_points > 1:
                            step = max(1, int(len(points) / perf_points))
                            sampled = [points[i] for i in range(0, len(points), step)]
                            price_series = sampled[:perf_points]
                        else:
                            price_series = points
        except Exception:
            price_series = None

        peers.append({"name": p.name, "ticker": p.ticker_symbol, "value": val, "performance": perf_pct, "price_series": price_series})

    # If we collected real peers, sort by value desc and limit
    if peers:
        peers = sorted(peers, key=lambda x: (x['value'] is None, -(x['value'] or 0)))[:limit]
    else:
        # No computable peers found -> fallback to mocked peers
        used_mock = True
        mock_names = [f"{stock.sector} Peer {i+1}" for i in range(limit)]
        for i, name in enumerate(mock_names):
            base = 50 if metric == 'market_cap' else (20 if metric == 'pe_ratio' else 5)
            val = round(base * (1 + (i - (limit/2)) * 0.08), 2)
            # create a small mocked price series (linear-ish) for visualization
            mock_series = []
            for j in range(perf_points):
                # simulate older -> newer
                price = max(0.1, val * (0.8 + (j / max(1, perf_points)) * 0.4))
                mock_series.append({"date": (datetime.utcnow().date() - timedelta(days=(perf_points - j) * 30)).strftime("%Y-%m-%d"), "close": round(price, 2)})
            peers.append({"name": name, "ticker": f"PEER{i+1}", "value": val, "performance": None, "price_series": mock_series})

    return {"stock_id": stock_id, "ticker": stock.ticker_symbol, "by": by, "metric": metric, "used_mock": used_mock, "peers": peers}


 # moved earlier


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
    
    # Get existing stocks in watchlist (StockService returns list of dicts)
    existing_entries = stock_service.get_stocks_in_watchlist(payload.watchlist_id)
    # Normalize existing tickers/isins from returned dicts
    existing_tickers = {(entry.get('ticker_symbol') or '').upper() for entry in existing_entries}
    existing_isins = {(entry.get('isin') or '').upper() for entry in existing_entries if entry.get('isin')}

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


@router.get("/search-db/", response_model=List[schemas.Stock])
def search_stocks_in_database(
    q: str = Query(..., min_length=1, description="Search query (Name, Ticker, ISIN, WKN)"),
    limit: int = Query(20, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for stocks in the local database by name, ticker symbol, ISIN, or WKN.
    Returns a list of matching stocks with their latest data.
    
    Search is case-insensitive and supports partial matches.
    """
    search_term = f"%{q}%"
    
    # Search across multiple fields using OR conditions
    query = db.query(StockModel).filter(
        (StockModel.name.ilike(search_term)) |
        (StockModel.ticker_symbol.ilike(search_term)) |
        (StockModel.isin.ilike(search_term)) |
        (StockModel.wkn.ilike(search_term))
    ).limit(limit)
    
    stocks = query.all()
    
    # Enrich stocks with latest data
    for stock in stocks:
        stock.latest_data = _get_latest_stock_data(db, stock.id)
        
        # Get the first watchlist this stock belongs to (if any)
        watchlist_entry = db.query(StockInWatchlistModel).filter(
            StockInWatchlistModel.stock_id == stock.id
        ).first()
        
        if watchlist_entry:
            stock.watchlist_id = watchlist_entry.watchlist_id
            stock.position = watchlist_entry.position
            stock.observation_reasons = watchlist_entry.observation_reasons or []
            stock.observation_notes = watchlist_entry.observation_notes
            stock.exchange = watchlist_entry.exchange
            stock.currency = watchlist_entry.currency
    
    return stocks


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


@router.get("/{stock_id}/calendar")
def get_stock_calendar(stock_id: int, db: Session = Depends(get_db)):
    """
    Get earnings calendar and related calendar info for a stock (via yfinance service)
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    try:
        cal = get_stock_calendar_and_earnings(stock.ticker_symbol)
        if not cal:
            raise HTTPException(status_code=400, detail="Could not fetch calendar/earnings data")
        return cal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in calendar endpoint for {stock.ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal error fetching calendar data")


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
    
    # Use cache service to get data (call safely in case implementation is missing)
    cache_service = StockDataCacheService(db)
    _getter = getattr(cache_service, 'get_cached_extended_data', None)
    if not callable(_getter):
        logging.warning(f"Cache service missing method get_cached_extended_data; cache_service={type(cache_service)}; attrs={[a for a in dir(cache_service) if not a.startswith('__')][:50]}")
        cached_data, cache_hit = None, False
    else:
        cached_data, cache_hit = _getter(stock_id, force_refresh)
    
    if not cached_data or not cached_data.get('extended_data'):
        raise HTTPException(
            status_code=400, 
            detail="Could not fetch extended data for this stock"
        )
    
    extended_data = cached_data['extended_data']
    # If cache exists but key fields are missing (old cache), try to fetch fresh data
    try:
        fr_missing = False
        fr = extended_data.get('financial_ratios', {}) or {}
        if fr.get('eps') is None:
            fr_missing = True
        if (extended_data.get('book_value') is None and extended_data.get('bookValue') is None and extended_data.get('bookValuePerShare') is None):
            fr_missing = True
        # also check volume averages
        vol = extended_data.get('volume_data', {}) or {}
        if vol.get('average_volume') is None or vol.get('average_volume_10days') is None:
            fr_missing = True

        if fr_missing and not force_refresh and not cache_hit:
            # attempt to fetch fresh extended data and prefer non-cached values
            try:
                fresh = get_extended_stock_data(stock.ticker_symbol)
                if fresh:
                    # merge fresh values into extended_data, favor fresh
                    merged = dict(extended_data)
                    for k, v in fresh.items():
                        if v is not None:
                            merged[k] = v
                    extended_data = merged
            except Exception:
                pass
    except Exception:
        # non-fatal: continue with cached data
        pass
    # Merge top-level short-interest keys into risk_metrics dict for schema compatibility
    def _to_int_safe(v):
        if v is None:
            return None
        try:
            return int(float(v))
        except Exception:
            return None

    def _to_float_safe(v):
        if v is None:
            return None
        try:
            return float(v)
        except Exception:
            return None

    risk_metrics_data = dict(extended_data.get('risk_metrics', {}) or {})
    # Common keys that may appear at top-level in yfinance dumps
    ss = _to_int_safe(extended_data.get('sharesShort'))
    sr = _to_float_safe(extended_data.get('shortRatio'))
    # Accept multiple common short-percent field names
    sp = _to_float_safe(extended_data.get('shortPercent') or extended_data.get('shortPercentOfFloat') or extended_data.get('shortPercentFloat'))
    if ss is not None:
        risk_metrics_data.setdefault('short_interest', ss)
    if sr is not None:
        risk_metrics_data.setdefault('short_ratio', sr)
    if sp is not None:
        risk_metrics_data.setdefault('short_percent', sp)
    # Include book value if present at top-level or inside common keys
    book_val = extended_data.get('book_value') or extended_data.get('bookValue') or extended_data.get('bookValuePerShare')

    # Normalize volume keys (accept several variants returned by different yfinance versions)
    vol_raw = extended_data.get('volume_data') or {}
    # Also allow top-level legacy keys
    vol_raw_top = extended_data
    avg = vol_raw.get('average_volume') or vol_raw.get('averageVolume') or vol_raw_top.get('averageVolume') or vol_raw_top.get('average_volume') or vol_raw_top.get('average_volume_10days')
    avg10 = vol_raw.get('average_volume_10days') or vol_raw.get('averageVolume10Days') or vol_raw_top.get('averageVolume10days') or vol_raw_top.get('ten_day_average_volume')

    volume_obj = schemas.VolumeData(
        volume=vol_raw.get('volume') or vol_raw_top.get('volume'),
        average_volume=_to_int_safe(avg),
        average_volume_10days=_to_int_safe(avg10)
    )

    return schemas.ExtendedStockData(
        business_summary=extended_data.get('business_summary'),
        financial_ratios=schemas.FinancialRatios(**extended_data.get('financial_ratios', {})),
        cashflow_data=schemas.CashflowData(**extended_data.get('cashflow_data', {})),
        dividend_info=schemas.DividendInfo(**extended_data.get('dividend_info', {})),
        price_data=schemas.PriceData(**extended_data.get('price_data', {})),
        volume_data=volume_obj,
        risk_metrics=schemas.RiskMetrics(**risk_metrics_data),
        book_value=book_val,
        enterprise_value=extended_data.get('enterprise_value') or extended_data.get('enterpriseValue'),
        website=extended_data.get('website') or extended_data.get('irWebsite') or extended_data.get('ir_website') or (extended_data.get('info_full') or {}).get('website'),
        ir_website=extended_data.get('irWebsite') or extended_data.get('ir_website') or extended_data.get('website')
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
        _getter = getattr(cache_service, 'get_cached_extended_data', None)
        if not callable(_getter):
            logger.warning(f"Cache service missing method get_cached_extended_data; cache_service={type(cache_service)}; attrs={[a for a in dir(cache_service) if not a.startswith('__')][:50]}")
            extended_data = None
        else:
            cached_data, cache_hit = _getter(stock_id, force_refresh)
            extended_data = cached_data.get('extended_data') if cached_data else None
        
            if not extended_data:
                # Fallback to direct API call if cache fails
                extended_data = get_extended_stock_data(stock.ticker_symbol)
            else:
                # If cached extended_data exists but lacks key fields (eps/book_value/volume averages), try a fresh fetch
                try:
                    fr = extended_data.get('financial_ratios', {}) or {}
                    vol = extended_data.get('volume_data', {}) or {}
                    missing_keys = (fr.get('eps') is None) or (extended_data.get('book_value') is None and extended_data.get('bookValue') is None and extended_data.get('bookValuePerShare') is None) or (vol.get('average_volume') is None or vol.get('average_volume_10days') is None)
                    if missing_keys and not force_refresh and not cache_hit:
                        fresh = get_extended_stock_data(stock.ticker_symbol)
                        if fresh:
                            merged = dict(extended_data)
                            for k, v in fresh.items():
                                if v is not None:
                                    merged[k] = v
                            extended_data = merged
                except Exception:
                    pass
    except Exception as e:
        # If cache fails, fallback to direct yfinance call
        import logging
        try:
            # If cache_service variable exists in scope, include its type and attributes for debugging
            cache_service_type = type(cache_service) if 'cache_service' in locals() else None
            cache_attrs = [a for a in dir(cache_service) if not a.startswith('__')] if 'cache_service' in locals() else []
        except Exception:
            cache_service_type = None
            cache_attrs = []
        logging.warning(f"Cache service failed for stock {stock_id}: {str(e)}; cache_service_type={cache_service_type}; sample_attrs={cache_attrs[:30]}")
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
        # Safely coerce possible top-level short-interest keys into risk_metrics
        def _to_int_safe(v):
            if v is None:
                return None
            try:
                return int(float(v))
            except Exception:
                return None

        def _to_float_safe(v):
            if v is None:
                return None
            try:
                return float(v)
            except Exception:
                return None

        risk_metrics_data = dict(extended_data.get('risk_metrics', {}) or {})
        ss = _to_int_safe(extended_data.get('sharesShort') or extended_data.get('sharesShortPriorMonth'))
        sr = _to_float_safe(extended_data.get('shortRatio'))
        sp = _to_float_safe(extended_data.get('shortPercent') or extended_data.get('shortPercentOfFloat') or extended_data.get('shortPercentFloat'))
        if ss is not None:
            risk_metrics_data.setdefault('short_interest', ss)
        if sr is not None:
            risk_metrics_data.setdefault('short_ratio', sr)
        if sp is not None:
            risk_metrics_data.setdefault('short_percent', sp)
        # Book value may be present at top-level or under different keys
        book_val = extended_data.get('book_value') or extended_data.get('bookValue') or extended_data.get('bookValuePerShare') or None

        # Normalize volume keys for compatibility
        vol_raw = extended_data.get('volume_data') or {}
        vol_raw_top = extended_data
        avg = vol_raw.get('average_volume') or vol_raw.get('averageVolume') or vol_raw_top.get('averageVolume') or vol_raw_top.get('average_volume')
        avg10 = vol_raw.get('average_volume_10days') or vol_raw.get('averageVolume10days') or vol_raw.get('averageVolume10Days') or vol_raw_top.get('averageVolume10days') or vol_raw_top.get('ten_day_average_volume')

        volume_obj = schemas.VolumeData(
            volume=vol_raw.get('volume') or vol_raw_top.get('volume'),
            average_volume=_to_int_safe(avg),
            average_volume_10days=_to_int_safe(avg10)
        )

        extended_data_obj = schemas.ExtendedStockData(
            business_summary=extended_data.get('business_summary'),
            financial_ratios=schemas.FinancialRatios(**extended_data.get('financial_ratios', {})),
            cashflow_data=schemas.CashflowData(**extended_data.get('cashflow_data', {})),
            dividend_info=schemas.DividendInfo(**extended_data.get('dividend_info', {})),
            price_data=schemas.PriceData(**extended_data.get('price_data', {})),
            volume_data=volume_obj,
            risk_metrics=schemas.RiskMetrics(**risk_metrics_data),
            book_value=book_val,
            enterprise_value=extended_data.get('enterprise_value') or extended_data.get('enterpriseValue'),
            website=extended_data.get('website') or extended_data.get('irWebsite') or extended_data.get('ir_website') or (extended_data.get('info_full') or {}).get('website'),
            ir_website=extended_data.get('irWebsite') or extended_data.get('ir_website') or extended_data.get('website')
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
        # ir_website will be populated from extended_data if present
        "ir_website": None,
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
    # Try to populate ir_website from extended_data (multiple possible keys)
    try:
        ir_website = None
        if extended_data and isinstance(extended_data, dict):
            ir_website = extended_data.get('irWebsite') or extended_data.get('ir_website') or extended_data.get('website') or (extended_data.get('info_full') or {}).get('website')
            ir_website = normalize_website_url(ir_website)
        # fallback to cache attached to stock model if available
        if not ir_website:
            try:
                cache_entry = getattr(stock, 'extended_cache', None)
                if cache_entry and getattr(cache_entry, 'extended_data', None):
                    ext = cache_entry.extended_data
                    ir_website = ext.get('irWebsite') or ext.get('ir_website') or ext.get('website') or (ext.get('info_full') or {}).get('website')
                    ir_website = normalize_website_url(ir_website)
            except Exception:
                ir_website = ir_website
        stock_dict['ir_website'] = ir_website
    except Exception:
        # don't fail response if website extraction fails
        pass

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
        _getter = getattr(cache_service, 'get_cached_extended_data', None)
        if not callable(_getter):
            logger.warning(f"Cache service missing method get_cached_extended_data; cache_service={type(cache_service)}; attrs={[a for a in dir(cache_service) if not a.startswith('__')][:50]}")
            extended_data = None
        else:
            cached_data, cache_hit = _getter(stock_id, force_refresh)
            extended_data = cached_data.get('extended_data') if cached_data else None
        
        if not extended_data:
            extended_data = get_extended_stock_data(stock.ticker_symbol)
    except Exception as e:
        logger.warning(f"Cache service failed for stock {stock_id}: {str(e)}")
        extended_data = get_extended_stock_data(stock.ticker_symbol)
    
    # Create extended data object
    extended_data_obj = None
    if extended_data:
        # Safely coerce possible top-level short-interest keys into risk_metrics
        def _to_int_safe(v):
            if v is None:
                return None
            try:
                return int(float(v))
            except Exception:
                return None

        def _to_float_safe(v):
            if v is None:
                return None
            try:
                return float(v)
            except Exception:
                return None

        risk_metrics_data = dict(extended_data.get('risk_metrics', {}) or {})
        ss = _to_int_safe(extended_data.get('sharesShort') or extended_data.get('sharesShortPriorMonth'))
        sr = _to_float_safe(extended_data.get('shortRatio'))
        sp = _to_float_safe(extended_data.get('shortPercent') or extended_data.get('shortPercentOfFloat') or extended_data.get('shortPercentFloat'))
        if ss is not None:
            risk_metrics_data.setdefault('short_interest', ss)
        if sr is not None:
            risk_metrics_data.setdefault('short_ratio', sr)
        if sp is not None:
            risk_metrics_data.setdefault('short_percent', sp)
        # Include book value when constructing ExtendedStockData
        book_val = extended_data.get('book_value') or extended_data.get('bookValue') or extended_data.get('bookValuePerShare') or None

        # Normalize volume keys for compatibility
        vol_raw = extended_data.get('volume_data') or {}
        vol_raw_top = extended_data
        avg = vol_raw.get('average_volume') or vol_raw.get('averageVolume') or vol_raw_top.get('averageVolume') or vol_raw_top.get('average_volume')
        avg10 = vol_raw.get('average_volume_10days') or vol_raw.get('averageVolume10days') or vol_raw.get('averageVolume10Days') or vol_raw_top.get('averageVolume10days') or vol_raw_top.get('ten_day_average_volume')

        volume_obj = schemas.VolumeData(
            volume=vol_raw.get('volume') or vol_raw_top.get('volume'),
            average_volume=_to_int_safe(avg),
            average_volume_10days=_to_int_safe(avg10)
        )

        extended_data_obj = schemas.ExtendedStockData(
            business_summary=extended_data.get('business_summary'),
            financial_ratios=schemas.FinancialRatios(**extended_data.get('financial_ratios', {})),
            cashflow_data=schemas.CashflowData(**extended_data.get('cashflow_data', {})),
            dividend_info=schemas.DividendInfo(**extended_data.get('dividend_info', {})),
            price_data=schemas.PriceData(**extended_data.get('price_data', {})),
            volume_data=volume_obj,
            risk_metrics=schemas.RiskMetrics(**risk_metrics_data),
            book_value=book_val,
            enterprise_value=extended_data.get('enterprise_value') or extended_data.get('enterpriseValue'),
            website=extended_data.get('website') or extended_data.get('irWebsite') or extended_data.get('ir_website') or (extended_data.get('info_full') or {}).get('website'),
            ir_website=extended_data.get('irWebsite') or extended_data.get('ir_website') or extended_data.get('website')
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
                historical_prices,
                display_period=period
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
    # Try to populate ir_website for this combined endpoint as well
    try:
        ir_website = None
        if extended_data and isinstance(extended_data, dict):
            ir_website = extended_data.get('irWebsite') or extended_data.get('ir_website') or extended_data.get('website') or (extended_data.get('info_full') or {}).get('website')
            ir_website = normalize_website_url(ir_website)
        if not ir_website:
            try:
                cache_entry = db.query(ExtendedStockDataCacheModel).filter(ExtendedStockDataCacheModel.stock_id == stock_id).first()
                if cache_entry and cache_entry.extended_data:
                    ext = cache_entry.extended_data
                    ir_website = ext.get('irWebsite') or ext.get('ir_website') or ext.get('website') or (ext.get('info_full') or {}).get('website')
                    ir_website = normalize_website_url(ir_website)
            except Exception:
                ir_website = ir_website
        if ir_website:
            stock_dict['ir_website'] = ir_website
    except Exception:
        pass
    
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


@router.get("/{stock_id}/seasonality")
def get_stock_seasonality(
    stock_id: int,
    years_back: Optional[int] = Query(15, description="Years to look back (use None for all)"),
    include_series: bool = Query(False, description="Include per-year monthly close series (up to 10 years)"),
    debug: bool = Query(False, description="Return debugging information in the response (dev only)"),
    db: Session = Depends(get_db)
):
    """
    Return monthly seasonality summary for a stock.

    Optional `include_series=true` returns an array of per-year monthly close series
    (newest first) for visualization when the requested window is reasonable (<=10 years).
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Use HistoricalPriceService to obtain a DataFrame of historical closes
    hist_service = HistoricalPriceService(db)
    df = hist_service.get_price_dataframe(stock_id)

    # Log request parameters and data availability at INFO so it's visible in standard dev output
    try:
        logger.info(f"Seasonality request stock_id={stock_id} years_back={years_back} include_series={include_series}")
        if df is None or df.empty:
            logger.info(f"No historical dataframe available for stock_id={stock_id}")
        else:
            logger.info(f"Historical dataframe for stock_id={stock_id}: rows={len(df)}, start={df.index.min()}, end={df.index.max()}, cols={list(df.columns)}")
    except Exception:
        # don't break on logging
        pass

    if df is None or df.empty:
        return {"seasonality": [], "series": [] if include_series else []}

    # Compute seasonalities for requested window. The service provides common windows.
    if years_back is None:
        results = get_all_seasonalities(df)
        season_df = results.get('all')
    elif years_back in (5, 10, 15):
        results = get_all_seasonalities(df)
        season_df = results.get(f'{years_back}y')
    else:
        # Compute ad-hoc window
        monthly_returns = calculate_monthly_returns(df)
        season_df = calculate_seasonality(monthly_returns, years_back=years_back)

    # Convert seasonality DataFrame to list of dicts
    try:
        seasonality = season_df.sort_values('month').to_dict(orient='records') if season_df is not None else []
    except Exception:
        seasonality = []

    series_out = []
    if include_series:
        # Only include per-year series for reasonably small windows (limit to 10 years)
        try:
            # Determine years to include (newest first)
            years = sorted(list(set(df.index.year)), reverse=True)
            logger.info(f"Computed years for series (pre-limit): {years}")
            # Limit to last 10 years
            years = years[:10]
            logger.info(f"Years used for series (post-limit): {years}")
            for y in years:
                monthly_closes = []
                for m in range(1, 13):
                    # find last available close for this year/month
                    mask = (df.index.year == y) & (df.index.month == m)
                    if mask.any():
                        # take last available
                        vals = df.loc[mask]['close'] if 'close' in df.columns else df.iloc[:, 0]
                        try:
                            val = float(vals.iloc[-1])
                        except Exception:
                            val = None
                    else:
                        val = None
                    monthly_closes.append(val)
                series_out.append({"year": int(y), "monthly_closes": monthly_closes})
        except Exception:
            series_out = []

    # Debug sample output
    try:
        logger.info(f"Seasonality result counts: seasonality_rows={len(seasonality) if seasonality is not None else 0}, series_count={len(series_out)}")
        if series_out:
            logger.info(f"Sample series first entry: {series_out[0]}" )
    except Exception:
        pass

    out = {"seasonality": seasonality, "series": series_out}
    # Provide availability metadata so the frontend can show why large windows may
    # return identical results (not enough history). This is non-breaking.
    try:
        available_years = sorted(list(set(df.index.year)), reverse=True)
        out["available_years"] = available_years
        out["available_range"] = {"start": str(df.index.min()), "end": str(df.index.max())}
    except Exception:
        out["available_years"] = []
        out["available_range"] = {"start": None, "end": None}
    if debug:
        try:
            years_pre = sorted(list(set(df.index.year)), reverse=True)
        except Exception:
            years_pre = []
        debug_obj = {
            "df_rows": len(df),
            "df_start": str(df.index.min()),
            "df_end": str(df.index.max()),
            "df_columns": list(df.columns),
            "years_pre_limit": years_pre,
            "years_used": years if include_series else [],
            "sample_series_first": series_out[0] if series_out else None
        }
        out["debug"] = debug_obj

    return out


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
        # Get current stock data (includes optional normalized timestamp)
        # prefer the wrapper that provides a normalized `timestamp` when available
        current_data = None
        try:
            current_data = get_fast_market_data_with_timestamp(stock.ticker_symbol)
        except Exception:
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
            _getter = getattr(cache_service, 'get_cached_extended_data', None)
            if not callable(_getter):
                logger.warning(f"Cache service missing method get_cached_extended_data during market update; cache_service={type(cache_service)}; attrs={[a for a in dir(cache_service) if not a.startswith('__')][:50]}")
                extended_data_result = None
            else:
                extended_data_result, _ = _getter(stock_id, force_refresh=True)
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
        data_obj = {
            "current_price": current_price,
            "pe_ratio": pe_ratio,
            "change": change,
            "change_percent": change_percent,
            "volume": volume,
            "date": price_date.isoformat() if isinstance(price_date, date) else str(price_date)
        }

        # If the service returned a normalized timestamp, include it
        if current_data and isinstance(current_data, dict):
            ts = current_data.get('timestamp') or current_data.get('last_updated')
            if ts:
                data_obj['timestamp'] = ts

        return {
            "success": True,
            "stock_id": stock_id,
            "ticker_symbol": stock.ticker_symbol,
            "data": data_obj,
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
