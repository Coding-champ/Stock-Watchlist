"""
Test Volume Profile Analysis
Run with: python tests/test_volume_profile.py
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_volume_profile_full(stock_id: int, ticker: str):
    """Test full volume profile calculation"""
    print_section(f"FULL VOLUME PROFILE - {ticker}")
    
    response = requests.get(
        f"{BASE_URL}/stock-data/{stock_id}/volume-profile",
        params={
            "period_days": 30,
            "num_bins": 50
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"\n📊 Stock: {data['ticker_symbol']}")
        print(f"Period: {data['period']['start']} to {data['period']['end']} ({data['period']['days']} trading days)")
        
        print(f"\n🎯 Point of Control (POC):")
        print(f"  Price: ${data['poc']:.2f}")
        print(f"  Volume: {data['poc_volume']:,.0f}")
        
        print(f"\n📈 Value Area (70% Volume):")
        va = data['value_area']
        print(f"  High: ${va['high']:.2f}")
        print(f"  Low: ${va['low']:.2f}")
        print(f"  Range: ${va['high'] - va['low']:.2f}")
        print(f"  Volume: {va['volume']:,.0f} ({va['volume_percent']:.1f}%)")
        
        print(f"\n💹 Price Range:")
        pr = data['price_range']
        print(f"  Min: ${pr['min']:.2f}")
        print(f"  Max: ${pr['max']:.2f}")
        print(f"  Range: ${pr['range']:.2f}")
        
        print(f"\n📊 Volume Statistics:")
        print(f"  Total Volume: {data['total_volume']:,.0f}")
        print(f"  Number of Bins: {data['num_bins']}")
        print(f"  Bin Size: ${data['bin_size']:.4f}")
        
        print(f"\n🔴 High Volume Nodes (HVN): {len(data['hvn_levels'])} levels")
        if data['hvn_levels']:
            print(f"  Prices: {', '.join([f'${p:.2f}' for p in data['hvn_levels'][:5]])}")
            if len(data['hvn_levels']) > 5:
                print(f"  ... and {len(data['hvn_levels']) - 5} more")
        
        print(f"\n🔵 Low Volume Nodes (LVN): {len(data['lvn_levels'])} levels")
        if data['lvn_levels']:
            print(f"  Prices: {', '.join([f'${p:.2f}' for p in data['lvn_levels'][:5]])}")
            if len(data['lvn_levels']) > 5:
                print(f"  ... and {len(data['lvn_levels']) - 5} more")
        
        # Show top 10 volume levels
        print(f"\n📊 Top 10 Volume Levels:")
        # Combine price levels and volumes
        levels_with_volume = list(zip(data['price_levels'], data['volumes']))
        # Sort by volume descending
        levels_with_volume.sort(key=lambda x: x[1], reverse=True)
        
        for i, (price, volume) in enumerate(levels_with_volume[:10], 1):
            marker = " 👑 POC" if abs(price - data['poc']) < 0.01 else ""
            print(f"  {i:2d}. ${price:7.2f}  →  {volume:>15,.0f}{marker}")
        
        return data
        
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)
        return None


def test_volume_profile_summary(stock_id: int, ticker: str):
    """Test volume profile summary"""
    print_section(f"VOLUME PROFILE SUMMARY - {ticker}")
    
    response = requests.get(
        f"{BASE_URL}/stock-data/{stock_id}/volume-profile/summary",
        params={"period_days": 30}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"\n📊 {data['ticker_symbol']} Summary:")
        print(f"  POC: ${data['poc']:.2f}")
        print(f"  Value Area High: ${data['value_area_high']:.2f}")
        print(f"  Value Area Low: ${data['value_area_low']:.2f}")
        print(f"  Period: {data['period']['start']} to {data['period']['end']}")
        
        return data
        
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)
        return None


def test_different_periods(stock_id: int, ticker: str):
    """Test different time periods"""
    print_section(f"DIFFERENT TIME PERIODS - {ticker}")
    
    periods = [7, 30, 90]
    
    for period in periods:
        print(f"\n📅 {period}-Day Period:")
        response = requests.get(
            f"{BASE_URL}/stock-data/{stock_id}/volume-profile/summary",
            params={"period_days": period}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ POC: ${data['poc']:.2f}")
            print(f"  📈 VA Range: ${data['value_area_low']:.2f} - ${data['value_area_high']:.2f}")
            print(f"     Width: ${data['value_area_high'] - data['value_area_low']:.2f}")
        else:
            print(f"  ❌ Error: {response.status_code}")


def test_different_bin_counts(stock_id: int, ticker: str):
    """Test different bin counts"""
    print_section(f"DIFFERENT BIN COUNTS - {ticker}")
    
    bin_counts = [20, 50, 100]
    
    for bins in bin_counts:
        print(f"\n🔢 {bins} Bins:")
        response = requests.get(
            f"{BASE_URL}/stock-data/{stock_id}/volume-profile",
            params={
                "period_days": 30,
                "num_bins": bins
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ POC: ${data['poc']:.2f}")
            print(f"  📊 Bin Size: ${data['bin_size']:.4f}")
            print(f"  🔴 HVN Count: {len(data['hvn_levels'])}")
            print(f"  🔵 LVN Count: {len(data['lvn_levels'])}")
        else:
            print(f"  ❌ Error: {response.status_code}")


def visualize_profile_ascii(data):
    """Create ASCII visualization of volume profile"""
    print_section("ASCII VISUALIZATION")
    
    # Get price levels and volumes
    levels = data['price_levels']
    volumes = data['volumes']
    poc = data['poc']
    va_high = data['value_area']['high']
    va_low = data['value_area']['low']
    
    # Normalize volumes for display (max 50 chars)
    max_volume = max(volumes)
    
    # Show every Nth level to fit screen
    step = max(1, len(levels) // 30)
    
    print("\nPrice Level    Volume Distribution")
    print("-" * 70)
    
    for i in range(0, len(levels), step):
        price = levels[i]
        volume = volumes[i]
        
        # Create bar
        bar_length = int((volume / max_volume) * 50) if max_volume > 0 else 0
        bar = "█" * bar_length
        
        # Markers
        marker = ""
        if abs(price - poc) < 0.5:
            marker = " ← POC"
            bar = f"\033[92m{bar}\033[0m"  # Green
        elif va_low <= price <= va_high:
            bar = f"\033[94m{bar}\033[0m"  # Blue (Value Area)
        
        print(f"${price:7.2f}  {bar}{marker}")
    
    print("-" * 70)
    print("Legend: \033[92m█\033[0m POC  \033[94m█\033[0m Value Area")


def main():
    print("\n" + "="*70)
    print("  🎯 VOLUME PROFILE ANALYSIS TESTING")
    print("="*70)
    print("\nMake sure backend is running on localhost:8000")
    
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("\n❌ Backend server not reachable!")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend server not running!")
        print("Start with: python -m uvicorn backend.app.main:app --reload")
        return
    
    # Get first stock from watchlist
    response = requests.get(f"{BASE_URL}/watchlists/")
    if response.status_code == 200:
        watchlists = response.json()
        if watchlists and watchlists[0].get('stocks'):
            stock = watchlists[0]['stocks'][0]
            stock_id = stock['id']
            ticker = stock['ticker_symbol']
            print(f"\n✅ Testing with: {ticker} (ID: {stock_id})")
        else:
            print("\n⚠️ No stocks found!")
            return
    else:
        print("\n❌ Could not get watchlists")
        return
    
    # Run tests
    profile_data = test_volume_profile_full(stock_id, ticker)
    
    if profile_data:
        visualize_profile_ascii(profile_data)
    
    test_volume_profile_summary(stock_id, ticker)
    test_different_periods(stock_id, ticker)
    test_different_bin_counts(stock_id, ticker)
    
    print("\n" + "="*70)
    print("  ✅ TESTING COMPLETE")
    print("="*70)
    print("\n💡 Next steps:")
    print("  1. Check the values make sense for the stock")
    print("  2. Compare POC with current price")
    print("  3. Look for patterns in HVN/LVN levels")
    print("  4. Test with different stocks and periods")
    print()


if __name__ == "__main__":
    main()
