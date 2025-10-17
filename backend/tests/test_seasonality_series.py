import json
from fastapi.testclient import TestClient
import sys
import os

# Ensure backend package is importable
# Ensure repository root is on sys.path so 'backend' package can be imported
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, repo_root)

from backend.app.main import app

client = TestClient(app)


def test_seasonality_include_series():
    # This test assumes there's at least one stock in the DB; we'll attempt to find one via /stocks/ endpoint
    resp = client.get('/stocks/')
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if not data:
        # No stocks available: skip test
        return
    stock = data[0]
    stock_id = stock.get('id') or stock.get('stock_id') or stock.get('pk')
    assert stock_id is not None

    # Request seasonality with include_series
    r = client.get(f'/stocks/{stock_id}/seasonality?years_back=5&include_series=true')
    assert r.status_code == 200
    body = r.json()

    # Body should be an object with seasonality and series
    assert isinstance(body, dict)
    assert 'seasonality' in body
    assert isinstance(body['seasonality'], list)
    assert 'series' in body
    assert isinstance(body['series'], list)

    # series entries should have year and monthly_closes
    for s in body['series']:
        assert 'year' in s
        assert 'monthly_closes' in s
        assert isinstance(s['monthly_closes'], list)
        # monthly_closes should have length 12 (nulls allowed)
        assert len(s['monthly_closes']) == 12
