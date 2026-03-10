"""
TODO/Task Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.models.base import Base


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCategory(str, Enum):
    """Task categories"""
    PERSONAL = "personal"
    WORK = "work"
    MEETING = "meeting"
    DEADLINE = "deadline"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class TodoTask(Base):
    """Tasks/TODO model"""
    __tablename__ = "todo_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    
    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(TaskCategory, native_enum=False), nullable=False, default=TaskCategory.WORK)
    
    # Status and priority
    status = Column(SQLEnum(TaskStatus, native_enum=False), nullable=False, default=TaskStatus.TODO)
    priority = Column(SQLEnum(TaskPriority, native_enum=False), nullable=False, default=TaskPriority.MEDIUM)
    
    # Dates
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    is_pinned = Column(Boolean, default=False)
    reminder_minutes = Column(Integer, nullable=True)  # Minutes before due date to remind
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    business = relationship("Business")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
