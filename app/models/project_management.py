"""
Project Management Models
Database models for Project Management System (TODO Module)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from app.models.base import Base


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task status enumeration"""
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    RUNNING = "Running"


class MemberRole(str, Enum):
    """Project member role enumeration"""
    MANAGER = "manager"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    ANALYST = "analyst"
    MEMBER = "member"


class Project(Base):
    """Project model for project management"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    
    # Basic project information
    name = Column(String(255), nullable=False, index=True)
    client = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Project dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    completed_at = Column(Date, nullable=True)
    
    # Project status and flags
    status = Column(SQLEnum(ProjectStatus, native_enum=False), nullable=False, default=ProjectStatus.ACTIVE)
    is_active = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Project metrics (calculated fields)
    total_tasks = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)
    total_members = Column(Integer, default=0, nullable=False)
    total_work_hours = Column(Numeric(10, 2), default=0.0, nullable=False)  # Total logged hours
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="projects")
    creator = relationship("User", foreign_keys=[created_by])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    activity_logs = relationship("ProjectActivityLog", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', client='{self.client}')>"


class Task(Base):
    """Task model for project tasks"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Basic task information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Task dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Task status
    status = Column(SQLEnum(TaskStatus, native_enum=False), nullable=False, default=TaskStatus.IN_PROGRESS)
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Projected time (in minutes for precision)
    projected_days = Column(Integer, default=0, nullable=False)
    projected_hours = Column(Integer, default=0, nullable=False)
    projected_minutes = Column(Integer, default=0, nullable=False)
    total_projected_minutes = Column(Integer, default=0, nullable=False)  # Calculated field
    
    # Time spent (in minutes for precision)
    time_spent_minutes = Column(Integer, default=0, nullable=False)  # Total logged time
    
    # Calculated fields
    date_range_display = Column(String(100), nullable=True)  # Formatted date range for display
    projected_time_display = Column(String(50), nullable=True)  # Formatted projected time (e.g., "05d 08h 30m")
    time_spent_display = Column(String(50), nullable=True)  # Formatted time spent (e.g., "03h 45m")
    
    # Working days calculation
    available_working_days = Column(Integer, default=0, nullable=False)
    available_working_hours = Column(Numeric(10, 2), default=0.0, nullable=False)
    
    # Time validation flags
    has_time_mismatch = Column(Boolean, default=False, nullable=False)
    time_shortage_hours = Column(Numeric(10, 2), default=0.0, nullable=False)
    time_buffer_hours = Column(Numeric(10, 2), default=0.0, nullable=False)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    creator = relationship("User", foreign_keys=[created_by])
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}', project_id={self.project_id})>"


class TimeEntry(Base):
    """Time entry model for time tracking"""
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    
    # Time entry details
    date = Column(Date, nullable=False, index=True)
    hours = Column(Integer, default=0, nullable=False)
    minutes = Column(Integer, default=0, nullable=False)
    total_minutes = Column(Integer, default=0, nullable=False)  # Calculated field
    description = Column(Text, nullable=True)
    
    # Display format
    duration_display = Column(String(20), nullable=True)  # Formatted duration (e.g., "03h 45m")
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="time_entries")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, task_id={self.task_id}, date={self.date})>"


class ProjectMember(Base):
    """Project member model for team management"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    
    # Member details
    role = Column(SQLEnum(MemberRole, native_enum=False), nullable=False, default=MemberRole.MEMBER)
    joined_date = Column(Date, nullable=False, default=func.current_date())
    
    # Member status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id})>"


class ProjectActivityLog(Base):
    """Project activity log model for tracking project activities"""
    __tablename__ = "project_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Activity details
    message = Column(String(500), nullable=False)
    activity_type = Column(String(50), nullable=False, default="general")  # general, task, member, status
    
    # Reference IDs for specific activities
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    member_id = Column(Integer, ForeignKey("project_members.id"), nullable=True)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="activity_logs")
    task = relationship("Task", foreign_keys=[task_id])
    member = relationship("ProjectMember", foreign_keys=[member_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ProjectActivityLog(id={self.id}, project_id={self.project_id}, message='{self.message}')>"