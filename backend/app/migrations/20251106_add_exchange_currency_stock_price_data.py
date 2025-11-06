"""
Migration: Add exchange and currency columns to stock_price_data
Date: 2025-11-06

This migration adds nullable `exchange` and `currency` columns to the
`stock_price_data` table so historical rows can record the source exchange
and trading currency. The columns are nullable to avoid breaking existing
rows; callers can backfill where possible in a separate step.
"""

from sqlalchemy import text, create_engine
from pathlib import Path
import sys
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
    """Apply migration: add columns if not present"""
    with engine.begin() as conn:
        logger.info("📥 Adding exchange and currency columns to stock_price_data if missing...")
        # Add exchange column
        conn.execute(text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='stock_price_data' AND column_name='exchange'
                ) THEN
                    ALTER TABLE stock_price_data ADD COLUMN exchange VARCHAR(50);
                END IF;
            END$$;
            """
        ))

        # Add currency column
        conn.execute(text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='stock_price_data' AND column_name='currency'
                ) THEN
                    ALTER TABLE stock_price_data ADD COLUMN currency VARCHAR(10);
                END IF;
            END$$;
            """
        ))

        logger.info("✅ Columns ensured on stock_price_data")


def downgrade():
    """Remove the columns added by this migration (if present)"""
    with engine.begin() as conn:
        logger.info("🗑️  Removing exchange and currency columns from stock_price_data if present...")
        conn.execute(text("ALTER TABLE stock_price_data DROP COLUMN IF EXISTS exchange;"))
        conn.execute(text("ALTER TABLE stock_price_data DROP COLUMN IF EXISTS currency;"))
        logger.info("✅ Columns removed")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--downgrade', action='store_true')
    args = parser.parse_args()
    if args.downgrade:
        downgrade()
    else:
        upgrade()
