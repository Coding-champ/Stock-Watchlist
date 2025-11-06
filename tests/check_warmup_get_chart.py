import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'backend' package can be imported when running tests directly
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.yfinance.price_data import get_chart_data


def run_check():
    ticker = 'AAPL'
    period = '1mo'
    interval = '1d'
    indicators = ['sma_50', 'sma_200', 'rsi', 'macd']

    print(f"Requesting chart data for {ticker}, period={period}, interval={interval}, indicators={indicators}")
    try:
        result = get_chart_data(ticker, period=period, interval=interval, indicators=indicators)
    except Exception as e:
        print('ERROR during get_chart_data call:', e)
        return

    if not result:
        print('No result returned')
        return

    dates = result.get('dates', [])
    indicators_res = result.get('indicators', {})

    if not dates:
        print('No dates in result')
        return

    first_date = dates[0]
    last_date = dates[-1]
    print(f'First visible date: {first_date}, last date: {last_date}, total points: {len(dates)}')

    # For each requested indicator, print first and last non-None value and first index value
    def first_non_none(lst):
        for i, v in enumerate(lst):
            if v is not None:
                return i, v
        return None, None

    checks = []
    for ind in indicators:
        if ind == 'macd':
            macd = indicators_res.get('macd')
            if not macd:
                checks.append((ind, False, 'no macd'))
                continue
            macd_series = macd.get('macd', [])
            signal_series = macd.get('signal', [])
            hist_series = macd.get('hist', [])
            i_m, v_m = first_non_none(macd_series)
            i_s, v_s = first_non_none(signal_series)
            i_h, v_h = first_non_none(hist_series)
            checks.append((ind, (i_m == 0 and i_s == 0 and i_h == 0), f'first_idxs macd={i_m},{i_s},{i_h}'))
        else:
            series = indicators_res.get(ind)
            if series is None:
                checks.append((ind, False, 'missing series'))
                continue
            i, v = first_non_none(series)
            checks.append((ind, i == 0, f'first_idx={i}'))

    print('\nIndicator warmup checks:')
    for name, ok, msg in checks:
        print(f' - {name}: start_at_first_visible={ok} ({msg})')

    # Print sample of first 5 values for visual inspection
    print('\nSample values (first 5 indices):')
    for i in range(min(5, len(dates))):
        row = {'date': dates[i]}
        for ind in indicators:
            if ind == 'macd':
                macd = indicators_res.get('macd') or {}
                row['macd'] = {
                    'macd': _safe_get(macd.get('macd', []), i),
                    'signal': _safe_get(macd.get('signal', []), i),
                    'hist': _safe_get(macd.get('hist', []), i)
                }
            else:
                row[ind] = _safe_get(indicators_res.get(ind, []), i)
        print(json.dumps(row))


def _safe_get(lst, idx):
    try:
        return lst[idx]
    except Exception:
        return None


if __name__ == '__main__':
    run_check()
