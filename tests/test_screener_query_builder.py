"""Tests for screener_query_builder utility."""
from backend.app.utils.screener_query_builder import build_query_parts


def test_build_query_parts_empty_filters():
    """Empty filters should produce base CTEs and joins without WHERE clause."""
    cte_sql, where_with_joins, params = build_query_parts({})
    assert "WITH" in cte_sql
    assert "latest_fundamental" in cte_sql
    assert "LEFT JOIN latest_fundamental lf" in where_with_joins
    assert "LEFT JOIN extended_stock_data_cache e" in where_with_joins
    assert "WHERE" not in where_with_joins
    assert params == {}


def test_build_query_parts_simple_text_filters():
    """Test simple textual filters (country, sector, industry)."""
    filters = {"country": "USA", "sector": "Technology", "industry": "Software"}
    cte_sql, where_with_joins, params = build_query_parts(filters)
    assert "WHERE" in where_with_joins
    assert "LOWER(s.country) = :country" in where_with_joins
    assert "LOWER(s.sector) = :sector" in where_with_joins
    assert "LOWER(s.industry) = :industry" in where_with_joins
    assert params["country"] == "usa"
    assert params["sector"] == "technology"
    assert params["industry"] == "software"


def test_build_query_parts_beta_range():
    """Test beta min/max filters from extended cache."""
    filters = {"beta_min": 0.5, "beta_max": 1.5}
    cte_sql, where_with_joins, params = build_query_parts(filters)
    assert "beta_min" in params
    assert "beta_max" in params
    assert params["beta_min"] == 0.5
    assert params["beta_max"] == 1.5
    assert "(e.extended_data->>'beta')::numeric >= :beta_min" in where_with_joins
    assert "(e.extended_data->>'beta')::numeric <= :beta_max" in where_with_joins


def test_build_query_parts_fundamental_filters():
    """Test fundamental ratio min/max filters."""
    filters = {
        "profit_margin_min": 0.1,
        "roe_min": 0.15,
        "debt_to_equity_max": 2.0,
    }
    cte_sql, where_with_joins, params = build_query_parts(filters)
    assert params["profit_margin_min"] == 0.1
    assert params["roe_min"] == 0.15
    assert params["debt_to_equity_max"] == 2.0
    assert "(lf.profit_margin >= :profit_margin_min)" in where_with_joins
    assert "(lf.return_on_equity >= :roe_min)" in where_with_joins
    assert "(lf.debt_to_equity <= :debt_to_equity_max)" in where_with_joins


def test_build_query_parts_price_vs_sma():
    """Test technical filters (price vs SMA50/SMA200) produce price_calc CTE."""
    filters = {"price_vs_sma50": "above", "price_vs_sma200": "below"}
    cte_sql, where_with_joins, params = build_query_parts(filters)
    assert "price_calc" in cte_sql
    assert "LEFT JOIN price_calc pc" in where_with_joins
    assert "(pc.close >= pc.sma50)" in where_with_joins
    assert "(pc.close <= pc.sma200)" in where_with_joins


def test_build_query_parts_search_query():
    """Test search query (q) produces LIKE filter."""
    filters = {"q": "AAPL"}
    cte_sql, where_with_joins, params = build_query_parts(filters)
    assert "q" in params
    assert params["q"] == "%aapl%"
    assert "LOWER(s.ticker_symbol) LIKE :q" in where_with_joins


def test_build_query_parts_observation_reason_fallback():
    """Test observation_reason filter with generic fallback (no engine)."""
    filters = {"observation_reason": "dividend"}
    cte_sql, where_with_joins, params = build_query_parts(filters, engine=None)
    # Without engine, should fall back to text matching
    assert "_obs_like" in params
    assert params["_obs_like"] == "%dividend%"
    assert "stocks_in_watchlist si" in where_with_joins
