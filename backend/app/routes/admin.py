from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.database import get_db
from backend.app.models import Stock, StockPriceData
from backend.app.services.historical_price_service import HistoricalPriceService
from backend.app.services.fundamental_data_service import FundamentalDataService
from backend.app.services.yfinance_service import get_stock_info

router = APIRouter(prefix="/admin", tags=["admin"])


def _expected_latest_trading_day() -> date:
    current = date.today()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def _asset_item(db: Session, stock: Stock) -> schemas.AdminAssetItem:
    latest = db.query(StockPriceData).filter(
        StockPriceData.stock_id == stock.id
    ).order_by(desc(StockPriceData.date)).first()
    expected = _expected_latest_trading_day()
    last_delivery = latest.date if latest else None
    return schemas.AdminAssetItem(
        id=stock.id,
        asset_type="stock",
        name=stock.name,
        ticker_symbol=stock.ticker_symbol,
        isin=stock.isin,
        data_source="yfinance",
        last_successful_delivery=last_delivery,
        expected_latest_trading_day=expected,
        quality_status="ok" if last_delivery and last_delivery >= expected else "missing",
        price_record_count=db.query(StockPriceData).filter(
            StockPriceData.stock_id == stock.id
        ).count(),
        is_active=stock.is_active,
    )


@router.get("/assets", response_model=schemas.AdminAssetListResponse)
def list_admin_assets(
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
):
    query = db.query(Stock)
    if not include_archived:
        query = query.filter(Stock.is_active.is_(True))
    assets = query.order_by(Stock.name.asc()).all()
    return {"items": [_asset_item(db, stock) for stock in assets], "total": len(assets)}


@router.put("/assets/{stock_id}", response_model=schemas.Stock)
def update_admin_asset(
    stock_id: int,
    payload: schemas.AdminAssetUpdate,
    db: Session = Depends(get_db),
):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Asset not found")
    values = payload.model_dump(exclude_unset=True)
    if "ticker_symbol" in values:
        values["ticker_symbol"] = values["ticker_symbol"].strip().upper()
    for field, value in values.items():
        setattr(stock, field, value)
    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/assets/{stock_id}", status_code=204)
def archive_admin_asset(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Asset not found")
    stock.is_active = False
    db.commit()


@router.post("/assets/{stock_id}/restore", response_model=schemas.Stock)
def restore_admin_asset(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Asset not found")
    stock.is_active = True
    db.commit()
    db.refresh(stock)
    return stock


@router.post("/assets/{stock_id}/reload", response_model=schemas.AdminAssetItem)
def reload_admin_asset(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Asset not found")
    result = HistoricalPriceService(db).load_and_save_historical_prices(
        stock_id, period="1mo", interval="1d"
    )
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Data reload failed"))
    return _asset_item(db, stock)


@router.post("/assets/reload-all", response_model=dict)
def reload_all_admin_assets(db: Session = Depends(get_db)):
    assets = db.query(Stock).filter(Stock.is_active.is_(True)).order_by(Stock.id.asc()).all()
    refreshed = []
    failed = []
    service = HistoricalPriceService(db)
    for stock in assets:
        result = service.load_and_save_historical_prices(
            stock.id, period="1mo", interval="1d"
        )
        if result.get("success"):
            refreshed.append(stock.ticker_symbol)
        else:
            failed.append({
                "ticker_symbol": stock.ticker_symbol,
                "error": result.get("error", "Data reload failed"),
            })
    return {
        "success": not failed,
        "total": len(assets),
        "refreshed": len(refreshed),
        "failed": len(failed),
        "refreshed_tickers": refreshed,
        "failures": failed,
    }


@router.post("/assets/reload-selected", response_model=dict)
def reload_selected_admin_assets(
    stock_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    assets = db.query(Stock).filter(
        Stock.id.in_(stock_ids),
        Stock.is_active.is_(True),
    ).order_by(Stock.id.asc()).all()
    found_ids = {stock.id for stock in assets}
    failures = [
        {"stock_id": stock_id, "error": "Asset not found or inactive"}
        for stock_id in stock_ids
        if stock_id not in found_ids
    ]
    refreshed = []
    service = HistoricalPriceService(db)
    for stock in assets:
        result = service.load_and_save_historical_prices(
            stock.id, period="1mo", interval="1d"
        )
        if result.get("success"):
            refreshed.append(stock.ticker_symbol)
        else:
            failures.append({
                "stock_id": stock.id,
                "ticker_symbol": stock.ticker_symbol,
                "error": result.get("error", "Data reload failed"),
            })
    return {
        "success": not failures,
        "total": len(stock_ids),
        "refreshed": len(refreshed),
        "failed": len(failures),
        "refreshed_tickers": refreshed,
        "failures": failures,
    }


@router.post("/assets/import", response_model=schemas.AdminAssetItem, status_code=201)
def import_admin_asset(payload: schemas.AdminAssetImport, db: Session = Depends(get_db)):
    ticker = payload.ticker_symbol.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")
    stock = db.query(Stock).filter(Stock.ticker_symbol == ticker).first()
    if not stock:
        info = get_stock_info(ticker)
        if not info:
            raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")
        stock = Stock(
            ticker_symbol=ticker,
            name=info.name or ticker,
            isin=info.isin,
            country=info.country,
            industry=info.industry,
            sector=info.sector,
            business_summary=info.business_summary,
        )
        db.add(stock)
        db.flush()
    else:
        stock.is_active = True
    price_result = HistoricalPriceService(db).load_and_save_historical_prices(
        stock.id, period=payload.period, interval=payload.interval
    )
    if not price_result.get("success"):
        db.rollback()
        raise HTTPException(status_code=502, detail=price_result.get("error", "Historical data import failed"))
    FundamentalDataService(db).load_and_save_fundamental_data(stock.id)
    db.refresh(stock)
    return _asset_item(db, stock)
