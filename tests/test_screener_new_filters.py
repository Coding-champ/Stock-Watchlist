"""
Test script for new screener filters:
- RSI
- Slow Stochastic (oversold/overbought)
- Market Cap
- PE Ratio (KGV)
- Price-to-Sales (KUV)
- Earnings Growth
- Revenue Growth
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.screener_service import run_screener


def test_rsi_filter():
    """Test RSI filter"""
    print("\n=== Testing RSI Filter ===")
    
    # Test RSI oversold (< 30)
    filters = {"rsi_min": 0, "rsi_max": 30}
    result = run_screener(filters, page=1, page_size=5)
    print(f"RSI oversold (0-30): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}: RSI={stock.get('ti_rsi', 'N/A')}")
    
    # Test RSI overbought (> 70)
    filters = {"rsi_min": 70, "rsi_max": 100}
    result = run_screener(filters, page=1, page_size=5)
    print(f"\nRSI overbought (70-100): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}: RSI={stock.get('ti_rsi', 'N/A')}")


def test_stochastic_filter():
    """Test Stochastic filter"""
    print("\n=== Testing Stochastic Filter ===")
    
    # Test oversold
    filters = {"stochastic_status": "oversold"}
    result = run_screener(filters, page=1, page_size=5)
    print(f"Stochastic oversold: Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}: Stoch %K={stock.get('ti_stoch_k', 'N/A')}")
    
    # Test overbought
    filters = {"stochastic_status": "overbought"}
    result = run_screener(filters, page=1, page_size=5)
    print(f"\nStochastic overbought: Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}: Stoch %K={stock.get('ti_stoch_k', 'N/A')}")


def test_market_cap_filter():
    """Test Market Cap filter"""
    print("\n=== Testing Market Cap Filter ===")
    
    # Test large cap (> 10 billion)
    filters = {"market_cap_min": 10_000_000_000}
    result = run_screener(filters, page=1, page_size=5)
    print(f"Large cap (>10B): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            mc = stock.get('e_market_cap')
            try:
                mc_val = float(mc) if mc is not None else None
            except Exception:
                mc_val = None
            mc_str = (
                f"{mc_val/1e9:.2f}B" if mc_val and mc_val >= 1e9 else (
                    f"{mc_val/1e6:.2f}M" if mc_val and mc_val >= 1e6 else (f"{mc_val:.0f}" if mc_val else "N/A")
                )
            )
            print(f"  {stock['ticker_symbol']}: Market Cap={mc_str}")


def test_pe_ratio_filter():
    """Test PE Ratio (KGV) filter"""
    print("\n=== Testing PE Ratio Filter ===")
    
    # Test low PE (value stocks)
    filters = {"pe_ratio_min": 0, "pe_ratio_max": 15}
    result = run_screener(filters, page=1, page_size=5)
    print(f"Low PE (0-15): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}: PE={stock.get('e_pe_ratio', 'N/A')}")


def test_price_to_sales_filter():
    """Test Price-to-Sales (KUV) filter"""
    print("\n=== Testing Price-to-Sales Filter ===")
    
    # Test low P/S
    filters = {"price_to_sales_min": 0, "price_to_sales_max": 2}
    result = run_screener(filters, page=1, page_size=5)
    print(f"Low P/S (0-2): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}: P/S={stock.get('e_price_to_sales', 'N/A')}")


def test_growth_filters():
    """Test Earnings and Revenue Growth filters"""
    print("\n=== Testing Growth Filters ===")
    
    # Test high earnings growth
    filters = {"earnings_growth_min": 0.15}  # 15% or more
    result = run_screener(filters, page=1, page_size=5)
    print(f"High earnings growth (>15%): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            eg = stock.get('e_earnings_growth')
            eg_str = f"{eg*100:.2f}%" if eg is not None else "N/A"
            print(f"  {stock['ticker_symbol']}: Earnings Growth={eg_str}")
    
    # Test high revenue growth
    filters = {"revenue_growth_min": 0.10}  # 10% or more
    result = run_screener(filters, page=1, page_size=5)
    print(f"\nHigh revenue growth (>10%): Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            rg = stock.get('e_revenue_growth')
            rg_str = f"{rg*100:.2f}%" if rg is not None else "N/A"
            print(f"  {stock['ticker_symbol']}: Revenue Growth={rg_str}")


def test_combined_filters():
    """Test combination of multiple filters"""
    print("\n=== Testing Combined Filters ===")
    
    # Growth stocks with reasonable valuation
    filters = {
        "earnings_growth_min": 0.10,  # 10%+ earnings growth
        "revenue_growth_min": 0.10,   # 10%+ revenue growth
        "pe_ratio_max": 30,            # PE < 30
        "market_cap_min": 1_000_000_000  # > 1B market cap
    }
    result = run_screener(filters, page=1, page_size=5)
    print(f"Growth stocks with reasonable valuation: Found {result['total']} stocks")
    if result['results']:
        print("Sample results:")
        for stock in result['results'][:3]:
            print(f"  {stock['ticker_symbol']}:")
            print(f"    PE: {stock.get('e_pe_ratio', 'N/A')}")
            eg = stock.get('e_earnings_growth')
            print(f"    Earnings Growth: {eg*100:.2f}%" if eg else "    Earnings Growth: N/A")
            rg = stock.get('e_revenue_growth')
            print(f"    Revenue Growth: {rg*100:.2f}%" if rg else "    Revenue Growth: N/A")
            mc = stock.get('e_market_cap')
            try:
                mc_val = float(mc) if mc is not None else None
            except Exception:
                mc_val = None
            if mc_val:
                disp = mc_val/1e9
                print(f"    Market Cap: {disp:.2f}B")
            else:
                print("    Market Cap: N/A")


if __name__ == "__main__":
    print("Testing new screener filters...")
    
    try:
        test_rsi_filter()
        test_stochastic_filter()
        test_market_cap_filter()
        test_pe_ratio_filter()
        test_price_to_sales_filter()
        test_growth_filters()
        test_combined_filters()
        
        print("\n" + "="*50)
        print("All tests completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
