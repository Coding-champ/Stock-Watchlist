import os
import sys
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make repo importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Disable background scheduler during tests
os.environ["ENABLE_SCHEDULER"] = "false"

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import MarketIndex, Stock, IndexConstituent, StockPriceData

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_breadth_modes.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
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


def _get(client: TestClient, path: str):
    # Some deployments use /api prefix; keep tests resilient.
    resp = client.get(path)
    if resp.status_code == 404:
        resp = client.get("/api" + path)
    return resp


def test_breadth_classic_snapshot_counts(client, db_session):
    idx = MarketIndex(ticker_symbol="^TEST", name="Test Index", region="US", index_type="broad_market")
    s1 = Stock(ticker_symbol="AAA", name="AAA")
    s2 = Stock(ticker_symbol="BBB", name="BBB")
    db_session.add_all([idx, s1, s2])
    db_session.flush()

    db_session.add_all(
        [
            IndexConstituent(index_id=idx.id, stock_id=s1.id, status="active", weight=0.5, date_added=date.today()),
            IndexConstituent(index_id=idx.id, stock_id=s2.id, status="active", weight=0.5, date_added=date.today()),
        ]
    )

    # Two days of daily closes so classic mode can compare latest to prior.
    d0 = date(2025, 12, 19)
    d1 = date(2025, 12, 20)
    db_session.add_all(
        [
            StockPriceData(stock_id=s1.id, date=d0, close=100.0),
            StockPriceData(stock_id=s1.id, date=d1, close=110.0),
            StockPriceData(stock_id=s2.id, date=d0, close=200.0),
            StockPriceData(stock_id=s2.id, date=d1, close=190.0),
        ]
    )
    db_session.flush()

    resp = _get(client, "/indices/%5ETEST/breadth?mode=classic")
    assert resp.status_code == 200
    data = resp.json()
    adv = data["advance_decline"]
    assert adv["advancing"] == 1
    assert adv["declining"] == 1
    assert adv["unchanged"] == 0
    assert adv["total_count"] == 2
    assert abs(adv["percentage_advancing"] - 50.0) < 1e-6


def test_breadth_mcclellan_history_includes_oscillator(client, db_session):
    # Seed same minimal dataset for this test (transaction is rolled back after test)
    idx = MarketIndex(ticker_symbol="^TEST", name="Test Index", region="US", index_type="broad_market")
    s1 = Stock(ticker_symbol="AAA", name="AAA")
    s2 = Stock(ticker_symbol="BBB", name="BBB")
    db_session.add_all([idx, s1, s2])
    db_session.flush()
    db_session.add_all(
        [
            IndexConstituent(index_id=idx.id, stock_id=s1.id, status="active", weight=0.5, date_added=date.today()),
            IndexConstituent(index_id=idx.id, stock_id=s2.id, status="active", weight=0.5, date_added=date.today()),
        ]
    )
    d0 = date(2025, 12, 19)
    d1 = date(2025, 12, 20)
    db_session.add_all(
        [
            StockPriceData(stock_id=s1.id, date=d0, close=100.0),
            StockPriceData(stock_id=s1.id, date=d1, close=110.0),
            StockPriceData(stock_id=s2.id, date=d0, close=200.0),
            StockPriceData(stock_id=s2.id, date=d1, close=190.0),
        ]
    )
    db_session.flush()

    resp = _get(client, "/indices/%5ETEST/breadth/history?days=10&mode=mcclellan")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("mode") == "mcclellan"
    assert "records" in data
    assert "mcclellan_oscillator" in data
    assert isinstance(data["mcclellan_oscillator"], list)
