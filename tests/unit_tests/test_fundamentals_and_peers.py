import sys
import os
from fastapi.testclient import TestClient

# Ensure backend package is importable
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, repo_root)

from backend.app.main import app

client = TestClient(app)


def _get_first_stock_id():
    resp = client.get('/stocks/')
    if resp.status_code != 200:
        return None
    data = resp.json()
    if not data:
        return None
    stock = data[0]
    return stock.get('id') or stock.get('stock_id') or stock.get('pk')


def test_fundamentals_timeseries_structure():
    stock_id = _get_first_stock_id()
    if not stock_id:
        # No stocks available in DB for testing; skip
        return

    r = client.get(f'/stocks/{stock_id}/fundamentals/timeseries?metric=pe_ratio&period=1y')
    assert r.status_code == 200
    body = r.json()

    # Expected keys
    assert 'stock_id' in body
    assert 'metric' in body
    assert 'period' in body
    assert 'used_mock' in body
    assert 'series' in body
    assert isinstance(body['series'], list)

    # Series entries should have date and value
    for entry in body['series']:
        assert 'date' in entry
        assert 'value' in entry
        # value may be null or numeric - when present should be int/float
        if entry['value'] is not None:
            assert isinstance(entry['value'], (int, float))


def test_peers_endpoint_structure():
    stock_id = _get_first_stock_id()
    if not stock_id:
        return

    r = client.get(f'/stocks/{stock_id}/peers?metric=market_cap&by=sector&limit=5')
    assert r.status_code == 200
    body = r.json()

    assert 'stock_id' in body
    assert 'ticker' in body
    assert 'by' in body
    assert 'metric' in body
    assert 'used_mock' in body
    assert 'peers' in body
    assert isinstance(body['peers'], list)

    for p in body['peers']:
        assert 'name' in p
        assert 'ticker' in p
        assert 'value' in p
        # Ensure numeric when possible
        if p['value'] is not None:
            assert isinstance(p['value'], (int, float))
