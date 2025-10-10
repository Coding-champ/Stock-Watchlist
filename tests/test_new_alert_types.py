"""
Tests for newly added alert types:
- percent_from_sma
- trailing_stop
- enhanced volume_spike options (baseline_days, use_zscore)

These tests validate that the alert service evaluates without errors and returns booleans.
They do not assert specific market conditions to avoid flakiness.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app.models import Stock, Alert as AlertModel
from backend.app.services.alert_service import AlertService


def _get_any_stock(db):
    return db.query(Stock).first()


def test_percent_from_sma_alert_evaluates():
    db = SessionLocal()
    try:
        stock = _get_any_stock(db)
        if not stock:
            print("Skipping: no stocks in DB")
            return
        alert = AlertModel(
            stock_id=stock.id,
            alert_type='percent_from_sma',
            condition='above',  # compares percent diff vs threshold
            threshold_value=0.0,  # 0% above/below boundary
            composite_conditions={"sma_period": 50},
            is_active=True,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        service = AlertService(db)
        result = service.check_single_alert(alert.id)
        assert 'is_triggered' in result
        assert isinstance(result['is_triggered'], bool)
    finally:
        # cleanup
        if 'alert' in locals() and alert.id:
            db.delete(alert)
            db.commit()
        db.close()


def test_trailing_stop_alert_evaluates():
    db = SessionLocal()
    try:
        stock = _get_any_stock(db)
        if not stock:
            print("Skipping: no stocks in DB")
            return
        alert = AlertModel(
            stock_id=stock.id,
            alert_type='trailing_stop',
            condition='below',  # not used; trailing stop uses threshold_value as percent
            threshold_value=10.0,  # 10% trail
            timeframe_days=60,     # track highest close over last 60 days
            is_active=True,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        service = AlertService(db)
        result = service.check_single_alert(alert.id)
        assert 'is_triggered' in result
        assert isinstance(result['is_triggered'], bool)
    finally:
        if 'alert' in locals() and alert.id:
            db.delete(alert)
            db.commit()
        db.close()


def test_volume_spike_zscore_option_evaluates():
    db = SessionLocal()
    try:
        stock = _get_any_stock(db)
        if not stock:
            print("Skipping: no stocks in DB")
            return
        alert = AlertModel(
            stock_id=stock.id,
            alert_type='volume_spike',
            condition='above',
            threshold_value=2.0,  # either 2x ratio or 2 std deviations if use_zscore
            composite_conditions={"baseline_days": 20, "use_zscore": True},
            is_active=True,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        service = AlertService(db)
        result = service.check_single_alert(alert.id)
        assert 'is_triggered' in result
        assert isinstance(result['is_triggered'], bool)
    finally:
        if 'alert' in locals() and alert.id:
            db.delete(alert)
            db.commit()
        db.close()
