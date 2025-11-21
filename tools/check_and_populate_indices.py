"""
Quick script to check which indices exist and populate price data for correlation matrix
"""
import sys
import os
# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

from backend.app.database import SessionLocal
from backend.app.models import MarketIndex, AssetPriceData, AssetType
from backend.app.services.index_service import IndexService

def main():
    db = SessionLocal()
    try:
        # Check existing indices
        indices = db.query(MarketIndex).all()
        print(f"\n=== Found {len(indices)} indices in database ===")
        for idx in indices:
            # Check if has price data
            price_count = db.query(AssetPriceData).filter(
                AssetPriceData.asset_type == AssetType.INDEX,
                AssetPriceData.ticker_symbol == idx.ticker_symbol
            ).count()
            print(f"  {idx.ticker_symbol:12} - {idx.name:40} ({price_count} price records)")
        
        # Load prices for indices that need it
        service = IndexService(db)
        target_symbols = ['^GSPC', '^IXIC', '^GDAXI', '^FTSE', '^N225']
        
        print(f"\n=== Checking target correlation indices ===")
        for symbol in target_symbols:
            idx = db.query(MarketIndex).filter(MarketIndex.ticker_symbol == symbol).first()
            if not idx:
                print(f"  ❌ {symbol} - NOT IN DATABASE (needs to be created first)")
                continue
            
            price_count = db.query(AssetPriceData).filter(
                AssetPriceData.asset_type == AssetType.INDEX,
                AssetPriceData.ticker_symbol == symbol
            ).count()
            
            if price_count == 0:
                print(f"  ⚠️  {symbol} - No price data, loading...")
                result = service.load_index_price_data(symbol, period="2y")
                if result["success"]:
                    print(f"      ✓ Loaded {result['count']} records")
                else:
                    print(f"      ✗ Failed: {result.get('error')}")
            else:
                print(f"  ✓ {symbol} - {price_count} records available")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
