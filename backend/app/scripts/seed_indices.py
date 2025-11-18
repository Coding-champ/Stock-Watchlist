"""
Seed Indices Script
Creates initial market indices and loads their constituents from CSV files
"""

import sys
from pathlib import Path
import logging
import time
from datetime import date
import csv
import yfinance as yf

# Setup path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.services.index_service import IndexService
from backend.app.services.index_constituent_service import IndexConstituentService
from backend.app.services.stock_service import StockService
from backend.app.models import Stock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Index definitions: (ticker, name, region, type, calc_method, benchmark, description)
INDICES = [
    # US Broad Market
    ("^GSPC", "S&P 500", "US", "broad_market", "market_cap_weighted", None, "US large-cap equity benchmark tracking 500 leading companies"),
    ("^DJI", "Dow Jones Industrial Average", "US", "broad_market", "price_weighted", None, "US blue-chip index of 30 major companies"),
    ("^IXIC", "NASDAQ Composite", "US", "broad_market", "market_cap_weighted", None, "Broad-based index of all NASDAQ-listed stocks"),
    ("^NDX", "NASDAQ-100", "US", "broad_market", "market_cap_weighted", None, "100 largest non-financial NASDAQ companies"),
    ("^RUT", "Russell 2000", "US", "broad_market", "market_cap_weighted", None, "Small-cap equity benchmark"),
    
    # US Sector Indices (S&P 500 sectors)
    ("XLK", "Technology Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Technology sector"),
    ("XLF", "Financial Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Financial sector"),
    ("XLV", "Health Care Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Healthcare sector"),
    ("XLE", "Energy Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Energy sector"),
    ("XLI", "Industrial Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Industrial sector"),
    ("XLP", "Consumer Staples Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Consumer Staples sector"),
    ("XLY", "Consumer Discretionary Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Consumer Discretionary sector"),
    ("XLU", "Utilities Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Utilities sector"),
    ("XLB", "Materials Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Materials sector"),
    ("XLRE", "Real Estate Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Real Estate sector"),
    ("XLC", "Communication Services Select Sector SPDR", "US", "sector", "market_cap_weighted", "^GSPC", "S&P 500 Communication Services sector"),
    
    # European Indices
    ("^GDAXI", "DAX 40", "Germany", "broad_market", "market_cap_weighted", None, "German blue-chip index of 40 major companies"),
    ("^STOXX50E", "EURO STOXX 50", "Europe", "broad_market", "market_cap_weighted", None, "50 leading companies from Eurozone"),
    ("^FTSE", "FTSE 100", "UK", "broad_market", "market_cap_weighted", None, "100 largest companies on London Stock Exchange"),
    ("^FCHI", "CAC 40", "France", "broad_market", "market_cap_weighted", None, "40 largest companies on Euronext Paris"),
    
    # Asian Indices
    ("^N225", "Nikkei 225", "Japan", "broad_market", "price_weighted", None, "Japanese stock market index"),
    ("^HSI", "Hang Seng Index", "Hong Kong", "broad_market", "market_cap_weighted", None, "Hong Kong stock market index"),
    ("000001.SS", "SSE Composite Index", "China", "broad_market", "market_cap_weighted", None, "Shanghai Stock Exchange Composite"),
]


def seed_indices(db: Session):
    """Create indices in database"""
    logger.info("Creating indices...")
    index_service = IndexService(db)
    
    created_indices = []
    for ticker, name, region, idx_type, calc_method, benchmark, description in INDICES:
        try:
            index = index_service.create_index(
                ticker_symbol=ticker,
                name=name,
                region=region,
                index_type=idx_type,
                calculation_method=calc_method,
                benchmark_index=benchmark,
                description=description
            )
            created_indices.append(index)
            logger.info(f"  ✓ Created: {name} ({ticker})")
        except Exception as e:
            logger.error(f"  ✗ Failed to create {name}: {e}")
    
    return created_indices


def load_index_prices(db: Session, indices):
    """Load historical price data for all indices"""
    logger.info("\nLoading historical price data...")
    index_service = IndexService(db)
    
    for index in indices:
        try:
            logger.info(f"  Loading prices for {index.name}...")
            result = index_service.load_index_price_data(
                ticker_symbol=index.ticker_symbol,
                period="max",
                interval="1d"
            )
            
            if result["success"]:
                logger.info(f"    ✓ Loaded {result['count']} price records")
                logger.info(f"      Date range: {result['date_range']['start']} to {result['date_range']['end']}")
            else:
                logger.warning(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
            
            # Rate limiting (yfinance has limits)
            time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"  ✗ Error loading prices for {index.name}: {e}")


def create_missing_stocks(db: Session, csv_mappings: dict):
    """
    Pre-scan CSV files and create missing stocks in database
    """
    logger.info("\nChecking for missing stocks and creating them...")
    
    # Collect all unique tickers from CSVs
    all_tickers = set()
    for csv_path in csv_mappings.values():
        csv_file = Path(project_root) / csv_path
        if not csv_file.exists():
            continue
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('ticker_symbol', '').strip()
                if ticker:
                    all_tickers.add(ticker)
    
    logger.info(f"  Found {len(all_tickers)} unique tickers in CSV files")
    
    # Check which stocks already exist
    existing_tickers = set()
    for ticker in all_tickers:
        stock = db.query(Stock).filter(Stock.ticker_symbol == ticker).first()
        if stock:
            existing_tickers.add(ticker)
    
    missing_tickers = all_tickers - existing_tickers
    logger.info(f"  {len(existing_tickers)} stocks already exist")
    logger.info(f"  {len(missing_tickers)} stocks need to be created")
    
    if not missing_tickers:
        logger.info("  ✓ All stocks already exist!")
        return
    
    # Create missing stocks
    stock_service = StockService(db)
    created_count = 0
    failed_count = 0
    
    for ticker in missing_tickers:
        try:
            logger.info(f"    Creating stock: {ticker}")
            
            # Fetch stock info from yfinance
            yf_ticker = yf.Ticker(ticker)
            info = {}
            try:
                info = yf_ticker.info or {}
            except Exception as e:
                logger.warning(f"      ⚠ Could not fetch yfinance info: {e}")
            
            # Extract data with fallbacks
            name = info.get('longName') or info.get('shortName') or ticker
            country = info.get('country')
            industry = info.get('industry')
            sector = info.get('sector')
            business_summary = info.get('longBusinessSummary')
            
            # Create stock
            stock = stock_service.create_stock(
                ticker_symbol=ticker,
                name=name,
                country=country,
                industry=industry,
                sector=sector,
                business_summary=business_summary
            )
            
            created_count += 1
            logger.info(f"      ✓ Created: {name}")
            
            # Rate limiting for yfinance
            time.sleep(1.5)
            
        except Exception as e:
            failed_count += 1
            logger.error(f"      ✗ Failed to create {ticker}: {e}")
    
    logger.info(f"\n  Summary: Created {created_count} stocks, {failed_count} failed")


def import_constituents(db: Session):
    """Import constituents from CSV files for major indices"""
    logger.info("\nImporting constituents from CSV files...")
    
    index_service = IndexService(db)
    constituent_service = IndexConstituentService(db)
    
    # Map ticker to CSV file
    csv_mappings = {
        "^GSPC": "data/index_constituents/sp500.csv",
        "^GDAXI": "data/index_constituents/dax40.csv",
        "^NDX": "data/index_constituents/nasdaq100.csv",
        "^FTSE": "data/index_constituents/ftse100.csv",
        "^N225": "data/index_constituents/nikkei225.csv",
        "^STOXX50E": "data/index_constituents/eurostoxx50.csv",
        "^HSI": "data/index_constituents/hangseng.csv",
        "^FCHI": "data/index_constituents/cac40.csv",
        "^RUT": "data/index_constituents/russell2000.csv",
    }
    
    # First, create missing stocks
    create_missing_stocks(db, csv_mappings)
    
    # Now import constituents
    for ticker, csv_path in csv_mappings.items():
        csv_file = Path(project_root) / csv_path
        
        if not csv_file.exists():
            logger.warning(f"  ✗ CSV file not found: {csv_file}")
            continue
        
        # Get index
        index = index_service.get_index_by_symbol(ticker)
        if not index:
            logger.warning(f"  ✗ Index not found: {ticker}")
            continue
        
        logger.info(f"  Importing constituents for {index.name}...")
        
        try:
            result = constituent_service.import_constituents_from_csv(
                index_id=index.id,
                csv_file_path=str(csv_file),
                replace_existing=True
            )
            
            if result["success"]:
                logger.info(f"    ✓ Imported {result['imported']} constituents")
                if result['skipped'] > 0:
                    logger.info(f"      Skipped {result['skipped']} entries")
                if result.get('errors'):
                    for error in result['errors'][:5]:  # Show first 5 errors
                        logger.warning(f"      ! {error}")
            else:
                logger.error(f"    ✗ Import failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"  ✗ Error importing constituents for {index.name}: {e}")


def ensure_stocks_exist(db: Session):
    """
    Check if necessary stocks exist in database.
    This function is now deprecated as create_missing_stocks handles this.
    """
    logger.info("\nNote: Stock existence will be checked during constituent import...")


def main():
    """Main seeding function"""
    logger.info("=" * 60)
    logger.info("INDICES SEEDING SCRIPT")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create indices
        indices = seed_indices(db)
        logger.info(f"\n✓ Created {len(indices)} indices")
        
        # Step 2: Load price data
        load_index_prices(db, indices)
        
        # Step 3: Import constituents (now creates missing stocks automatically)
        import_constituents(db)
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ SEEDING COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
