"""
Employee Relative Model
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class EmployeeRelative(Base):
    """Employee relatives table"""
    __tablename__ = "employee_relatives"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Relative Information
    relation = Column(String(100), nullable=False)  # Father, Mother, Spouse, Child, etc.
    relative_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date)
    dependent = Column(String(10), default="No")  # Yes or No
    phone = Column(String(20))
    email = Column(String(255))
    notes = Column(String(500))
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="relatives")