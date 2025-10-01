#!/usr/bin/env python3
"""
Simple test for yfinance service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.yfinance_service import get_stock_info, get_current_stock_data

def test_yfinance_service():
    print("Testing yfinance service...")
    
    # Test 1: Get stock info for Apple
    print("\n1. Testing get_stock_info for AAPL...")
    stock_info = get_stock_info("AAPL")
    if stock_info:
        print(f"✅ Stock info retrieved:")
        print(f"   Name: {stock_info.name}")
        print(f"   Ticker: {stock_info.ticker}")
        print(f"   Sector: {stock_info.sector}")
        print(f"   Industry: {stock_info.industry}")
        print(f"   Country: {stock_info.country}")
        print(f"   Current Price: ${stock_info.current_price}")
        print(f"   P/E Ratio: {stock_info.pe_ratio}")
        print(f"   ISIN: {stock_info.isin}")
    else:
        print("❌ Failed to get stock info")
    
    # Test 2: Get current market data
    print("\n2. Testing get_current_stock_data for AAPL...")
    market_data = get_current_stock_data("AAPL")
    if market_data:
        print(f"✅ Market data retrieved:")
        for key, value in market_data.items():
            if value is not None:
                print(f"   {key}: {value}")
    else:
        print("❌ Failed to get market data")
    
    # Test 3: Test with invalid ticker
    print("\n3. Testing with invalid ticker...")
    invalid_stock = get_stock_info("INVALID_TICKER_123")
    if invalid_stock is None:
        print("✅ Correctly returned None for invalid ticker")
    else:
        print("❌ Should have returned None for invalid ticker")

if __name__ == "__main__":
    test_yfinance_service()