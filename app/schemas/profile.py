"""
Profile Schemas
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProfileBasicInfoUpdate(BaseModel):
    """Schema for updating basic profile information"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    # Legacy field for backward compatibility
    name: Optional[str] = Field(None, max_length=255)
    mobile: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=50)


class ProfileAddressUpdate(BaseModel):
    """Schema for updating address information"""
    address: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Legacy field for backward compatibility
    website: Optional[str] = Field(None, max_length=255)


class ProfilePasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


class ProfileResponse(BaseModel):
    """Schema for profile response"""
    id: int
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    mobile: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    website: Optional[str] = None
    profile_image: Optional[str] = None
    account_url: Optional[str] = None
    plan_name: Optional[str] = None
    plan_type: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginSession(BaseModel):
    """Schema for login session information"""
    session_id: str
    login_time: datetime
    last_seen: datetime
    ip_address: str
    user_agent: Optional[str] = None
    is_current: bool = False
    ageing_days: int = 0


class LoginSessionsResponse(BaseModel):
    """Schema for login sessions response"""
    sessions: List[LoginSession]
    total_sessions: int


class LogoutSessionRequest(BaseModel):
    """Schema for logout session request"""
    session_id: str


class ProfileUpdateResponse(BaseModel):
    """Schema for profile update response"""
    success: bool
    message: str
    profile: Optional[ProfileResponse] = None


class PasswordChangeResponse(BaseModel):
    """Schema for password change response"""
    success: bool
    message: str