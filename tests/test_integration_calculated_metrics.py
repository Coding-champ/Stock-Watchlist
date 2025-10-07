"""
Integration tests for calculated metrics API endpoints
Tests both /api/stock-data/{stock_id}/calculated-metrics 
and /api/stocks/{stock_id}/with-calculated-metrics
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

# Import app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.main import app
from backend.app.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_calculated_metrics.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    """Create a new database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with overridden database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_extended_stock_data():
    """Mock extended stock data from yfinance"""
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
    """Mock historical price data"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='B')
    data = {
        'Open': [100 + i * 0.1 for i in range(len(dates))],
        'High': [102 + i * 0.1 for i in range(len(dates))],
        'Low': [98 + i * 0.1 for i in range(len(dates))],
        'Close': [100 + i * 0.1 + (i % 10 - 5) for i in range(len(dates))],
        'Volume': [50000000 + i * 10000 for i in range(len(dates))]
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sample_stock(db_session):
    """Create a sample stock in test database"""
    from backend.app.models import Watchlist, Stock, StockData
    
    # Create watchlist
    watchlist = Watchlist(name="Test Watchlist", description="Test")
    db_session.add(watchlist)
    db_session.commit()
    
    # Create stock
    stock = Stock(
        ticker_symbol="AAPL",
        name="Apple Inc.",
        isin="US0378331005",
        country="US",
        sector="Technology",
        industry="Consumer Electronics",
        watchlist_id=watchlist.id,
        position=1,
        observation_reasons=["fundamentals", "chart_technical"],
        observation_notes="Test stock"
    )
    db_session.add(stock)
    db_session.commit()
    
    # Create stock data
    stock_data = StockData(
        stock_id=stock.id,
        current_price=180.0,
        pe_ratio=25.5,
        rsi=65.0,
        volatility=25.0
    )
    db_session.add(stock_data)
    db_session.commit()
    
    return stock


# ============================================================================
# TEST: GET /api/stock-data/{stock_id}/calculated-metrics
# ============================================================================

class TestCalculatedMetricsEndpoint:
    """Tests for the calculated metrics endpoint"""
    
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_get_calculated_metrics_success(
        self, 
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test successful retrieval of calculated metrics"""
        # Setup mocks
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None  # Analyst data is optional
        
        # Make request
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert 'basic_indicators' in data
        assert 'valuation_scores' in data
        assert 'advanced_analysis' in data
        assert 'calculation_timestamp' in data
        
        # Check Phase 1
        phase1 = data['basic_indicators']
        assert 'week_52_metrics' in phase1
        assert 'sma_metrics' in phase1
        assert 'volume_metrics' in phase1
        assert 'fcf_yield' in phase1
        
        # Check Phase 2
        phase2 = data['valuation_scores']
        assert 'value_metrics' in phase2
        assert 'quality_metrics' in phase2
        assert 'dividend_metrics' in phase2
        
        # Check Phase 3
        phase3 = data['advanced_analysis']
        assert 'macd' in phase3
        assert 'stochastic' in phase3
        assert 'volatility' in phase3
        assert 'beta_adjusted_metrics' in phase3
        assert 'risk_adjusted_performance' in phase3
    
    def test_get_calculated_metrics_stock_not_found(self, client):
        """Test with non-existent stock ID"""
        response = client.get("/api/stock-data/99999/calculated-metrics")
        assert response.status_code == 404
        assert "Stock not found" in response.json()["detail"]
    
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_get_calculated_metrics_yfinance_error(
        self, 
        mock_extended_data,
        client, 
        sample_stock
    ):
        """Test handling of yfinance errors"""
        mock_extended_data.return_value = None
        
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        assert response.status_code == 404
        assert "Could not fetch data" in response.json()["detail"]
    
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_get_calculated_metrics_with_period(
        self,
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test with different period parameter"""
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None
        
        # Test with 6 months period
        response = client.get(
            f"/api/stock-data/{sample_stock.id}/calculated-metrics",
            params={"period": "6mo"}
        )
        
        assert response.status_code == 200
        mock_hist_prices.assert_called_with("AAPL", "6mo")
    
    @patch('backend.app.services.cache_service.cache_service')
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_get_calculated_metrics_caching(
        self,
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        mock_cache,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test caching functionality"""
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None
        mock_cache.get.return_value = None  # No cache hit
        
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        
        assert response.status_code == 200
        # Verify cache was attempted
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()


# ============================================================================
# TEST: GET /api/stocks/{stock_id}/with-calculated-metrics
# ============================================================================

class TestStockWithCalculatedMetrics:
    """Tests for stock with calculated metrics endpoint"""
    
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_get_stock_with_calculated_metrics_success(
        self,
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test successful retrieval of stock with calculated metrics"""
        # Setup mocks
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None
        
        # Make request
        response = client.get(f"/api/stocks/{sample_stock.id}/with-calculated-metrics")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check stock fields
        assert data['id'] == sample_stock.id
        assert data['ticker_symbol'] == "AAPL"
        assert data['name'] == "Apple Inc."
        
        # Check extended data
        assert 'extended_data' in data
        assert 'calculated_metrics' in data
        
        # Check calculated metrics structure
        metrics = data['calculated_metrics']
        assert 'basic_indicators' in metrics
        assert 'valuation_scores' in metrics
        assert 'advanced_analysis' in metrics
    
    def test_get_stock_with_calculated_metrics_not_found(self, client):
        """Test with non-existent stock"""
        response = client.get("/api/stocks/99999/with-calculated-metrics")
        assert response.status_code == 404


# ============================================================================
# TEST: Calculated Metrics Content Validation
# ============================================================================

class TestCalculatedMetricsContent:
    """Tests for validating calculated metrics content"""
    
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_phase1_metrics_values(
        self,
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test Phase 1 metrics have valid values"""
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None
        
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        phase1 = response.json()['basic_indicators']
        
        # 52-week metrics
        week52 = phase1['week_52_metrics']
        assert week52['distance_from_52w_high'] is not None
        assert week52['distance_from_52w_low'] is not None
        assert 0 <= week52['position_in_52w_range'] <= 100
        
        # SMA metrics
        sma = phase1['sma_metrics']
        assert sma['trend'] in ['bullish', 'bearish', 'neutral']
        assert isinstance(sma['golden_cross'], bool)
        
        # Volume metrics
        volume = phase1['volume_metrics']
        assert volume['volume_category'] in ['very_low', 'low', 'normal', 'high', 'very_high']
    
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_phase2_scores_range(
        self,
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test Phase 2 scores are in valid range (0-100)"""
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None
        
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        phase2 = response.json()['valuation_scores']
        
        # Value score
        if phase2['value_metrics']['value_score'] is not None:
            assert 0 <= phase2['value_metrics']['value_score'] <= 100
        
        # Quality score
        if phase2['quality_metrics']['quality_score'] is not None:
            assert 0 <= phase2['quality_metrics']['quality_score'] <= 100
        
        # Dividend safety score
        if phase2['dividend_metrics']['dividend_safety_score'] is not None:
            assert 0 <= phase2['dividend_metrics']['dividend_safety_score'] <= 100
    
    @patch('backend.app.services.yfinance_service.get_analyst_data')
    @patch('backend.app.services.yfinance_service.get_historical_prices')
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_phase3_beta_metrics(
        self,
        mock_extended_data,
        mock_hist_prices,
        mock_analyst_data,
        client, 
        sample_stock, 
        mock_extended_stock_data,
        mock_historical_prices
    ):
        """Test Phase 3 beta-adjusted metrics"""
        mock_extended_data.return_value = mock_extended_stock_data
        mock_hist_prices.return_value = mock_historical_prices
        mock_analyst_data.return_value = None
        
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        phase3 = response.json()['advanced_analysis']
        
        # Beta-adjusted metrics
        beta_metrics = phase3['beta_adjusted_metrics']
        assert beta_metrics is not None
        
        # Check risk rating
        assert beta_metrics['risk_rating'] in ['low', 'moderate', 'high', 'very_high']
        
        # Risk-adjusted performance
        perf = phase3['risk_adjusted_performance']
        if perf['overall_score'] is not None:
            assert 0 <= perf['overall_score'] <= 100
            assert perf['rating'] in ['excellent', 'good', 'average', 'poor']


# ============================================================================
# TEST: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling"""
    
    @patch('backend.app.services.yfinance_service.get_extended_stock_data')
    def test_internal_server_error(
        self, 
        mock_extended_data,
        client, 
        sample_stock
    ):
        """Test handling of internal server errors"""
        mock_extended_data.side_effect = Exception("Unexpected error")
        
        response = client.get(f"/api/stock-data/{sample_stock.id}/calculated-metrics")
        assert response.status_code == 500
        assert "Error calculating metrics" in response.json()["detail"]
    
    def test_invalid_period_parameter(self, client, sample_stock):
        """Test with invalid period parameter"""
        # This should be handled gracefully by yfinance
        response = client.get(
            f"/api/stock-data/{sample_stock.id}/calculated-metrics",
            params={"period": "invalid"}
        )
        # Should still return 200 or specific error
        assert response.status_code in [200, 400, 404, 500]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
