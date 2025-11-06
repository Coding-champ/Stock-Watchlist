"""
Backfill script: populate `exchange` and `currency` in `stock_price_data` rows

Strategy:
- Find all stock_id values that have price rows where exchange or currency is NULL
- For each stock, try the following in order:
  1. Read `extended_stock_data_cache.extended_data` JSON and look for exchange/currency fields
  2. If not found and configured, query yfinance (Ticker.info) for `exchange` and `currency`
- Update all rows for that stock where exchange/currency is NULL

Usage:
    python -m backend.app.scripts.backfill_stock_price_metadata --dry-run
    python -m backend.app.scripts.backfill_stock_price_metadata --batch 100 --use-yfinance

Be careful when running in production; the script updates rows in-place. By default it runs in dry-run mode.
"""

import argparse
import logging
import time
from typing import Optional

import yfinance as yf
from sqlalchemy import or_

from backend.app.database import SessionLocal
from backend.app.models import Stock, StockPriceData, ExtendedStockDataCache, StockInWatchlist

logger = logging.getLogger("backfill_stock_price_metadata")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def extract_from_extended(extended: dict) -> (Optional[str], Optional[str]):
    """Try common paths in extended data JSON to find exchange and currency"""
    if not extended or not isinstance(extended, dict):
        return None, None

    # Common keys
    exchange = extended.get("exchange") or extended.get("market") or extended.get("exchangeName")
    currency = extended.get("currency") or extended.get("quoteCurrency")

    # Nested possibilities
    if not exchange:
        # price_data or summaryDetail
        price_data = extended.get("price") or extended.get("price_data") or {}
        if isinstance(price_data, dict):
            exchange = exchange or price_data.get("exchange") or price_data.get("market")
            currency = currency or price_data.get("currency") or price_data.get("quoteCurrency")

    # yfinance's 'summaryDetail' nested keys
    summary = extended.get("summaryDetail") or extended.get("summary") or {}
    if isinstance(summary, dict):
        exchange = exchange or summary.get("exchange") or summary.get("market")
        currency = currency or summary.get("currency")

    # final cleanup
    if isinstance(exchange, str):
        exchange = exchange.strip() or None
    else:
        exchange = None
    if isinstance(currency, str):
        currency = currency.strip() or None
    else:
        currency = None

    return exchange, currency


def backfill(dry_run: bool = True, limit: Optional[int] = None, use_yfinance: bool = False, sleep_between: float = 0.5):
    session = SessionLocal()
    try:
        # Find stocks with missing metadata in their price rows
        q = session.query(StockPriceData.stock_id).filter(
            or_(StockPriceData.exchange == None, StockPriceData.currency == None)
        ).distinct()

        if limit:
            q = q.limit(limit)

        rows = q.all()
        stock_ids = [r[0] for r in rows]
        logger.info(f"Found {len(stock_ids)} stocks with missing exchange/currency (limit={limit})")

        summary = {
            "processed": 0,
            "updated_rows": 0,
            "skipped": 0,
            "failed": 0,
        }

        for sid in stock_ids:
            try:
                stock = session.query(Stock).filter(Stock.id == sid).first()
                if not stock:
                    logger.warning(f"Stock id {sid} not found in stocks table; skipping")
                    summary["skipped"] += 1
                    continue

                ticker = stock.ticker_symbol
                logger.info(f"Processing stock_id={sid} ticker={ticker}")

                # 1) Try stocks_in_watchlist entries (watchlist context often contains exchange/currency)
                exchange = None
                currency = None
                try:
                    entries = session.query(StockInWatchlist).filter(StockInWatchlist.stock_id == sid).all()
                    for e in entries:
                        if not exchange and getattr(e, 'exchange', None):
                            exchange = getattr(e, 'exchange')
                        if not currency and getattr(e, 'currency', None):
                            currency = getattr(e, 'currency')
                        if exchange and currency:
                            break
                    if exchange or currency:
                        logger.info(f"  -> Found from stocks_in_watchlist: exchange={exchange} currency={currency}")
                except Exception as e:
                    logger.debug(f"  -> Failed to read stocks_in_watchlist for {ticker}: {e}")

                # 2) Try extended cache
                cache = session.query(ExtendedStockDataCache).filter(ExtendedStockDataCache.stock_id == sid).first()
                if cache and cache.extended_data and (not exchange or not currency):
                    try:
                        ex, cur = extract_from_extended(cache.extended_data)
                        exchange = exchange or ex
                        currency = currency or cur
                        if ex or cur:
                            logger.info(f"  -> Found from extended cache: exchange={ex} currency={cur}")
                    except Exception as e:
                        logger.debug(f"  -> Failed to extract from extended cache for {ticker}: {e}")

                # 2) Fallback to yfinance if allowed
                if (not exchange or not currency) and use_yfinance:
                    try:
                        logger.info(f"  -> Querying yfinance for {ticker}")
                        t = yf.Ticker(ticker)
                        info = t.info or {}
                        exchange = exchange or info.get("exchange") or info.get("market")
                        currency = currency or info.get("currency")
                        logger.info(f"  -> yfinance returned: exchange={exchange} currency={currency}")
                        time.sleep(sleep_between)
                    except Exception as e:
                        logger.warning(f"  -> yfinance lookup failed for {ticker}: {e}")

                # If still nothing, skip
                if not exchange and not currency:
                    logger.info(f"  -> No exchange/currency info found for {ticker}; skipping")
                    summary["skipped"] += 1
                    continue

                # Build update dict only for non-None values
                update_vals = {}
                if exchange:
                    update_vals[StockPriceData.exchange] = exchange
                if currency:
                    update_vals[StockPriceData.currency] = currency

                # Count rows that would be updated
                target_q = session.query(StockPriceData).filter(
                    StockPriceData.stock_id == sid,
                    or_(StockPriceData.exchange == None, StockPriceData.currency == None)
                )
                rows_to_update = target_q.count()

                if rows_to_update == 0:
                    logger.info(f"  -> No rows to update for {ticker}")
                    summary["skipped"] += 1
                    continue

                logger.info(f"  -> Will update {rows_to_update} rows for stock {ticker} with {update_vals}")

                if not dry_run:
                    res = target_q.update(update_vals, synchronize_session=False)
                    session.commit()
                    summary["updated_rows"] += res
                    logger.info(f"  -> Updated {res} rows for {ticker}")
                else:
                    logger.info(f"  -> Dry run: not updating database")

                summary["processed"] += 1

            except Exception as e:
                logger.exception(f"Failed processing stock_id={sid}: {e}")
                session.rollback()
                summary["failed"] += 1

        logger.info(f"Backfill complete: {summary}")
        return summary

    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill exchange/currency into stock_price_data")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes to DB (default: True)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of stocks to process")
    parser.add_argument("--use-yfinance", action="store_true", help="Allow fallback to yfinance when extended cache missing")
    parser.add_argument("--sleep", type=float, default=0.5, help="Seconds to sleep between yfinance calls to avoid rate limits")

    args = parser.parse_args()

    # Default dry-run True unless explicitly disabled
    dry_run = bool(args.dry_run)

    logger.info(f"Starting backfill (dry_run={dry_run}, limit={args.limit}, use_yfinance={args.use_yfinance})")
    summary = backfill(dry_run=dry_run, limit=args.limit, use_yfinance=args.use_yfinance, sleep_between=args.sleep)
    logger.info("Done. Summary:\n%s", summary)


if __name__ == "__main__":
    main()
