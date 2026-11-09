"""Add an archive flag for admin-managed assets."""

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
            ALTER TABLE stocks
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_stocks_is_active ON stocks (is_active)
        """))


if __name__ == "__main__":
    upgrade()
