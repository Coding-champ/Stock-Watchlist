"""
Admin script to refresh historical price data for stocks via the backend API.

Usage:
  - Refresh specific IDs:
      python scripts/admin_refresh_prices.py --ids 1,2,3 --period max --delay 2

  - Refresh IDs from a file (one id per line or CSV):
      python scripts/admin_refresh_prices.py --file ./ids.txt --period max --delay 2

  - Refresh all stocks known by the API (use with caution; may hit rate limits):
      python scripts/admin_refresh_prices.py --all --period max --delay 2

Notes:
  - Defaults: API base http://127.0.0.1:8080, period='max', delay=1s between calls
  - The script uses POST /stocks/{id}/price-history/refresh?period=<period>
  - Retries transient HTTP errors with exponential backoff
"""

import argparse
import time
import requests
import sys
from typing import List, Optional


DEFAULT_API = "http://127.0.0.1:8080"
REFRESH_PATH = "/stocks/{id}/price-history/refresh"
# A fallback older endpoint exists at /stock-data/{id}/refresh-history; script can try both if first fails
REFRESH_FALLBACK_PATH = "/stock-data/{id}/refresh-history"
GET_STOCKS_PATH = "/stocks"


def get_all_stock_ids(api_base: str) -> List[int]:
    """Fetch all stocks from the API and return their IDs."""
    url = api_base.rstrip('/') + GET_STOCKS_PATH
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        ids = [int(s['id']) for s in data if 'id' in s]
        return ids
    except Exception as e:
        print(f"Error fetching stocks list from {url}: {e}")
        return []


def refresh_one_stock(api_base: str, stock_id: int, period: str = 'max', max_retries: int = 3) -> Optional[dict]:
    """Call the refresh endpoint for a single stock. Tries primary path then fallback.

    Returns the JSON response on success, or None on unrecoverable failure.
    """
    api_base = api_base.rstrip('/')
    paths_to_try = [REFRESH_PATH.format(id=stock_id), REFRESH_FALLBACK_PATH.format(id=stock_id)]

    for path in paths_to_try:
        url = api_base + path
        params = {'period': period}
        attempt = 0
        backoff = 1.0
        while attempt <= max_retries:
            try:
                r = requests.post(url, params=params, timeout=60)
                # Accept both 200/202 as success depending on endpoint
                if r.status_code in (200, 202):
                    try:
                        return r.json()
                    except Exception:
                        return {'status_code': r.status_code, 'text': r.text}
                else:
                    print(f"Refresh failed for id={stock_id} on {url} (status={r.status_code}): {r.text}")
                    # For client errors (4xx) don't retry this path
                    if 400 <= r.status_code < 500:
                        break
                    # else treat as transient and retry
            except requests.exceptions.RequestException as e:
                print(f"Request error for id={stock_id} on {url}: {e}")
            attempt += 1
            time.sleep(backoff)
            backoff *= 2
        # try next path
    print(f"All refresh paths failed for id={stock_id}")
    return None


def refresh_ids(api_base: str, ids: List[int], period: str = 'max', delay: float = 1.0, verbose: bool = True):
    """Refresh a list of stock ids sequentially, with a delay between calls.

    Returns summary dict: { 'success': [ids], 'failed': [ids], 'details': {id: resp or None} }
    """
    summary = {'success': [], 'failed': [], 'details': {}}
    total = len(ids)
    for idx, sid in enumerate(ids, start=1):
        if verbose:
            print(f"[{idx}/{total}] Refreshing stock id={sid} (period={period})")
        resp = refresh_one_stock(api_base, sid, period=period)
        summary['details'][sid] = resp
        if resp:
            summary['success'].append(sid)
            if verbose:
                # Safely print some numbers from response if present
                try:
                    recs = resp.get('records_updated') if isinstance(resp, dict) else None
                    dr = resp.get('date_range') if isinstance(resp, dict) else None
                    print(f"  -> OK, records_updated={recs}, date_range={dr}")
                except Exception:
                    print("  -> OK (response received)")
        else:
            summary['failed'].append(sid)
            print(f"  -> FAILED for id={sid}")
        # delay unless last
        if idx < total and delay and delay > 0:
            time.sleep(delay)
    return summary


def parse_ids_from_file(path: str) -> List[int]:
    ids = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                # allow CSV style or one-per-line, strip comments
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue
                for part in line.split(','):
                    p = part.strip()
                    if not p:
                        continue
                    try:
                        ids.append(int(p))
                    except Exception:
                        print(f"Skipping invalid id: {p}")
    except Exception as e:
        print(f"Error reading ids from file {path}: {e}")
    return ids


def main(argv=None):
    parser = argparse.ArgumentParser(description="Admin: Refresh historical price data for stocks via backend API")
    parser.add_argument('--api-base', type=str, default=DEFAULT_API, help='Base URL for backend API (default: http://127.0.0.1:8080)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ids', type=str, help='Comma-separated list of stock IDs to refresh (e.g. 1,2,3)')
    group.add_argument('--file', type=str, help='Path to file with stock IDs (one per line or CSV)')
    group.add_argument('--all', action='store_true', help='Refresh all stocks returned by GET /stocks (use with caution)')
    parser.add_argument('--period', type=str, default='max', help="Period to request from yfinance: e.g. '1mo', '1y', '5y', 'max' (default: max)")
    parser.add_argument('--delay', type=float, default=1.0, help='Seconds to wait between refresh calls (default 1.0)')
    parser.add_argument('--no-prompt', action='store_true', help="Don't prompt for confirmation when --all is used")
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args(argv)

    api_base = args.api_base.rstrip('/')

    ids = []
    if args.ids:
        try:
            ids = [int(x.strip()) for x in args.ids.split(',') if x.strip()]
        except Exception:
            print("Invalid --ids format. Use comma-separated integers like: 1,2,3")
            sys.exit(2)
    elif args.file:
        ids = parse_ids_from_file(args.file)
    elif args.all:
        if not args.no_prompt:
            ans = input(f"You are about to refresh ALL stocks from {api_base}. This may be slow and hit rate limits. Continue? [y/N]: ")
            if ans.strip().lower() not in ('y', 'yes'):
                print('Aborted by user')
                sys.exit(0)
        ids = get_all_stock_ids(api_base)

    if not ids:
        print("No stock ids to refresh")
        sys.exit(0)

    print(f"Starting refresh for {len(ids)} stocks (period={args.period}) against {api_base}")
    summary = refresh_ids(api_base, ids, period=args.period, delay=args.delay, verbose=args.verbose)

    print('\nSummary:')
    print(f"  Success: {len(summary['success'])}")
    print(f"  Failed: {len(summary['failed'])}")
    if summary['failed']:
        print('Failed IDs:', ','.join(str(x) for x in summary['failed']))


if __name__ == '__main__':
    main()
