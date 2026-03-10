from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class LWFSettings(BaseModel):
    """LWF Settings - Main configuration"""
    
    __tablename__ = "lwf_settings"
    
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, unique=True, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    business = relationship("Business", back_populates="lwf_settings")
    rates = relationship("LWFRate", back_populates="lwf_settings", cascade="all, delete-orphan")
 
 
class LWFRate(BaseModel):
    """LWF Rate - Labour Welfare Fund rates by state"""

    __tablename__ = "lwf_rates"
 
    state = Column(String(100), nullable=False)

    effective_from = Column(Date, nullable=False)
 
    employee_contribution = Column(Numeric(10, 2), nullable=False)

    employer_contribution = Column(Numeric(10, 2), nullable=False)
    
    # LWF Settings foreign key
    lwf_settings_id = Column(Integer, ForeignKey("lwf_settings.id"), nullable=False, index=True)
    
    # Business foreign key — links rates to a Business (kept for backward compatibility)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # Relationships
    lwf_settings = relationship("LWFSettings", back_populates="rates")
    business = relationship("Business", back_populates="lwf_rates")
 
    frequency = Column(String(20), default="Monthly")
 