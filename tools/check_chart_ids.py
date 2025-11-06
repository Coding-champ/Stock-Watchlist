"""
Try multiple stock IDs against the chart endpoint and report which ones return chart data.
"""
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

HOST = '127.0.0.1'
PORT = '8080'


def first_non_null_index(arr):
    if not isinstance(arr, list):
        return None
    for i, v in enumerate(arr):
        if v is not None:
            return i
    return None


def check_id(stock_id, period='1y', interval='1d'):
    url = f'http://{HOST}:{PORT}/stock-data/{stock_id}/chart?period={period}&interval={interval}&include_volume=false'
    req = Request(url)
    req.add_header('Accept', 'application/json')
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            data = json.loads(body)
            indicators = data.get('indicators', {})
            out = {'id': stock_id, 'ok': True}
            for name in ['sma_50', 'sma_200']:
                arr = indicators.get(name)
                if arr is None:
                    out[name] = None
                else:
                    out[name] = {
                        'length': len(arr),
                        'first_non_null_index': first_non_null_index(arr)
                    }
            return out
    except HTTPError as e:
        return {'id': stock_id, 'ok': False, 'status': e.code, 'detail': safe_read(e)}
    except URLError as e:
        return {'id': stock_id, 'ok': False, 'error': str(e.reason)}
    except Exception as e:
        return {'id': stock_id, 'ok': False, 'error': str(e)}


def safe_read(e):
    try:
        return e.read().decode('utf-8')
    except Exception:
        return ''


def main():
    results = []
    for i in range(1, 21):
        print(f'Checking id={i}...', end='')
        r = check_id(i)
        results.append(r)
        if r.get('ok'):
            print(' OK')
            s50 = r.get('sma_50')
            s200 = r.get('sma_200')
            print(f"  sma_50 first_non_null={s50.get('first_non_null_index') if s50 else 'missing'}, sma_200 first_non_null={s200.get('first_non_null_index') if s200 else 'missing'}")
        else:
            print(f" FAIL ({r.get('status') or r.get('error')})")
    # Print summary
    print('\nSummary:')
    for r in results:
        if r.get('ok'):
            print(f"id={r['id']} -> ok, sma_50={r.get('sma_50')}, sma_200={r.get('sma_200')}")
    sys.exit(0)

if __name__ == '__main__':
    main()
