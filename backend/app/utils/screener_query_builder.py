"""Utility for building dynamic SQL query parts for stock screener filters.

Provides granular query construction logic so screener_service can
orchestrate without embedding complex SQL generation inline.

Functions:
    build_query_parts(filters, engine) -> (cte_sql, where_sql_with_joins, params)
"""
from typing import Dict, Any, List, Tuple


def build_query_parts(filters: Dict[str, Any], engine=None) -> Tuple[str, str, Dict[str, Any], Dict[str, bool]]:
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
            - flags: Dict indicating which optional tables/CTEs are included (e.g., {"has_technical_indicators": True})
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

    # Extended data filters (from extended_stock_data_cache JSON)
    # NOTE: Extended JSON is nested; we fall back over multiple possible locations/legacy keys.
    # Helper SQL fragments (Postgres JSON path casts). For other dialects these may need adaptation.
    market_cap_sql = "COALESCE( (e.extended_data->'market_data'->>'market_cap')::numeric, (e.extended_data->'financial_ratios'->>'market_cap')::numeric, (e.extended_data->>'marketCap')::numeric )"
    pe_sql = "COALESCE( (e.extended_data->'financial_ratios'->>'pe_ratio')::numeric, (e.extended_data->>'trailingPE')::numeric, (e.extended_data->>'forwardPE')::numeric )"
    ps_sql = "COALESCE( (e.extended_data->'financial_ratios'->>'price_to_sales')::numeric, (e.extended_data->>'priceToSalesTrailing12Months')::numeric )"
    earnings_growth_sql = "COALESCE( (e.extended_data->'financial_ratios'->>'earnings_growth')::numeric, (e.extended_data->>'earningsGrowth')::numeric )"
    revenue_growth_sql = "COALESCE( (e.extended_data->'financial_ratios'->>'revenue_growth')::numeric, (e.extended_data->>'revenueGrowth')::numeric )"
    beta_sql = "COALESCE( (e.extended_data->'risk_metrics'->>'beta')::numeric, (e.extended_data->>'beta')::numeric )"

    if (mc_min := filters.get("market_cap_min")) is not None:
        clauses.append(f"( {market_cap_sql} >= :market_cap_min )")
        params["market_cap_min"] = float(mc_min)
    if (mc_max := filters.get("market_cap_max")) is not None:
        clauses.append(f"( {market_cap_sql} <= :market_cap_max )")
        params["market_cap_max"] = float(mc_max)

    if (pe_min := filters.get("pe_ratio_min")) is not None:
        clauses.append(f"( {pe_sql} >= :pe_ratio_min )")
        params["pe_ratio_min"] = float(pe_min)
    if (pe_max := filters.get("pe_ratio_max")) is not None:
        clauses.append(f"( {pe_sql} <= :pe_ratio_max )")
        params["pe_ratio_max"] = float(pe_max)

    if (ps_min := filters.get("price_to_sales_min")) is not None:
        clauses.append(f"( {ps_sql} >= :price_to_sales_min )")
        params["price_to_sales_min"] = float(ps_min)
    if (ps_max := filters.get("price_to_sales_max")) is not None:
        clauses.append(f"( {ps_sql} <= :price_to_sales_max )")
        params["price_to_sales_max"] = float(ps_max)

    if (eg_min := filters.get("earnings_growth_min")) is not None:
        clauses.append(f"( {earnings_growth_sql} >= :earnings_growth_min )")
        params["earnings_growth_min"] = float(eg_min)
    if (eg_max := filters.get("earnings_growth_max")) is not None:
        clauses.append(f"( {earnings_growth_sql} <= :earnings_growth_max )")
        params["earnings_growth_max"] = float(eg_max)

    if (rg_min := filters.get("revenue_growth_min")) is not None:
        clauses.append(f"( {revenue_growth_sql} >= :revenue_growth_min )")
        params["revenue_growth_min"] = float(rg_min)
    if (rg_max := filters.get("revenue_growth_max")) is not None:
        clauses.append(f"( {revenue_growth_sql} <= :revenue_growth_max )")
        params["revenue_growth_max"] = float(rg_max)

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

    # RSI filters
    needs_rsi = False
    if (rsi_min := filters.get("rsi_min")) is not None:
        needs_rsi = True
        clauses.append("(ti.rsi >= :rsi_min)")
        params["rsi_min"] = float(rsi_min)
    if (rsi_max := filters.get("rsi_max")) is not None:
        needs_rsi = True
        clauses.append("(ti.rsi <= :rsi_max)")
        params["rsi_max"] = float(rsi_max)

    # Stochastic filters
    needs_stochastic = False
    stoch_status = filters.get("stochastic_status")  # "oversold", "overbought", "neutral"
    if stoch_status:
        needs_stochastic = True
        if stoch_status == "oversold":
            clauses.append("(ti.stoch_k <= 20)")
        elif stoch_status == "overbought":
            clauses.append("(ti.stoch_k >= 80)")
        elif stoch_status == "neutral":
            clauses.append("(ti.stoch_k > 20 AND ti.stoch_k < 80)")

    # Add technical indicators CTE if needed
    if needs_rsi or needs_stochastic:
        # Calculate RSI and Stochastic from recent price data
        ctes.append(
            """
            technical_indicators AS (
              SELECT
                stock_id,
                -- RSI calculation (14-period)
                CASE
                  WHEN SUM(CASE WHEN gain > 0 THEN gain ELSE 0 END) OVER w = 0 THEN 0
                  WHEN SUM(CASE WHEN loss > 0 THEN loss ELSE 0 END) OVER w = 0 THEN 100
                  ELSE 100 - (100 / (1 + (
                    SUM(CASE WHEN gain > 0 THEN gain ELSE 0 END) OVER w /
                    NULLIF(SUM(CASE WHEN loss > 0 THEN loss ELSE 0 END) OVER w, 0)
                  )))
                END AS rsi,
                -- Stochastic %K (14-period)
                CASE
                  WHEN MAX(high) OVER w14 - MIN(low) OVER w14 = 0 THEN 50
                  ELSE 100 * (close - MIN(low) OVER w14) / NULLIF(MAX(high) OVER w14 - MIN(low) OVER w14, 0)
                END AS stoch_k,
                ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY date DESC) AS rn
              FROM (
                SELECT
                  stock_id,
                  date,
                  close,
                  high,
                  low,
                  GREATEST(close - LAG(close) OVER (PARTITION BY stock_id ORDER BY date), 0) AS gain,
                  GREATEST(LAG(close) OVER (PARTITION BY stock_id ORDER BY date) - close, 0) AS loss
                FROM stock_price_data
                WHERE date >= CURRENT_DATE - INTERVAL '60 days'
              ) price_changes
              WINDOW
                w AS (PARTITION BY stock_id ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW),
                w14 AS (PARTITION BY stock_id ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
            )
            """
        )
        joins.append("LEFT JOIN technical_indicators ti ON ti.stock_id = s.id AND ti.rn = 1")

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
    
    # Return flags indicating which optional parts are included
    flags = {
        "has_technical_indicators": needs_rsi or needs_stochastic,
        "has_price_calc": needs_price
    }
    
    return cte_sql, join_sql + ("\n" + where_sql if where_sql else ""), params, flags
