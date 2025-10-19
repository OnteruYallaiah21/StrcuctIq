"""
Service layer for business logic and database operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, time
from app.models.models import Receipt, Item
from app.schemas.schemas import ReceiptCreate, ReceiptUpdate, AnalyticsResponse


class ReceiptService:
    """Service class for receipt operations."""
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        if isinstance(date_str, date):
            return date_str
        
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
    
    @staticmethod
    def _parse_time(time_str: Optional[str]) -> Optional[time]:
        """Parse time string to time object."""
        if not time_str:
            return None
        if isinstance(time_str, time):
            return time_str
        
        # Try different time formats
        for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        return None
    
    @staticmethod
    def create_receipt(db: Session, receipt_data: ReceiptCreate) -> Receipt:
        """Create a new receipt with items."""
        db_receipt = Receipt(
            store_name=receipt_data.store_name,
            date=ReceiptService._parse_date(receipt_data.date),
            time=ReceiptService._parse_time(receipt_data.time),
            subtotal=receipt_data.subtotal,
            tax=receipt_data.tax,
            total=receipt_data.total,
            payment_method=receipt_data.payment_method
        )
        
        db.add(db_receipt)
        db.flush()  # Get the ID
        
        # Add items
        for item_data in receipt_data.items:
            db_item = Item(
                receipt_id=db_receipt.id,
                item_name=item_data.item_name,
                item_price=item_data.item_price
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_receipt)
        return db_receipt
    
    @staticmethod
    def get_receipt(db: Session, receipt_id: int) -> Optional[Receipt]:
        """Get a receipt by ID."""
        return db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    @staticmethod
    def get_receipts(db: Session, skip: int = 0, limit: int = 100) -> List[Receipt]:
        """Get receipts with pagination."""
        return db.query(Receipt).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_receipts_by_store(db: Session, store_name: str, skip: int = 0, limit: int = 100) -> List[Receipt]:
        """Get receipts by store name."""
        return db.query(Receipt).filter(
            Receipt.store_name.ilike(f"%{store_name}%")
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_receipts_by_date_range(db: Session, start_date, end_date, skip: int = 0, limit: int = 100) -> List[Receipt]:
        """Get receipts within a date range."""
        return db.query(Receipt).filter(
            Receipt.date >= start_date,
            Receipt.date <= end_date
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_receipt(db: Session, receipt_id: int, receipt_data: ReceiptUpdate) -> Optional[Receipt]:
        """Update a receipt."""
        db_receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not db_receipt:
            return None
        
        # Update receipt fields
        for field, value in receipt_data.dict(exclude_unset=True).items():
            if field != 'items':
                setattr(db_receipt, field, value)
        
        # Update items if provided
        if receipt_data.items is not None:
            # Delete existing items
            db.query(Item).filter(Item.receipt_id == receipt_id).delete()
            
            # Add new items
            for item_data in receipt_data.items:
                db_item = Item(
                    receipt_id=receipt_id,
                    item_name=item_data.item_name,
                    item_price=item_data.item_price
                )
                db.add(db_item)
        
        db.commit()
        db.refresh(db_receipt)
        return db_receipt
    
    @staticmethod
    def delete_receipt(db: Session, receipt_id: int) -> bool:
        """Delete a receipt."""
        db_receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not db_receipt:
            return False
        
        db.delete(db_receipt)
        db.commit()
        return True
    
    @staticmethod
    def get_analytics(db: Session) -> AnalyticsResponse:
        """Get analytics data."""
        # Total receipts
        total_receipts = db.query(Receipt).count()
        
        # Total amount spent
        total_amount = db.query(Receipt.total).all()
        total_spent = sum(float(amount[0]) for amount in total_amount if amount[0])
        
        # Average receipt amount
        avg_amount = total_spent / total_receipts if total_receipts > 0 else 0
        
        # Top stores by spending
        top_stores = db.query(
            Receipt.store_name,
            db.query(Receipt.total).filter(Receipt.store_name == Receipt.store_name).sum().label('total_spent')
        ).group_by(Receipt.store_name).order_by('total_spent').limit(10).all()
        
        # Date range
        date_range = db.query(
            db.query(Receipt.date).min().label('earliest'),
            db.query(Receipt.date).max().label('latest')
        ).first()
        
        return AnalyticsResponse(
            total_receipts=total_receipts,
            total_amount_spent=round(total_spent, 2),
            average_receipt_amount=round(avg_amount, 2),
            top_stores=[{"store": store[0], "total": float(store[1])} for store in top_stores],
            date_range={
                "earliest": date_range.earliest.isoformat() if date_range.earliest else None,
                "latest": date_range.latest.isoformat() if date_range.latest else None
            }
        )
    
    @staticmethod
    def count_receipts(db: Session) -> int:
        """Count total receipts."""
        return db.query(Receipt).count()
    
    @staticmethod
    def count_receipts_by_store(db: Session, store_name: str) -> int:
        """Count receipts by store."""
        return db.query(Receipt).filter(
            Receipt.store_name.ilike(f"%{store_name}%")
        ).count()
    
    @staticmethod
    def count_receipts_by_date_range(db: Session, start_date, end_date) -> int:
        """Count receipts by date range."""
        return db.query(Receipt).filter(
            Receipt.date >= start_date,
            Receipt.date <= end_date
        ).count()
