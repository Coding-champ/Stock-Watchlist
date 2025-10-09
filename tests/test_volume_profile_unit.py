"""
Unit tests for Volume Profile Service
Run with: pytest tests/test_volume_profile_unit.py -v
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import Stock as StockModel, StockPriceData as StockPriceDataModel
from backend.app.services.volume_profile_service import VolumeProfileService


# Test database setup
@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_stock(db_session):
    """Create a sample stock"""
    stock = StockModel(
        ticker_symbol="TEST",
        name="Test Stock",
        sector="Technology"
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


@pytest.fixture
def sample_price_data(db_session, sample_stock):
    """Create sample price data with known characteristics"""
    # Create 30 days of data
    # Price range: $100 - $110
    # High volume at $105 (POC should be here)
    
    prices = []
    # Use dates in the past (30 days ago to today)
    end_date = datetime.now().date()
    base_date = end_date - timedelta(days=29)  # Start 29 days ago
    
    for i in range(30):
        current_date = base_date + timedelta(days=i)
        
        # Prices centered around $105
        if i < 10:
            # Days 0-9: Lower prices ($100-$103)
            low = 100 + (i * 0.3)
            high = low + 2
            volume = 1_000_000  # Low volume
        elif i < 20:
            # Days 10-19: Around POC ($104-$106)
            low = 104 + (i % 2)
            high = low + 1.5
            volume = 5_000_000  # High volume (POC area)
        else:
            # Days 20-29: Higher prices ($107-$110)
            low = 107 + ((i - 20) * 0.3)
            high = low + 2
            volume = 1_500_000  # Medium volume
        
        price = StockPriceDataModel(
            stock_id=sample_stock.id,
            date=current_date,
            open=low + 0.5,
            high=high,
            low=low,
            close=high - 0.5,
            volume=volume
        )
        prices.append(price)
        db_session.add(price)
    
    db_session.commit()
    return prices


def test_service_initialization(db_session):
    """Test service can be initialized"""
    service = VolumeProfileService(db_session)
    assert service is not None
    assert service.db == db_session


def test_calculate_profile_basic(db_session, sample_stock, sample_price_data):
    """Test basic volume profile calculation"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    # Check all required fields are present
    assert "stock_id" in result
    assert "ticker_symbol" in result
    assert "price_levels" in result
    assert "volumes" in result
    assert "poc" in result
    assert "poc_volume" in result
    assert "value_area" in result
    assert "hvn_levels" in result
    assert "lvn_levels" in result
    assert "total_volume" in result
    assert "period" in result
    assert "price_range" in result
    
    # Check data types
    assert isinstance(result["price_levels"], list)
    assert isinstance(result["volumes"], list)
    assert isinstance(result["poc"], float)
    assert isinstance(result["poc_volume"], float)
    assert isinstance(result["value_area"], dict)
    
    # Check lengths match
    assert len(result["price_levels"]) == len(result["volumes"])
    assert len(result["price_levels"]) == 50  # num_bins


def test_poc_identification(db_session, sample_stock, sample_price_data):
    """Test Point of Control is correctly identified"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    # POC should be around $105 (where we had highest volume)
    assert 104.0 <= result["poc"] <= 106.0
    
    # POC volume should be the maximum
    max_volume = max(result["volumes"])
    assert result["poc_volume"] == max_volume


def test_value_area_calculation(db_session, sample_stock, sample_price_data):
    """Test Value Area contains approximately 70% of volume"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    va = result["value_area"]
    
    # Check structure
    assert "high" in va
    assert "low" in va
    assert "volume_percent" in va
    
    # Volume should be around 70% (allow some tolerance)
    assert 65.0 <= va["volume_percent"] <= 75.0
    
    # VAH should be > VAL
    assert va["high"] > va["low"]
    
    # POC should be within Value Area
    assert va["low"] <= result["poc"] <= va["high"]


