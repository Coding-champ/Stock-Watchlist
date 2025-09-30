from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
from backend.app import schemas
from backend.app.models import Stock as StockModel, StockData as StockDataModel
from backend.app.database import get_db

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


@router.post("/{stock_id}/move", response_model=schemas.Stock)
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
