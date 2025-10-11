"""
Add performance indexes to optimize common queries:
1. idx_stock_date_desc on stock_price_data (stock_id, date DESC) - for latest price queries
2. idx_stock_active on alerts (stock_id, is_active) - for active alert checks

Database: PostgreSQL
Date: 2025-10-11
"""

import sys
from pathlib import Path
from sqlalchemy import text, create_engine
import os
import logging

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from backend.app.database import engine
except Exception:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/stock_watchlist",
    )
    engine = create_engine(DATABASE_URL)


def upgrade():
    """Apply performance indexes"""
    with engine.begin() as conn:
        logger.info("📊 Adding performance indexes...")
        
        # Index for "get latest price" queries (ORDER BY date DESC)
        logger.info("  → Creating idx_stock_date_desc on stock_price_data...")
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_stock_date_desc 
            ON stock_price_data (stock_id, date DESC);
            """
        ))
        
        # Index for checking active alerts per stock
        logger.info("  → Creating idx_stock_active on alerts...")
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_stock_active 
            ON alerts (stock_id, is_active);
            """
        ))
        
        # Add index to stock_id on alerts if not exists (referenced in model changes)
        logger.info("  → Ensuring stock_id index exists on alerts...")
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_stock_id 
            ON alerts (stock_id);
            """
        ))
        
        logger.info("✅ Performance indexes added successfully!")


def downgrade():
    """Remove performance indexes"""
    with engine.begin() as conn:
        logger.info("🗑️  Removing performance indexes...")
        
        conn.execute(text("DROP INDEX IF EXISTS idx_stock_date_desc;"))
        conn.execute(text("DROP INDEX IF EXISTS idx_stock_active;"))
        conn.execute(text("DROP INDEX IF EXISTS idx_alerts_stock_id;"))
        
        logger.info("✅ Performance indexes removed successfully!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--downgrade", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.downgrade:
        logger.info("🔄 Running downgrade...")
        downgrade()
    else:
        logger.info("⬆️  Running upgrade...")
        upgrade()
    
    logger.info("🎉 Migration completed!")
