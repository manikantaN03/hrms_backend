"""
EPF Settings Model
Employee Provident Fund configuration
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class EPFSettings(BaseModel):
    """EPF Settings - Main configuration"""
    
    __tablename__ = "epf_settings"
    
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    calculation_base = Column(String(50), default="Gross Salary")  # Gross Salary, Earned Salary
    
    # Relationships
    business = relationship("Business", back_populates="epf_settings")
    component_mappings = relationship("EPFComponentMapping", back_populates="epf_settings", cascade="all, delete-orphan")
    rate_changes = relationship("EPFRateChange", back_populates="epf_settings", cascade="all, delete-orphan")


class EPFComponentMapping(BaseModel):
    """EPF Component Mapping - Which salary components are included"""
    
    __tablename__ = "epf_component_mappings"
    
    epf_settings_id = Column(Integer, ForeignKey("epf_settings.id"), nullable=False, index=True)
    component_name = Column(String(100), nullable=False)
    component_code = Column(String(50), nullable=False)
    component_type = Column(String(50), nullable=False)  # Paid Days, Variable, System
    is_selected = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    epf_settings = relationship("EPFSettings", back_populates="component_mappings")


class EPFRateChange(BaseModel):
    """EPF Rate Changes - Historical rate configurations"""
    
    __tablename__ = "epf_rate_changes"
    
    epf_settings_id = Column(Integer, ForeignKey("epf_settings.id"), nullable=False, index=True)
    status = Column(String(20), default="Enabled", nullable=False)  # Enabled, Disabled
    effective_from = Column(Date, nullable=False)
    
    # Non-Senior rates
    emp_pf_rate_non_senior = Column(Float, nullable=False, default=12.0)
    employer_pf_rate_non_senior = Column(Float, nullable=False, default=12.0)
    pension_rate_non_senior = Column(Float, nullable=False, default=8.33)
    
    # Senior rates
    emp_pf_rate_senior = Column(Float, nullable=False, default=12.0)
    employer_pf_rate_senior = Column(Float, nullable=False, default=12.0)
    pension_rate_senior = Column(Float, nullable=False, default=0.0)
    
    # Other settings
    edli_rate = Column(Float, nullable=False, default=0.5)
    wage_ceiling = Column(Float, nullable=False, default=15000.0)
    senior_age = Column(Integer, nullable=False, default=58)
    
    # Relationships
    epf_settings = relationship("EPFSettings", back_populates="rate_changes")
