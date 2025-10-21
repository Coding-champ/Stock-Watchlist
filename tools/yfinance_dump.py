"""
Simple helper script to dump yfinance data for a ticker as JSON.
Usage:
  python tools\yfinance_dump.py AAPL

It prints a JSON object with keys: ticker, fast_info, info (selected), history_last_index, history_tail (last few rows as list), and raw attributes where available.
"""
import sys
import json
import yfinance as yf

from datetime import datetime

KEYS_INFO = [
    'symbol', 'shortName', 'longName', 'currency', 'exchange', 'marketState',
    'regularMarketPrice', 'currentPrice', 'previousClose', 'open', 'dayHigh', 'dayLow',
    'volume', 'averageVolume', 'marketCap', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow',
    'fiftyDayAverage', 'twoHundredDayAverage', 'trailingPE', 'forwardPE', 'lastUpdated',
    'regularMarketTime', 'preMarketTime', 'postMarketTime'
]

HISTORY_PERIODS = ['1d', '5d', '1mo']

def to_serializable(obj):
    try:
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)
    except Exception:
        return repr(obj)


def dump_ticker(ticker_symbol: str, history_period: str = '1d') -> dict:
    t = yf.Ticker(ticker_symbol)

    out = {'ticker': ticker_symbol}

    # fast_info
    try:
        fi = getattr(t, 'fast_info', None)
        if fi is not None:
            # fast_info can be a simple object with attributes
            try:
                fast_dict = {k: to_serializable(getattr(fi, k)) for k in dir(fi) if not k.startswith('_') and not callable(getattr(fi, k))}
            except Exception:
                # fallback: try converting to dict
                fast_dict = dict(fi.__dict__) if hasattr(fi, '__dict__') else {}
            out['fast_info'] = fast_dict
        else:
            out['fast_info'] = None
    except Exception as e:
        out['fast_info_error'] = str(e)

    # info (selected keys)
    try:
        info = getattr(t, 'info', {}) or {}
        info_sel = {k: to_serializable(info.get(k)) for k in KEYS_INFO if k in info}
        out['info_selected'] = info_sel
        # Also include lastUpdated/raw if present
        out['info_raw_lastUpdated'] = to_serializable(info.get('lastUpdated')) if info.get('lastUpdated') else None
        out['info_raw_regularMarketTime'] = info.get('regularMarketTime') if info.get('regularMarketTime') else None
    except Exception as e:
        out['info_error'] = str(e)

    # full info (large) - include for debugging
    try:
        out['info_full'] = {k: to_serializable(v) for k, v in (getattr(t, 'info', {}) or {}).items()}
    except Exception as e:
        out['info_full_error'] = str(e)

    # raw attributes on ticker
    try:
        raw = {}
        for attr in ['recommendations', 'analyst_price_targets', 'actions']:
            try:
                val = getattr(t, attr, None)
                raw[attr] = to_serializable(val)
            except Exception:
                raw[attr] = None
        out['ticker_raw_attrs'] = raw
    except Exception as e:
        out['raw_attrs_error'] = str(e)

    # history
    try:
        out['history'] = {}
        for p in HISTORY_PERIODS:
            try:
                hist = t.history(period=p)
                if hist is not None and not hist.empty:
                    last_idx = hist.index[-1]
                    tail = []
                    for idx, row in hist.tail(5).iterrows():
                        rowd = {c: to_serializable(row[c]) for c in hist.columns}
                        rowd['index'] = to_serializable(idx)
                        tail.append(rowd)
                    out['history'][p] = {'last_index': to_serializable(last_idx), 'tail': tail}
                else:
                    out['history'][p] = {'last_index': None, 'tail': []}
            except Exception as e:
                out['history'][p] = {'error': str(e)}
    except Exception as e:
        out['history_error'] = str(e)

    # dividends, splits, actions, calendar, options
    try:
        try:
            out['dividends'] = to_serializable(getattr(t, 'dividends', None))
        except Exception as e:
            out['dividends_error'] = str(e)
        try:
            out['splits'] = to_serializable(getattr(t, 'splits', None))
        except Exception as e:
            out['splits_error'] = str(e)
        try:
            out['actions'] = to_serializable(getattr(t, 'actions', None))
        except Exception as e:
            out['actions_error'] = str(e)
        try:
            out['calendar'] = to_serializable(getattr(t, 'calendar', None))
        except Exception as e:
            out['calendar_error'] = str(e)
        try:
            opts = getattr(t, 'options', None)
            if opts:
                out['options'] = [to_serializable(o) for o in opts]
            else:
                out['options'] = None
        except Exception as e:
            out['options_error'] = str(e)
    except Exception:
        pass

    return out


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools\\yfinance_dump.py <TICKER> [history_period]')
        sys.exit(1)

    ticker_symbol = sys.argv[1]
    period = sys.argv[2] if len(sys.argv) > 2 else '1d'

    data = dump_ticker(ticker_symbol, history_period=period)
    print(json.dumps(data, indent=2, ensure_ascii=False))
