"""
Remote Session Model
Model for managing remote support sessions
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from .base import BaseModel


class RemoteSessionStatus(PyEnum):
    """Remote session status enumeration"""
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RemoteSessionType(PyEnum):
    """Remote session type enumeration"""
    TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT"
    SOFTWARE_INSTALLATION = "SOFTWARE_INSTALLATION"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    TRAINING = "TRAINING"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    OTHER = "OTHER"


class RemoteSession(BaseModel):
    """Remote session model for IT support"""
    __tablename__ = "remote_sessions"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    support_agent_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    
    # Session Details
    session_type = Column(Enum(RemoteSessionType, name='remotesessiontype', create_type=False), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(RemoteSessionStatus, name='remotesessionstatus', create_type=False), default=RemoteSessionStatus.PENDING, nullable=False)
    
    # Scheduling
    requested_date = Column(DateTime, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Technical Details
    computer_name = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    operating_system = Column(String(100), nullable=True)
    issue_category = Column(String(100), nullable=True)
    
    # Session Notes
    agent_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Session Rating
    rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback = Column(Text, nullable=True)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", foreign_keys=[employee_id], backref="remote_sessions_requested")
    support_agent = relationship("Employee", foreign_keys=[support_agent_id], backref="remote_sessions_handled")
