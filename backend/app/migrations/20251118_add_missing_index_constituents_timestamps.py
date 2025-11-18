"""
Migration: Add missing created_at / updated_at columns to index_constituents if absent.
Date: 2025-11-18
This is a safety patch for environments where the initial indices migration
was partially applied or an older table definition exists without timestamps.
"""

from sqlalchemy import text, create_engine
import os
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.app.database import engine
except Exception:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/stock_watchlist",
    )
    engine = create_engine(DATABASE_URL)


def upgrade():
    """Add created_at and updated_at columns if they do not exist."""
    with engine.begin() as conn:
        logger.info("🔧 Checking index_constituents for missing timestamp columns...")
        conn.execute(text(
            """
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='index_constituents' AND column_name='created_at'
                ) THEN
                    ALTER TABLE index_constituents 
                    ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='index_constituents' AND column_name='updated_at'
                ) THEN
                    ALTER TABLE index_constituents 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
                END IF;
            END $$;
            """
        ))
        logger.info("✅ Timestamp column check completed.")


def downgrade():
    """Optionally remove the columns (only if they exist)."""
    with engine.begin() as conn:
        logger.info("🗑️  Dropping timestamp columns from index_constituents if present...")
        conn.execute(text(
            """
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='index_constituents' AND column_name='created_at'
                ) THEN
                    ALTER TABLE index_constituents DROP COLUMN created_at;
                END IF;
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='index_constituents' AND column_name='updated_at'
                ) THEN
                    ALTER TABLE index_constituents DROP COLUMN updated_at;
                END IF;
            END $$;
            """
        ))
        logger.info("✅ Timestamp columns removed (if they existed).")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--downgrade", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    if args.downgrade:
        downgrade()
    else:
        upgrade()
    logger.info("🎉 Migration completed!")
