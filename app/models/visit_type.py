"""
Visit Type Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class VisitType(Base):
    __tablename__ = "visit_types"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    business = relationship("Business", back_populates="visit_types")
    
    def __repr__(self):
        return f"<VisitType(id={self.id}, name='{self.name}', business_id={self.business_id})>"