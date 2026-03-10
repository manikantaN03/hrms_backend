"""
ESI Settings Model
Employee State Insurance configuration
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ESISettings(BaseModel):
    """ESI Settings - Main configuration"""
    
    __tablename__ = "esi_settings"
    
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    calculation_base = Column(String(50), default="Gross Salary")  # Gross Salary, Earned Salary
    
    # Relationships
    business = relationship("Business", back_populates="esi_settings")
    component_mappings = relationship("ESIComponentMapping", back_populates="esi_settings", cascade="all, delete-orphan")
    rate_changes = relationship("ESIRateChange", back_populates="esi_settings", cascade="all, delete-orphan")


class ESIComponentMapping(BaseModel):
    """ESI Component Mapping - Which salary components are included"""
    
    __tablename__ = "esi_component_mappings"
    
    esi_settings_id = Column(Integer, ForeignKey("esi_settings.id"), nullable=False, index=True)
    component_name = Column(String(100), nullable=False)
    component_code = Column(String(50), nullable=False)
    component_type = Column(String(50), nullable=False)  # Paid Days, Variable, System
    is_selected = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    esi_settings = relationship("ESISettings", back_populates="component_mappings")


class ESIRateChange(BaseModel):
    """ESI Rate Changes - Historical rate configurations"""
    
    __tablename__ = "esi_rate_changes"
    
    esi_settings_id = Column(Integer, ForeignKey("esi_settings.id"), nullable=False, index=True)
    status = Column(String(20), default="Enabled", nullable=False)  # Enabled, Disabled
    effective_from = Column(Date, nullable=False)
    employee_rate = Column(Float, nullable=False)  # e.g., 0.75
    employer_rate = Column(Float, nullable=False)  # e.g., 3.25
    wage_limit = Column(Float, nullable=False)  # e.g., 21000
    
    # Relationships
    esi_settings = relationship("ESISettings", back_populates="rate_changes")