def test_hvn_lvn_identification(db_session, sample_stock, sample_price_data):
    """Test High/Low Volume Nodes are identified"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    # Should have some HVN levels (high volume nodes)
    assert len(result["hvn_levels"]) > 0
    
    # HVN levels should be within price range
    for level in result["hvn_levels"]:
        assert result["price_range"]["min"] <= level <= result["price_range"]["max"]
    
    # LVN levels should be within price range
    for level in result["lvn_levels"]:
        assert result["price_range"]["min"] <= level <= result["price_range"]["max"]


def test_price_range_calculation(db_session, sample_stock, sample_price_data):
    """Test price range is calculated correctly"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    pr = result["price_range"]
    
    # Check structure
    assert "min" in pr
    assert "max" in pr
    assert "range" in pr
    
    # Expected range: ~$100 - ~$112 (with some tolerance)
    assert 99.0 <= pr["min"] <= 101.0
    assert 109.0 <= pr["max"] <= 113.0  # Allow higher max due to last day's high
    
    # Range should be max - min
    assert abs(pr["range"] - (pr["max"] - pr["min"])) < 0.01


def test_total_volume_calculation(db_session, sample_stock, sample_price_data):
    """Test total volume is calculated correctly"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    # Total volume should be sum of all bin volumes
    calculated_total = sum(result["volumes"])
    assert abs(result["total_volume"] - calculated_total) < 1.0
    
    # Should be positive
    assert result["total_volume"] > 0


def test_different_bin_counts(db_session, sample_stock, sample_price_data):
    """Test volume profile with different bin counts"""
    service = VolumeProfileService(db_session)
    
    for num_bins in [10, 50, 100]:
        result = service.calculate_volume_profile(
            stock_id=sample_stock.id,
            period_days=30,
            num_bins=num_bins
        )
        
        # Should have correct number of bins
        assert len(result["price_levels"]) == num_bins
        assert len(result["volumes"]) == num_bins
        
        # POC should be roughly consistent (within $1)
        assert 103.0 <= result["poc"] <= 107.0


def test_summary_endpoint(db_session, sample_stock, sample_price_data):
    """Test volume profile summary"""
    service = VolumeProfileService(db_session)
    
    result = service.get_volume_profile_summary(
        stock_id=sample_stock.id,
        period_days=30
    )
    
    # Check required fields
    assert "stock_id" in result
    assert "ticker_symbol" in result
    assert "poc" in result
    assert "value_area_high" in result
    assert "value_area_low" in result
    assert "period" in result
    
    # Check values are reasonable
    assert result["value_area_high"] > result["value_area_low"]
    assert result["value_area_low"] <= result["poc"] <= result["value_area_high"]


def test_no_data_handling(db_session, sample_stock):
    """Test handling when no price data exists"""
    service = VolumeProfileService(db_session)
    
    # No price data added
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    # Should return error
    assert "error" in result
    assert result["stock_id"] == sample_stock.id


def test_invalid_stock_id(db_session):
    """Test handling of invalid stock ID"""
    service = VolumeProfileService(db_session)
    
    with pytest.raises(ValueError, match="Stock with id .* not found"):
        service.calculate_volume_profile(
            stock_id=999,
            period_days=30,
            num_bins=50
        )


def test_custom_date_range(db_session, sample_stock, sample_price_data):
    """Test volume profile with custom date range"""
    service = VolumeProfileService(db_session)
    
    # Use dates that match the sample data
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)
    
    # Get a subset: days 10-20 (10 days)
    subset_start = start_date + timedelta(days=10)
    subset_end = start_date + timedelta(days=20)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        num_bins=50,
        start_date=subset_start,
        end_date=subset_end
    )
    
    # Check period is correct
    assert result["period"]["start"] == subset_start.isoformat()
    assert result["period"]["end"] == subset_end.isoformat()
    
    # Should have ~10 trading days
    assert result["period"]["days"] <= 11


def test_bin_size_calculation(db_session, sample_stock, sample_price_data):
    """Test bin size is calculated correctly"""
    service = VolumeProfileService(db_session)
    
    result = service.calculate_volume_profile(
        stock_id=sample_stock.id,
        period_days=30,
        num_bins=50
    )
    
    # Bin size should be range / num_bins
    expected_bin_size = result["price_range"]["range"] / 50
    assert abs(result["bin_size"] - expected_bin_size) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
