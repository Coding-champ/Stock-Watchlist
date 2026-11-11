"""Store historical inputs required for valuation time series."""

import os
from pathlib import Path
import sys
from sqlalchemy import create_engine, text

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.app.database import engine
except Exception:
    engine = create_engine(os.getenv("DATABASE_URL", "postgresql://localhost:5432/stock_watchlist"))


def upgrade():
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE stock_fundamental_data
            ADD COLUMN IF NOT EXISTS shares_outstanding NUMERIC(20, 4)
        """))
        conn.execute(text("""
            ALTER TABLE stock_fundamental_data
            ADD COLUMN IF NOT EXISTS total_debt NUMERIC(20, 2)
        """))
        conn.execute(text("""
            ALTER TABLE stock_fundamental_data
            ADD COLUMN IF NOT EXISTS total_cash NUMERIC(20, 2)
        """))


if __name__ == "__main__":
    upgrade()
