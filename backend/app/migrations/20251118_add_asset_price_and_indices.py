"""
Add universal asset price data and market indices support:
1. asset_price_data table - universal OHLCV data for stocks, indices, ETFs, bonds, crypto
2. market_indices table - index metadata and information
3. index_constituents table - relationship between indices and stocks

Database: PostgreSQL
Date: 2025-11-18
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
    """Apply asset price and indices schema"""
    with engine.begin() as conn:
        logger.info("📊 Adding asset price and indices tables...")
        
        # Create asset_type enum
        logger.info("  → Creating asset_type enum...")
        conn.execute(text(
            """
            DO $$ BEGIN
                CREATE TYPE assettype AS ENUM ('stock', 'index', 'etf', 'bond', 'crypto');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """
        ))
        
        # Create asset_price_data table
        logger.info("  → Creating asset_price_data table...")
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS asset_price_data (
                id SERIAL PRIMARY KEY,
                asset_type assettype NOT NULL,
                ticker_symbol VARCHAR NOT NULL,
                date DATE NOT NULL,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT NOT NULL,
                volume BIGINT,
                adjusted_close FLOAT,
                dividends FLOAT DEFAULT 0.0,
                stock_splits FLOAT,
                exchange VARCHAR,
                currency VARCHAR,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT uq_asset_price_date UNIQUE (asset_type, ticker_symbol, date)
            );
            """
        ))
        
        # Add indexes for asset_price_data
        logger.info("  → Creating indexes on asset_price_data...")
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_asset_type_ticker_date 
            ON asset_price_data (asset_type, ticker_symbol, date);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_asset_type_ticker_date_desc 
            ON asset_price_data (asset_type, ticker_symbol, date DESC);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_asset_type 
            ON asset_price_data (asset_type);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_asset_ticker_symbol 
            ON asset_price_data (ticker_symbol);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_asset_date 
            ON asset_price_data (date);
            """
        ))
        
        # Create market_indices table
        logger.info("  → Creating market_indices table...")
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS market_indices (
                id SERIAL PRIMARY KEY,
                ticker_symbol VARCHAR NOT NULL UNIQUE,
                name VARCHAR NOT NULL,
                region VARCHAR,
                index_type VARCHAR,
                calculation_method VARCHAR,
                benchmark_index VARCHAR,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        ))
        
        # Add indexes for market_indices
        logger.info("  → Creating indexes on market_indices...")
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_market_indices_ticker 
            ON market_indices (ticker_symbol);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_market_indices_region 
            ON market_indices (region);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_market_indices_type 
            ON market_indices (index_type);
            """
        ))
        
        # Create index_constituents table
        logger.info("  → Creating index_constituents table...")
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS index_constituents (
                id SERIAL PRIMARY KEY,
                index_id INTEGER NOT NULL REFERENCES market_indices(id) ON DELETE CASCADE,
                stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
                weight FLOAT,
                status VARCHAR NOT NULL DEFAULT 'active',
                date_added DATE NOT NULL,
                date_removed DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        ))
        
        # Add indexes for index_constituents
        logger.info("  → Creating indexes on index_constituents...")
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_index_stock_status 
            ON index_constituents (index_id, stock_id, status);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_index_date_added 
            ON index_constituents (index_id, date_added);
            """
        ))
        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_constituent_stock_id 
            ON index_constituents (stock_id);
            """
        ))
        
        logger.info("✅ Asset price and indices tables created successfully!")


def downgrade():
    """Remove asset price and indices schema"""
    with engine.begin() as conn:
        logger.info("🗑️  Removing asset price and indices tables...")
        
        # Drop tables in reverse order (respecting foreign keys)
        conn.execute(text("DROP TABLE IF EXISTS index_constituents;"))
        conn.execute(text("DROP TABLE IF EXISTS market_indices;"))
        conn.execute(text("DROP TABLE IF EXISTS asset_price_data;"))
        
        # Drop enum type
        conn.execute(text("DROP TYPE IF EXISTS assettype;"))
        
        logger.info("✅ Asset price and indices tables removed successfully!")


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
