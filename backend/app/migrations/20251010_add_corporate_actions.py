"""
Create corporate_actions table with JSONB meta and strict checks per action_type.
Database: PostgreSQL
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
    with engine.begin() as conn:
        logger.info("📅 Creating table corporate_actions …")
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS corporate_actions (
                id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
                action_type VARCHAR(16) NOT NULL,
                action_date DATE NOT NULL,
                source VARCHAR(64),
                meta_json JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT ck_corp_actions_type CHECK (action_type IN ('earnings','dividend','split','guidance','other'))
            );
            """
        ))

        logger.info("🔐 Adding unique constraint and indexes …")
        conn.execute(text(
            """
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_corp_actions_stock_type_date_source'
                ) THEN
                    ALTER TABLE corporate_actions
                    ADD CONSTRAINT uq_corp_actions_stock_type_date_source
                    UNIQUE (stock_id, action_type, action_date, COALESCE(source, ''));
                END IF;
            END $$;
            """
        ))

    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_corp_actions_stock ON corporate_actions(stock_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_corp_actions_date ON corporate_actions(action_date);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_corp_actions_type ON corporate_actions(action_type);"))

    logger.info("✅ Adding JSONB validation checks …")
    # Ensure meta_json is object or null
    conn.execute(text(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_corp_actions_meta_is_object'
            ) THEN
            ALTER TABLE corporate_actions ADD CONSTRAINT ck_corp_actions_meta_is_object
            CHECK (meta_json IS NULL OR jsonb_typeof(meta_json) = 'object');
            END IF;
        END $$;
        """
    ))

    # Per-type allowed/required keys and simple type checks
    conn.execute(text(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_corp_actions_meta_policy'
            ) THEN
            ALTER TABLE corporate_actions ADD CONSTRAINT ck_corp_actions_meta_policy CHECK (
                CASE action_type
                WHEN 'earnings' THEN (
                    (meta_json - ARRAY['period','time_of_day','eps_est','eps_actual','revenue_est','revenue_actual','currency']::text[]) = '{}'::jsonb
                    AND (meta_json ? 'period')
                    AND (meta_json ? 'time_of_day')
                    AND ((meta_json ? 'eps_est') IS FALSE OR jsonb_typeof(meta_json->'eps_est') = 'number')
                    AND ((meta_json ? 'eps_actual') IS FALSE OR jsonb_typeof(meta_json->'eps_actual') = 'number')
                    AND ((meta_json ? 'revenue_est') IS FALSE OR jsonb_typeof(meta_json->'revenue_est') = 'number')
                    AND ((meta_json ? 'revenue_actual') IS FALSE OR jsonb_typeof(meta_json->'revenue_actual') = 'number')
                    AND ((meta_json ? 'currency') IS FALSE OR jsonb_typeof(meta_json->'currency') = 'string')
                )
                WHEN 'dividend' THEN (
                    (meta_json - ARRAY['ex_date','record_date','pay_date','amount','currency','frequency']::text[]) = '{}'::jsonb
                    AND (meta_json ? 'amount')
                    AND jsonb_typeof(meta_json->'amount') = 'number'
                    AND ((meta_json ? 'currency') IS FALSE OR jsonb_typeof(meta_json->'currency') = 'string')
                )
                WHEN 'split' THEN (
                    (meta_json - ARRAY['ratio','announced','effective']::text[]) = '{}'::jsonb
                    AND (meta_json ? 'ratio')
                    AND jsonb_typeof(meta_json->'ratio') = 'number'
                )
                WHEN 'guidance' THEN (
                    (meta_json - ARRAY['eps_guidance_low','eps_guidance_high','revenue_guidance_low','revenue_guidance_high','period']::text[]) = '{}'::jsonb
                    AND (meta_json ? 'period')
                )
                ELSE TRUE
                END
            );
            END IF;
        END $$;
        """
    ))

    logger.info("🎉 corporate_actions created with checks")


def downgrade():
  with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS corporate_actions CASCADE;"))
    logger.info("Dropped table corporate_actions")
