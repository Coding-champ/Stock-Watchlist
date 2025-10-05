from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app import schemas
from backend.app.models import Alert as AlertModel
from backend.app.database import get_db
from backend.app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[schemas.Alert])
def get_alerts(
    stock_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering"""
    query = db.query(AlertModel)
    
    if stock_id is not None:
        query = query.filter(AlertModel.stock_id == stock_id)
    
    if is_active is not None:
        query = query.filter(AlertModel.is_active == is_active)
    
    alerts = query.offset(skip).limit(limit).all()
    return alerts


@router.get("/{alert_id}", response_model=schemas.Alert)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert"""
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/", response_model=schemas.Alert, status_code=201)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert"""
    from backend.app.models import Stock
    
    # Convert stock_symbol to stock_id if needed
    stock_id = alert.stock_id
    if stock_id is None and alert.stock_symbol:
        stock = db.query(Stock).filter(Stock.ticker_symbol == alert.stock_symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {alert.stock_symbol} not found")
        stock_id = stock.id
    
    if stock_id is None:
        raise HTTPException(status_code=400, detail="Either stock_id or stock_symbol must be provided")
    
    # Use threshold if threshold_value not provided
    threshold_value = alert.threshold_value if alert.threshold_value is not None else alert.threshold
    if threshold_value is None:
        threshold_value = 0.0  # Default for composite alerts
    
    # Prepare data for database
    alert_data = {
        'stock_id': stock_id,
        'alert_type': alert.alert_type,
        'condition': alert.condition,
        'threshold_value': threshold_value,
        'timeframe_days': alert.timeframe_days,
        'composite_conditions': alert.composite_conditions,
        'is_active': alert.is_active,
        'expiry_date': alert.expiry_date,
        'notes': alert.notes
    }
    
    db_alert = AlertModel(**alert_data)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


@router.put("/{alert_id}", response_model=schemas.Alert)
def update_alert(
    alert_id: int,
    alert: schemas.AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert"""
    db_alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    update_data = alert.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_alert, field, value)
    
    db.commit()
    db.refresh(db_alert)
    return db_alert


@router.delete("/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert"""
    db_alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(db_alert)
    db.commit()
    return None


@router.post("/check-all")
def check_all_alerts(db: Session = Depends(get_db)):
    """Check all active alerts and return triggered ones"""
    alert_service = AlertService(db)
    result = alert_service.check_all_active_alerts()
    return result


@router.post("/check/{alert_id}")
def check_single_alert(alert_id: int, db: Session = Depends(get_db)):
    """Check a specific alert manually"""
    alert_service = AlertService(db)
    result = alert_service.check_single_alert(alert_id)
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result
