"""
Rollback partially completed migration
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rollback():
    """Rollback partially completed migration"""
    with engine.begin() as conn:
        logger.info("🔄 Rolling back partially completed migration...")
        
        # Check if backup exists
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'stocks_backup_20251005'
        """))
        
        if result.scalar() == 0:
            logger.error("❌ No backup found! Cannot rollback.")
            return False
        
        # Drop new tables if they exist
        logger.info("🗑️  Dropping new tables...")
        conn.execute(text("DROP TABLE IF EXISTS stocks_in_watchlist CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS stock_price_data CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS stock_fundamental_data CASCADE"))
        
        # Restore stocks table from backup
        logger.info("💾 Restoring stocks table from backup...")
        conn.execute(text("DROP TABLE IF EXISTS stocks CASCADE"))
        conn.execute(text("ALTER TABLE stocks_backup_20251005 RENAME TO stocks"))
        
        # Recreate constraints on stocks table
        logger.info("🔧 Recreating constraints...")
        conn.execute(text("""
            ALTER TABLE stocks 
            ADD CONSTRAINT uq_stocks_watchlist_ticker UNIQUE (watchlist_id, ticker_symbol)
        """))
        
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'uq_stocks_watchlist_isin'
                ) THEN
                    ALTER TABLE stocks 
                    ADD CONSTRAINT uq_stocks_watchlist_isin UNIQUE (watchlist_id, isin);
                END IF;
            END $$;
        """))
        
        logger.info("✅ Rollback completed successfully!")
        return True

if __name__ == "__main__":
    success = rollback()
    sys.exit(0 if success else 1)
