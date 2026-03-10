"""
User Preferences Schemas
Pydantic models for user preferences request/response validation
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences"""
    
    # Communication Preferences
    send_email_alerts: bool = True
    send_sms_alerts: bool = False
    send_browser_push_alerts: bool = False
    
    # Alert Preferences
    daily_attendance_summary: bool = True
    onboarding_form_updates: bool = True
    employee_confirmation_reminders: bool = True
    flight_risk_changes: bool = False


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences"""
    pass


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences (all fields optional)"""
    
    # Communication Preferences
    send_email_alerts: Optional[bool] = None
    send_sms_alerts: Optional[bool] = None
    send_browser_push_alerts: Optional[bool] = None
    
    # Alert Preferences
    daily_attendance_summary: Optional[bool] = None
    onboarding_form_updates: Optional[bool] = None
    employee_confirmation_reminders: Optional[bool] = None
    flight_risk_changes: Optional[bool] = None


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response"""
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
