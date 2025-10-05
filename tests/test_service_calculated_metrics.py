"""
Simplified integration tests for calculated metrics API
Tests the service layer directly without complex mocking
"""

import pytest
import pandas as pd
from datetime import datetime

# Import services directly
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services import calculated_metrics_service


@pytest.fixture
def sample_extended_data():
    """Sample extended stock data"""
    return {
        'business_summary': 'Test company',
        'pe_ratio': 25.5,
        'peg_ratio': 2.1,
        'price_to_book': 8.5,
        'price_to_sales': 5.2,
        'profit_margins': 0.25,
        'operating_margins': 0.30,
        'return_on_equity': 1.50,
        'return_on_assets': 0.20,
        'market_cap': 3000000000000,
        'operating_cashflow': 100000000000,
        'free_cashflow': 80000000000,
        'total_cash': 50000000000,
        'total_debt': 120000000000,
        'debt_to_equity': 1.2,
        'dividend_rate': 0.92,
        'dividend_yield': 0.005,
        'payout_ratio': 0.15,
        'five_year_avg_dividend_yield': 0.013,
        'current_price': 180.0,
        'day_high': 182.0,
        'day_low': 178.0,
        'fifty_two_week_high': 200.0,
        'fifty_two_week_low': 120.0,
        'fifty_day_average': 170.0,
        'two_hundred_day_average': 160.0,
        'volume': 50000000,
        'average_volume': 55000000,
        'average_volume_10days': 52000000,
        'beta': 1.09,
        'volatility_30d': 0.25,
        'shares_outstanding': 16000000000,
        'float_shares': 15000000000,
        'held_percent_insiders': 0.001,
        'held_percent_institutions': 0.60
    }


@pytest.fixture
def sample_historical_prices():
    """Sample historical price data (1 year)"""
    dates = pd.date_range(start='2024-01-01', periods=252, freq='B')
    data = {
        'Open': [100 + i * 0.1 for i in range(252)],
        'High': [102 + i * 0.1 for i in range(252)],
        'Low': [98 + i * 0.1 for i in range(252)],
        'Close': [100 + i * 0.1 + (i % 10 - 5) for i in range(252)],
        'Volume': [50000000 + i * 10000 for i in range(252)]
    }
    return pd.DataFrame(data, index=dates)


