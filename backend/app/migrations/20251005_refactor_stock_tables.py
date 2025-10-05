"""
Database Migration: Refactor Stock Tables for Historical Data
Version: 20251005
Description: 
    - Restructure stocks table to contain only master data (Stammdaten)
    - Create stocks_in_watchlist table for n:m relationship
    - Create stock_price_data table for historical daily prices
    - Create stock_fundamental_data table for quarterly financials
    - Migrate existing data from stocks to new structure
    - Remove stock_data table (deprecated)
    
Database: PostgreSQL
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, create_engine
import logging

# Import database connection
try:
    from backend.app.database import engine
except ImportError:
    # Fallback: create engine from environment or default
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/stock_watchlist"
    )
    engine = create_engine(DATABASE_URL)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """Apply migration"""
    with engine.begin() as conn:
        logger.info("🚀 Starting database migration: Stock table refactoring")
        
        # Step 1: Create new stocks_in_watchlist table
        logger.info("📊 Step 1: Creating stocks_in_watchlist table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks_in_watchlist (
                id SERIAL PRIMARY KEY,
                watchlist_id INTEGER NOT NULL,
                stock_id INTEGER NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                exchange VARCHAR(50),
                currency VARCHAR(10),
                observation_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
                observation_notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
                FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
                CONSTRAINT uq_watchlist_stock UNIQUE (watchlist_id, stock_id)
            )
        """))
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_position 
            ON stocks_in_watchlist(watchlist_id, position)
        """))
        
        # Step 2: Create stock_price_data table
        logger.info("📊 Step 2: Creating stock_price_data table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_price_data (
                id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL,
                date DATE NOT NULL,
                open NUMERIC(20, 4),
                high NUMERIC(20, 4),
                low NUMERIC(20, 4),
                close NUMERIC(20, 4) NOT NULL,
                volume BIGINT,
                adjusted_close NUMERIC(20, 4),
                dividends NUMERIC(20, 4) DEFAULT 0.0,
                stock_splits NUMERIC(10, 4),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
                CONSTRAINT uq_stock_price_date UNIQUE (stock_id, date)
            )
        """))
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_stock_date 
            ON stock_price_data(stock_id, date DESC)
        """))
        
        # Step 3: Create stock_fundamental_data table
        logger.info("📊 Step 3: Creating stock_fundamental_data table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_fundamental_data (
                id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL,
                period VARCHAR(20) NOT NULL,
                period_end_date DATE,
                revenue NUMERIC(20, 2),
                earnings NUMERIC(20, 2),
                eps_basic NUMERIC(20, 4),
                eps_diluted NUMERIC(20, 4),
                operating_income NUMERIC(20, 2),
                gross_profit NUMERIC(20, 2),
                ebitda NUMERIC(20, 2),
                total_assets NUMERIC(20, 2),
                total_liabilities NUMERIC(20, 2),
                shareholders_equity NUMERIC(20, 2),
                operating_cashflow NUMERIC(20, 2),
                free_cashflow NUMERIC(20, 2),
                profit_margin NUMERIC(10, 4),
                operating_margin NUMERIC(10, 4),
                return_on_equity NUMERIC(10, 4),
                return_on_assets NUMERIC(10, 4),
                debt_to_equity NUMERIC(10, 4),
                current_ratio NUMERIC(10, 4),
                quick_ratio NUMERIC(10, 4),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
                CONSTRAINT uq_stock_fundamental_period UNIQUE (stock_id, period)
            )
        """))
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_stock_period 
            ON stock_fundamental_data(stock_id, period DESC)
        """))
        
        # Step 4: Backup existing stocks data (in separate table)
        logger.info("💾 Step 4: Creating backup of stocks table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks_backup_20251005 AS 
            SELECT * FROM stocks
        """))
        
        # Step 5: Migrate data from stocks to stocks_in_watchlist
        logger.info("🔄 Step 5: Migrating data to stocks_in_watchlist...")
        
        # First, identify and consolidate duplicate stocks by ticker_symbol
        logger.info("   🔍 Step 5a: Identifying duplicate ticker symbols...")
        
        # For each duplicate ticker, keep the record with the most complete data (has ISIN)
        # and create separate watchlist entries for all occurrences
        conn.execute(text("""
            -- Create temp table to store master stock IDs for each ticker
            CREATE TEMP TABLE stock_master_mapping (
                old_stock_id INTEGER,
                master_stock_id INTEGER,
                watchlist_id INTEGER,
                position INTEGER,
                observation_reasons JSONB,
                observation_notes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        
        # Find the "best" stock for each ticker (prefer ones with ISIN, then lowest ID)
        logger.info("   🎯 Step 5b: Selecting master stock for each ticker...")
        conn.execute(text("""
            INSERT INTO stock_master_mapping
            SELECT 
                s.id as old_stock_id,
                master.id as master_stock_id,
                s.watchlist_id,
                s.position,
                COALESCE(s.observation_reasons, '[]'::jsonb) as observation_reasons,
                s.observation_notes,
                s.created_at,
                s.updated_at
            FROM stocks s
            INNER JOIN (
                SELECT 
                    ticker_symbol,
                    MIN(
                        CASE 
                            WHEN isin IS NOT NULL AND isin != '' THEN id
                            ELSE 999999 
                        END
                    ) as best_id_with_isin,
                    MIN(id) as first_id
                FROM stocks
                GROUP BY ticker_symbol
            ) candidates ON s.ticker_symbol = candidates.ticker_symbol
            INNER JOIN stocks master ON master.id = COALESCE(
                NULLIF(candidates.best_id_with_isin, 999999),
                candidates.first_id
            )
        """))
        
        # Insert into stocks_in_watchlist using master stock IDs
        logger.info("   📝 Step 5c: Creating watchlist entries...")
        conn.execute(text("""
            INSERT INTO stocks_in_watchlist 
                (watchlist_id, stock_id, position, observation_reasons, observation_notes, created_at, updated_at)
            SELECT DISTINCT ON (watchlist_id, master_stock_id)
                watchlist_id,
                master_stock_id as stock_id,
                position,
                observation_reasons,
                observation_notes,
                created_at,
                updated_at
            FROM stock_master_mapping
            ORDER BY watchlist_id, master_stock_id, old_stock_id
        """))
        
        # Update stock_data foreign keys to point to master stocks
        logger.info("   🔄 Step 5d: Updating stock_data foreign keys...")
        conn.execute(text("""
            UPDATE stock_data sd
            SET stock_id = m.master_stock_id
            FROM stock_master_mapping m
            WHERE sd.stock_id = m.old_stock_id
                AND m.old_stock_id != m.master_stock_id
        """))
        
        # Update alerts foreign keys
        logger.info("   🔄 Step 5e: Updating alerts foreign keys...")
        conn.execute(text("""
            UPDATE alerts a
            SET stock_id = m.master_stock_id
            FROM stock_master_mapping m
            WHERE a.stock_id = m.old_stock_id
                AND m.old_stock_id != m.master_stock_id
        """))
        
        # For extended_stock_data_cache, delete duplicates first (has UNIQUE constraint on stock_id)
        logger.info("   🧹 Step 5f: Removing cache entries for duplicate stocks...")
        conn.execute(text("""
            DELETE FROM extended_stock_data_cache
            WHERE stock_id IN (
                SELECT DISTINCT old_stock_id
                FROM stock_master_mapping
                WHERE old_stock_id != master_stock_id
            )
        """))
        
        # Delete duplicate stock_data entries (keep most recent per master stock)
        logger.info("   🧹 Step 5g: Removing duplicate stock_data entries...")
        conn.execute(text("""
            DELETE FROM stock_data
            WHERE id NOT IN (
                SELECT DISTINCT ON (stock_id) id
                FROM stock_data
                ORDER BY stock_id, timestamp DESC
            )
        """))
        
        # Delete duplicate stocks (keep only master stocks)
        logger.info("   🗑️  Step 5h: Removing duplicate stocks...")
        conn.execute(text("""
            DELETE FROM stocks 
            WHERE id NOT IN (
                SELECT DISTINCT master_stock_id FROM stock_master_mapping
            )
        """))
        
        rows_deleted = conn.execute(text("SELECT COUNT(*) FROM stocks_backup_20251005")).scalar()
        rows_kept = conn.execute(text("SELECT COUNT(*) FROM stocks")).scalar()
        logger.info(f"   ✅ Consolidated {rows_deleted} original stocks into {rows_kept} unique stocks")
        
        # Clean up temp table
        conn.execute(text("DROP TABLE stock_master_mapping"))
        
        # Step 6: Add new columns to stocks table
        logger.info("📝 Step 6: Adding new columns to stocks table...")
        
        # Check and add wkn column
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='stocks' AND column_name='wkn'
                ) THEN
                    ALTER TABLE stocks ADD COLUMN wkn VARCHAR(50);
                    CREATE INDEX idx_stocks_wkn ON stocks(wkn);
                END IF;
            END $$;
        """))
        
        # Check and add business_summary column
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='stocks' AND column_name='business_summary'
                ) THEN
                    ALTER TABLE stocks ADD COLUMN business_summary TEXT;
                END IF;
            END $$;
        """))
        
        # Step 7: Drop old columns from stocks table
        logger.info("🗑️  Step 7: Removing old columns from stocks table...")
        
        # Drop constraints first
        conn.execute(text("""
            ALTER TABLE stocks 
            DROP CONSTRAINT IF EXISTS uq_stocks_watchlist_ticker CASCADE
        """))
        
        conn.execute(text("""
            ALTER TABLE stocks 
            DROP CONSTRAINT IF EXISTS uq_stocks_watchlist_isin CASCADE
        """))
        
        # Drop columns
        try:
            conn.execute(text("ALTER TABLE stocks DROP COLUMN IF EXISTS watchlist_id CASCADE"))
            conn.execute(text("ALTER TABLE stocks DROP COLUMN IF EXISTS position CASCADE"))
            conn.execute(text("ALTER TABLE stocks DROP COLUMN IF EXISTS observation_reasons CASCADE"))
            conn.execute(text("ALTER TABLE stocks DROP COLUMN IF EXISTS observation_notes CASCADE"))
            logger.info("✅ Old columns removed from stocks table")
        except Exception as e:
            logger.warning(f"Could not drop some columns: {e}")
        
        # Step 8: Add new unique constraints for stocks table
        logger.info("� Step 8: Adding new constraints to stocks table...")
        conn.execute(text("""
            ALTER TABLE stocks
            DROP CONSTRAINT IF EXISTS uq_stocks_ticker CASCADE
        """))
        
        conn.execute(text("""
            ALTER TABLE stocks
            ADD CONSTRAINT uq_stocks_ticker UNIQUE (ticker_symbol)
        """))
        
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_stocks_isin'
                ) THEN
                    ALTER TABLE stocks ADD CONSTRAINT uq_stocks_isin UNIQUE (isin);
                END IF;
            END $$;
        """))
        
        # Step 9: Drop stock_data table (deprecated)
        logger.info("🗑️  Step 9: Removing deprecated stock_data table...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS stock_data CASCADE"))
            logger.info("✅ stock_data table removed successfully")
        except Exception as e:
            logger.warning(f"Could not drop stock_data table: {e}")
        
        logger.info("✅ Migration completed successfully!")


def downgrade():
    """Rollback migration"""
    with engine.begin() as conn:
        logger.info("⏪ Rolling back database migration...")
        
        try:
            # Drop new tables
            conn.execute(text("DROP TABLE IF EXISTS stocks_in_watchlist CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS stock_price_data CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS stock_fundamental_data CASCADE"))
            
            # Restore stocks from backup
            conn.execute(text("DROP TABLE IF EXISTS stocks CASCADE"))
            conn.execute(text("""
                CREATE TABLE stocks AS 
                SELECT * FROM stocks_backup_20251005
            """))
            
            # Recreate stock_data table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    id SERIAL PRIMARY KEY,
                    stock_id INTEGER NOT NULL,
                    current_price NUMERIC(20, 4),
                    pe_ratio NUMERIC(10, 4),
                    rsi NUMERIC(10, 4),
                    volatility NUMERIC(10, 4),
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks(id)
                )
            """))
            
            logger.info("✅ Rollback completed successfully!")
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
