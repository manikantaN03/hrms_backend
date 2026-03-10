from sqlalchemy import Column, Integer, String, DECIMAL, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class LeaveBalance(Base):
    """Employee leave balance tracking"""
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False, index=True)
    
    # Balance tracking
    opening_balance = Column(DECIMAL(5, 2), default=0, nullable=False)
    activity_balance = Column(DECIMAL(5, 2), default=0, nullable=False)  # Used/Taken leaves
    correction_balance = Column(DECIMAL(5, 2), default=0, nullable=False)  # Manual corrections
    closing_balance = Column(DECIMAL(5, 2), default=0, nullable=False)
    
    # Period tracking
    balance_year = Column(Integer, nullable=False)
    balance_month = Column(Integer, nullable=False)
    balance_date = Column(Date, nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee")
    leave_type = relationship("LeaveType")


class LeaveCorrection(Base):
    """Leave correction history tracking"""
    __tablename__ = "leave_corrections"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_balance_id = Column(Integer, ForeignKey("leave_balances.id"), nullable=False, index=True)
    
    # Correction details
    correction_amount = Column(DECIMAL(5, 2), nullable=False)
    previous_balance = Column(DECIMAL(5, 2), nullable=False)
    new_balance = Column(DECIMAL(5, 2), nullable=False)
    correction_reason = Column(String(500))
    
    # Period
    correction_year = Column(Integer, nullable=False)
    correction_month = Column(Integer, nullable=False)
    correction_date = Column(Date, nullable=False)
    
    # Audit
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee")
    leave_balance = relationship("LeaveBalance")
    creator = relationship("User", foreign_keys=[created_by])