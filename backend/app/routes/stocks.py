from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from backend.app import schemas
from backend.app.models import Stock as StockModel, StockData as StockDataModel, Watchlist as WatchlistModel
from backend.app.database import get_db
from backend.app.services.yfinance_service import get_stock_info, get_current_stock_data

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/", response_model=List[schemas.Stock])
def get_stocks(
    watchlist_id: Optional[int] = None,
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get stocks with optional filtering and sorting"""
    query = db.query(StockModel)
    
    if watchlist_id:
        query = query.filter(StockModel.watchlist_id == watchlist_id)
    
    # Apply sorting
    if sort_by:
        order_func = desc if sort_order.lower() == "desc" else asc
        if hasattr(StockModel, sort_by):
            query = query.order_by(order_func(getattr(StockModel, sort_by)))
    else:
        query = query.order_by(StockModel.position)
    
    stocks = query.offset(skip).limit(limit).all()
    
    # Attach latest stock data to each stock
    for stock in stocks:
        latest = db.query(StockDataModel).filter(
            StockDataModel.stock_id == stock.id
        ).order_by(desc(StockDataModel.timestamp)).first()
        stock.latest_data = latest
    
    return stocks


@router.get("/{stock_id}", response_model=schemas.Stock)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """Get a specific stock with its latest data"""
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get latest stock data
    latest = db.query(StockDataModel).filter(
        StockDataModel.stock_id == stock_id
    ).order_by(desc(StockDataModel.timestamp)).first()
    stock.latest_data = latest
    
    return stock


@router.post("/", response_model=schemas.Stock, status_code=201)
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    """Add a stock to a watchlist"""
    # Get the highest position in the watchlist
    max_position = db.query(StockModel).filter(
        StockModel.watchlist_id == stock.watchlist_id
    ).count()
    
    db_stock = StockModel(**stock.model_dump(), position=max_position)
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.put("/{stock_id}", response_model=schemas.Stock)
def update_stock(
    stock_id: int,
    stock: schemas.StockUpdate,
    db: Session = Depends(get_db)
):
    """Update a stock"""
    db_stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    update_data = stock.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_stock, field, value)
    
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.put("/{stock_id}/move", response_model=schemas.Stock)
def move_stock(
    stock_id: int,
    move_data: schemas.StockMove,
    db: Session = Depends(get_db)
):
    """Move a stock to another watchlist"""
    db_stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    old_watchlist_id = db_stock.watchlist_id
    db_stock.watchlist_id = move_data.target_watchlist_id
    
    # Set position in new watchlist
    if move_data.position is not None:
        db_stock.position = move_data.position
    else:
        # Move to end of new watchlist
        max_position = db.query(StockModel).filter(
            StockModel.watchlist_id == move_data.target_watchlist_id
        ).count()
        db_stock.position = max_position
    
    # Reorder stocks in old watchlist
    old_stocks = db.query(StockModel).filter(
        StockModel.watchlist_id == old_watchlist_id
    ).order_by(StockModel.position).all()
    for i, stock in enumerate(old_stocks):
        if stock.id != stock_id:
            stock.position = i
    
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.delete("/{stock_id}", status_code=204)
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    """Delete a stock"""
    db_stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    watchlist_id = db_stock.watchlist_id
    
    db.delete(db_stock)
    db.commit()
    
    # Reorder remaining stocks
    stocks = db.query(StockModel).filter(
        StockModel.watchlist_id == watchlist_id
    ).order_by(StockModel.position).all()
    for i, stock in enumerate(stocks):
        stock.position = i
    db.commit()
    
    return None


@router.post("/add-by-ticker", response_model=schemas.Stock, status_code=201)
def add_stock_by_ticker(stock_data: schemas.StockCreateByTicker, db: Session = Depends(get_db)):
    """
    Füge eine Aktie zur Watchlist hinzu, indem nur das Ticker-Symbol angegeben wird.
    Die restlichen Informationen werden über yfinance API abgerufen.
    """
    # Prüfe ob die Watchlist existiert
    watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == stock_data.watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # Hole Aktieninformationen von yfinance
    stock_info = get_stock_info(stock_data.ticker_symbol)
    if not stock_info:
        raise HTTPException(
            status_code=404, 
            detail=f"Stock with ticker '{stock_data.ticker_symbol}' not found"
        )
    
    # Prüfe ob die Aktie bereits in der Watchlist existiert
    existing_stock = db.query(StockModel).filter(
        StockModel.ticker_symbol == stock_data.ticker_symbol,
        StockModel.watchlist_id == stock_data.watchlist_id
    ).first()
    
    if existing_stock:
        raise HTTPException(
            status_code=400, 
            detail=f"Stock '{stock_data.ticker_symbol}' already exists in this watchlist"
        )
    
    # Bestimme die Position in der Watchlist
    max_position = db.query(StockModel).filter(
        StockModel.watchlist_id == stock_data.watchlist_id
    ).count()
    
    # Erstelle neue Aktie mit Daten von yfinance
    db_stock = StockModel(
        watchlist_id=stock_data.watchlist_id,
        ticker_symbol=stock_info.ticker,
        name=stock_info.name,
        isin=stock_info.isin or "",
        country=stock_info.country,
        industry=stock_info.industry,
        sector=stock_info.sector,
        position=max_position
    )
    
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    
    # Füge aktuelle Marktdaten hinzu, falls verfügbar
    if stock_info.current_price or stock_info.pe_ratio:
        stock_data_entry = StockDataModel(
            stock_id=db_stock.id,
            current_price=stock_info.current_price,
            pe_ratio=stock_info.pe_ratio
        )
        db.add(stock_data_entry)
        db.commit()
        db.refresh(stock_data_entry)
        db_stock.latest_data = stock_data_entry
    
    return db_stock


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


@router.post("/{stock_id}/update-market-data")
def update_stock_market_data(stock_id: int, db: Session = Depends(get_db)):
    """
    Aktualisiere die Marktdaten einer Aktie über yfinance
    """
    stock = db.query(StockModel).filter(StockModel.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Hole aktuelle Marktdaten
    market_data = get_current_stock_data(stock.ticker_symbol)
    if not market_data:
        raise HTTPException(
            status_code=400, 
            detail="Could not fetch market data for this stock"
        )
    
    # Erstelle neuen StockData Eintrag
    stock_data_entry = StockDataModel(
        stock_id=stock_id,
        current_price=market_data.get('current_price'),
        pe_ratio=market_data.get('pe_ratio')
    )
    
    db.add(stock_data_entry)
    db.commit()
    db.refresh(stock_data_entry)
    
    return {
        "message": "Market data updated successfully",
        "data": {
            "current_price": stock_data_entry.current_price,
            "pe_ratio": stock_data_entry.pe_ratio,
            "timestamp": stock_data_entry.timestamp
        }
    }
