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
    # Beta range
    beta_min: Optional[float] = None,
    beta_max: Optional[float] = None,
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
            "beta_min": beta_min,
            "beta_max": beta_max,
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
        }.items() if v is not None and v != ""
    }
    return run_screener(filters, page=page, page_size=page_size, sort=sort, order=order)


@router.get("/filters")
def filters():
    return get_filter_facets()
