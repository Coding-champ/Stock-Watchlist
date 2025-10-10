from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from backend.app.database import engine


def _build_query_parts(filters: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build dynamic SQL parts: optional CTEs, JOINs, and WHERE clause based on filters.
    Returns: (cte_sql, where_sql_with_joins, params)
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


def run_screener(filters: Dict[str, Any], page: int = 1, page_size: int = 25,
                 sort: str = "ticker_symbol", order: str = "asc") -> Dict[str, Any]:
    """
    Minimal screener: filters on stocks master table.
    Later we can join to price/fundamental tables for richer filters.
    """
    allowed_sort = {"ticker_symbol", "name", "sector", "industry", "country", "id", "e_beta", "lf_profit_margin", "lf_return_on_equity", "lf_current_ratio"}
    if sort not in allowed_sort:
        sort = "ticker_symbol"
    order = "desc" if str(order).lower() == "desc" else "asc"

    cte_sql, where_with_joins, params = _build_query_parts(filters)

    offset = max(page - 1, 0) * max(page_size, 1)
    limit = max(min(page_size, 200), 1)

    base_from = "FROM stocks s"
    count_sql = f"""
        {cte_sql}
        SELECT COUNT(*) {base_from}
        {where_with_joins}
    """

    data_sql = f"""
        {cte_sql}
        SELECT 
          s.id, s.ticker_symbol, s.name, s.country, s.sector, s.industry,
          (e.extended_data->>'beta')::numeric AS e_beta,
          lf.profit_margin AS lf_profit_margin,
          lf.return_on_equity AS lf_return_on_equity,
          lf.current_ratio AS lf_current_ratio
        {base_from}
        {where_with_joins}
        ORDER BY {sort} {order}
        LIMIT :limit OFFSET :offset
    """

    with engine.begin() as conn:
        total = conn.execute(text(count_sql), params).scalar() or 0
        params_with_paging = dict(params)
        params_with_paging.update({"limit": limit, "offset": offset})
        rows = conn.execute(text(data_sql), params_with_paging).mappings().all()

    return {
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "results": list(rows),
        "sort": sort,
        "order": order,
    }


def get_filter_facets() -> Dict[str, List[str]]:
    """Return distinct values for basic facets: country, sector, industry."""
    sql = text(
        """
        SELECT DISTINCT s.country FROM stocks s WHERE s.country IS NOT NULL AND s.country <> '' ORDER BY s.country;
        """
    )
    sql2 = text(
        """
        SELECT DISTINCT s.sector FROM stocks s WHERE s.sector IS NOT NULL AND s.sector <> '' ORDER BY s.sector;
        """
    )
    sql3 = text(
        """
        SELECT DISTINCT s.industry FROM stocks s WHERE s.industry IS NOT NULL AND s.industry <> '' ORDER BY s.industry;
        """
    )
    with engine.begin() as conn:
        countries = [r[0] for r in conn.execute(sql).all()]
        sectors = [r[0] for r in conn.execute(sql2).all()]
        industries = [r[0] for r in conn.execute(sql3).all()]
    return {
        "countries": countries,
        "sectors": sectors,
        "industries": industries,
    }
