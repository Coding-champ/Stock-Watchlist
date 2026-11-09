"""Orchestrate the session-only investment check without mutating holdings."""

from datetime import date
from typing import Any, Dict, Optional
import logging
from time import perf_counter

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models import AssetType, Stock, StockFundamentalData, StockPriceData
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.historical_price_service import HistoricalPriceService
from backend.app.services.investment_check_rules import evaluate_all
from backend.app.services.portfolio_service import PortfolioService
from backend.app.services.yfinance_service import get_fast_market_data

logger = logging.getLogger(__name__)

REFERENCE_ASSETS = [
    {"symbol": "^GSPC", "asset_type": "index"},
    {"symbol": "^IXIC", "asset_type": "index"},
    {"symbol": "^GDAXI", "asset_type": "index"},
    {"symbol": "^FTSE", "asset_type": "index"},
    {"symbol": "^N225", "asset_type": "index"},
]
MAX_PRICE_AGE_DAYS = 3


class InvestmentCheckService:
    """Collect check data and calculate a hypothetical allocation."""

    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.historical_service = HistoricalPriceService(db)
        self.comparison_service = ComparisonService(db)

    def _ensure_stock(self, identifier: str) -> Stock:
        stock = self.portfolio_service._resolve_stock(identifier)
        has_price = (
            self.db.query(StockPriceData)
            .filter(StockPriceData.stock_id == stock.id)
            .first()
        )
        if not has_price:
            try:
                # Unknown check symbols need local master data and prices, but
                # this only creates price history; it never creates a holding.
                self.historical_service.load_and_save_historical_prices(
                    stock.id, period="1y"
                )
            except Exception:
                logger.exception("Could not load prices for investment check stock_id=%s", stock.id)
        return stock

    def _latest_price(self, stock: Stock) -> Optional[StockPriceData]:
        return (
            self.db.query(StockPriceData)
            .filter(StockPriceData.stock_id == stock.id)
            .order_by(desc(StockPriceData.date))
            .first()
        )

    def _data_freshness(self, latest: Optional[StockPriceData]) -> Dict[str, Any]:
        """Describe price recency explicitly; do not silently use stale data."""
        if latest is None:
            return {
                "status": "missing",
                "latest_date": None,
                "age_days": None,
                "max_age_days": MAX_PRICE_AGE_DAYS,
                "is_stale": True,
            }

        age_days = (date.today() - latest.date).days
        return {
            "status": "stale" if age_days > MAX_PRICE_AGE_DAYS else "current",
            "latest_date": latest.date,
            "age_days": age_days,
            "max_age_days": MAX_PRICE_AGE_DAYS,
            "is_stale": age_days > MAX_PRICE_AGE_DAYS,
        }

    def _fundamentals(self, stock: Stock) -> Dict[str, Any]:
        row = (
            self.db.query(StockFundamentalData)
            .filter(StockFundamentalData.stock_id == stock.id)
            .order_by(desc(StockFundamentalData.period_end_date))
            .first()
        )
        if not row:
            return {}
        return {
            field: getattr(row, field)
            for field in (
                "period", "period_end_date", "revenue", "earnings", "profit_margin",
                "operating_margin", "return_on_equity", "debt_to_equity",
                "current_ratio", "free_cashflow",
            )
        }

    def _chart_data(self, stock: Stock) -> Dict[str, Any]:
        # TODO: Define per-step data availability and error semantics. Missing
        # history, stale prices, and calculation failures need distinct API
        # states instead of being represented only by an empty data object.
        rows = (
            self.db.query(StockPriceData)
            .filter(StockPriceData.stock_id == stock.id)
            .order_by(StockPriceData.date)
            .all()
        )
        if not rows:
            return {}
        closes = [row.close for row in rows if row.close is not None]
        latest = rows[-1]
        return {
            "latest_price": latest.close,
            "latest_date": latest.date,
            "observations": len(closes),
            "period_start": rows[0].date,
            "period_end": latest.date,
            "sma_20": sum(closes[-20:]) / min(len(closes), 20) if closes else None,
        }

    def _stock_metrics(self, stock: Stock, latest: Optional[StockPriceData]) -> Dict[str, Any]:
        fast = get_fast_market_data(stock.ticker_symbol) or {}
        return {
            "current_price": latest.close if latest else fast.get("last_price"),
            "market_cap": fast.get("market_cap"),
            "beta": fast.get("beta"),
            "volume": fast.get("last_volume"),
            "pe_ratio": fast.get("pe_ratio"),
            "currency": latest.currency if latest else fast.get("currency"),
        }

    def _seasonality(self, stock: Stock) -> Dict[str, Any]:
        frame = self.historical_service.get_price_dataframe(stock.id)
        if frame is None or frame.empty:
            return {}
        close_column = "close" if "close" in frame.columns else "Close"
        monthly = frame[close_column].resample("M").last().pct_change().dropna()
        current = monthly[monthly.index.month == date.today().month]
        return {
            "current_month": date.today().month,
            "historical_average_return": float(current.mean()) if not current.empty else None,
            "observations": int(current.count()),
        }

    def _peer_market(self, stock: Stock, benchmark: Dict[str, Any]) -> Dict[str, Any]:
        """Return real same-industry/sector peers for the check.

        Peer ranking is descriptive for now. Pass/fail remains disabled until
        the user defines the peer and benchmark thresholds.
        """
        group_field = "industry" if stock.industry else "sector"
        group_value = getattr(stock, group_field, None)
        if not group_value:
            return {"benchmark": benchmark, "peers": [], "peer_group": None}

        peers = (
            self.db.query(Stock)
            .filter(
                getattr(Stock, group_field) == group_value,
                Stock.id != stock.id,
            )
            .order_by(Stock.ticker_symbol)
            .limit(10)
            .all()
        )
        peer_rows = []
        for peer in peers:
            latest = self._latest_price(peer)
            if latest is None or latest.close is None:
                continue
            peer_rows.append({
                "stock_id": peer.id,
                "ticker_symbol": peer.ticker_symbol,
                "name": peer.name,
                "current_price": latest.close,
                "currency": latest.currency,
            })

        peer_rows.sort(key=lambda item: item["current_price"], reverse=True)
        for rank, peer in enumerate(peer_rows, start=1):
            peer["rank"] = rank

        return {
            "benchmark": benchmark,
            "peers": peer_rows,
            "peer_group": {"field": group_field, "value": group_value},
            "peer_count": len(peer_rows),
        }

    def _allocation(self, portfolio: Dict[str, Any], stock: Stock, quantity: float, price: Optional[float]) -> Dict[str, Any]:
        current_value = price * quantity if price is not None else None
        existing = sum(item["market_value"] or 0 for item in portfolio["holdings"])
        before = [
            {
                "ticker_symbol": item["ticker_symbol"],
                "value": item["market_value"],
                "weight_percent": (item["market_value"] or 0) / existing * 100 if existing else None,
            }
            for item in portfolio["holdings"]
        ]
        after_total = existing + (current_value or 0)
        after = [
            {
                "ticker_symbol": item["ticker_symbol"],
                "value": item["market_value"],
                "weight_percent": (item["market_value"] or 0) / after_total * 100 if after_total else None,
            }
            for item in portfolio["holdings"]
        ]
        after.append({
            "ticker_symbol": stock.ticker_symbol,
            "value": current_value,
            "weight_percent": current_value / after_total * 100 if current_value is not None and after_total else None,
        })
        return {
            "before": before,
            "after": after,
            "total_before": existing,
            "total_after": after_total,
            "currency_warning": portfolio["currency_warning"],
        }

    def run(self, identifier: str, quantity: float) -> Dict[str, Any]:
        portfolio = self.portfolio_service.get_portfolio()
        if not portfolio["holdings"]:
            raise ValueError("Für den Investitions-Check muss zuerst eine Portfolio-Position angelegt werden.")
        stock = self._ensure_stock(identifier)
        latest = self._latest_price(stock)
        freshness = self._data_freshness(latest)
        step_errors: Dict[str, Dict[str, str]] = {}
        step_timings: Dict[str, float] = {}

        def collect(step: str, callback):
            started = perf_counter()
            try:
                return callback()
            except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as exc:
                logger.exception("Investment check step failed: %s", step)
                step_errors[step] = {
                    "type": exc.__class__.__name__,
                    "message": str(exc) or "Unbekannter Fehler bei der Berechnung.",
                }
                return {}
            finally:
                step_timings[step] = round((perf_counter() - started) * 1000, 2)

        chart = collect("chart", lambda: self._chart_data(stock))
        # TODO: Integrate the existing RSI, MACD, Bollinger, and other
        # technical-indicator services here. The chart step currently exposes
        # only the basic SMA context and must not imply pattern recognition.
        fundamentals = collect("fundamentals", lambda: self._fundamentals(stock))
        metrics = collect("stock_metrics", lambda: self._stock_metrics(stock, latest))
        benchmark = collect(
            "benchmark",
            lambda: self.comparison_service.benchmark_comparison(stock.id, "^GSPC", "1y"),
        )
        peer_market = collect("peer_market", lambda: self._peer_market(stock, benchmark))
        seasonality = collect("seasonality", lambda: self._seasonality(stock))
        correlations = {}
        def collect_correlations():
            stock_prices = self.comparison_service._load_price_dataframe(
                stock.ticker_symbol, AssetType.STOCK, 252
            )
            stock_returns = self.comparison_service._compute_returns(stock_prices)
            for reference in REFERENCE_ASSETS:
                reference_prices = self.comparison_service._load_price_dataframe(
                    reference["symbol"], AssetType.INDEX, 252
                )
                correlations[reference["symbol"]] = self.comparison_service.calculate_correlation(
                    stock_returns,
                    self.comparison_service._compute_returns(reference_prices),
                )
            return correlations

        collect("dependent_assets", collect_correlations)
        allocation = collect(
            "allocation",
            lambda: self._allocation(portfolio, stock, quantity, metrics.get("current_price")),
        )

        data_by_step = {
            "chart": chart,
            "fundamentals": fundamentals,
            "stock_metrics": metrics,
            "peer_market": peer_market,
            "seasonality": seasonality,
            "dependent_assets": {"references": REFERENCE_ASSETS, "correlations": correlations},
            "allocation": allocation,
        }
        return {
            "input": {
                "identifier": identifier,
                "ticker_symbol": stock.ticker_symbol,
                "stock_id": stock.id,
                "quantity": quantity,
                "valid": bool(stock.ticker_symbol and quantity > 0),
            },
            "data_quality": {
                "price": freshness,
                "policy": (
                    "Kursdaten gelten bis zu drei Kalendertage als aktuell. "
                    "Veraltete oder fehlende Daten werden angezeigt und nicht "
                    "stillschweigend als bestanden bewertet."
                ),
            },
            "step_errors": step_errors,
            "step_timings_ms": step_timings,
            "steps": evaluate_all(data_by_step),
            "result": {
                "status": "not_evaluated",
                "reason": "Eine Gesamtbewertung bleibt offen, solange Schwellenwerte fehlen.",
            },
        }
