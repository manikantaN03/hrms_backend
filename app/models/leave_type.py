from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    alias = Column(String, nullable=False)
    color = Column(String, nullable=False, default="#e7f3ff")
    paid = Column(Boolean, default=True)
    track_balance = Column(Boolean, default=True)
    probation = Column(String, nullable=False, default="Allow")
    allow_requests = Column(Boolean, default=True)
    allow_future_requests = Column(Boolean, default=True)
    advance_leaves = Column(Integer, default=0)
    past_days = Column(Integer, default=0)
    monthly_limit = Column(Integer, default=0)
    
    # relationship to Business
    business = relationship("Business", back_populates="leave_types")
