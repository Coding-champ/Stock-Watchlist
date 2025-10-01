#!/usr/bin/env python3
"""
Test script for the new cache system
Tests cache functionality and performance improvements
"""

import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models import Stock as StockModel
from backend.app.services.cache_service import StockDataCacheService

def test_cache_system():
    """Test the cache system with real stock data"""
    db = SessionLocal()
    
    try:
        print("🧪 Testing Cache System")
        print("=" * 50)
        
        # Get a stock from the database
        stock = db.query(StockModel).first()
        if not stock:
            print("❌ No stocks found in database. Please run sample_data.py first.")
            return
        
        print(f"📊 Testing with stock: {stock.name} ({stock.ticker_symbol})")
        print()
        
        # Initialize cache service
        cache_service = StockDataCacheService(db)
        
        # Test 1: First fetch (should be MISS)
        print("1️⃣ First fetch (expecting cache MISS):")
        start_time = time.time()
        data, cache_hit = cache_service.get_cached_extended_data(stock.id)
        fetch_time = time.time() - start_time
        
        print(f"   Result: {'HIT' if cache_hit else 'MISS'}")
        print(f"   Time: {fetch_time:.2f} seconds")
        print(f"   Data available: {bool(data)}")
        if data and data.get('extended_data'):
            print(f"   Business summary: {bool(data['extended_data'].get('business_summary'))}")
        print()
        
        # Test 2: Second fetch (should be HIT)
        print("2️⃣ Second fetch (expecting cache HIT):")
        start_time = time.time()
        data2, cache_hit2 = cache_service.get_cached_extended_data(stock.id)
        fetch_time2 = time.time() - start_time
        
        print(f"   Result: {'HIT' if cache_hit2 else 'MISS'}")
        print(f"   Time: {fetch_time2:.2f} seconds")
        print(f"   Speed improvement: {((fetch_time - fetch_time2) / fetch_time * 100):.1f}%")
        print()
        
        # Test 3: Force refresh
        print("3️⃣ Force refresh (expecting fresh data):")
        start_time = time.time()
        data3, cache_hit3 = cache_service.get_cached_extended_data(stock.id, force_refresh=True)
        fetch_time3 = time.time() - start_time
        
        print(f"   Result: {'HIT' if cache_hit3 else 'MISS'}")
        print(f"   Time: {fetch_time3:.2f} seconds")
        print()
        
        # Test 4: Cache stats
        print("4️⃣ Cache statistics:")
        stats = cache_service.get_cache_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()
        
        # Test 5: Cache invalidation
        print("5️⃣ Testing cache invalidation:")
        success = cache_service.invalidate_cache(stock.id)
        print(f"   Invalidation successful: {success}")
        
        # Fetch after invalidation (should be MISS)
        data4, cache_hit4 = cache_service.get_cached_extended_data(stock.id)
        print(f"   Next fetch result: {'HIT' if cache_hit4 else 'MISS'}")
        print()
        
        print("✅ Cache system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cache test: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

def test_api_performance():
    """Test API performance with and without cache"""
    import requests
    
    print("\n🚀 API Performance Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Get a stock ID
        stocks_response = requests.get(f"{base_url}/stocks/")
        if stocks_response.status_code != 200:
            print("❌ Backend not running or stocks not available")
            return
            
        stocks = stocks_response.json()
        if not stocks:
            print("❌ No stocks found")
            return
            
        stock_id = stocks[0]['id']
        ticker = stocks[0]['ticker_symbol']
        
        print(f"📊 Testing API performance with {ticker} (ID: {stock_id})")
        print()
        
        # Test with cache
        print("1️⃣ Testing cached API endpoint:")
        start_time = time.time()
        response1 = requests.get(f"{base_url}/stocks/{stock_id}/detailed")
        api_time1 = time.time() - start_time
        
        print(f"   Status: {response1.status_code}")
        print(f"   Time: {api_time1:.2f} seconds")
        print()
        
        # Test second call (should be faster)
        print("2️⃣ Second API call (cached):")
        start_time = time.time()
        response2 = requests.get(f"{base_url}/stocks/{stock_id}/detailed")
        api_time2 = time.time() - start_time
        
        print(f"   Status: {response2.status_code}")
        print(f"   Time: {api_time2:.2f} seconds")
        if api_time1 > 0:
            improvement = ((api_time1 - api_time2) / api_time1 * 100)
            print(f"   Performance improvement: {improvement:.1f}%")
        print()
        
        # Test cache stats endpoint
        print("3️⃣ Cache statistics endpoint:")
        stats_response = requests.get(f"{base_url}/stocks/cache/stats")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"   Cache hit rate: {stats_data['cache_statistics'].get('cache_hit_rate', 'N/A')}")
        print()
        
        print("✅ API performance test completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running. Please start with 'uvicorn backend.app.main:app --reload'")
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")

if __name__ == "__main__":
    print("🎯 Cache System Integration Test")
    print("=" * 60)
    
    # Test 1: Direct cache service
    test_cache_system()
    
    # Test 2: API performance
    test_api_performance()
    
    print("\n🎉 All tests completed!")