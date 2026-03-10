"""
Business Information Model
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class BusinessInformation(Base):
    __tablename__ = "business_information"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True, unique=True)
    
    # Bank Details
    bank_name = Column(String(255), nullable=True)
    bank_branch = Column(String(255), nullable=True)
    bank_ifsc = Column(String(50), nullable=True)
    bank_account = Column(String(100), nullable=True)
    
    # Statutory Information
    pan = Column(String(50), nullable=True)
    tan = Column(String(50), nullable=True)
    gstin = Column(String(50), nullable=True)
    esi = Column(String(100), nullable=True)
    pf = Column(String(100), nullable=True)
    shop_act = Column(String(100), nullable=True)
    labour_act = Column(String(100), nullable=True)
    
    # Employee Additional Info (stored as JSON array)
    employee_info = Column(JSON, default=[])  # List of 10 strings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    business = relationship("Business", back_populates="business_information")
    
    def __repr__(self):
        return f"<BusinessInformation(id={self.id}, business_id={self.business_id})>"