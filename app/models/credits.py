"""
Credit System Models
User credit management for verification services
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
from datetime import datetime


class UserCredits(Base):
    """User credit balance tracking"""
    __tablename__ = "user_credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Credit balance
    credits = Column(Integer, default=0, nullable=False)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    business = relationship("Business")
    transactions = relationship("CreditTransaction", back_populates="user_credits")


class CreditTransaction(Base):
    """Credit transaction history"""
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_credits_id = Column(Integer, ForeignKey("user_credits.id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # purchase, deduction, refund
    amount = Column(Integer, nullable=False)  # Positive for credit, negative for debit
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Transaction metadata
    description = Column(String(500))
    reference_id = Column(String(255))  # External transaction ID
    reference_type = Column(String(100))  # bulk_onboarding, manual, etc.
    
    # Payment details (for purchases)
    payment_method = Column(String(100))
    payment_reference = Column(String(255))
    payment_amount = Column(Numeric(10, 2))  # Actual money paid
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user_credits = relationship("UserCredits", back_populates="transactions")
    creator = relationship("User")


class CreditPricing(Base):
    """Credit pricing for different verification services"""
    __tablename__ = "credit_pricing"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Service details
    service_name = Column(String(100), nullable=False)  # mobile, pan, bank, aadhaar
    service_display_name = Column(String(255), nullable=False)
    credits_required = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_free = Column(Boolean, default=False)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    business = relationship("Business")
    creator = relationship("User")