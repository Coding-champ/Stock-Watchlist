import traceback
import os
import sys
# Make repo importable when running from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.database import SessionLocal
from backend.app.services.persistent_cache_service import StockDataCacheService

if __name__ == '__main__':
    s = SessionLocal()
    svc = StockDataCacheService(s)
    try:
        res, hit = svc.get_cached_extended_data(1, True)
        print('RESULT HIT=', hit)
        if res and 'extended_data' in res:
            rd = res['extended_data']
            rm = rd.get('risk_metrics') if isinstance(rd, dict) else None
            print('risk_metrics keys:', list(rm.keys()) if rm else None)
            print('short_interest:', rm.get('short_interest') if rm else None)
            print('short_ratio:', rm.get('short_ratio') if rm else None)
            print('short_percent:', rm.get('short_percent') if rm else None)
        else:
            print('no extended_data returned')
    except Exception as e:
        print('EXCEPTION:')
        traceback.print_exc()
    finally:
        s.close()
