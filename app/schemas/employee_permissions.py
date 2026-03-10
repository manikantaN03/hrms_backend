"""
Employee Permissions Pydantic Schemas
Validation schemas for employee permissions API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class EmployeePermissionsBase(BaseModel):
    """Base schema for employee permissions"""
    
    # Attendance & Punches Permissions
    selfie_punch: bool = Field(default=True, description="Allow selfie punch")
    selfie_face_recognition: bool = Field(default=False, description="Require face recognition for selfie punch")
    selfie_all_locations: bool = Field(default=False, description="Allow selfie punch from all locations")
    remote_punch: bool = Field(default=True, description="Allow remote punch")
    missed_punch: bool = Field(default=True, description="Allow missed punch requests")
    missed_punch_limit: int = Field(default=0, ge=0, le=31, description="Monthly missed punch limit")
    web_punch: bool = Field(default=False, description="Allow web/chat punch")
    time_relaxation: bool = Field(default=False, description="Allow time relaxation")
    scan_all_locations: bool = Field(default=True, description="Allow QR scan at all locations")
    ignore_time_strikes: bool = Field(default=False, description="Ignore time strikes for attendance")
    auto_punch: bool = Field(default=False, description="Enable auto punch in/out")
    
    # Travel & Visit Tracking Permissions
    visit_punch: bool = Field(default=False, description="Allow visit punch")
    visit_punch_approval: bool = Field(default=False, description="Require approval for visit punch")
    visit_punch_attendance: bool = Field(default=False, description="Mark attendance with visit punch")
    live_travel: bool = Field(default=False, description="Allow live travel tracking")
    live_travel_attendance: bool = Field(default=False, description="Mark attendance with live travel")
    
    # Rewards and Recognition Permissions
    give_badges: bool = Field(default=False, description="Allow giving badges to others")
    give_rewards: bool = Field(default=False, description="Allow giving rewards to others")


class EmployeePermissionsCreate(EmployeePermissionsBase):
    """Schema for creating employee permissions"""
    employee_id: int = Field(..., gt=0, description="Employee ID")
    
    @validator('missed_punch_limit')
    def validate_missed_punch_limit(cls, v):
        if v < 0 or v > 31:
            raise ValueError('Missed punch limit must be between 0 and 31')
        return v


class EmployeePermissionsUpdate(EmployeePermissionsBase):
    """Schema for updating employee permissions"""
    
    @validator('missed_punch_limit')
    def validate_missed_punch_limit(cls, v):
        if v < 0 or v > 31:
            raise ValueError('Missed punch limit must be between 0 and 31')
        return v


class EmployeePermissionsResponse(EmployeePermissionsBase):
    """Schema for employee permissions response"""
    id: int
    employee_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmployeePermissionsDisplay(BaseModel):
    """Schema for displaying employee permissions in frontend format"""
    
    # Employee info
    id: int = Field(..., description="Employee ID")
    name: str = Field(..., description="Employee full name")
    code: str = Field(..., description="Employee code")
    
    # Permissions in frontend format
    permissions: dict = Field(..., description="Permissions data in frontend format")


class EmployeePermissionsFrontendUpdate(BaseModel):
    """Schema for frontend permissions update format"""
    
    # Attendance & Punches (frontend field names)
    chkSelfiePunch: bool = Field(default=True)
    chkSelfieFaceMatch: bool = Field(default=False)
    chkSelfieAllLocations: bool = Field(default=False)
    chkRemotePunch: bool = Field(default=True)
    chkMissedPunch: bool = Field(default=True)
    txtMissedPunchCount: str = Field(default="0", pattern=r'^\d{1,2}$')
    chkWebPunch: bool = Field(default=False)
    chkTimeRelaxation: bool = Field(default=False)
    chkQrAllLocations: bool = Field(default=True)
    chkDisableStrikes: bool = Field(default=False)
    chkAutoPunch: bool = Field(default=False)
    
    # Travel & Visit Tracking (frontend field names)
    chkTravelPunch: bool = Field(default=False)
    chkTravelPunchApproval: bool = Field(default=False)
    chkTravelPunchAttendance: bool = Field(default=False)
    chkLiveTravel: bool = Field(default=False)
    chkLiveTravelAttendance: bool = Field(default=False)
    
    # Rewards and Recognition (frontend field names)
    chkGiveBadges: bool = Field(default=False)
    chkGiveRewards: bool = Field(default=False)
    
    @validator('txtMissedPunchCount')
    def validate_missed_punch_count(cls, v):
        # Handle None or empty values
        if v is None:
            return "0"
        
        # Convert to string if not already
        v = str(v).strip()
        
        # Allow empty string and convert to "0"
        if not v or v == "":
            return "0"
        
        # Check if it's a valid number
        try:
            count = int(v)
        except ValueError:
            raise ValueError('Missed punch count must be a valid number')
        
        # Validate range
        if count < 0:
            raise ValueError('Missed punch count cannot be negative')
        if count > 31:
            raise ValueError('Missed punch count cannot exceed 31 (days in a month)')
        
        return str(count)


class EmployeePermissionsUpdateResponse(BaseModel):
    """Schema for permissions update response"""
    success: bool
    message: str
    employee: dict = Field(..., description="Employee basic info")
    permissions: dict = Field(..., description="Updated permissions in frontend format")