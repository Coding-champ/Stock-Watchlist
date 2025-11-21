from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from backend.app.services.screener_service import run_screener, get_filter_facets

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get("/run")
def run(
    q: Optional[str] = Query(default=None, description="Suche Ticker/Name"),
    country: Optional[str] = None,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    # Technical filters
    price_vs_sma50: Optional[str] = Query(default=None, description="above|below"),
    price_vs_sma200: Optional[str] = Query(default=None, description="above|below"),
    rsi_min: Optional[float] = Query(default=None, description="RSI minimum (0-100)"),
    rsi_max: Optional[float] = Query(default=None, description="RSI maximum (0-100)"),
    stochastic_status: Optional[str] = Query(default=None, description="oversold|overbought|neutral"),
    # Beta range
    beta_min: Optional[float] = None,
    beta_max: Optional[float] = None,
    # Market fundamentals
    market_cap_min: Optional[float] = Query(default=None, description="Minimum market cap"),
    market_cap_max: Optional[float] = Query(default=None, description="Maximum market cap"),
    pe_ratio_min: Optional[float] = Query(default=None, description="Minimum KGV/PE ratio"),
    pe_ratio_max: Optional[float] = Query(default=None, description="Maximum KGV/PE ratio"),
    price_to_sales_min: Optional[float] = Query(default=None, description="Minimum KUV/Price-to-Sales"),
    price_to_sales_max: Optional[float] = Query(default=None, description="Maximum KUV/Price-to-Sales"),
    earnings_growth_min: Optional[float] = Query(default=None, description="Minimum earnings growth"),
    earnings_growth_max: Optional[float] = Query(default=None, description="Maximum earnings growth"),
    revenue_growth_min: Optional[float] = Query(default=None, description="Minimum revenue growth"),
    revenue_growth_max: Optional[float] = Query(default=None, description="Maximum revenue growth"),
    # Fundamental ranges
    profit_margin_min: Optional[float] = None,
    roe_min: Optional[float] = None,
    current_ratio_min: Optional[float] = None,
    quick_ratio_min: Optional[float] = None,
    operating_cashflow_min: Optional[float] = None,
    free_cashflow_min: Optional[float] = None,
    shareholders_equity_min: Optional[float] = None,
    total_assets_min: Optional[float] = None,
    debt_to_equity_max: Optional[float] = None,
    total_liabilities_max: Optional[float] = None,
    # Observation reasons (from watchlist entries)
    observation_reason: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    sort: str = "ticker_symbol",
    order: str = "asc",
):
    filters: Dict[str, Any] = {
        k: v for k, v in {
            "q": q,
            "country": country,
            "sector": sector,
            "industry": industry,
            "price_vs_sma50": price_vs_sma50,
            "price_vs_sma200": price_vs_sma200,
            "rsi_min": rsi_min,
            "rsi_max": rsi_max,
            "stochastic_status": stochastic_status,
            "beta_min": beta_min,
            "beta_max": beta_max,
            "market_cap_min": market_cap_min,
            "market_cap_max": market_cap_max,
            "pe_ratio_min": pe_ratio_min,
            "pe_ratio_max": pe_ratio_max,
            "price_to_sales_min": price_to_sales_min,
            "price_to_sales_max": price_to_sales_max,
            "earnings_growth_min": earnings_growth_min,
            "earnings_growth_max": earnings_growth_max,
            "revenue_growth_min": revenue_growth_min,
            "revenue_growth_max": revenue_growth_max,
            "profit_margin_min": profit_margin_min,
            "roe_min": roe_min,
            "current_ratio_min": current_ratio_min,
            "quick_ratio_min": quick_ratio_min,
            "operating_cashflow_min": operating_cashflow_min,
            "free_cashflow_min": free_cashflow_min,
            "shareholders_equity_min": shareholders_equity_min,
            "total_assets_min": total_assets_min,
            "debt_to_equity_max": debt_to_equity_max,
            "total_liabilities_max": total_liabilities_max,
            "observation_reason": observation_reason,
        }.items() if v is not None and v != ""
    }
    return run_screener(filters, page=page, page_size=page_size, sort=sort, order=order)


@router.get("/filters")
def filters():
    return get_filter_facets()
