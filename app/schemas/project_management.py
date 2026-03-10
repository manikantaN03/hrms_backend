"""
Project Management Schemas
Pydantic models for Project Management API validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


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


# Base Schemas
class ProjectBase(BaseModel):
    """Base project schema"""
    name: str = Field(..., min_length=1, max_length=255)
    client: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: date
    end_date: date
    status: ProjectStatus = ProjectStatus.ACTIVE
    is_active: bool = True
    is_completed: bool = False

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating projects"""
    business_id: Optional[int] = None  # Will be set from current user


class ProjectUpdate(BaseModel):
    """Schema for updating projects"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    client: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    is_active: Optional[bool] = None
    is_completed: Optional[bool] = None
    completed_at: Optional[date] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: int
    business_id: int
    name: str
    client: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    completed_at: Optional[date] = None
    status: ProjectStatus
    is_active: bool
    is_completed: bool
    total_tasks: int
    completed_tasks: int
    total_members: int
    total_work_hours: Decimal
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    """Schema for project summary (list view)"""
    id: int
    name: str
    client: str
    start_date: date
    end_date: date
    status: ProjectStatus
    total_tasks: int
    completed_tasks: int
    total_members: int
    completion_percentage: float
    is_overdue: bool

    model_config = ConfigDict(from_attributes=True)


# Task Schemas
class TaskBase(BaseModel):
    """Base task schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: date
    end_date: date
    status: TaskStatus = TaskStatus.IN_PROGRESS
    projected_days: int = Field(0, ge=0, le=999)
    projected_hours: int = Field(0, ge=0, le=23)
    projected_minutes: int = Field(0, ge=0, le=59)
    is_completed: bool = False

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('projected_hours')
    def validate_projected_time(cls, v, values):
        # Ensure at least some projected time is provided
        days = values.get('projected_days', 0)
        minutes = values.get('projected_minutes', 0)
        if days == 0 and v == 0 and minutes == 0:
            raise ValueError('Projected time must be greater than 0')
        return v


class TaskCreate(TaskBase):
    """Schema for creating tasks"""
    project_id: int


