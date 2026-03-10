"""
Employee Permissions Model
Stores specific permissions for attendance, travel, and rewards
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class EmployeePermissions(Base):
    """Employee permissions table for attendance, travel, and rewards permissions"""
    __tablename__ = "employee_permissions"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, unique=True)
    
    # Attendance & Punches Permissions
    selfie_punch = Column(Boolean, default=True)
    selfie_face_recognition = Column(Boolean, default=False)
    selfie_all_locations = Column(Boolean, default=False)
    remote_punch = Column(Boolean, default=True)
    missed_punch = Column(Boolean, default=True)
    missed_punch_limit = Column(Integer, default=0)
    web_punch = Column(Boolean, default=False)
    time_relaxation = Column(Boolean, default=False)
    scan_all_locations = Column(Boolean, default=True)
    ignore_time_strikes = Column(Boolean, default=False)
    auto_punch = Column(Boolean, default=False)
    
    # Travel & Visit Tracking Permissions
    visit_punch = Column(Boolean, default=False)
    visit_punch_approval = Column(Boolean, default=False)
    visit_punch_attendance = Column(Boolean, default=False)
    live_travel = Column(Boolean, default=False)
    live_travel_attendance = Column(Boolean, default=False)
    
    # Rewards and Recognition Permissions
    give_badges = Column(Boolean, default=False)
    give_rewards = Column(Boolean, default=False)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="permissions")