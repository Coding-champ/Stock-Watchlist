"""
Add portfolios + holdings and seed the single default portfolio.

v1: one implicit portfolio ("Mein Portfolio"). The portfolios table exists so
additional depots can be added later without a schema change; the UI must not
expose a portfolio picker yet.

Database: PostgreSQL
Date: 2026-11-07
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
    from backend.app.models import DEFAULT_PORTFOLIO_NAME
except Exception:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/stock_watchlist",
    )
    engine = create_engine(DATABASE_URL)
    DEFAULT_PORTFOLIO_NAME = "Mein Portfolio"


def upgrade():
    with engine.begin() as conn:
        logger.info("Adding portfolios and holdings tables...")

        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS portfolios (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        ))

        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS holdings (
                id SERIAL PRIMARY KEY,
                portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
                stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
                quantity FLOAT NOT NULL,
                purchase_price FLOAT NOT NULL,
                purchase_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT uq_portfolio_stock UNIQUE (portfolio_id, stock_id)
            );
            """
        ))

        conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_holding_portfolio
            ON holdings (portfolio_id);
            """
        ))

        conn.execute(
            text(
                """
                INSERT INTO portfolios (name)
                SELECT :name
                WHERE NOT EXISTS (
                    SELECT 1 FROM portfolios WHERE name = :name
                );
                """
            ),
            {"name": DEFAULT_PORTFOLIO_NAME},
        )

        logger.info("Portfolios/holdings schema ready (default portfolio seeded).")


def downgrade():
    with engine.begin() as conn:
        logger.info("Removing holdings and portfolios tables...")
        conn.execute(text("DROP TABLE IF EXISTS holdings;"))
        conn.execute(text("DROP TABLE IF EXISTS portfolios;"))
        logger.info("Portfolios/holdings tables removed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--downgrade", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.downgrade:
        logger.info("Running downgrade...")
        downgrade()
    else:
        logger.info("Running upgrade...")
        upgrade()

    logger.info("Migration completed.")
