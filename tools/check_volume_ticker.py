"""
Check volumeMA10 availability internally for a given ticker using get_chart_with_indicators.
Usage:
  python tools/check_volume_ticker.py --ticker AAPL
"""
import argparse
import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.services.chart_core import get_chart_with_indicators
import numpy as np


def first_non_nan_index(arr):
    if not isinstance(arr, list):
        return None
    for i, v in enumerate(arr):
        try:
            if v is None:
                continue
            if isinstance(v, float) and np.isnan(v):
                continue
            return i
        except Exception:
            return i
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', required=True)
    parser.add_argument('--period', default='1y')
    parser.add_argument('--interval', default='1d')
    args = parser.parse_args()

    ticker = args.ticker
    data = get_chart_with_indicators(ticker_symbol=ticker, period=args.period, interval=args.interval, indicators=['sma_50','sma_200','rsi'], include_volume=True)
    if not data:
        print('No data returned')
        sys.exit(1)
    ind = data.get('indicators', {})
    vol_ma = ind.get('volumeMA10') or []
    idx = first_non_nan_index(vol_ma)
    print(f'volumeMA10: first_non_nan_index={idx} (len={len(vol_ma)})')
    # Also check chart_data top-level
    cd = data.get('chart_data', [])
    print('chart_data length:', len(cd))
    if cd:
        # print first 3 samples (keys only to keep output small)
        for i, sample in enumerate(cd[:3]):
            print(f'chart_data[{i}] keys:', list(sample.keys()))
            print(f'chart_data[{i}] volumeMA10:', sample.get('volumeMA10'))

if __name__ == '__main__':
    main()
