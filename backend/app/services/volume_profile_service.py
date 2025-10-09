"""
Volume Profile Analysis Service

Calculates volume distribution across price levels to identify:
- Point of Control (POC) - price level with highest volume
- Value Area (VA) - price range containing 70% of volume
- High/Low Volume Nodes (HVN/LVN) - support/resistance levels
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import pandas as pd
import numpy as np

from backend.app.models import (
    Stock as StockModel,
    StockPriceData as StockPriceDataModel
)

logger = logging.getLogger(__name__)


class VolumeProfileService:
    """Service for Volume Profile analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_volume_profile(
        self,
        stock_id: int,
        period_days: int = 30,
        num_bins: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate Volume Profile for a stock over a period
        
        Args:
            stock_id: Stock ID
            period_days: Number of days to analyze (if start_date not provided)
            num_bins: Number of price levels (bins) to create
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            {
                "price_levels": [...],        # Price levels (bin centers)
                "volumes": [...],             # Volume at each level
                "poc": 123.45,                # Point of Control
                "poc_volume": 1000000,        # Volume at POC
                "value_area": {
                    "high": 125.00,           # VAH
                    "low": 121.00,            # VAL
                    "volume_percent": 70.0    # % of volume in VA
                },
                "hvn_levels": [...],          # High Volume Nodes
                "lvn_levels": [...],          # Low Volume Nodes
                "total_volume": 1000000,
                "period": {
                    "start": "2024-12-08",
                    "end": "2025-01-08",
                    "days": 30
                },
                "price_range": {
                    "min": 180.00,
                    "max": 195.00,
                    "range": 15.00
                }
            }
        """
        stock = self.db.query(StockModel).filter(StockModel.id == stock_id).first()
        if not stock:
            raise ValueError(f"Stock with id {stock_id} not found")
        
        # Determine date range
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=period_days)
        
        # Get historical price data
        price_data = self.db.query(StockPriceDataModel).filter(
            StockPriceDataModel.stock_id == stock_id,
            StockPriceDataModel.date >= start_date,
            StockPriceDataModel.date <= end_date
        ).order_by(StockPriceDataModel.date).all()
        
        if not price_data:
            return {
                "error": "No price data available for the specified period",
                "stock_id": stock_id,
                "ticker_symbol": stock.ticker_symbol,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days
                }
            }
        
        # Calculate volume profile
        result = self._calculate_profile(price_data, num_bins)
        
        # Add metadata
        result["stock_id"] = stock_id
        result["ticker_symbol"] = stock.ticker_symbol
        result["period"] = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": len(price_data),
            "actual_days": (end_date - start_date).days
        }
        
        return result
    
    def _calculate_profile(
        self,
        price_data: List[StockPriceDataModel],
        num_bins: int
    ) -> Dict[str, Any]:
        """
        Core volume profile calculation
        
        Algorithm:
        1. Determine price range (min/max)
        2. Create bins (price levels)
        3. Distribute volume from each candle to bins
        4. Calculate POC (bin with max volume)
        5. Calculate Value Area (70% volume around POC)
        6. Identify HVN/LVN
        """
        # Step 1: Extract price and volume data
        df = pd.DataFrame([
            {
                'date': p.date,
                'open': float(p.open) if p.open else None,
                'high': float(p.high) if p.high else None,
                'low': float(p.low) if p.low else None,
                'close': float(p.close) if p.close else None,
                'volume': int(p.volume) if p.volume else 0
            }
            for p in price_data
        ])
        
        # Filter out rows with missing data
        df = df.dropna(subset=['high', 'low', 'volume'])
        df = df[df['volume'] > 0]
        
        if df.empty:
            return {"error": "No valid price data with volume"}
        
        # Step 2: Determine price range
        price_min = df['low'].min()
        price_max = df['high'].max()
        
        # Check for NaN values
        if pd.isna(price_min) or pd.isna(price_max):
            return {"error": "Invalid price data (NaN values)"}
        
        price_range = price_max - price_min
        
        if price_range == 0 or price_range < 0.01:
            return {"error": "Price range is too small or zero"}
        
        # Step 3: Create bins
        bin_size = price_range / num_bins
        bin_edges = np.linspace(price_min, price_max, num_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Initialize volume array for each bin
        bin_volumes = np.zeros(num_bins)
        
        # Step 4: Distribute volume to bins
        for _, row in df.iterrows():
            low = row['low']
            high = row['high']
            volume = row['volume']
            
            # Find bins that this candle touches
            # Bins are 0-indexed
            bin_low_idx = int((low - price_min) / bin_size)
            bin_high_idx = int((high - price_min) / bin_size)
            
            # Clamp to valid range
            bin_low_idx = max(0, min(bin_low_idx, num_bins - 1))
            bin_high_idx = max(0, min(bin_high_idx, num_bins - 1))
            
            # Distribute volume across touched bins
            # Simple approach: equal distribution
            # Advanced: weight by price range within bin
            num_touched_bins = bin_high_idx - bin_low_idx + 1
            
            if num_touched_bins > 0:
                volume_per_bin = volume / num_touched_bins
                for bin_idx in range(bin_low_idx, bin_high_idx + 1):
                    bin_volumes[bin_idx] += volume_per_bin
        
        total_volume = bin_volumes.sum()
        
        # Check for valid total volume
        if total_volume == 0 or np.isnan(total_volume) or np.isinf(total_volume):
            return {"error": "Invalid total volume calculation"}
        
        # Step 5: Calculate POC (Point of Control)
        poc_idx = np.argmax(bin_volumes)
        poc_price = bin_centers[poc_idx]
        poc_volume = bin_volumes[poc_idx]
        
        # Validate POC values
        if np.isnan(poc_price) or np.isinf(poc_price):
            return {"error": "Invalid POC calculation"}
        
        # Step 6: Calculate Value Area (70% of volume)
        value_area = self._calculate_value_area(
            bin_volumes, bin_centers, poc_idx, total_volume
        )
        
        if "error" in value_area:
            return value_area
        
        # Step 7: Identify HVN and LVN
        hvn_levels, lvn_levels = self._identify_nodes(
            bin_volumes, bin_centers, total_volume
        )
        
        # Clean lists from NaN/Inf values
        hvn_levels = [x for x in hvn_levels if not (np.isnan(x) or np.isinf(x))]
        lvn_levels = [x for x in lvn_levels if not (np.isnan(x) or np.isinf(x))]
        
        # Clean bin_centers and bin_volumes from NaN/Inf
        valid_indices = [i for i in range(len(bin_centers)) 
                        if not (np.isnan(bin_centers[i]) or np.isinf(bin_centers[i]) or 
                               np.isnan(bin_volumes[i]) or np.isinf(bin_volumes[i]))]
        
        clean_price_levels = [bin_centers[i] for i in valid_indices]
        clean_volumes = [bin_volumes[i] for i in valid_indices]
        
        return {
            "price_levels": clean_price_levels,
            "volumes": clean_volumes,
            "poc": float(poc_price),
            "poc_volume": float(poc_volume),
            "value_area": value_area,
            "hvn_levels": hvn_levels,
            "lvn_levels": lvn_levels,
            "total_volume": float(total_volume),
            "price_range": {
                "min": float(price_min),
                "max": float(price_max),
                "range": float(price_range)
            },
            "num_bins": num_bins,
            "bin_size": float(bin_size)
        }
    
    def _calculate_value_area(
        self,
        bin_volumes: np.ndarray,
        bin_centers: np.ndarray,
        poc_idx: int,
        total_volume: float
    ) -> Dict[str, Any]:
        """
        Calculate Value Area (70% of volume around POC)
        
        Algorithm:
        1. Start at POC
        2. Expand up and down alternately
        3. Add bin with higher volume first
        4. Stop when accumulated volume >= 70% of total
        """
        if total_volume == 0 or np.isnan(total_volume) or np.isinf(total_volume):
            return {"error": "Invalid total volume for value area calculation"}
        
        target_volume = total_volume * 0.70
        accumulated_volume = bin_volumes[poc_idx]
        
        # Indices for expanding range
        low_idx = poc_idx
        high_idx = poc_idx
        
        num_bins = len(bin_volumes)
        
        # Expand until we reach 70% volume
        while accumulated_volume < target_volume:
            # Check if we can expand
            can_expand_up = high_idx < num_bins - 1
            can_expand_down = low_idx > 0
            
            if not can_expand_up and not can_expand_down:
                break
            
            # Determine which direction to expand
            expand_up = False
            if can_expand_up and can_expand_down:
                # Expand in direction with higher volume
                vol_up = bin_volumes[high_idx + 1]
                vol_down = bin_volumes[low_idx - 1]
                expand_up = vol_up >= vol_down
            elif can_expand_up:
                expand_up = True
            
            # Expand
            if expand_up:
                high_idx += 1
                accumulated_volume += bin_volumes[high_idx]
            else:
                low_idx -= 1
                accumulated_volume += bin_volumes[low_idx]
        
        # Calculate percentage
        volume_percent = (accumulated_volume / total_volume) * 100 if total_volume > 0 else 0
        
        # Validate results
        vah = float(bin_centers[high_idx])
        val = float(bin_centers[low_idx])
        
        if np.isnan(vah) or np.isinf(vah) or np.isnan(val) or np.isinf(val):
            return {"error": "Invalid value area calculation (NaN or Inf)"}
        
        return {
            "high": vah,
            "low": val,
            "volume": float(accumulated_volume),
            "volume_percent": float(volume_percent)
        }
    
    def _identify_nodes(
        self,
        bin_volumes: np.ndarray,
        bin_centers: np.ndarray,
        total_volume: float
    ) -> Tuple[List[float], List[float]]:
        """
        Identify High Volume Nodes (HVN) and Low Volume Nodes (LVN)
        
        HVN: Volume > mean + 0.5 * std
        LVN: Volume < mean - 0.5 * std (and > 0)
        """
        # Filter out zero/invalid volumes for statistics
        valid_volumes = bin_volumes[bin_volumes > 0]
        
        if len(valid_volumes) == 0:
            return [], []
        
        mean_volume = valid_volumes.mean()
        std_volume = valid_volumes.std()
        
        # Check for valid statistics
        if np.isnan(mean_volume) or np.isnan(std_volume) or np.isinf(mean_volume) or np.isinf(std_volume):
            return [], []
        
        # Thresholds
        hvn_threshold = mean_volume + 0.5 * std_volume
        lvn_threshold = max(0, mean_volume - 0.5 * std_volume)
        
        hvn_levels = []
        lvn_levels = []
        
        for i, volume in enumerate(bin_volumes):
            # Skip invalid values
            if np.isnan(volume) or np.isinf(volume) or np.isnan(bin_centers[i]) or np.isinf(bin_centers[i]):
                continue
                
            if volume > hvn_threshold:
                hvn_levels.append(float(bin_centers[i]))
            elif 0 < volume < lvn_threshold:
                lvn_levels.append(float(bin_centers[i]))
        
        return hvn_levels, lvn_levels
    
    def get_volume_profile_summary(
        self,
        stock_id: int,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get a simplified volume profile summary
        Just returns POC and Value Area
        """
        profile = self.calculate_volume_profile(
            stock_id=stock_id,
            period_days=period_days,
            num_bins=50
        )
        
        if "error" in profile:
            return profile
        
        return {
            "stock_id": profile["stock_id"],
            "ticker_symbol": profile["ticker_symbol"],
            "poc": profile["poc"],
            "value_area_high": profile["value_area"]["high"],
            "value_area_low": profile["value_area"]["low"],
            "period": profile["period"]
        }
