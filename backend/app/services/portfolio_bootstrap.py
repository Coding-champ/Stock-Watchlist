"""Ensure the single v1 default portfolio row exists."""

from sqlalchemy.orm import Session

from backend.app.models import DEFAULT_PORTFOLIO_NAME, Portfolio


def ensure_default_portfolio(db: Session) -> Portfolio:
    """Return the implicit v1 portfolio, creating it if missing.

    UI must not offer a portfolio picker; additional named portfolios are a
    later feature that can reuse this table.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.name == DEFAULT_PORTFOLIO_NAME).first()
    if portfolio:
        return portfolio
    portfolio = Portfolio(name=DEFAULT_PORTFOLIO_NAME)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio
