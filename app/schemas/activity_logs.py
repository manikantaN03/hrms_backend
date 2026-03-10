"""
Activity Logs Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ActivityTypeEnum(str, Enum):
    """Activity type enumeration"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    APPROVE = "approve"
    REJECT = "reject"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    LOGIN = "login"
    LOGOUT = "logout"

class ActivityModuleEnum(str, Enum):
    """Activity module enumeration"""
    EMPLOYEE_MANAGEMENT = "Employee Management"
    ATTENDANCE = "Attendance"
    LEAVE_MANAGEMENT = "Leave Management"
    PAYROLL = "Payroll"
    DOCUMENT_MANAGEMENT = "Document Management"
    HR_POLICIES = "HR Policies"
    ONBOARDING = "Onboarding"
    ASSET_MANAGEMENT = "Asset Management"
    USER_MANAGEMENT = "User Management"
    SYSTEM = "System"

class ActivityLogBase(BaseModel):
    """Base activity log schema"""
    action: str = Field(..., min_length=1, max_length=200, description="Action performed")
    module: ActivityModuleEnum = Field(..., description="Module where action was performed")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the action")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")

    @validator('action')
    def validate_action(cls, v):
        if not v or not v.strip():
            raise ValueError('Action cannot be empty')
        return v.strip()

class ActivityLogCreate(ActivityLogBase):
    """Schema for creating activity log"""
    user_id: int = Field(..., gt=0, description="ID of the user who performed the action")
    employee_id: Optional[int] = Field(None, gt=0, description="ID of the employee affected by the action")

class ActivityLogUpdate(BaseModel):
    """Schema for updating activity log"""
    action: Optional[str] = Field(None, min_length=1, max_length=200)
    module: Optional[ActivityModuleEnum] = None
    details: Optional[Dict[str, Any]] = None

class ActivityLogResponse(ActivityLogBase):
    """Schema for activity log response"""
    id: int = Field(..., description="Activity log ID")
    user_id: int = Field(..., description="User ID who performed the action")
    employee_id: Optional[int] = Field(None, description="Employee ID affected by the action")
    created_at: datetime = Field(..., description="Timestamp when the activity was logged")
    
    # Related data
    user_name: Optional[str] = Field(None, description="Name of the user who performed the action")
    employee_name: Optional[str] = Field(None, description="Name of the employee affected")
    
    class Config:
        from_attributes = True

class ActivityLogListResponse(BaseModel):
    """Schema for activity log list response"""
    logs: List[ActivityLogResponse] = Field(..., description="List of activity logs")
    total: int = Field(..., ge=0, description="Total number of logs")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Number of logs per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

class EmployeeActivityResponse(BaseModel):
    """Schema for employee activity response"""
    id: int = Field(..., description="Employee ID")
    name: str = Field(..., description="Employee name")
    code: str = Field(..., description="Employee code")
    
    class ActivityData(BaseModel):
        system_logs: List[Dict[str, Any]] = Field(default_factory=list, description="System activity logs")
        database_logs: List[Dict[str, Any]] = Field(default_factory=list, description="Database activity logs")
        recent_activities: List[Dict[str, Any]] = Field(default_factory=list, description="Recent activities")
        
        class AttendanceHistory(BaseModel):
            total_days_worked: int = Field(0, ge=0)
            total_hours_worked: int = Field(0, ge=0)
            average_hours_per_day: float = Field(0.0, ge=0.0)
            late_arrivals: int = Field(0, ge=0)
            early_departures: int = Field(0, ge=0)
        
        class LeaveHistory(BaseModel):
            total_leaves_taken: int = Field(0, ge=0)
            sick_leaves: int = Field(0, ge=0)
            casual_leaves: int = Field(0, ge=0)
            annual_leaves: int = Field(0, ge=0)
            pending_applications: int = Field(0, ge=0)
        
        class PerformanceMetrics(BaseModel):
            tasks_completed: int = Field(0, ge=0)
            projects_involved: int = Field(0, ge=0)
            meetings_attended: int = Field(0, ge=0)
            training_completed: int = Field(0, ge=0)
        
        class SystemActivity(BaseModel):
            last_login: Optional[str] = None
            total_logins: int = Field(0, ge=0)
            profile_updates: int = Field(0, ge=0)
            document_uploads: int = Field(0, ge=0)
        
        attendance_history: AttendanceHistory = Field(default_factory=AttendanceHistory)
        leave_history: LeaveHistory = Field(default_factory=LeaveHistory)
        performance_metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
        system_activity: SystemActivity = Field(default_factory=SystemActivity)
    
    activity: ActivityData = Field(default_factory=ActivityData, description="Activity data")

class ActivityLogFilterRequest(BaseModel):
    """Schema for filtering activity logs"""
    employee_id: Optional[int] = Field(None, gt=0, description="Filter by employee ID")
    user_id: Optional[int] = Field(None, gt=0, description="Filter by user ID")
    module: Optional[ActivityModuleEnum] = Field(None, description="Filter by module")
    action_contains: Optional[str] = Field(None, min_length=1, max_length=100, description="Filter by action containing text")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Number of logs per page")

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to must be greater than or equal to date_from')
        return v