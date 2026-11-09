"""Add global application settings and seed defaults."""

import os
from pathlib import Path
import sys
from sqlalchemy import create_engine, text

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.app.database import engine
except Exception:
    engine = create_engine(os.getenv("DATABASE_URL", "******localhost:5432/stock_watchlist"))


def upgrade():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS application_settings (
                key VARCHAR PRIMARY KEY,
                value VARCHAR NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        for key, value in (
            ("display_mode", "compact"),
            ("default_page", "overview"),
            ("theme", "default"),
        ):
            conn.execute(text("""
                INSERT INTO application_settings (key, value)
                SELECT :key, :value
                WHERE NOT EXISTS (
                    SELECT 1 FROM application_settings WHERE key = :key
                )
            """), {"key": key, "value": value})


if __name__ == "__main__":
    upgrade()