class TestCalculatedMetricsService:
    """Test the calculated metrics service"""
    
    def test_calculate_all_metrics(self, sample_extended_data, sample_historical_prices):
        """Test that all metrics are calculated"""
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        
        # Check that result contains all phases
        assert 'phase1_basic_indicators' in result
        assert 'phase2_valuation_scores' in result
        assert 'phase3_advanced_analysis' in result
        assert 'calculation_timestamp' in result
        
        print("\n✅ All metrics calculated successfully")
    
    def test_phase1_metrics(self, sample_extended_data, sample_historical_prices):
        """Test Phase 1 metrics"""
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        
        phase1 = result['phase1_basic_indicators']
        
        # Check 52-week metrics
        assert 'week_52_metrics' in phase1
        week52 = phase1['week_52_metrics']
        assert week52['distance_from_52w_high'] is not None
        assert 0 <= week52['position_in_52w_range'] <= 100
        
        # Check SMA metrics
        assert 'sma_metrics' in phase1
        sma = phase1['sma_metrics']
        assert sma['trend'] in ['bullish', 'bearish', 'neutral']
        
        # Check volume metrics
        assert 'volume_metrics' in phase1
        volume = phase1['volume_metrics']
        assert volume['volume_category'] in ['very_low', 'low', 'normal', 'high', 'very_high']
        
        # Check FCF yield
        assert 'fcf_yield' in phase1
        
        print(f"\n✅ Phase 1 Metrics:")
        print(f"   52W Position: {week52['position_in_52w_range']:.1f}%")
        print(f"   SMA Trend: {sma['trend']}")
        print(f"   Volume: {volume['volume_category']}")
    
    def test_phase2_scores(self, sample_extended_data, sample_historical_prices):
        """Test Phase 2 scores"""
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        
        phase2 = result['phase2_valuation_scores']
        
        # Check value metrics
        assert 'value_metrics' in phase2
        if phase2['value_metrics']['value_score'] is not None:
            assert 0 <= phase2['value_metrics']['value_score'] <= 100
        
        # Check quality metrics
        assert 'quality_metrics' in phase2
        if phase2['quality_metrics']['quality_score'] is not None:
            assert 0 <= phase2['quality_metrics']['quality_score'] <= 100
        
        # Check dividend metrics
        assert 'dividend_metrics' in phase2
        if phase2['dividend_metrics']['dividend_safety_score'] is not None:
            assert 0 <= phase2['dividend_metrics']['dividend_safety_score'] <= 100
        
        print(f"\n✅ Phase 2 Scores:")
        print(f"   Value Score: {phase2['value_metrics']['value_score']}")
        print(f"   Quality Score: {phase2['quality_metrics']['quality_score']}")
        print(f"   Dividend Safety: {phase2['dividend_metrics']['dividend_safety_score']}")
    
    def test_phase3_advanced_metrics(self, sample_extended_data, sample_historical_prices):
        """Test Phase 3 advanced metrics"""
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        
        phase3 = result['phase3_advanced_analysis']
        
        # Check MACD
        assert 'macd' in phase3
        assert phase3['macd'] is not None
        
        # Check Stochastic
        assert 'stochastic' in phase3
        assert phase3['stochastic'] is not None
        
        # Check Volatility
        assert 'volatility' in phase3
        assert phase3['volatility'] is not None
        
        # Check Beta-adjusted metrics
        assert 'beta_adjusted_metrics' in phase3
        beta_metrics = phase3['beta_adjusted_metrics']
        assert beta_metrics is not None
        assert beta_metrics['risk_rating'] in ['low', 'moderate', 'high', 'very_high']
        
        # Check Risk-adjusted performance
        assert 'risk_adjusted_performance' in phase3
        perf = phase3['risk_adjusted_performance']
        if perf['overall_score'] is not None:
            assert 0 <= perf['overall_score'] <= 100
            assert perf['rating'] in ['excellent', 'good', 'average', 'poor']
        
        print(f"\n✅ Phase 3 Advanced Metrics:")
        print(f"   MACD Trend: {phase3['macd']['trend']}")
        print(f"   Stochastic: {phase3['stochastic']['k_percent']:.2f}%")
        print(f"   Volatility (30d): {phase3['volatility']['volatility_30d']:.2f}%")
        print(f"   Sharpe Ratio: {beta_metrics['sharpe_ratio']:.3f}")
        print(f"   Risk-Adjusted Score: {perf['overall_score']:.1f}/100 ({perf['rating']})")
    
    def test_beta_adjusted_calculations(self, sample_extended_data, sample_historical_prices):
        """Test beta-adjusted metrics calculations"""
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        
        beta_metrics = result['phase3_advanced_analysis']['beta_adjusted_metrics']
        
        # Check all beta-adjusted metrics are present
        assert beta_metrics['sharpe_ratio'] is not None
        assert beta_metrics['alpha'] is not None
        assert beta_metrics['treynor_ratio'] is not None
        assert beta_metrics['sortino_ratio'] is not None
        assert beta_metrics['information_ratio'] is not None
        assert beta_metrics['beta_adjusted_return'] is not None
        
        print(f"\n✅ Beta-Adjusted Metrics:")
        print(f"   Sharpe Ratio: {beta_metrics['sharpe_ratio']:.3f}")
        print(f"   Alpha: {beta_metrics['alpha']:.2f}%")
        print(f"   Treynor Ratio: {beta_metrics['treynor_ratio']:.3f}")
        print(f"   Sortino Ratio: {beta_metrics['sortino_ratio']:.3f}")
        print(f"   Information Ratio: {beta_metrics['information_ratio']:.3f}")
    
    def test_risk_adjusted_performance_score(self, sample_extended_data, sample_historical_prices):
        """Test risk-adjusted performance score calculation"""
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        
        perf = result['phase3_advanced_analysis']['risk_adjusted_performance']
        
        # Check overall score and rating
        assert perf['overall_score'] is not None
        assert 0 <= perf['overall_score'] <= 100
        assert perf['rating'] in ['excellent', 'good', 'average', 'poor']
        
        # Check individual contributions (they're named differently)
        assert 'sharpe_contribution' in perf
        assert 'alpha_contribution' in perf
        assert 'sortino_contribution' in perf
        assert 'information_contribution' in perf
        
        print(f"\n✅ Risk-Adjusted Performance:")
        print(f"   Overall Score: {perf['overall_score']:.1f}/100")
        print(f"   Rating: {perf['rating'].upper()}")
        print(f"   Sharpe Contribution: {perf['sharpe_contribution']:.1f}")
        print(f"   Alpha Contribution: {perf['alpha_contribution']:.1f}")
    
    def test_calculation_performance(self, sample_extended_data, sample_historical_prices):
        """Test that calculations complete in reasonable time"""
        import time
        
        start_time = time.time()
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=sample_historical_prices
        )
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Should complete within 2 seconds
        assert calculation_time < 2.0, f"Calculation took {calculation_time:.2f}s (expected < 2s)"
        print(f"\n✅ Performance: All metrics calculated in {calculation_time:.3f}s")


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_missing_extended_data_fields(self, sample_historical_prices):
        """Test with minimal extended data"""
        minimal_data = {
            'current_price': 100.0,
            'fifty_two_week_high': 150.0,
            'fifty_two_week_low': 75.0,
            'beta': 1.0
        }
        
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=minimal_data,
            historical_prices=sample_historical_prices
        )
        
        # Should still return result, with None values where data is missing
        assert result is not None
        assert 'phase1_basic_indicators' in result
        print("\n✅ Handles missing data gracefully")
    
    def test_short_historical_data(self, sample_extended_data):
        """Test with only 30 days of data"""
        dates = pd.date_range(start='2024-12-01', periods=30, freq='B')
        short_data = pd.DataFrame({
            'Open': [100 + i for i in range(30)],
            'High': [102 + i for i in range(30)],
            'Low': [98 + i for i in range(30)],
            'Close': [100 + i for i in range(30)],
            'Volume': [50000000 for _ in range(30)]
        }, index=dates)
        
        result = calculated_metrics_service.calculate_all_metrics(
            stock_data=sample_extended_data,
            historical_prices=short_data
        )
        
        # Should still work with 30 days (minimum for beta calculations)
        assert result is not None
        assert result['phase3_advanced_analysis']['beta_adjusted_metrics'] is not None
        print("\n✅ Works with 30-day minimum data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
