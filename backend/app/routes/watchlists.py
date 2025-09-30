from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app import schemas
from backend.app.models import Watchlist as WatchlistModel
from backend.app.database import get_db

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("/", response_model=List[schemas.Watchlist])
def get_watchlists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all watchlists"""
    watchlists = db.query(WatchlistModel).offset(skip).limit(limit).all()
    return watchlists


@router.get("/{watchlist_id}", response_model=schemas.WatchlistWithStocks)
def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Get a specific watchlist with all its stocks"""
    watchlist = db.query(WatchlistModel).filter(WatchlistModel.id == watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


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
