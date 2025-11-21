"""
Calculate and update index constituent weights
Automatically determines weights based on market capitalization
"""

import sys
from pathlib import Path
import logging
import argparse

# Setup path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.services.index_service import IndexService
from backend.app.services.index_weight_calculator import IndexWeightCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_weights(
    db: Session,
    ticker_symbol: str = None,
    method: str = "market_cap",
    dry_run: bool = False
):
    """
    Calculate weights for index constituents
    
    Args:
        db: Database session
        ticker_symbol: Specific index ticker (e.g., '^GSPC') or None for all
        method: Calculation method ('market_cap' or 'equal')
        dry_run: If True, only show what would be updated without saving
    """
    index_service = IndexService(db)
    calculator = IndexWeightCalculator(db)
    
    if ticker_symbol:
        # Calculate for specific index
        index = index_service.get_index_by_symbol(ticker_symbol)
        if not index:
            logger.error(f"Index {ticker_symbol} not found")
            return
        
        logger.info(f"Calculating weights for: {index.name} ({ticker_symbol})")
        logger.info(f"Method: {method}")
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be saved")
        
        if method == "market_cap":
            result = calculator.calculate_market_cap_weights(index.id, refresh_market_caps=True)
        elif method == "equal":
            result = calculator.calculate_equal_weights(index.id)
        else:
            logger.error(f"Unknown method: {method}")
            return
        
        # Display results
        if result.get("success"):
            logger.info(f"\n{'='*60}")
            logger.info(f"SUCCESS - {result['index']}")
            logger.info(f"{'='*60}")
            logger.info(f"Updated: {result['updated']} constituents")
            
            if result.get('failed'):
                logger.warning(f"Failed: {result['failed']} constituents")
                if result.get('failed_tickers'):
                    logger.warning(f"  Tickers: {', '.join(result['failed_tickers'][:10])}")
            
            if result.get('total_market_cap'):
                logger.info(f"Total Market Cap: ${result['total_market_cap']:,.0f}")
            
            if result.get('equal_weight'):
                logger.info(f"Equal Weight: {result['equal_weight']:.4f}%")
            
            # Show top weights
            if result.get('weights'):
                logger.info(f"\nTop 10 Weights:")
                for i, w in enumerate(result['weights'], 1):
                    old = f"{w['old_weight']:.2f}%" if w['old_weight'] else "N/A"
                    new = f"{w['new_weight']:.2f}%"
                    change = ""
                    if w['old_weight']:
                        diff = w['new_weight'] - w['old_weight']
                        change = f" ({diff:+.2f}%)"
                    logger.info(f"  {i:2d}. {w['ticker']:6s}: {old:>7s} -> {new:>7s}{change}")
        else:
            logger.error(f"FAILED: {result.get('error', 'Unknown error')}")
        
        if dry_run:
            logger.info("\nDRY RUN - Rolling back changes")
            db.rollback()
        
    else:
        # Calculate for all indices
        logger.info(f"Calculating weights for ALL indices")
        logger.info(f"Method: {method}")
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be saved")
        
        results = calculator.recalculate_all_indices(method=method)
        
        # Summary
        total_success = sum(1 for r in results if r.get('success'))
        total_failed = len(results) - total_success
        total_updated = sum(r.get('updated', 0) for r in results if r.get('success'))
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total indices processed: {len(results)}")
        logger.info(f"Successful: {total_success}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Total constituents updated: {total_updated}")
        
        # Show failures
        failures = [r for r in results if not r.get('success')]
        if failures:
            logger.warning(f"\nFailed indices:")
            for r in failures:
                logger.warning(f"  {r.get('index_ticker', 'Unknown')}: {r.get('error', 'Unknown error')}")
        
        if dry_run:
            logger.info("\nDRY RUN - Rolling back all changes")
            db.rollback()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Calculate index constituent weights")
    parser.add_argument(
        "--index",
        type=str,
        default=None,
        help="Specific index ticker symbol (e.g., '^GSPC'), or leave empty for all indices"
    )
    parser.add_argument(
        "--method",
        type=str,
        default="market_cap",
        choices=["market_cap", "equal"],
        help="Calculation method: market_cap (default) or equal"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate calculation without saving changes"
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        logger.info("Starting weight calculation")
        logger.info(f"Index: {args.index or 'ALL'}")
        logger.info(f"Method: {args.method}")
        if args.dry_run:
            logger.info("Mode: DRY RUN")
        
        calculate_weights(
            db=db,
            ticker_symbol=args.index,
            method=args.method,
            dry_run=args.dry_run
        )
        
        if not args.dry_run:
            logger.info("\n✓ Completed successfully!")
        else:
            logger.info("\n✓ Dry run completed - no changes saved")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
