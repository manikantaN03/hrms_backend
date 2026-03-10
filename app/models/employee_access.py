"""
Employee Access Model
Stores employee login and access permissions
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class EmployeeAccess(Base):
    """Employee access table for login and system access permissions"""
    __tablename__ = "employee_access"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, unique=True)
    
    # Mobile Login Options
    pin_never_expires = Column(Boolean, default=False)
    multi_device_logins = Column(Boolean, default=False)
    mobile_access_enabled = Column(Boolean, default=True)
    
    # Web Login Options
    web_access_enabled = Column(Boolean, default=True)
    
    # Org Wall Access
    wall_admin = Column(Boolean, default=False)
    wall_posting = Column(Boolean, default=True)
    wall_commenting = Column(Boolean, default=True)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="access_settings")


class EmployeeLoginSession(Base):
    """Employee login sessions table"""
    __tablename__ = "employee_login_sessions"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Session Details
    session_token = Column(String(255), nullable=False, unique=True)
    device_name = Column(String(255))
    device_type = Column(String(50))  # mobile, web, tablet
    os_version = Column(String(100))
    app_version = Column(String(50))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Session Status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    logout_time = Column(DateTime(timezone=True))
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee")