"""
Shift Policy Model
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class ShiftPolicy(Base):
    __tablename__ = "shift_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    default_shift_id = Column(Integer, ForeignKey('work_shifts.id'), nullable=True)
    
    # Store weekly rotating shifts as JSON: {"Monday": shift_id, "Tuesday": shift_id, ...}
    weekly_shifts = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="shift_policies")
    default_shift = relationship("WorkShift", back_populates="default_for_policies", foreign_keys=[default_shift_id])
    
    def __repr__(self):
        return f"<ShiftPolicy(id={self.id}, title='{self.title}', business_id={self.business_id})>"
