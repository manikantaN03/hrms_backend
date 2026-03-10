"""
Employee Additional Information Model
Stores customizable additional fields for employees
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class EmployeeAdditionalInfo(Base):
    """Employee additional information table for custom fields"""
    __tablename__ = "employee_additional_info"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # 10 customizable fields as shown in the UI
    other_info_1 = Column(Text)
    other_info_2 = Column(Text)
    other_info_3 = Column(Text)
    other_info_4 = Column(Text)
    other_info_5 = Column(Text)
    other_info_6 = Column(Text)
    other_info_7 = Column(Text)
    other_info_8 = Column(Text)
    other_info_9 = Column(Text)
    other_info_10 = Column(Text)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="additional_info")