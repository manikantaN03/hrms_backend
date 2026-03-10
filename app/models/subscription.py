"""
Subscription Models
Manages company subscriptions, payments, and billing cycles
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class Subscription(BaseModel):
    """
    Company subscription records with payment and billing information.
    """
    
    __tablename__ = "subscriptions"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Subscriber
    
    # ========================================================================
    # Subscription Details
    # ========================================================================
    plan_name = Column(String(100), nullable=False)  # Basic, Advanced, Enterprise
    plan_type = Column(String(50), nullable=False)   # Monthly, Yearly
    billing_cycle = Column(String(100), nullable=False)  # "30 Days", "365 Days"
    
    # ========================================================================
    # Payment Information
    # ========================================================================
    payment_method = Column(String(100), nullable=False)  # Credit Card, PayPal, Debit Card
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    payment_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # ========================================================================
    # Billing Dates
    # ========================================================================
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================================================
    # Status and Flags
    # ========================================================================
    status = Column(String(50), nullable=False, default="Active")  # Active, Expired, Cancelled, Paid
    is_active = Column(Boolean, default=True, nullable=False)
    auto_renew = Column(Boolean, default=True, nullable=False)
    
    # ========================================================================
    # Additional Information
    # ========================================================================
    notes = Column(Text, nullable=True)
    
    # ========================================================================
    # Relationships
    # ========================================================================
    business = relationship("Business", backref="subscriptions")
    user = relationship("User", backref="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionPayment(BaseModel):
    """
    Individual payment records for subscriptions.
    """
    
    __tablename__ = "subscription_payments"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    
    # ========================================================================
    # Payment Details
    # ========================================================================
    payment_id = Column(String(100), nullable=False, unique=True, index=True)
    transaction_id = Column(String(100), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    
    # ========================================================================
    # Payment Method and Gateway
    # ========================================================================
    payment_method = Column(String(100), nullable=False)  # Credit Card, PayPal, etc.
    gateway = Column(String(100), nullable=True)  # Stripe, PayPal, Razorpay, etc.
    gateway_response = Column(Text, nullable=True)  # JSON response from gateway
    
    # ========================================================================
    # Payment Status and Dates
    # ========================================================================
    status = Column(String(50), nullable=False, default="Pending")  # Pending, Success, Failed, Refunded
    payment_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    # ========================================================================
    # Additional Information
    # ========================================================================
    description = Column(String(500), nullable=True)
    failure_reason = Column(String(500), nullable=True)
    
    # ========================================================================
    # Relationships
    # ========================================================================
    subscription = relationship("Subscription", back_populates="payments")


class SubscriptionPlan(BaseModel):
    """
    Available subscription plans and pricing.
    """
    
    __tablename__ = "subscription_plans"
    
    # ========================================================================
    # Plan Details
    # ========================================================================
    name = Column(String(100), nullable=False, unique=True, index=True)  # Basic, Advanced, Enterprise
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # ========================================================================
    # Pricing
    # ========================================================================
    monthly_price = Column(Numeric(10, 2), nullable=False)
    yearly_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    
    # ========================================================================
    # Plan Features and Limits
    # ========================================================================
    max_employees = Column(Integer, nullable=False, default=0)  # 0 = unlimited
    max_businesses = Column(Integer, nullable=False, default=1)
    features = Column(Text, nullable=True)  # JSON string of features
    
    # ========================================================================
    # Plan Status
    # ========================================================================
    is_active = Column(Boolean, default=True, nullable=False)
    is_popular = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    
    # ========================================================================
    # Trial Information
    # ========================================================================
    trial_days = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<SubscriptionPlan(name='{self.name}', monthly_price={self.monthly_price})>"