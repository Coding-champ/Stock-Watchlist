"""Utility for building dynamic SQL query parts for stock screener filters.

Provides granular query construction logic so screener_service can
orchestrate without embedding complex SQL generation inline.

Functions:
    build_query_parts(filters, engine) -> (cte_sql, where_sql_with_joins, params)
"""
from typing import Dict, Any, List, Tuple


def build_query_parts(filters: Dict[str, Any], engine=None) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build dynamic SQL parts: optional CTEs, JOINs, and WHERE clause based on filters.
    
    Args:
        filters: Dict of filter keys and values (e.g., q, country, beta_min, etc.)
        engine: SQLAlchemy engine (optional, needed for dialect detection for observation_reason)
    
    Returns:
        Tuple of:
            - cte_sql: WITH clause SQL (includes trailing newline if non-empty)
            - where_sql_with_joins: JOIN clauses + WHERE clause (combined string)
            - params: Dict of named parameters for SQL execution
    """
    clauses: List[str] = []
    joins: List[str] = []
    ctes: List[str] = []
    params: Dict[str, Any] = {}

    # Always join latest fundamentals and extended cache for beta display/sorts
    ctes.append(
        """
        latest_fundamental AS (
          SELECT DISTINCT ON (stock_id)
            stock_id, period, period_end_date,
            profit_margin, return_on_equity, current_ratio, quick_ratio,
            operating_cashflow, free_cashflow, total_assets, total_liabilities, shareholders_equity,
            debt_to_equity
          FROM stock_fundamental_data
          ORDER BY stock_id, COALESCE(period_end_date, DATE '1900-01-01') DESC, period DESC
        )
        """
    )
    joins.append("LEFT JOIN latest_fundamental lf ON lf.stock_id = s.id")
    joins.append("LEFT JOIN extended_stock_data_cache e ON e.stock_id = s.id")

    # Simple textual filters on master stock data
    if q := filters.get("q"):
        clauses.append("(LOWER(s.ticker_symbol) LIKE :q OR LOWER(s.name) LIKE :q)")
        params["q"] = f"%{q.lower()}%"

    if country := filters.get("country"):
        clauses.append("LOWER(s.country) = :country")
        params["country"] = country.lower()

    if sector := filters.get("sector"):
        clauses.append("LOWER(s.sector) = :sector")
        params["sector"] = sector.lower()

    if industry := filters.get("industry"):
        clauses.append("LOWER(s.industry) = :industry")
        params["industry"] = industry.lower()

    # Filter by observation reason (from stocks_in_watchlist.observation_reasons JSON array)
    if (obs := filters.get("observation_reason")):
        # Use Postgres JSONB extraction when available for accurate matching, otherwise fall back to text matching
        dialect_name = None
        if engine:
            dialect = getattr(engine, 'dialect', None)
            dialect_name = getattr(dialect, 'name', None)
        
        if dialect_name == 'postgresql':
            clauses.append(
                "EXISTS (SELECT 1 FROM stocks_in_watchlist si, jsonb_array_elements_text(si.observation_reasons::jsonb) reason WHERE si.stock_id = s.id AND reason = :observation_reason)"
            )
            params["observation_reason"] = obs
        else:
            # Generic fallback: match reason inside JSON/text representation (case-insensitive)
            clauses.append(
                "EXISTS (SELECT 1 FROM stocks_in_watchlist si WHERE si.stock_id = s.id AND LOWER(CAST(si.observation_reasons AS TEXT)) LIKE :_obs_like)"
            )
            params["_obs_like"] = f"%{str(obs).lower()}%"

    # Beta range from extended cache JSON
    if (bmin := filters.get("beta_min")) is not None:
        clauses.append("( (e.extended_data->>'beta')::numeric >= :beta_min )")
        params["beta_min"] = float(bmin)
    if (bmax := filters.get("beta_max")) is not None:
        clauses.append("( (e.extended_data->>'beta')::numeric <= :beta_max )")
        params["beta_max"] = float(bmax)

    # Fundamental ratio filters
    def add_min(field_key: str, sql_expr: str):
        val = filters.get(field_key)
        if val is not None:
            clauses.append(f"({sql_expr} >= :{field_key})")
            params[field_key] = float(val)

    def add_max(field_key: str, sql_expr: str):
        val = filters.get(field_key)
        if val is not None:
            clauses.append(f"({sql_expr} <= :{field_key})")
            params[field_key] = float(val)

    add_min("profit_margin_min", "lf.profit_margin")
    add_min("roe_min", "lf.return_on_equity")
    add_min("current_ratio_min", "lf.current_ratio")
    add_min("quick_ratio_min", "lf.quick_ratio")
    add_min("operating_cashflow_min", "lf.operating_cashflow")
    add_min("free_cashflow_min", "lf.free_cashflow")
    add_min("shareholders_equity_min", "lf.shareholders_equity")
    add_min("total_assets_min", "lf.total_assets")

    add_max("debt_to_equity_max", "lf.debt_to_equity")
    add_max("total_liabilities_max", "lf.total_liabilities")

    # Technical filters (price vs SMA50/SMA200)
    needs_price = False
    if (p50 := filters.get("price_vs_sma50")) in ("above", "below"):
        needs_price = True
        op = ">=" if p50 == "above" else "<="
        clauses.append(f"(pc.close {op} pc.sma50)")
    if (p200 := filters.get("price_vs_sma200")) in ("above", "below"):
        needs_price = True
        op = ">=" if p200 == "above" else "<="
        clauses.append(f"(pc.close {op} pc.sma200)")

    if needs_price:
        ctes.append(
            """
            price_calc AS (
              SELECT stock_id, close, sma50, sma200 FROM (
                SELECT
                  spd.stock_id,
                  spd.date,
                  spd.close,
                  AVG(spd.close) OVER (PARTITION BY spd.stock_id ORDER BY spd.date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma50,
                  AVG(spd.close) OVER (PARTITION BY spd.stock_id ORDER BY spd.date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma200,
                  ROW_NUMBER() OVER (PARTITION BY spd.stock_id ORDER BY spd.date DESC) AS rn
                FROM stock_price_data spd
              ) t WHERE t.rn = 1
            )
            """
        )
        joins.append("LEFT JOIN price_calc pc ON pc.stock_id = s.id")

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    join_sql = ("\n" + "\n".join(joins)) if joins else ""
    cte_sql = ("WITH " + ",\n".join(ctes) + "\n") if ctes else ""
    return cte_sql, join_sql + ("\n" + where_sql if where_sql else ""), params
