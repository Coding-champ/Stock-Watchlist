import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make repo importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.main import app
from backend.app.database import Base
from backend.app.database import get_db
from backend.app.models import Watchlist as WatchlistModel, Stock as StockModel

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_extended_data.db"
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
    wl = WatchlistModel(name="Ext Test WL", description="test")
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


def test_extended_fields_exposed_in_detailed(client, sample_stock):
    # Build an extended_data payload that contains the new keys
    extended = {
        "extended_data": {
            "business_summary": "Test",
            "enterprise_value": 1234567890,
            "financial_ratios": {
                "gross_margins": 0.45,
                "ebitda_margins": 0.30,
                "earnings_growth": 0.12,
                "revenue_growth": 0.08
            },
            "dividend_info": {
                "last_dividend_value": 0.25,
                "last_dividend_date": 1700000000
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

        ext = data['extended_data']
        # enterprise_value as top-level on ExtendedStockData
        assert ext.get('enterprise_value') == 1234567890

        fr = ext.get('financial_ratios') or {}
        # gross and ebitda margins available and numeric
        assert abs(fr.get('gross_margins') - 0.45) < 1e-6
        assert abs(fr.get('ebitda_margins') - 0.30) < 1e-6

        div = ext.get('dividend_info') or {}
        assert abs(div.get('last_dividend_value') - 0.25) < 1e-6
        assert div.get('last_dividend_date') == 1700000000
