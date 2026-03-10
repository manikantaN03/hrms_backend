"""
Week Off Policy Model
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class WeekOffPolicy(Base):
    __tablename__ = "weekoff_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # Store as JSON arrays
    general_week_offs = Column(JSON, default=[])  # ["Monday", "Sunday"]
    alternating_week_offs = Column(JSON, default=[])  # [[false, true, ...], ...]
    
    weekoffs_payable = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    business = relationship("Business", back_populates="weekoff_policies")
    
    def __repr__(self):
        return f"<WeekOffPolicy(id={self.id}, title='{self.title}', business_id={self.business_id})>"