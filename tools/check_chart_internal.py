"""
Call get_chart_with_indicators internally and report first non-NaN index for sma_50 and sma_200 and rsi.
"""
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
            # non-float value, assume valid
            return i
    return None


def main():
    ticker = 'PL'
    data = get_chart_with_indicators(ticker_symbol=ticker, period='1y', interval='1d', indicators=['sma_50','sma_200','rsi'])
    if not data:
        print('No data returned')
        sys.exit(1)
    ind = data.get('indicators', {})
    for name in ['sma_50','sma_200','rsi']:
        series = ind.get(name)
        if series is None:
            print(f'{name}: missing')
            continue
        idx = first_non_nan_index(series)
        print(f'{name}: first_non_nan_index={idx} (len={len(series)})')

if __name__ == '__main__':
    main()
