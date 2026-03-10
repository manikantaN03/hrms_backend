"""
Purchase Transaction Repository
Database operations for purchase transaction management
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, extract
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.purchase_transaction import PurchaseTransaction, TransactionLineItem, PaymentLog
from app.models.business import Business
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class PurchaseTransactionRepository(BaseRepository[PurchaseTransaction]):
    """Repository for purchase transaction operations."""
    
    def __init__(self, db: Session):
        super().__init__(PurchaseTransaction, db)
    
    def get_with_business_info(self, transaction_id: int) -> Optional[PurchaseTransaction]:
        """Get transaction with business and user information"""
        return (
            self.db.query(PurchaseTransaction)
            .options(
                joinedload(PurchaseTransaction.business).joinedload(Business.owner),
                joinedload(PurchaseTransaction.user),
                joinedload(PurchaseTransaction.subscription),
                joinedload(PurchaseTransaction.line_items)
            )
            .filter(PurchaseTransaction.id == transaction_id)
            .first()
        )
    
    def get_by_invoice_id(self, invoice_id: str) -> Optional[PurchaseTransaction]:
        """Get transaction by invoice ID"""
        return (
            self.db.query(PurchaseTransaction)
            .options(joinedload(PurchaseTransaction.business))
            .filter(PurchaseTransaction.invoice_id == invoice_id)
            .first()
        )
    
    def get_all_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        payment_method_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        business_id: Optional[int] = None,
        search_term: Optional[str] = None,
        sort_by: str = "transaction_date",
        sort_order: str = "desc"
    ) -> List[PurchaseTransaction]:
        """Get all transactions with filters and sorting"""
        
        query = (
            self.db.query(PurchaseTransaction)
            .options(
                joinedload(PurchaseTransaction.business),
                joinedload(PurchaseTransaction.user)
            )
        )
        
        # Apply filters
        if status_filter:
            query = query.filter(PurchaseTransaction.payment_status == status_filter)
        
        if payment_method_filter:
            query = query.filter(PurchaseTransaction.payment_method == payment_method_filter)
        
        if business_id:
            query = query.filter(PurchaseTransaction.business_id == business_id)
        
        if date_from:
            query = query.filter(PurchaseTransaction.transaction_date >= date_from)
        
        if date_to:
            query = query.filter(PurchaseTransaction.transaction_date <= date_to)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.join(Business).filter(
                or_(
                    Business.business_name.ilike(search_pattern),
                    PurchaseTransaction.invoice_id.ilike(search_pattern),
                    PurchaseTransaction.invoice_to_email.ilike(search_pattern)
                )
            )
        
        # Apply sorting
        sort_column = getattr(PurchaseTransaction, sort_by, PurchaseTransaction.transaction_date)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_business_id(self, business_id: int) -> List[PurchaseTransaction]:
        """Get all transactions for a business"""
        return (
            self.db.query(PurchaseTransaction)
            .filter(PurchaseTransaction.business_id == business_id)
            .order_by(desc(PurchaseTransaction.transaction_date))
            .all()
        )
    
    def get_pending_payments(self) -> List[PurchaseTransaction]:
        """Get all pending payment transactions"""
        return (
            self.db.query(PurchaseTransaction)
            .options(joinedload(PurchaseTransaction.business))
            .filter(PurchaseTransaction.payment_status == "Pending")
            .order_by(asc(PurchaseTransaction.due_date))
            .all()
        )
    
    def get_overdue_payments(self) -> List[PurchaseTransaction]:
        """Get overdue payment transactions"""
        current_date = datetime.utcnow()
        
        return (
            self.db.query(PurchaseTransaction)
            .options(joinedload(PurchaseTransaction.business))
            .filter(
                and_(
                    PurchaseTransaction.payment_status == "Pending",
                    PurchaseTransaction.due_date < current_date
                )
            )
            .order_by(asc(PurchaseTransaction.due_date))
            .all()
        )
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        
        # Basic counts
        total_transactions = self.db.query(PurchaseTransaction).count()
        paid_transactions = self.db.query(PurchaseTransaction).filter(
            PurchaseTransaction.payment_status == "Paid"
        ).count()
        pending_transactions = self.db.query(PurchaseTransaction).filter(
            PurchaseTransaction.payment_status == "Pending"
        ).count()
        failed_transactions = self.db.query(PurchaseTransaction).filter(
            PurchaseTransaction.payment_status == "Failed"
        ).count()
        
        # Revenue calculations
        total_revenue = self.db.query(func.sum(PurchaseTransaction.total_amount)).filter(
            PurchaseTransaction.payment_status == "Paid"
        ).scalar() or Decimal('0.0')
        
        avg_transaction = self.db.query(func.avg(PurchaseTransaction.total_amount)).scalar() or Decimal('0.0')
        
        return {
            "total_transactions": total_transactions,
            "paid_transactions": paid_transactions,
            "unpaid_transactions": pending_transactions + failed_transactions,
            "pending_transactions": pending_transactions,
            "failed_transactions": failed_transactions,
            "total_revenue": total_revenue,
            "average_transaction_amount": avg_transaction
        }
    
    def get_monthly_revenue(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly revenue data"""
        
        result = (
            self.db.query(
                extract('year', PurchaseTransaction.transaction_date).label('year'),
                extract('month', PurchaseTransaction.transaction_date).label('month'),
                func.sum(PurchaseTransaction.total_amount).label('revenue'),
                func.count(PurchaseTransaction.id).label('transaction_count')
            )
            .filter(
                and_(
                    PurchaseTransaction.payment_status == "Paid",
                    PurchaseTransaction.transaction_date >= datetime.utcnow() - timedelta(days=months * 30)
                )
            )
            .group_by(
                extract('year', PurchaseTransaction.transaction_date),
                extract('month', PurchaseTransaction.transaction_date)
            )
            .order_by(
                extract('year', PurchaseTransaction.transaction_date),
                extract('month', PurchaseTransaction.transaction_date)
            )
            .all()
        )
        
        return [
            {
                "year": int(row.year),
                "month": int(row.month),
                "revenue": float(row.revenue or 0),
                "transaction_count": row.transaction_count
            }
            for row in result
        ]
    
    def get_payment_method_stats(self) -> List[Dict[str, Any]]:
        """Get payment method statistics"""
        
        result = (
            self.db.query(
                PurchaseTransaction.payment_method,
                func.count(PurchaseTransaction.id).label('count'),
                func.sum(PurchaseTransaction.total_amount).label('total_amount')
            )
            .filter(PurchaseTransaction.payment_status == "Paid")
            .group_by(PurchaseTransaction.payment_method)
            .order_by(desc(func.count(PurchaseTransaction.id)))
            .all()
        )
        
        return [
            {
                "payment_method": row.payment_method,
                "count": row.count,
                "total_amount": float(row.total_amount or 0)
            }
            for row in result
        ]
    
    def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by transaction volume"""
        
        result = (
            self.db.query(
                Business.business_name,
                User.email.label('business_email'),
                func.count(PurchaseTransaction.id).label('transaction_count'),
                func.sum(PurchaseTransaction.total_amount).label('total_spent')
            )
            .join(Business, PurchaseTransaction.business_id == Business.id)
            .join(User, Business.owner_id == User.id)
            .filter(PurchaseTransaction.payment_status == "Paid")
            .group_by(Business.id, Business.business_name, User.email)
            .order_by(desc(func.sum(PurchaseTransaction.total_amount)))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "business_name": row.business_name,
                "business_email": row.business_email,
                "transaction_count": row.transaction_count,
                "total_spent": float(row.total_spent or 0)
            }
            for row in result
        ]
    
    def invoice_exists(self, invoice_id: str, exclude_id: Optional[int] = None) -> bool:
        """Check if invoice ID already exists"""
        query = self.db.query(PurchaseTransaction).filter(PurchaseTransaction.invoice_id == invoice_id)
        
        if exclude_id:
            query = query.filter(PurchaseTransaction.id != exclude_id)
        
        return query.first() is not None
    
    def update_payment_status(
        self, 
        transaction_id: int, 
        status: str, 
        payment_reference: Optional[str] = None,
        payment_date: Optional[datetime] = None
    ) -> bool:
        """Update payment status for a transaction"""
        
        transaction = self.get(transaction_id)
        if not transaction:
            return False
        
        transaction.payment_status = status
        if payment_reference:
            transaction.payment_reference = payment_reference
        if payment_date:
            transaction.payment_date = payment_date
        elif status == "Paid" and not transaction.payment_date:
            transaction.payment_date = datetime.utcnow()
        
        transaction.updated_at = datetime.utcnow()
        self.db.commit()
        return True


class TransactionLineItemRepository(BaseRepository[TransactionLineItem]):
    """Repository for transaction line item operations."""
    
    def __init__(self, db: Session):
        super().__init__(TransactionLineItem, db)
    
    def get_by_transaction_id(self, transaction_id: int) -> List[TransactionLineItem]:
        """Get all line items for a transaction"""
        return (
            self.db.query(TransactionLineItem)
            .filter(TransactionLineItem.transaction_id == transaction_id)
            .all()
        )


class PaymentLogRepository(BaseRepository[PaymentLog]):
    """Repository for payment log operations."""
    
    def __init__(self, db: Session):
        super().__init__(PaymentLog, db)
    
    def get_by_transaction_id(self, transaction_id: int) -> List[PaymentLog]:
        """Get all payment logs for a transaction"""
        return (
            self.db.query(PaymentLog)
            .filter(PaymentLog.transaction_id == transaction_id)
            .order_by(desc(PaymentLog.created_at))
            .all()
        )
    
    def get_failed_payments(self, limit: int = 100) -> List[PaymentLog]:
        """Get recent failed payment attempts"""
        return (
            self.db.query(PaymentLog)
            .filter(PaymentLog.status == "failed")
            .order_by(desc(PaymentLog.created_at))
            .limit(limit)
            .all()
        )