import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure backend package is importable
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, repo_root)

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Watchlist, Stock, StockInWatchlist

client = TestClient(app)


def test_screener_returns_observation_reasons():
    """Integration test: insert a watchlist + stock + watchlist entry with observation_reasons
    and assert /screener/filters returns the concrete reasons.
    """
    session = SessionLocal()
    watchlist = None
    stock = None
    entry = None
    try:
        # Create a unique watchlist
        wl_name = f"test-wl-{uuid.uuid4().hex[:8]}"
        watchlist = Watchlist(name=wl_name, description="Temp test watchlist")
        session.add(watchlist)
        session.commit()
        session.refresh(watchlist)

        # Create a minimal stock record
        ticker = f"TST{uuid.uuid4().hex[:4].upper()}"
        stock = Stock(ticker_symbol=ticker, name="Test Stock for Screener")
        session.add(stock)
        session.commit()
        session.refresh(stock)

        # Add a StockInWatchlist entry with observation_reasons
        reasons = ["fundamentals", "chart_technical"]
        entry = StockInWatchlist(watchlist_id=watchlist.id, stock_id=stock.id, position=0, observation_reasons=reasons)
        session.add(entry)
        session.commit()

        # Now call the filters endpoint
        resp = client.get("/screener/filters")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        obs = body.get("observation_reasons") or []
        # Both reasons should be present
        for r in reasons:
            assert r in obs

        # Also call the screener run endpoint with the observation_reason filter and ensure our stock appears
        resp2 = client.get(f"/screener/run?observation_reason={reasons[0]}")
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert isinstance(body2, dict)
        results = body2.get('results') or []
        # There should be at least one result and one of them should match our ticker
        assert any((r.get('ticker_symbol') == ticker or r.get('ticker_symbol') == ticker.upper()) for r in results)

    finally:
        # Cleanup: remove created entries
        try:
            if entry and entry.id:
                session.delete(session.merge(entry))
                session.commit()
        except Exception:
            session.rollback()
        try:
            if stock and stock.id:
                session.delete(session.merge(stock))
                session.commit()
        except Exception:
            session.rollback()
        try:
            if watchlist and watchlist.id:
                session.delete(session.merge(watchlist))
                session.commit()
        except Exception:
            session.rollback()
        session.close()