class TaskUpdate(BaseModel):
    """Schema for updating tasks"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    projected_days: Optional[int] = Field(None, ge=0, le=999)
    projected_hours: Optional[int] = Field(None, ge=0, le=23)
    projected_minutes: Optional[int] = Field(None, ge=0, le=59)
    is_completed: Optional[bool] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    project_id: int
    project_name: str
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    status: TaskStatus
    is_completed: bool
    projected_days: int
    projected_hours: int
    projected_minutes: int
    total_projected_minutes: int
    time_spent_minutes: int
    date_range_display: Optional[str] = None
    projected_time_display: Optional[str] = None
    time_spent_display: Optional[str] = None
    available_working_days: int
    available_working_hours: Decimal
    has_time_mismatch: bool
    time_shortage_hours: Decimal
    time_buffer_hours: Decimal
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    """Schema for task summary (list view)"""
    id: int
    name: str
    project_name: str
    status: TaskStatus
    date_range_display: str
    projected_time_display: str
    time_spent_display: str
    has_time_mismatch: bool
    is_overdue: bool

    model_config = ConfigDict(from_attributes=True)


# Time Entry Schemas
class TimeEntryBase(BaseModel):
    """Base time entry schema"""
    date: date
    hours: int = Field(0, ge=0, le=23)
    minutes: int = Field(0, ge=0, le=59)
    description: Optional[str] = Field(None, max_length=500)

    @validator('minutes')
    def validate_time(cls, v, values):
        hours = values.get('hours', 0)
        if hours == 0 and v == 0:
            raise ValueError('Time entry must be greater than 0')
        return v


class TimeEntryCreate(TimeEntryBase):
    """Schema for creating time entries"""
    task_id: int


class TimeEntryUpdate(BaseModel):
    """Schema for updating time entries"""
    date: Optional[date] = None
    hours: Optional[int] = Field(None, ge=0, le=23)
    minutes: Optional[int] = Field(None, ge=0, le=59)
    description: Optional[str] = Field(None, max_length=500)


class TimeEntryResponse(BaseModel):
    """Schema for time entry response"""
    id: int
    task_id: int
    task_name: str
    project_name: str
    date: date
    hours: int
    minutes: int
    total_minutes: int
    duration_display: Optional[str] = None
    description: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Project Member Schemas
class ProjectMemberBase(BaseModel):
    """Base project member schema"""
    role: MemberRole = MemberRole.MEMBER
    joined_date: date = Field(default_factory=date.today)


class ProjectMemberCreate(ProjectMemberBase):
    """Schema for creating project members"""
    project_id: int
    user_id: Optional[int] = None
    employee_id: Optional[int] = None

    @validator('employee_id')
    def validate_member_reference(cls, v, values):
        user_id = values.get('user_id')
        if not user_id and not v:
            raise ValueError('Either user_id or employee_id must be provided')
        return v


class ProjectMemberUpdate(BaseModel):
    """Schema for updating project members"""
    role: Optional[MemberRole] = None
    is_active: Optional[bool] = None


class ProjectMemberResponse(BaseModel):
    """Schema for project member response"""
    id: int
    project_id: int
    user_id: Optional[int] = None
    employee_id: Optional[int] = None
    role: MemberRole
    joined_date: date
    is_active: bool
    member_name: str
    member_email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Activity Log Schemas
class ProjectActivityLogCreate(BaseModel):
    """Schema for creating project activity logs"""
    project_id: int
    message: str = Field(..., min_length=1, max_length=500)
    activity_type: str = Field("general", max_length=50)
    task_id: Optional[int] = None
    member_id: Optional[int] = None


class ProjectActivityLogResponse(BaseModel):
    """Schema for project activity log response"""
    id: int
    project_id: int
    message: str
    activity_type: str
    task_id: Optional[int] = None
    member_id: Optional[int] = None
    created_by: int
    creator_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Analytics Schemas
class ProjectAnalytics(BaseModel):
    """Schema for project analytics"""
    total_projects: int
    active_projects: int
    completed_projects: int
    on_hold_projects: int
    cancelled_projects: int
    completion_rate: float
    on_time_completion_rate: float
    overdue_projects: int
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float
    total_work_hours: Decimal
    average_project_duration: float


class TaskAnalytics(BaseModel):
    """Schema for task analytics"""
    total_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    on_hold_tasks: int
    running_tasks: int
    overdue_tasks: int
    completion_rate: float
    average_task_duration: float
    total_projected_hours: Decimal
    total_logged_hours: Decimal
    time_accuracy_rate: float


class TimeTrackingAnalytics(BaseModel):
    """Schema for time tracking analytics"""
    total_time_entries: int
    total_logged_hours: Decimal
    total_projected_hours: Decimal
    time_utilization_rate: float
    average_daily_hours: Decimal
    most_productive_day: str
    time_by_project: List[Dict[str, Any]]
    time_by_task_status: List[Dict[str, Any]]


# Filter Schemas
class ProjectFilters(BaseModel):
    """Schema for project filters"""
    status: Optional[List[ProjectStatus]] = None
    client: Optional[str] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    is_overdue: Optional[bool] = None
    created_by: Optional[int] = None


class TaskFilters(BaseModel):
    """Schema for task filters"""
    project_id: Optional[int] = None
    status: Optional[List[TaskStatus]] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    is_overdue: Optional[bool] = None
    has_time_mismatch: Optional[bool] = None
    created_by: Optional[int] = None


class TimeEntryFilters(BaseModel):
    """Schema for time entry filters"""
    task_id: Optional[int] = None
    project_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    created_by: Optional[int] = None


# Validation Response Schema
class TimeValidationResponse(BaseModel):
    """Schema for time validation response"""
    is_valid: bool
    available_working_days: int
    available_working_hours: Decimal
    projected_hours: Decimal
    has_mismatch: bool
    shortage_hours: Decimal
    buffer_hours: Decimal
    warning_message: Optional[str] = None
    error_message: Optional[str] = None