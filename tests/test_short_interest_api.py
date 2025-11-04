import pytest
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make repo importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.main import app
from backend.app.database import Base
from backend.app.database import get_db
from backend.app.models import Watchlist as WatchlistModel, Stock as StockModel

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_short_interest.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_stock(db_session):
    wl = WatchlistModel(name="Short Test WL", description="test")
    db_session.add(wl)
    db_session.commit()

    stock = StockModel(
        ticker_symbol="AAPL",
        name="Apple Inc.",
        isin="US0378331005",
    )
    db_session.add(stock)
    db_session.commit()
    return stock


def test_short_interest_exposed_in_extended_data(client, sample_stock):
    extended = {
        "extended_data": {
            "business_summary": "Test",
            "sharesShort": 5000000,
            "shortRatio": 3.5,
            "risk_metrics": {
                "beta": 1.1
            }
        }
    }

    patch_target = 'backend.app.routes.stocks.StockDataCacheService.get_cached_extended_data'
    with patch(patch_target, return_value=(extended, True)):
        resp = client.get(f"/api/stocks/{sample_stock.id}/detailed")
        if resp.status_code == 404:
            resp = client.get(f"/stocks/{sample_stock.id}/detailed")

        assert resp.status_code == 200
        data = resp.json()
        assert 'extended_data' in data
        rm = data['extended_data']['risk_metrics']
        assert rm.get('short_interest') == 5000000
        assert abs(rm.get('short_ratio') - 3.5) < 1e-6


def test_short_interest_exposed_in_detailed(client, sample_stock):
    # Patch cache getter to return sharesShort and shortRatio at top-level
    extended = {"extended_data": {"sharesShort": 123456, "shortRatio": 5.2}}
    patch_target = 'backend.app.routes.stocks.StockDataCacheService.get_cached_extended_data'
    with patch(patch_target, return_value=(extended, True)):
        resp = client.get(f"/api/stocks/{sample_stock.id}/detailed")
        if resp.status_code == 404:
            resp = client.get(f"/stocks/{sample_stock.id}/detailed")

        assert resp.status_code == 200
        data = resp.json()
        # Ensure nested extended_data -> risk_metrics contains short_interest and short_ratio
        rm = data.get('extended_data', {}).get('risk_metrics', {})
        assert rm.get('short_interest') == 123456
        assert abs(rm.get('short_ratio') - 5.2) < 1e-6
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
