"""
Simple script to query the local chart endpoint and report
first non-null indices for sma_50 and sma_200.

Usage:
  python tools/check_chart_indicators.py --stock-id 1 --period 1y --interval 1d

The script uses urllib (no external deps) so it should run in most envs.
"""
import argparse
import json
import sys
try:
    # Python 3
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except Exception:
    print("urllib not available")
    sys.exit(1)


def first_non_null_index(arr):
    if not isinstance(arr, list):
        return None
    for i, v in enumerate(arr):
        if v is not None:
            return i
    return None


def summarize_indicator(arr, name, show=40):
    idx = first_non_null_index(arr)
    leading_nulls = idx if idx is not None else len(arr) if isinstance(arr, list) else None
    sample = arr[:show] if isinstance(arr, list) else []
    return {
        'name': name,
        'length': len(arr) if isinstance(arr, list) else 0,
        'first_non_null_index': idx,
        'leading_nulls': leading_nulls,
        'sample_first_values': sample
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', help='API host')
    parser.add_argument('--port', default='8080', help='API port')
    parser.add_argument('--stock-id', type=int, default=1, help='Stock id to query')
    parser.add_argument('--period', default='1y', help='Period for chart (e.g. 1y)')
    parser.add_argument('--interval', default='1d', help='Interval (e.g. 1d)')
    parser.add_argument('--include-volume', action='store_true', help='Include volume param')
    args = parser.parse_args()

    host = args.host
    port = args.port
    stock_id = args.stock_id
    period = args.period
    interval = args.interval
    include_volume = 'true' if args.include_volume else 'false'

    url = f'http://{host}:{port}/stock-data/{stock_id}/chart?period={period}&interval={interval}&include_volume={include_volume}'
    print(f'Requesting: {url}')

    req = Request(url)
    req.add_header('Accept', 'application/json')
    try:
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            data = json.loads(body)
    except HTTPError as e:
        print(f'HTTP error: {e.code} {e.reason}')
        try:
            print(e.read().decode('utf-8'))
        except Exception:
            pass
        sys.exit(2)
    except URLError as e:
        print(f'Connection error: {e.reason}')
        sys.exit(3)
    except Exception as e:
        print(f'Unexpected error: {e}')
        sys.exit(4)

    indicators = data.get('indicators', {})
    dates = data.get('dates', [])
    close = data.get('close', [])
    print(f'Got {len(dates)} dates, {len(close)} close values')

    results = []
    for name in ['sma_50', 'sma_200']:
        arr = indicators.get(name)
        if arr is None:
            print(f'Indicator {name} not present in response')
            results.append({ 'name': name, 'present': False })
            continue
        summary = summarize_indicator(arr, name, show=40)
        print(f"Indicator {name}: length={summary['length']}, first_non_null_index={summary['first_non_null_index']}, leading_nulls={summary['leading_nulls']}")
        print(f"Sample first values ({len(summary['sample_first_values'])}): {summary['sample_first_values']}")
        results.append(summary)

    # Also print a short macd/rsi check
    if 'rsi' in indicators:
        rsi_idx = first_non_null_index(indicators.get('rsi', []))
        print(f"RSI first_non_null_index={rsi_idx}")
    if 'macd' in indicators and isinstance(indicators['macd'], dict):
        macd_series = indicators['macd'].get('macd', [])
        macd_idx = first_non_null_index(macd_series)
        print(f"MACD first_non_null_index={macd_idx}")

    # Exit 0 for success
    sys.exit(0)

if __name__ == '__main__':
    main()
