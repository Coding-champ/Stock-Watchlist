"""
Index Constituent Service
Service for managing index constituents (CSV import, status tracking)
"""

import csv
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from backend.app.models import MarketIndex, IndexConstituent, Stock

logger = logging.getLogger(__name__)


class IndexConstituentService:
    """Service for managing index constituents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_constituent(
        self,
        index_id: int,
        stock_id: int,
        weight: Optional[float] = None,
        date_added: Optional[date] = None,
        status: str = "active"
    ) -> IndexConstituent:
        """
        Add a stock to an index
        
        Args:
            index_id: Market index ID
            stock_id: Stock ID
            weight: Weight in index (optional)
            date_added: Date added to index (defaults to today)
            status: Status ('active' or 'removed')
        
        Returns:
            Created IndexConstituent
        """
        if date_added is None:
            date_added = date.today()
        
        # Check if already exists (active)
        existing = self.db.query(IndexConstituent).filter(
            and_(
                IndexConstituent.index_id == index_id,
                IndexConstituent.stock_id == stock_id,
                IndexConstituent.status == "active"
            )
        ).first()
        
        if existing:
            logger.warning(f"Constituent already exists: index_id={index_id}, stock_id={stock_id}")
            return existing
        
        constituent = IndexConstituent(
            index_id=index_id,
            stock_id=stock_id,
            weight=weight,
            date_added=date_added,
            status=status
        )
        
        self.db.add(constituent)
        self.db.commit()
        self.db.refresh(constituent)
        
        logger.info(f"Added constituent: index_id={index_id}, stock_id={stock_id}")
        return constituent
    
    def remove_constituent(
        self,
        index_id: int,
        stock_id: int,
        date_removed: Optional[date] = None
    ) -> bool:
        """
        Remove a stock from an index (marks as inactive, keeps history)
        
        Args:
            index_id: Market index ID
            stock_id: Stock ID
            date_removed: Date removed (defaults to today)
        
        Returns:
            True if removed, False if not found
        """
        if date_removed is None:
            date_removed = date.today()
        
        constituent = self.db.query(IndexConstituent).filter(
            and_(
                IndexConstituent.index_id == index_id,
                IndexConstituent.stock_id == stock_id,
                IndexConstituent.status == "active"
            )
        ).first()
        
        if not constituent:
            return False
        
        constituent.status = "inactive"
        constituent.date_removed = date_removed
        constituent.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Removed constituent: index_id={index_id}, stock_id={stock_id}")
        return True
    
    def get_active_constituents(
        self,
        index_id: int
    ) -> List[IndexConstituent]:
        """
        Get all active constituents of an index
        
        Args:
            index_id: Market index ID
        
        Returns:
            List of active IndexConstituent
        """
        return self.db.query(IndexConstituent).filter(
            and_(
                IndexConstituent.index_id == index_id,
                IndexConstituent.status == "active"
            )
        ).order_by(desc(IndexConstituent.weight)).all()
    
    def get_all_constituents(
        self,
        index_id: int,
        include_removed: bool = False
    ) -> List[IndexConstituent]:
        """
        Get all constituents (optionally including inactive/removed)
        
        Args:
            index_id: Market index ID
            include_removed: Include inactive constituents
        
        Returns:
            List of IndexConstituent
        """
        query = self.db.query(IndexConstituent).filter(
            IndexConstituent.index_id == index_id
        )
        
        if not include_removed:
            query = query.filter(IndexConstituent.status == "active")
        
        return query.order_by(desc(IndexConstituent.weight)).all()
    
    def update_constituent_weight(
        self,
        index_id: int,
        stock_id: int,
        new_weight: float
    ) -> bool:
        """
        Update constituent weight in index
        
        Args:
            index_id: Market index ID
            stock_id: Stock ID
            new_weight: New weight value
        
        Returns:
            True if updated, False if not found
        """
        constituent = self.db.query(IndexConstituent).filter(
            and_(
                IndexConstituent.index_id == index_id,
                IndexConstituent.stock_id == stock_id,
                IndexConstituent.status == "active"
            )
        ).first()
        
        if not constituent:
            return False
        
        constituent.weight = new_weight
        constituent.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Updated weight: index_id={index_id}, stock_id={stock_id}, weight={new_weight}")
        return True
    
    def import_constituents_from_csv(
        self,
        index_id: int,
        csv_file_path: str,
        replace_existing: bool = False,
        auto_calculate_weights: bool = True,
        weight_method: str = "market_cap"
    ) -> Dict[str, Any]:
        """
        Import constituents from CSV file
        
        Expected CSV columns:
        - ticker_symbol (required)
        - weight (optional, can be omitted if auto_calculate_weights=True)
        - date_added (optional, defaults to today)
        
        Args:
            index_id: Market index ID
            csv_file_path: Path to CSV file
            replace_existing: If True, marks old constituents as removed
            auto_calculate_weights: If True, automatically calculates weights after import
            weight_method: Method for weight calculation ('market_cap' or 'equal')
        
        Returns:
            Result dict with counts and weight calculation info
        """
        try:
            # Get index
            index = self.db.query(MarketIndex).filter(MarketIndex.id == index_id).first()
            if not index:
                return {"success": False, "error": "Index not found"}
            
            # If replacing, mark all current constituents as removed
            if replace_existing:
                active_constituents = self.get_active_constituents(index_id)
                for constituent in active_constituents:
                    self.remove_constituent(index_id, constituent.stock_id)
            
            # Read CSV
            imported = 0
            skipped = 0
            errors = []
            
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    ticker_symbol = row.get('ticker_symbol', '').strip()
                    if not ticker_symbol:
                        skipped += 1
                        continue
                    
                    # Find stock by ticker
                    stock = self.db.query(Stock).filter(
                        Stock.ticker_symbol == ticker_symbol
                    ).first()
                    
                    if not stock:
                        errors.append(f"Stock not found: {ticker_symbol}")
                        skipped += 1
                        continue
                    
                    # Parse weight
                    weight = None
                    if 'weight' in row and row['weight']:
                        try:
                            weight = float(row['weight'])
                        except ValueError:
                            pass
                    
                    # Parse date_added
                    date_added = date.today()
                    if 'date_added' in row and row['date_added']:
                        try:
                            date_added = datetime.strptime(row['date_added'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    # Add constituent
                    self.add_constituent(
                        index_id=index_id,
                        stock_id=stock.id,
                        weight=weight,
                        date_added=date_added
                    )
                    imported += 1
            
            logger.info(f"Imported {imported} constituents for index {index.name}")
            
            result = {
                "success": True,
                "imported": imported,
                "skipped": skipped,
                "errors": errors
            }
            
            # Auto-calculate weights if enabled
            if auto_calculate_weights and imported > 0:
                try:
                    from backend.app.services.index_weight_calculator import IndexWeightCalculator
                    
                    calculator = IndexWeightCalculator(self.db)
                    weight_result = calculator.calculate_market_cap_weights(
                        index_id=index_id,
                        refresh_market_caps=True
                    ) if weight_method == "market_cap" else calculator.calculate_equal_weights(index_id)
                    
                    result["weights_calculated"] = True
                    result["weights_method"] = weight_method
                    result["weights_updated"] = weight_result.get("updated_count", 0)
                    result["total_market_cap"] = weight_result.get("total_market_cap")
                    
                    logger.info(f"Auto-calculated weights for {weight_result.get('updated_count', 0)} constituents using {weight_method} method")
                except Exception as e:
                    logger.warning(f"Failed to auto-calculate weights: {e}")
                    result["weights_calculated"] = False
                    result["weights_error"] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"Error importing constituents: {e}")
            return {"success": False, "error": str(e)}
    
    def export_constituents_to_csv(
        self,
        index_id: int,
        csv_file_path: str,
        include_removed: bool = False
    ) -> Dict[str, Any]:
        """
        Export constituents to CSV file
        
        Args:
            index_id: Market index ID
            csv_file_path: Output CSV file path
            include_removed: Include removed constituents
        
        Returns:
            Result dict with count
        """
        try:
            constituents = self.get_all_constituents(index_id, include_removed)
            
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['ticker_symbol', 'name', 'weight', 'status', 'date_added', 'date_removed']
                )
                writer.writeheader()
                
                for constituent in constituents:
                    writer.writerow({
                        'ticker_symbol': constituent.stock.ticker_symbol,
                        'name': constituent.stock.name,
                        'weight': constituent.weight,
                        'status': constituent.status,
                        'date_added': constituent.date_added.isoformat(),
                        'date_removed': constituent.date_removed.isoformat() if constituent.date_removed else ''
                    })
            
            logger.info(f"Exported {len(constituents)} constituents to {csv_file_path}")
            
            return {
                "success": True,
                "count": len(constituents),
                "file_path": csv_file_path
            }
            
        except Exception as e:
            logger.error(f"Error exporting constituents: {e}")
            return {"success": False, "error": str(e)}
