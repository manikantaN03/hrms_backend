"""
Employee Access Pydantic Schemas
Validation schemas for employee access API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class EmployeeAccessBase(BaseModel):
    """Base schema for employee access settings"""
    
    # Mobile Login Options
    pin_never_expires: bool = Field(default=False, description="PIN never expires after logout")
    multi_device_logins: bool = Field(default=False, description="Allow multiple simultaneous logins")
    mobile_access_enabled: bool = Field(default=True, description="Enable mobile app access")
    
    # Web Login Options
    web_access_enabled: bool = Field(default=True, description="Enable web portal access")
    
    # Org Wall Access
    wall_admin: bool = Field(default=False, description="Make user wall admin")
    wall_posting: bool = Field(default=True, description="Allow wall posting")
    wall_commenting: bool = Field(default=True, description="Allow wall commenting")


class EmployeeAccessCreate(EmployeeAccessBase):
    """Schema for creating employee access settings"""
    employee_id: int = Field(..., gt=0, description="Employee ID")


class EmployeeAccessUpdate(EmployeeAccessBase):
    """Schema for updating employee access settings"""
    pass


class EmployeeAccessFrontendUpdate(BaseModel):
    """Schema for frontend access settings update format"""
    
    # Frontend field names matching the component
    pinNeverExpires: bool = Field(default=False)
    multiDeviceLogins: bool = Field(default=False)
    mobileAccessEnabled: bool = Field(default=True)
    webAccessEnabled: bool = Field(default=True)
    wallAdmin: bool = Field(default=False)
    wallPosting: bool = Field(default=True)
    wallCommenting: bool = Field(default=True)


class EmployeeLoginSessionBase(BaseModel):
    """Base schema for employee login sessions"""
    
    session_token: str = Field(..., min_length=1, max_length=255, description="Session token")
    device_name: Optional[str] = Field(None, max_length=255, description="Device name")
    device_type: Optional[str] = Field(None, max_length=50, description="Device type (mobile, web, tablet)")
    os_version: Optional[str] = Field(None, max_length=100, description="Operating system version")
    app_version: Optional[str] = Field(None, max_length=50, description="Application version")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class EmployeeLoginSessionCreate(EmployeeLoginSessionBase):
    """Schema for creating employee login session"""
    employee_id: int = Field(..., gt=0, description="Employee ID")


class EmployeeLoginSessionResponse(EmployeeLoginSessionBase):
    """Schema for login session response"""
    id: int
    employee_id: int
    is_active: bool
    last_activity: Optional[datetime]
    login_time: Optional[datetime]
    logout_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class EmployeeLoginSessionDisplay(BaseModel):
    """Schema for displaying login sessions in frontend format"""
    id: int
    sessionToken: str
    deviceName: str
    deviceType: str
    osVersion: str
    appVersion: str
    ipAddress: str
    lastActivity: Optional[str]  # ISO format string
    loginTime: Optional[str]     # ISO format string
    isActive: bool


class EmployeeAccessResponse(EmployeeAccessBase):
    """Schema for employee access response"""
    id: int
    employee_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class EmployeeAccessDisplay(BaseModel):
    """Schema for displaying employee access in frontend format"""
    
    # Employee info
    id: int = Field(..., description="Employee ID")
    name: str = Field(..., description="Employee full name")
    code: str = Field(..., description="Employee code")
    companyCode: str = Field(..., description="Company code")
    employeeCode: str = Field(..., description="Employee code")
    
    # Access settings in frontend format
    access: dict = Field(..., description="Access settings in frontend format")
    
    # Login sessions
    loginSessions: List[EmployeeLoginSessionDisplay] = Field(default=[], description="Active login sessions")


class EmployeeAccessUpdateResponse(BaseModel):
    """Schema for access settings update response"""
    success: bool
    message: str
    employee: dict = Field(..., description="Employee basic info")
    access: dict = Field(..., description="Updated access settings in frontend format")


class EmployeeAccessActionResponse(BaseModel):
    """Schema for access action responses (send login, reset pin, etc.)"""
    success: bool
    message: str
    employee: Optional[dict] = Field(None, description="Employee basic info")


class LogoutSessionRequest(BaseModel):
    """Schema for logout session request"""
    session_id: int = Field(..., gt=0, description="Session ID to logout")


class LogoutSessionResponse(BaseModel):
    """Schema for logout session response"""
    success: bool
    message: str
    sessionId: int = Field(..., description="Logged out session ID")