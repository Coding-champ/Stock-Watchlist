"""
Load price data for index constituents
Populates asset_price_data table for stocks in index constituents
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Setup path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.services.index_service import IndexService
from backend.app.services.index_constituent_service import IndexConstituentService
from backend.app.services.asset_price_service import AssetPriceService
from backend.app.models import AssetType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_constituent_prices(
    db: Session,
    ticker_symbol: str = None,
    period: str = "1mo",
    interval: str = "1d",
    limit_constituents: int = None
):
    """
    Load price data for constituents of an index (or all indices)
    
    Args:
        db: Database session
        ticker_symbol: Specific index ticker (e.g., '^GSPC') or None for all
        period: Time period to load ('1d', '1mo', '3mo', '1y', 'max')
        interval: Data interval ('1d', '1wk', '1mo')
        limit_constituents: Max number of constituents to process per index
    """
    index_service = IndexService(db)
    constituent_service = IndexConstituentService(db)
    price_service = AssetPriceService(db)
    
    # Get indices to process
    if ticker_symbol:
        index = index_service.get_index_by_symbol(ticker_symbol)
        if not index:
            logger.error(f"Index {ticker_symbol} not found")
            return
        indices = [index]
    else:
        indices = index_service.get_all_indices()
    
    logger.info(f"Processing {len(indices)} index/indices")
    
    total_stocks = 0
    total_success = 0
    total_failed = 0
    
    for index in indices:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {index.name} ({index.ticker_symbol})")
        logger.info(f"{'='*60}")
        
        # Get active constituents
        constituents = constituent_service.get_active_constituents(index.id)
        logger.info(f"Found {len(constituents)} active constituents")
        
        if limit_constituents:
            constituents = constituents[:limit_constituents]
            logger.info(f"Limited to first {limit_constituents} constituents")
        
        # Load price data for each constituent
        for i, constituent in enumerate(constituents, 1):
            stock = constituent.stock
            ticker = stock.ticker_symbol
            
            logger.info(f"[{i}/{len(constituents)}] Loading {ticker} ({stock.name})...")
            
            try:
                result = price_service.load_and_save_price_data(
                    ticker_symbol=ticker,
                    asset_type=AssetType.STOCK,
                    period=period,
                    interval=interval
                )
                
                if result.get("success"):
                    total_success += 1
                    logger.info(f"  ✓ Saved {result.get('count', 0)} records")
                    if result.get("date_range"):
                        dr = result["date_range"]
                        logger.info(f"    Range: {dr.get('start')} to {dr.get('end')}")
                else:
                    total_failed += 1
                    logger.warning(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                
                total_stocks += 1
                
            except Exception as e:
                total_failed += 1
                logger.error(f"  ✗ Error loading {ticker}: {e}")
        
        logger.info(f"\nCompleted {index.ticker_symbol}")
        logger.info(f"  Processed: {len(constituents)} stocks")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total stocks processed: {total_stocks}")
    logger.info(f"Successful: {total_success}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Success rate: {(total_success/total_stocks*100) if total_stocks > 0 else 0:.1f}%")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load price data for index constituents")
    parser.add_argument(
        "--index",
        type=str,
        default=None,
        help="Specific index ticker symbol (e.g., '^GSPC'), or leave empty for all indices"
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1mo",
        choices=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        help="Time period to load (default: 1mo)"
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        choices=["1d", "1wk", "1mo"],
        help="Data interval (default: 1d)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of constituents per index (useful for testing)"
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        logger.info("Starting constituent price data loader")
        logger.info(f"Index: {args.index or 'ALL'}")
        logger.info(f"Period: {args.period}")
        logger.info(f"Interval: {args.interval}")
        if args.limit:
            logger.info(f"Limit: {args.limit} constituents per index")
        
        load_constituent_prices(
            db=db,
            ticker_symbol=args.index,
            period=args.period,
            interval=args.interval,
            limit_constituents=args.limit
        )
        
        logger.info("\nCompleted successfully!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
