from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class LeavePolicy(Base):
    __tablename__ = "leave_policies"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    leave_type = Column(String(100), nullable=False)
    policy_name = Column(String(200), nullable=False)
    description = Column(String(500))

    # Grant Settings
    grant_enabled = Column(Boolean, default=True)
    grant_condition = Column(Integer, default=0)  # Minimum presents required
    monthly_grant_leaves = Column(JSON, default=list)  # Array of 12 months
    reset_negative_balance = Column(Boolean, default=False)

    # Lapse Settings
    lapse_enabled = Column(Boolean, default=False)
    monthly_lapse_limits = Column(JSON, default=list)  # Array of 12 months

    # Other Options
    do_not_apply_during_probation = Column(Boolean, default=False)
    do_not_apply_after_probation = Column(Boolean, default=False)
    auto_apply = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # relationship to Business
    business = relationship("Business", back_populates="leave_policies")
