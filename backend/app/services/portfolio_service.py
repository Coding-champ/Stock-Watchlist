"""Portfolio v1 operations and read-time valuation."""

from datetime import date
from typing import Dict, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from backend.app.models import (
    DEFAULT_PORTFOLIO_NAME,
    Holding,
    Portfolio,
    Stock,
    StockPriceData,
)
from backend.app.services.portfolio_bootstrap import ensure_default_portfolio
from backend.app.services.yfinance_service import get_stock_info_by_identifier


MIXED_CURRENCY_WARNING = (
    "Die Gesamtsumme addiert Börsenwährungen ohne Umrechnung und ist bei "
    "mehreren Währungen nicht vergleichbar."
)


class PortfolioService:
    """Manage the single implicit v1 portfolio."""

    def __init__(self, db: Session):
        self.db = db

    def get_default_portfolio(self) -> Portfolio:
        return ensure_default_portfolio(self.db)

    def _resolve_stock(self, identifier: str) -> Stock:
        normalized = identifier.strip().upper()
        if not normalized:
            raise ValueError("Identifier darf nicht leer sein.")
        stock = (
            self.db.query(Stock)
            .filter(or_(Stock.ticker_symbol == normalized, Stock.isin == normalized))
            .first()
        )
        if stock:
            return stock

        stock_info = get_stock_info_by_identifier(normalized)
        if not stock_info:
            raise ValueError(f"Keine Aktie für Identifier '{identifier}' gefunden.")

        stock = Stock(
            ticker_symbol=stock_info.ticker.upper(),
            name=stock_info.name or stock_info.ticker,
            isin=stock_info.isin,
            country=stock_info.country,
            industry=stock_info.industry,
            sector=stock_info.sector,
            business_summary=stock_info.business_summary,
        )
        self.db.add(stock)
        self.db.flush()
        return stock

    def _latest_price(self, stock_id: int) -> Optional[StockPriceData]:
        return (
            self.db.query(StockPriceData)
            .filter(StockPriceData.stock_id == stock_id)
            .order_by(desc(StockPriceData.date))
            .first()
        )

    def _holding_dict(self, holding: Holding) -> Dict:
        latest = self._latest_price(holding.stock_id)
        current_price = latest.close if latest else None
        currency = latest.currency if latest else None
        market_value = current_price * holding.quantity if current_price is not None else None
        profit_loss = (
            (current_price - holding.purchase_price) * holding.quantity
            if current_price is not None
            else None
        )
        invested = holding.purchase_price * holding.quantity
        return {
            "id": holding.id,
            "stock_id": holding.stock_id,
            "ticker_symbol": holding.stock.ticker_symbol,
            "isin": holding.stock.isin,
            "name": holding.stock.name,
            "quantity": holding.quantity,
            "purchase_price": holding.purchase_price,
            "purchase_date": holding.purchase_date,
            "current_price": current_price,
            "currency": currency,
            "market_value": market_value,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss / invested * 100 if profit_loss is not None and invested else None,
        }

    def get_portfolio(self) -> Dict:
        portfolio = self.get_default_portfolio()
        holdings = (
            self.db.query(Holding)
            .options(joinedload(Holding.stock))
            .filter(Holding.portfolio_id == portfolio.id)
            .order_by(Holding.id)
            .all()
        )
        items = [self._holding_dict(holding) for holding in holdings]
        currencies = {item["currency"] for item in items if item["currency"]}
        # v1 deliberately performs no FX conversion; values in mixed currencies
        # are naively added and explicitly marked as not comparable.
        return {
            "id": portfolio.id,
            "name": portfolio.name,
            "holdings": items,
            "total_value": sum(item["market_value"] or 0 for item in items),
            "has_mixed_currencies": len(currencies) > 1,
            "currency_warning": MIXED_CURRENCY_WARNING if len(currencies) > 1 else None,
        }

    def add_holding(
        self,
        identifier: str,
        quantity: float,
        purchase_price: float,
        purchase_date: date,
    ) -> Holding:
        portfolio = self.get_default_portfolio()
        stock = self._resolve_stock(identifier)
        holding = (
            self.db.query(Holding)
            .filter(Holding.portfolio_id == portfolio.id, Holding.stock_id == stock.id)
            .first()
        )
        if holding:
            return self.buy_holding(holding.id, quantity, purchase_price, purchase_date)

        # A holding is one row per stock; future buys must use the weighted
        # averaging endpoint rather than overwriting these values.
        holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
        )
        self.db.add(holding)
        self.db.commit()
        self.db.refresh(holding)
        return holding

    def buy_holding(
        self,
        holding_id: int,
        quantity: float,
        purchase_price: float,
        purchase_date: Optional[date] = None,
    ) -> Holding:
        portfolio = self.get_default_portfolio()
        holding = (
            self.db.query(Holding)
            .filter(Holding.id == holding_id, Holding.portfolio_id == portfolio.id)
            .first()
        )
        if not holding:
            raise LookupError("Holding nicht gefunden.")

        # Nachkauf uses a quantity-weighted average; it is not FIFO or an
        # unweighted average, and the first purchase date remains unchanged.
        old_quantity = holding.quantity
        holding.purchase_price = (
            old_quantity * holding.purchase_price + quantity * purchase_price
        ) / (old_quantity + quantity)
        holding.quantity = old_quantity + quantity
        self.db.commit()
        self.db.refresh(holding)
        return holding

    def delete_holding(self, holding_id: int) -> None:
        portfolio = self.get_default_portfolio()
        holding = (
            self.db.query(Holding)
            .filter(Holding.id == holding_id, Holding.portfolio_id == portfolio.id)
            .first()
        )
        if not holding:
            raise LookupError("Holding nicht gefunden.")
        self.db.delete(holding)
        self.db.commit()
