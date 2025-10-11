import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from backend.app.models import Stock as StockModel
from backend.app.services.yfinance_service import get_chart_data
from backend.app.services.cache_service import get_cached_chart_data, cache_chart_data


class ChartDataServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ChartDataService:
    def __init__(self, db: Session):
        self._db = db
        self._logger = logging.getLogger(__name__)

    def _get_stock(self, stock_id: int) -> StockModel:
        stock = self._db.query(StockModel).filter(StockModel.id == stock_id).first()
        if not stock:
            raise ChartDataServiceError(404, "Stock not found")
        return stock

    def get_chart_data(
        self,
        stock_id: int,
        period: str,
        interval: str,
        include_volume: bool,
        start: Optional[str],
        end: Optional[str],
    ) -> Dict[str, Any]:
        stock = self._get_stock(stock_id)
        ticker = stock.ticker_symbol
        use_cache = not start and not end

        if use_cache:
            try:
                cached_data = get_cached_chart_data(ticker, period, interval)
                if cached_data:
                    self._logger.debug(f"Using cached chart data for {ticker} ({period}/{interval})")
                    return cached_data
            except Exception as exc:
                self._logger.warning(f"Failed to retrieve cached chart data: {exc}")

        try:
            chart_data = get_chart_data(
                ticker_symbol=ticker,
                period=period if use_cache else None,
                interval=interval,
                start=start,
                end=end,
                include_dividends=True,
                include_volume=include_volume,
            )
        except Exception as exc:
            self._logger.error(f"Error fetching chart data for {ticker}: {exc}")
            raise ChartDataServiceError(500, f"Failed to fetch chart data: {exc}") from exc

        if not chart_data:
            raise ChartDataServiceError(404, f"No chart data found for {ticker}")

        if use_cache:
            ttl = 1800 if interval in ["1m", "5m", "15m", "30m"] else 3600
            try:
                cache_chart_data(ticker, period, interval, chart_data, ttl=ttl)
            except Exception as exc:
                self._logger.warning(f"Failed to cache chart data: {exc}")

        return chart_data

    def get_intraday_chart(self, stock_id: int, days: int) -> Dict[str, Any]:
        stock = self._get_stock(stock_id)
        period_map = {
            1: ("1d", "5m"),
            2: ("2d", "5m"),
            5: ("5d", "5m"),
        }
        period, interval = period_map.get(days, ("1d", "5m"))

        try:
            chart_data = get_chart_data(
                ticker_symbol=stock.ticker_symbol,
                period=period,
                interval=interval,
                include_dividends=False,
                include_volume=True,
            )
        except Exception as exc:
            self._logger.error(f"Error fetching intraday data for {stock.ticker_symbol}: {exc}")
            raise ChartDataServiceError(500, f"Failed to fetch intraday data: {exc}") from exc

        if not chart_data:
            raise ChartDataServiceError(404, f"No intraday data found for {stock.ticker_symbol}")

        return chart_data
