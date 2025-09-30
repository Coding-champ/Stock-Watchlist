from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app import schemas
from backend.app.models import StockData as StockDataModel
from backend.app.database import get_db

router = APIRouter(prefix="/stock-data", tags=["stock-data"])


@router.get("/{stock_id}", response_model=List[schemas.StockData])
def get_stock_data(stock_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get historical data for a stock"""
    stock_data = db.query(StockDataModel).filter(
        StockDataModel.stock_id == stock_id
    ).order_by(StockDataModel.timestamp.desc()).offset(skip).limit(limit).all()
    return stock_data


@router.post("/", response_model=schemas.StockData, status_code=201)
def create_stock_data(stock_data: schemas.StockDataCreate, db: Session = Depends(get_db)):
    """Create new stock data entry"""
    db_stock_data = StockDataModel(**stock_data.model_dump())
    db.add(db_stock_data)
    db.commit()
    db.refresh(db_stock_data)
    return db_stock_data
