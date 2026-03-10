"""
Asset Models
Employee asset management data models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class AssetType(str, enum.Enum):
    LAPTOP = "laptop"
    DESKTOP = "desktop"
    MONITOR = "monitor"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    MOBILE = "mobile"
    TABLET = "tablet"
    PRINTER = "printer"
    HEADSET = "headset"
    WEBCAM = "webcam"
    CHAIR = "chair"
    DESK = "desk"
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"
    MAINTENANCE = "maintenance"
    LOST = "lost"
    DAMAGED = "damaged"


class AssetCondition(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Asset(Base):
    """Asset table for employee asset management"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Asset Information
    asset_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    brand = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    
    # Asset Details
    description = Column(Text)
    specifications = Column(Text)  # JSON string for technical specs
    purchase_date = Column(Date)
    purchase_cost = Column(Numeric(15, 2))
    estimated_value = Column(Numeric(15, 2))
    
    # Warranty Information
    warranty_start_date = Column(Date)
    warranty_end_date = Column(Date)
    warranty_provider = Column(String(200))
    
    # Status and Condition
    status = Column(Enum(AssetStatus), default=AssetStatus.ACTIVE)
    condition = Column(Enum(AssetCondition), default=AssetCondition.GOOD)
    
    # Location and Assignment
    current_location = Column(String(200))
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    assigned_date = Column(Date)
    return_date = Column(Date)
    
    # Business Association
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    business = relationship("Business")
    assigned_employee = relationship("Employee", back_populates="assets")
    
    @property
    def is_warranty_expired(self):
        """Check if warranty has expired"""
        if not self.warranty_end_date:
            return False
        from datetime import date
        return self.warranty_end_date < date.today()
    
    @property
    def warranty_status(self):
        """Get warranty status"""
        if not self.warranty_end_date:
            return "No Warranty"
        
        from datetime import date, timedelta
        today = date.today()
        
        if self.warranty_end_date < today:
            return "Expired"
        elif self.warranty_end_date <= today + timedelta(days=30):
            return "Expiring Soon"
        else:
            return "Active"


class AssetHistory(Base):
    """Asset assignment history"""
    __tablename__ = "asset_history"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    
    # Assignment Details
    assigned_date = Column(Date, nullable=False)
    return_date = Column(Date)
    assignment_reason = Column(String(500))
    return_reason = Column(String(500))
    
    # Condition at assignment/return
    condition_at_assignment = Column(Enum(AssetCondition))
    condition_at_return = Column(Enum(AssetCondition))
    
    # Notes
    assignment_notes = Column(Text)
    return_notes = Column(Text)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    asset = relationship("Asset")
    employee = relationship("Employee")