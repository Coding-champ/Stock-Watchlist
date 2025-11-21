"""
Index Weight Calculator Service
Automatically calculates constituent weights based on market capitalization
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
import yfinance as yf

from backend.app.models import MarketIndex, IndexConstituent, Stock

logger = logging.getLogger(__name__)


class IndexWeightCalculator:
    """Service for calculating and updating index constituent weights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_market_cap_weights(
        self,
        index_id: int,
        refresh_market_caps: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate constituent weights based on market capitalization
        
        For market-cap weighted indices like S&P 500, DAX, etc.
        Weight = (Stock Market Cap / Sum of All Constituent Market Caps) * 100
        
        Args:
            index_id: Market index ID
            refresh_market_caps: If True, fetch fresh market caps from yfinance
        
        Returns:
            Result dict with updated count and summary
        """
        try:
            # Get index
            index = self.db.query(MarketIndex).filter(MarketIndex.id == index_id).first()
            if not index:
                return {"success": False, "error": "Index not found"}
            
            # Get active constituents
            constituents = self.db.query(IndexConstituent).filter(
                IndexConstituent.index_id == index_id,
                IndexConstituent.status == "active"
            ).all()
            
            if not constituents:
                return {"success": False, "error": "No active constituents found"}
            
            logger.info(f"Calculating weights for {index.name} ({len(constituents)} constituents)")
            
            # Collect market caps
            market_caps = {}
            failed = []
            
            for constituent in constituents:
                stock = constituent.stock
                ticker = stock.ticker_symbol
                
                if refresh_market_caps:
                    # Fetch fresh market cap from yfinance
                    try:
                        yf_ticker = yf.Ticker(ticker)
                        info = yf_ticker.info or {}
                        market_cap = info.get('marketCap')
                        
                        if market_cap and market_cap > 0:
                            market_caps[constituent.id] = market_cap
                            logger.debug(f"  {ticker}: ${market_cap:,.0f}")
                        else:
                            logger.warning(f"  {ticker}: No market cap available")
                            failed.append(ticker)
                    except Exception as e:
                        logger.error(f"  {ticker}: Error fetching market cap: {e}")
                        failed.append(ticker)
                else:
                    # Use stored market cap from stock table (if available)
                    # Note: This would require adding market_cap field to Stock model
                    logger.warning("Using stored market caps not yet implemented")
                    return {"success": False, "error": "Stored market caps feature not available"}
            
            if not market_caps:
                return {
                    "success": False,
                    "error": "No market caps could be retrieved",
                    "failed": failed
                }
            
            # Calculate total market cap
            total_market_cap = sum(market_caps.values())
            logger.info(f"Total market cap: ${total_market_cap:,.0f}")
            
            # Calculate and update weights
            updated = 0
            weights_summary = []
            
            for constituent_id, market_cap in market_caps.items():
                weight = (market_cap / total_market_cap) * 100
                
                constituent = self.db.query(IndexConstituent).filter(
                    IndexConstituent.id == constituent_id
                ).first()
                
                if constituent:
                    old_weight = constituent.weight
                    constituent.weight = round(weight, 4)
                    constituent.updated_at = datetime.utcnow()
                    
                    weights_summary.append({
                        "ticker": constituent.stock.ticker_symbol,
                        "old_weight": round(old_weight, 2) if old_weight else None,
                        "new_weight": round(weight, 2),
                        "market_cap": market_cap
                    })
                    
                    updated += 1
            
            self.db.commit()
            
            # Sort by weight descending
            weights_summary.sort(key=lambda x: x['new_weight'], reverse=True)
            
            logger.info(f"✓ Updated weights for {updated} constituents")
            
            return {
                "success": True,
                "index": index.name,
                "total_constituents": len(constituents),
                "updated": updated,
                "failed": len(failed),
                "failed_tickers": failed,
                "total_market_cap": total_market_cap,
                "weights": weights_summary[:10],  # Top 10 for summary
                "calculation_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating weights: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_equal_weights(
        self,
        index_id: int
    ) -> Dict[str, Any]:
        """
        Calculate equal weights for all constituents
        
        Used for equal-weighted indices
        Weight = 100 / Number of Constituents
        
        Args:
            index_id: Market index ID
        
        Returns:
            Result dict with updated count
        """
        try:
            # Get index
            index = self.db.query(MarketIndex).filter(MarketIndex.id == index_id).first()
            if not index:
                return {"success": False, "error": "Index not found"}
            
            # Get active constituents
            constituents = self.db.query(IndexConstituent).filter(
                IndexConstituent.index_id == index_id,
                IndexConstituent.status == "active"
            ).all()
            
            if not constituents:
                return {"success": False, "error": "No active constituents found"}
            
            # Calculate equal weight
            equal_weight = 100.0 / len(constituents)
            
            logger.info(f"Setting equal weights for {index.name}: {equal_weight:.4f}% each")
            
            # Update all constituents
            updated = 0
            for constituent in constituents:
                constituent.weight = round(equal_weight, 4)
                constituent.updated_at = datetime.utcnow()
                updated += 1
            
            self.db.commit()
            
            logger.info(f"✓ Updated weights for {updated} constituents")
            
            return {
                "success": True,
                "index": index.name,
                "updated": updated,
                "equal_weight": round(equal_weight, 4)
            }
            
        except Exception as e:
            logger.error(f"Error calculating equal weights: {e}")
            return {"success": False, "error": str(e)}
    
    def recalculate_all_indices(
        self,
        method: str = "market_cap"
    ) -> List[Dict[str, Any]]:
        """
        Recalculate weights for all indices
        
        Args:
            method: Calculation method ('market_cap' or 'equal')
        
        Returns:
            List of result dicts for each index
        """
        results = []
        
        # Get all indices
        indices = self.db.query(MarketIndex).all()
        
        for index in indices:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {index.name}")
            logger.info(f"{'='*60}")
            
            if method == "market_cap":
                result = self.calculate_market_cap_weights(index.id)
            elif method == "equal":
                result = self.calculate_equal_weights(index.id)
            else:
                result = {"success": False, "error": f"Unknown method: {method}"}
            
            result["index_ticker"] = index.ticker_symbol
            results.append(result)
        
        return results
