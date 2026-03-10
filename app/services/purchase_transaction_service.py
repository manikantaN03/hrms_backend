"""
Purchase Transaction Service
Business logic for purchase transaction management
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import uuid

from app.models.purchase_transaction import PurchaseTransaction, TransactionLineItem, PaymentLog
from app.models.business import Business
from app.repositories.purchase_transaction_repository import (
    PurchaseTransactionRepository,
    TransactionLineItemRepository,
    PaymentLogRepository
)
from app.schemas.purchase_transaction import (
    PurchaseTransactionCreate,
    PurchaseTransactionUpdate,
    TransactionListResponse,
    TransactionFilters
)

logger = logging.getLogger(__name__)


class PurchaseTransactionService:
    """Service for purchase transaction management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = PurchaseTransactionRepository(db)
        self.line_item_repo = TransactionLineItemRepository(db)
        self.payment_log_repo = PaymentLogRepository(db)
    
    def get_all_transactions_for_frontend(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[TransactionFilters] = None
    ) -> List[TransactionListResponse]:
        """Get all transactions formatted for frontend"""
        
        # Apply filters if provided
        filter_kwargs = {}
        if filters:
            if filters.status:
                filter_kwargs['status_filter'] = filters.status
            if filters.payment_method:
                filter_kwargs['payment_method_filter'] = filters.payment_method
            if filters.date_from:
                filter_kwargs['date_from'] = filters.date_from
            if filters.date_to:
                filter_kwargs['date_to'] = filters.date_to
            if filters.business_id:
                filter_kwargs['business_id'] = filters.business_id
            if filters.search_term:
                filter_kwargs['search_term'] = filters.search_term
            if filters.sort_by:
                filter_kwargs['sort_by'] = filters.sort_by
            if filters.sort_order:
                filter_kwargs['sort_order'] = filters.sort_order
        
        transactions = self.transaction_repo.get_all_with_filters(
            skip=skip,
            limit=limit,
            **filter_kwargs
        )
        
        result = []
        for transaction in transactions:
            # Format for frontend compatibility
            transaction_response = TransactionListResponse(
                id=transaction.invoice_id,
                company=transaction.business.business_name if transaction.business else "Unknown Business",
                email=transaction.invoice_to_email,
                date=transaction.transaction_date.strftime("%d %b %Y") if transaction.transaction_date else "",
                amount=float(transaction.total_amount),
                method=transaction.payment_method,
                status=transaction.payment_status,
                logo=f"/assets/img/icons/{transaction.plan_name.lower().replace(' ', '-')}-icon.svg",
                
                # Invoice details
                from_info={
                    "name": transaction.invoice_from_name,
                    "address": transaction.invoice_from_address or "456 Green St, Hyderabad",
                    "email": transaction.invoice_from_email or "info@dcm.com"
                },
                to_info={
                    "name": transaction.invoice_to_name,
                    "address": transaction.invoice_to_address or "Business Address",
                    "email": transaction.invoice_to_email
                },
                plan=transaction.plan_name,
                billingCycle=transaction.billing_cycle,
                createdDate=transaction.service_start_date.strftime("%d %b %Y") if transaction.service_start_date else transaction.created_at.strftime("%d %b %Y"),
                expiringOn=transaction.service_end_date.strftime("%d %b %Y") if transaction.service_end_date else "",
                subtotal=float(transaction.subtotal),
                tax=float(transaction.tax_amount),
                total=float(transaction.total_amount),
                dueDate=transaction.due_date.strftime("%d %b %Y") if transaction.due_date else ""
            )
            result.append(transaction_response)
        
        return result
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[PurchaseTransaction]:
        """Get transaction by ID with business info"""
        return self.transaction_repo.get_with_business_info(transaction_id)
    
    def get_transaction_by_invoice_id(self, invoice_id: str) -> Optional[PurchaseTransaction]:
        """Get transaction by invoice ID"""
        return self.transaction_repo.get_by_invoice_id(invoice_id)
    
    def create_transaction(self, transaction_data: PurchaseTransactionCreate) -> PurchaseTransaction:
        """Create a new purchase transaction"""
        
        # Check if invoice ID already exists
        if self.transaction_repo.invoice_exists(transaction_data.invoice_id):
            raise ValueError(f"Invoice ID '{transaction_data.invoice_id}' already exists")
        
        # Create transaction
        transaction_dict = transaction_data.model_dump()
        transaction_dict["transaction_date"] = datetime.utcnow()
        
        # Set default due date if not provided (30 days from now)
        if not transaction_dict.get("due_date"):
            transaction_dict["due_date"] = datetime.utcnow() + timedelta(days=30)
        
        transaction = self.transaction_repo.create(transaction_dict)
        
        # Create payment log entry
        self._create_payment_log(
            transaction.id,
            "initiated",
            "Transaction created"
        )
        
        logger.info(f"Transaction created: {transaction.invoice_id} for business {transaction.business_id}")
        return transaction
    
    def update_transaction(self, transaction_id: int, update_data: PurchaseTransactionUpdate) -> Optional[PurchaseTransaction]:
        """Update a purchase transaction"""
        
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()
        
        # Log payment status changes
        if "payment_status" in update_dict and update_dict["payment_status"] != transaction.payment_status:
            self._create_payment_log(
                transaction_id,
                update_dict["payment_status"].lower(),
                f"Status changed from {transaction.payment_status} to {update_dict['payment_status']}"
            )
        
        return self.transaction_repo.update(transaction, update_dict)
    
    def update_payment_status(
        self,
        transaction_id: int,
        status: str,
        payment_reference: Optional[str] = None,
        gateway_response: Optional[str] = None
    ) -> Optional[PurchaseTransaction]:
        """Update payment status with logging"""
        
        success = self.transaction_repo.update_payment_status(
            transaction_id,
            status,
            payment_reference,
            datetime.utcnow() if status == "Paid" else None
        )
        
        if success:
            # Create payment log
            self._create_payment_log(
                transaction_id,
                status.lower(),
                f"Payment status updated to {status}",
                gateway_response=gateway_response
            )
            
            logger.info(f"Payment status updated for transaction {transaction_id}: {status}")
            return self.transaction_repo.get(transaction_id)
        
        return None
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a purchase transaction"""
        
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            return False
        
        # Only allow deletion of pending transactions
        if transaction.payment_status == "Paid":
            raise ValueError("Cannot delete paid transactions")
        
        # Delete associated line items and logs
        line_items = self.line_item_repo.get_by_transaction_id(transaction_id)
        for item in line_items:
            self.line_item_repo.delete(item.id)
        
        payment_logs = self.payment_log_repo.get_by_transaction_id(transaction_id)
        for log in payment_logs:
            self.payment_log_repo.delete(log.id)
        
        # Delete transaction
        self.transaction_repo.delete(transaction_id)
        
        logger.info(f"Transaction deleted: {transaction.invoice_id}")
        return True
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics for dashboard"""
        return self.transaction_repo.get_transaction_stats()
    
    def get_pending_payments(self) -> List[PurchaseTransaction]:
        """Get all pending payment transactions"""
        return self.transaction_repo.get_pending_payments()
    
    def get_overdue_payments(self) -> List[PurchaseTransaction]:
        """Get overdue payment transactions"""
        return self.transaction_repo.get_overdue_payments()
    
    def get_monthly_revenue(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly revenue analytics"""
        return self.transaction_repo.get_monthly_revenue(months)
    
    def get_payment_method_stats(self) -> List[Dict[str, Any]]:
        """Get payment method analytics"""
        return self.transaction_repo.get_payment_method_stats()
    
    def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by transaction volume"""
        return self.transaction_repo.get_top_customers(limit)
    
    def search_transactions(self, search_term: str, skip: int = 0, limit: int = 100) -> List[TransactionListResponse]:
        """Search transactions by business name, invoice ID, or email"""
        filters = TransactionFilters(search_term=search_term)
        return self.get_all_transactions_for_frontend(skip=skip, limit=limit, filters=filters)
    
    def generate_invoice_id(self) -> str:
        """Generate a unique invoice ID"""
        while True:
            # Generate invoice ID in format INV001, INV002, etc.
            count = self.transaction_repo.count() + 1
            invoice_id = f"INV{count:03d}"
            
            if not self.transaction_repo.invoice_exists(invoice_id):
                return invoice_id
            
            # If exists, try with random suffix
            invoice_id = f"INV{count:03d}_{uuid.uuid4().hex[:4].upper()}"
            if not self.transaction_repo.invoice_exists(invoice_id):
                return invoice_id
    
    def process_payment(
        self,
        transaction_id: int,
        payment_method: str,
        payment_reference: str,
        gateway_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process payment for a transaction"""
        
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.payment_status == "Paid":
            raise ValueError("Transaction already paid")
        
        try:
            # Mock payment processing (in real implementation, integrate with payment gateway)
            # For demo purposes, we'll simulate success
            
            success = self.transaction_repo.update_payment_status(
                transaction_id,
                "Paid",
                payment_reference,
                datetime.utcnow()
            )
            
            if success:
                self._create_payment_log(
                    transaction_id,
                    "success",
                    "Payment processed successfully",
                    gateway_response=gateway_response
                )
                
                logger.info(f"Payment processed for transaction {transaction_id}")
                return {
                    "success": True,
                    "message": "Payment processed successfully",
                    "transaction_id": transaction_id,
                    "payment_reference": payment_reference
                }
            else:
                raise Exception("Failed to update payment status")
                
        except Exception as e:
            # Log failed payment attempt
            self._create_payment_log(
                transaction_id,
                "failed",
                f"Payment processing failed: {str(e)}",
                gateway_response=gateway_response
            )
            
            logger.error(f"Payment processing failed for transaction {transaction_id}: {e}")
            return {
                "success": False,
                "message": f"Payment processing failed: {str(e)}",
                "transaction_id": transaction_id
            }
    
    def _create_payment_log(
        self,
        transaction_id: int,
        status: str,
        message: str,
        gateway_response: Optional[str] = None
    ) -> PaymentLog:
        """Create a payment log entry"""
        
        log_data = {
            "transaction_id": transaction_id,
            "status": status,
            "gateway_response": gateway_response or message,
            "processed_at": datetime.utcnow()
        }
        
        return self.payment_log_repo.create(log_data)


class TransactionAnalyticsService:
    """Service for transaction analytics and reporting."""
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = PurchaseTransactionRepository(db)
    
    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for dashboard"""
        
        stats = self.transaction_repo.get_transaction_stats()
        monthly_revenue = self.transaction_repo.get_monthly_revenue(12)
        payment_methods = self.transaction_repo.get_payment_method_stats()
        top_customers = self.transaction_repo.get_top_customers(5)
        
        return {
            "summary": stats,
            "monthly_revenue": monthly_revenue,
            "payment_method_stats": payment_methods,
            "top_customers": top_customers
        }
    
    def get_revenue_trends(self, period: str = "monthly") -> List[Dict[str, Any]]:
        """Get revenue trends by period"""
        
        if period == "monthly":
            return self.transaction_repo.get_monthly_revenue(12)
        else:
            # For other periods, we can extend this method
            return self.transaction_repo.get_monthly_revenue(12)