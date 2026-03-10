"""
Purchase Transaction Models
Manages purchase transactions, invoices, and billing for businesses
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Numeric, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class PurchaseTransaction(BaseModel):
    """
    Purchase transactions for business subscriptions and services.
    """
    
    __tablename__ = "purchase_transactions"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Purchaser
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True, index=True)
    
    # ========================================================================
    # Transaction Details
    # ========================================================================
    invoice_id = Column(String(50), nullable=False, unique=True, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================================================
    # Financial Details
    # ========================================================================
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0.0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    
    # ========================================================================
    # Payment Information
    # ========================================================================
    payment_method = Column(String(100), nullable=False)  # Credit Card, Bank Transfer, PayPal, etc.
    payment_status = Column(String(50), nullable=False, default="Pending")  # Pending, Paid, Failed, Refunded
    payment_reference = Column(String(255), nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================================================
    # Service Details
    # ========================================================================
    plan_name = Column(String(100), nullable=False)
    billing_cycle = Column(String(50), nullable=False)  # Monthly, Yearly
    service_start_date = Column(DateTime(timezone=True), nullable=True)
    service_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================================================
    # Invoice Information
    # ========================================================================
    invoice_from_name = Column(String(255), nullable=False, default="DCM")
    invoice_from_address = Column(Text, nullable=True)
    invoice_from_email = Column(String(255), nullable=True)
    
    invoice_to_name = Column(String(255), nullable=False)
    invoice_to_address = Column(Text, nullable=True)
    invoice_to_email = Column(String(255), nullable=False)
    
    # ========================================================================
    # Additional Information
    # ========================================================================
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # ========================================================================
    # Relationships
    # ========================================================================
    business = relationship("Business", backref="purchase_transactions")
    user = relationship("User", backref="purchase_transactions")
    subscription = relationship("Subscription", backref="purchase_transactions")
    
    def __repr__(self):
        return f"<PurchaseTransaction(invoice_id='{self.invoice_id}', amount={self.total_amount})>"


class TransactionLineItem(BaseModel):
    """
    Line items for purchase transactions (for detailed billing).
    """
    
    __tablename__ = "transaction_line_items"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    transaction_id = Column(Integer, ForeignKey("purchase_transactions.id"), nullable=False, index=True)
    
    # ========================================================================
    # Item Details
    # ========================================================================
    item_name = Column(String(255), nullable=False)
    item_description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    
    # ========================================================================
    # Additional Information
    # ========================================================================
    item_type = Column(String(100), nullable=True)  # subscription, addon, service, etc.
    item_reference = Column(String(255), nullable=True)  # Reference to subscription, plan, etc.
    
    # ========================================================================
    # Relationships
    # ========================================================================
    transaction = relationship("PurchaseTransaction", backref="line_items")
    
    def __repr__(self):
        return f"<TransactionLineItem(name='{self.item_name}', price={self.total_price})>"


class PaymentLog(BaseModel):
    """
    Payment processing logs and audit trail.
    """
    
    __tablename__ = "payment_logs"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    transaction_id = Column(Integer, ForeignKey("purchase_transactions.id"), nullable=False, index=True)
    
    # ========================================================================
    # Payment Processing Details
    # ========================================================================
    payment_gateway = Column(String(100), nullable=True)  # Stripe, PayPal, Razorpay, etc.
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_response = Column(Text, nullable=True)  # JSON response from gateway
    
    # ========================================================================
    # Status and Timing
    # ========================================================================
    status = Column(String(50), nullable=False)  # initiated, processing, success, failed
    attempt_number = Column(Integer, nullable=False, default=1)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================================================
    # Error Handling
    # ========================================================================
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # ========================================================================
    # Additional Information
    # ========================================================================
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # ========================================================================
    # Relationships
    # ========================================================================
    transaction = relationship("PurchaseTransaction", backref="payment_logs")
    
    def __repr__(self):
        return f"<PaymentLog(transaction_id={self.transaction_id}, status='{self.status}')>"