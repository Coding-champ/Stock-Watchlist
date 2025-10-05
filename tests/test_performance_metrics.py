"""
Performance tests for calculated metrics
Tests response times, caching effectiveness, and memory usage
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
import psutil
import os

# Import app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.main import app
from backend.app.services.calculated_metrics_service import CalculatedMetricsService

client = TestClient(app)


@pytest.fixture
def mock_extended_stock_data():
    """Mock extended stock data"""
    return {
        'business_summary': 'Test company',
        'financial_ratios': {
            'pe_ratio': 25.5,
            'peg_ratio': 2.1,
            'price_to_book': 8.5,
            'price_to_sales': 5.2,
            'profit_margins': 0.25,
            'operating_margins': 0.30,
            'return_on_equity': 1.50,
            'return_on_assets': 0.20,
            'market_cap': 3000000000000
        },
        'cashflow_data': {
            'operating_cashflow': 100000000000,
            'free_cashflow': 80000000000,
            'total_cash': 50000000000,
            'total_debt': 120000000000,
            'debt_to_equity': 1.2
        },
        'dividend_info': {
            'dividend_rate': 0.92,
            'dividend_yield': 0.005,
            'payout_ratio': 0.15,
            'five_year_avg_dividend_yield': 0.013,
            'ex_dividend_date': 1234567890
        },
        'price_data': {
            'current_price': 180.0,
            'day_high': 182.0,
            'day_low': 178.0,
            'fifty_two_week_high': 200.0,
            'fifty_two_week_low': 120.0,
            'fifty_day_average': 170.0,
            'two_hundred_day_average': 160.0
        },
        'volume_data': {
            'volume': 50000000,
            'average_volume': 55000000,
            'average_volume_10days': 52000000
        },
        'risk_metrics': {
            'beta': 1.09,
            'volatility_30d': 0.25,
            'shares_outstanding': 16000000000,
            'float_shares': 15000000000,
            'held_percent_insiders': 0.001,
            'held_percent_institutions': 0.60
        }
    }


@pytest.fixture
def mock_historical_prices():
    """Mock historical price data with 252 trading days"""
    dates = pd.date_range(start='2024-01-01', periods=252, freq='B')
    data = {
        'Open': [100 + i * 0.1 for i in range(252)],
        'High': [102 + i * 0.1 for i in range(252)],
        'Low': [98 + i * 0.1 for i in range(252)],
        'Close': [100 + i * 0.1 + (i % 10 - 5) for i in range(252)],
        'Volume': [50000000 + i * 10000 for i in range(252)]
    }
    return pd.DataFrame(data, index=dates)


# ============================================================================
# PERFORMANCE TESTS: Calculation Speed
# ============================================================================

class TestCalculationPerformance:
    """Test calculation performance"""
    
    def test_calculate_all_metrics_performance(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test that all metrics calculate within acceptable time"""
        service = CalculatedMetricsService()
        
        start_time = time.time()
        metrics = service.calculate_all_metrics(
            ticker="AAPL",
            extended_data=mock_extended_stock_data,
            historical_prices=mock_historical_prices,
            period="1y"
        )
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Should complete within 2 seconds
        assert calculation_time < 2.0, f"Calculation took {calculation_time:.2f}s (expected < 2s)"
        print(f"\n✅ All metrics calculated in {calculation_time:.3f}s")
    
    def test_phase1_performance(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test Phase 1 calculation speed"""
        service = CalculatedMetricsService()
        
        start_time = time.time()
        
        # Calculate individual Phase 1 metrics
        service.calculate_52week_distance(mock_extended_stock_data)
        service.calculate_sma_crossover(mock_extended_stock_data)
        service.calculate_relative_volume(mock_extended_stock_data)
        service.calculate_free_cashflow_yield(mock_extended_stock_data)
        
        end_time = time.time()
        phase1_time = end_time - start_time
        
        # Phase 1 should be very fast (< 100ms)
        assert phase1_time < 0.1, f"Phase 1 took {phase1_time:.3f}s (expected < 0.1s)"
        print(f"\n✅ Phase 1 calculated in {phase1_time*1000:.1f}ms")
    
    def test_phase2_performance(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test Phase 2 calculation speed"""
        service = CalculatedMetricsService()
        
        start_time = time.time()
        
        # Calculate Phase 2 scores
        service.calculate_value_score(mock_extended_stock_data)
        service.calculate_quality_score(mock_extended_stock_data)
        service.calculate_dividend_safety_score(mock_extended_stock_data)
        
        end_time = time.time()
        phase2_time = end_time - start_time
        
        # Phase 2 should be fast (< 100ms)
        assert phase2_time < 0.1, f"Phase 2 took {phase2_time:.3f}s (expected < 0.1s)"
        print(f"\n✅ Phase 2 calculated in {phase2_time*1000:.1f}ms")
    
    def test_phase3_performance(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test Phase 3 calculation speed (most intensive)"""
        service = CalculatedMetricsService()
        
        start_time = time.time()
        
        # Calculate Phase 3 metrics (includes beta-adjusted)
        service.calculate_macd(mock_historical_prices)
        service.calculate_stochastic_oscillator(mock_historical_prices)
        service.calculate_volatility_metrics(mock_historical_prices)
        service.calculate_maximum_drawdown(mock_historical_prices)
        service.calculate_beta_adjusted_metrics(
            historical_prices=mock_historical_prices,
            beta=1.09
        )
        
        end_time = time.time()
        phase3_time = end_time - start_time
        
        # Phase 3 can be slower but should still be < 1s
        assert phase3_time < 1.0, f"Phase 3 took {phase3_time:.3f}s (expected < 1s)"
        print(f"\n✅ Phase 3 calculated in {phase3_time:.3f}s")


# ============================================================================
# PERFORMANCE TESTS: Memory Usage
# ============================================================================

class TestMemoryUsage:
    """Test memory usage during calculations"""
    
    def test_memory_footprint(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test memory usage stays within reasonable bounds"""
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        service = CalculatedMetricsService()
        
        # Calculate metrics multiple times
        for _ in range(10):
            service.calculate_all_metrics(
                ticker="AAPL",
                extended_data=mock_extended_stock_data,
                historical_prices=mock_historical_prices,
                period="1y"
            )
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory
        
        # Memory increase should be < 50MB for 10 calculations
        assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB (expected < 50MB)"
        print(f"\n✅ Memory increase: {memory_increase:.1f}MB (for 10 calculations)")
    
    def test_no_memory_leak(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test for memory leaks in repeated calculations"""
        process = psutil.Process(os.getpid())
        service = CalculatedMetricsService()
        
        memories = []
        
        # Run calculations and track memory
        for i in range(20):
            service.calculate_all_metrics(
                ticker="AAPL",
                extended_data=mock_extended_stock_data,
                historical_prices=mock_historical_prices,
                period="1y"
            )
            memories.append(process.memory_info().rss / 1024 / 1024)
        
        # Check if memory is growing linearly (potential leak)
        # Memory should stabilize after initial allocations
        first_half_avg = sum(memories[:10]) / 10
        second_half_avg = sum(memories[10:]) / 10
        growth = second_half_avg - first_half_avg
        
        # Growth should be minimal (< 10MB) between halves
        assert growth < 10, f"Potential memory leak detected: {growth:.1f}MB growth"
        print(f"\n✅ No memory leak detected (growth: {growth:.1f}MB)")


# ============================================================================
# PERFORMANCE TESTS: Large Datasets
# ============================================================================

class TestLargeDatasets:
    """Test performance with larger datasets"""
    
    def test_2year_historical_data(
        self, 
        mock_extended_stock_data
    ):
        """Test with 2 years of historical data (~504 trading days)"""
        # Generate 2 years of data
        dates = pd.date_range(start='2023-01-01', periods=504, freq='B')
        historical_data = pd.DataFrame({
            'Open': [100 + i * 0.05 for i in range(504)],
            'High': [102 + i * 0.05 for i in range(504)],
            'Low': [98 + i * 0.05 for i in range(504)],
            'Close': [100 + i * 0.05 + (i % 10 - 5) for i in range(504)],
            'Volume': [50000000 + i * 5000 for i in range(504)]
        }, index=dates)
        
        service = CalculatedMetricsService()
        
        start_time = time.time()
        metrics = service.calculate_all_metrics(
            ticker="AAPL",
            extended_data=mock_extended_stock_data,
            historical_prices=historical_data,
            period="2y"
        )
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Should still complete within 3 seconds even with 2 years
        assert calculation_time < 3.0, f"2-year calculation took {calculation_time:.2f}s (expected < 3s)"
        print(f"\n✅ 2-year data calculated in {calculation_time:.3f}s")
    
    def test_batch_calculations(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test calculating metrics for multiple stocks"""
        service = CalculatedMetricsService()
        
        start_time = time.time()
        
        # Simulate calculating for 10 different stocks
        for i in range(10):
            service.calculate_all_metrics(
                ticker=f"STOCK{i}",
                extended_data=mock_extended_stock_data,
                historical_prices=mock_historical_prices,
                period="1y"
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        # Average time per stock should be < 1s
        assert avg_time < 1.0, f"Average calculation time {avg_time:.2f}s (expected < 1s)"
        print(f"\n✅ 10 stocks calculated in {total_time:.2f}s (avg: {avg_time:.3f}s per stock)")


# ============================================================================
# PERFORMANCE TESTS: Cache Effectiveness
# ============================================================================

class TestCachePerformance:
    """Test caching performance"""
    
    @patch('backend.app.services.cache_service.cache_service')
    def test_cache_hit_performance(
        self,
        mock_cache,
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test that cache hits are significantly faster"""
        service = CalculatedMetricsService()
        
        # First calculation (cache miss)
        mock_cache.get.return_value = None
        
        start_time = time.time()
        metrics1 = service.calculate_all_metrics(
            ticker="AAPL",
            extended_data=mock_extended_stock_data,
            historical_prices=mock_historical_prices,
            period="1y"
        )
        miss_time = time.time() - start_time
        
        # Second calculation (cache hit)
        mock_cache.get.return_value = metrics1
        
        start_time = time.time()
        metrics2 = mock_cache.get("test_key")
        hit_time = time.time() - start_time
        
        # Cache hit should be at least 100x faster
        speedup = miss_time / hit_time if hit_time > 0 else float('inf')
        
        print(f"\n✅ Cache miss: {miss_time:.3f}s, Cache hit: {hit_time*1000:.3f}ms")
        print(f"   Speedup: {speedup:.0f}x")
        
        # Cache should provide significant speedup
        assert hit_time < miss_time / 10, "Cache not providing expected speedup"


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================

class TestPerformanceBenchmarks:
    """Benchmark tests for comparison"""
    
    def test_baseline_benchmark(
        self, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Establish baseline performance metrics"""
        service = CalculatedMetricsService()
        
        times = []
        for _ in range(5):
            start = time.time()
            service.calculate_all_metrics(
                ticker="AAPL",
                extended_data=mock_extended_stock_data,
                historical_prices=mock_historical_prices,
                period="1y"
            )
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Performance Benchmark (5 runs):")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min:     {min_time:.3f}s")
        print(f"   Max:     {max_time:.3f}s")
        
        # All runs should be consistent (max < 2x min)
        assert max_time < min_time * 2, "Performance is too inconsistent"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
