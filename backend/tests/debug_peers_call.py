from fastapi.testclient import TestClient
import json
import sys
import os

# Ensure repo root on path (tests run may already set this)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, repo_root)

from backend.app.main import app

client = TestClient(app)


def main():
    r = client.get('/stocks/')
    print('GET /stocks/ ->', r.status_code)
    try:
        stocks = r.json()
    except Exception as e:
        print('Failed to parse /stocks/ response', e)
        return

    print('Stocks returned:', len(stocks))
    if not stocks:
        print('No stocks in DB — cannot inspect peers')
        return

    stock = stocks[0]
    stock_id = stock.get('id') or stock.get('stock_id') or stock.get('pk')
    print('Using stock id:', stock_id, 'ticker:', stock.get('ticker_symbol') or stock.get('ticker'))

    r2 = client.get(f'/stocks/{stock_id}/peers?metric=market_cap&by=sector&limit=8')
    print('\nGET /stocks/{id}/peers ->', r2.status_code)
    try:
        body = r2.json()
    except Exception as e:
        print('Failed to parse peers response', e)
        print(r2.text)
        return

    print(json.dumps(body, indent=2, ensure_ascii=False))

    print('\nPeer value types:')
    for p in body.get('peers', []):
        v = p.get('value')
        print(p.get('ticker'), '->', type(v), v)


if __name__ == '__main__':
    main()
