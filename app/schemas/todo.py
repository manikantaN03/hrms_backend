"""
TODO/Task Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


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


# Base schemas
class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: TaskCategory = TaskCategory.WORK
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    assigned_to_id: Optional[int] = None
    tags: Optional[str] = None
    is_pinned: bool = False
    reminder_minutes: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating tasks"""
    business_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for updating tasks"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    assigned_to_id: Optional[int] = None
    tags: Optional[str] = None
    is_pinned: Optional[bool] = None
    reminder_minutes: Optional[int] = None


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    user_id: int
    business_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: TaskCategory
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    tags: Optional[str] = None
    is_pinned: bool
    reminder_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)


class TaskStats(BaseModel):
    """Task statistics"""
    total_tasks: int
    todo_count: int
    in_progress_count: int
    completed_count: int
    overdue_count: int
    high_priority_count: int
    completion_rate: float


class TaskFilters(BaseModel):
    """Task filters"""
    status: Optional[List[TaskStatus]] = None
    priority: Optional[List[TaskPriority]] = None
    category: Optional[List[TaskCategory]] = None
    assigned_to_id: Optional[int] = None
    is_pinned: Optional[bool] = None
    overdue_only: bool = False
    search: Optional[str] = None
