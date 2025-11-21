from typing import Dict, Any, List
from sqlalchemy import text
from backend.app.database import engine
from backend.app.utils.screener_query_builder import build_query_parts


def run_screener(filters: Dict[str, Any], page: int = 1, page_size: int = 25,
                 sort: str = "ticker_symbol", order: str = "asc") -> Dict[str, Any]:
    """
    Minimal screener: filters on stocks master table.
    Later we can join to price/fundamental tables for richer filters.
    """
    allowed_sort = {
        "ticker_symbol", "name", "sector", "industry", "country", "id",
        "e_beta", "lf_profit_margin", "lf_return_on_equity", "lf_current_ratio",
        "e_market_cap", "e_pe_ratio", "e_price_to_sales", "e_earnings_growth", "e_revenue_growth",
        "ti_rsi", "ti_stoch_k"
    }
    if sort not in allowed_sort:
        sort = "ticker_symbol"
    order = "desc" if str(order).lower() == "desc" else "asc"

    cte_sql, where_with_joins, params, flags = build_query_parts(filters, engine)

    offset = max(page - 1, 0) * max(page_size, 1)
    limit = max(min(page_size, 200), 1)

    base_from = "FROM stocks s"
    count_sql = f"""
        {cte_sql}
        SELECT COUNT(*) {base_from}
        {where_with_joins}
    """

    select_fields = [
        "s.id", "s.ticker_symbol", "s.name", "s.country", "s.sector", "s.industry",
        "COALESCE( (e.extended_data->'risk_metrics'->>'beta')::numeric, (e.extended_data->>'beta')::numeric ) AS e_beta",
        "lf.profit_margin AS lf_profit_margin",
        "lf.return_on_equity AS lf_return_on_equity",
        "lf.current_ratio AS lf_current_ratio",
        "COALESCE( (e.extended_data->'market_data'->>'market_cap')::numeric, (e.extended_data->'financial_ratios'->>'market_cap')::numeric, (e.extended_data->>'marketCap')::numeric ) AS e_market_cap",
        "COALESCE( (e.extended_data->'financial_ratios'->>'pe_ratio')::numeric, (e.extended_data->>'trailingPE')::numeric, (e.extended_data->>'forwardPE')::numeric ) AS e_pe_ratio",
        "COALESCE( (e.extended_data->'financial_ratios'->>'price_to_sales')::numeric, (e.extended_data->>'priceToSalesTrailing12Months')::numeric ) AS e_price_to_sales",
        "COALESCE( (e.extended_data->'financial_ratios'->>'earnings_growth')::numeric, (e.extended_data->>'earningsGrowth')::numeric ) AS e_earnings_growth",
        "COALESCE( (e.extended_data->'financial_ratios'->>'revenue_growth')::numeric, (e.extended_data->>'revenueGrowth')::numeric ) AS e_revenue_growth",
    ]
    if flags.get("has_technical_indicators"):
        select_fields.extend([
            "ti.rsi AS ti_rsi",
            "ti.stoch_k AS ti_stoch_k",
        ])

    data_sql = f"""
        {cte_sql}
        SELECT 
          {', '.join(select_fields)}
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
        # Collect observation reasons in Python to avoid DB-specific JSON functions
        observation_reasons = []
        try:
            # Don't filter by string '[]' here since JSON/driver representations vary across DBs
            rows = conn.execute(text("SELECT observation_reasons FROM stocks_in_watchlist WHERE observation_reasons IS NOT NULL"))
            reasons_set = set()
            import json
            for r in rows.fetchall():
                val = r[0]
                if val is None:
                    continue
                # val may already be a Python list (DB driver) or a JSON string
                if isinstance(val, (list, tuple)):
                    for item in val:
                        if item:
                            reasons_set.add(str(item))
                else:
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, (list, tuple)):
                            for item in parsed:
                                if item:
                                    reasons_set.add(str(item))
                    except Exception:
                        # If not JSON, treat whole value as single reason
                        reasons_set.add(str(val))
            observation_reasons = sorted(reasons_set)
        except Exception:
            observation_reasons = []
    return {
        "countries": countries,
        "sectors": sectors,
        "industries": industries,
        "observation_reasons": observation_reasons,
    }
