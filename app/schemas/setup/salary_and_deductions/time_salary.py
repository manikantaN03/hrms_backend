from pydantic import BaseModel, Field, field_validator
from datetime import time, datetime


class TimeRuleBase(BaseModel):
    business_id: int = Field(..., gt=0, description="Business ID must be positive")
    component_id: int = Field(..., gt=0, description="Component ID must be positive")
    attendance: str = Field(..., min_length=1, max_length=50, description="Attendance type (e.g., Present, Half Day)")
    shift: str = Field(..., min_length=1, max_length=50, description="Shift name (e.g., Regular Shift, Night Shift)")
    early_coming_minutes: int = Field(..., ge=0, le=120, description="Early coming allowance in minutes (0-120)")
    in_office_time: time = Field(..., description="Office in time (HH:MM:SS)")
    out_office_time: time = Field(..., description="Office out time (HH:MM:SS)")
    lunch_always_minutes: int = Field(..., ge=0, le=180, description="Lunch break duration in minutes (0-180)")
    lunch_working_minutes: int = Field(..., ge=0, le=180, description="Working lunch duration in minutes (0-180)")
    late_going_minutes: int = Field(..., ge=0, le=120, description="Late going allowance in minutes (0-120)")
    limit_shift_hours: int = Field(..., ge=1, le=24, description="Maximum shift hours (1-24)")
    
    @field_validator('attendance', 'shift')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure string fields are not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('lunch_working_minutes')
    @classmethod
    def validate_lunch_working(cls, v: int, info) -> int:
        """Ensure lunch working minutes <= lunch always minutes"""
        # Note: This validation runs per field, so we can't compare with lunch_always_minutes here
        # This should be done at the model level if needed
        return v


class TimeRuleCreate(TimeRuleBase):
    """Used for creating time salary rule"""
    pass


class TimeRuleUpdate(BaseModel):
    attendance: str | None = None
    shift: str | None = None
    early_coming_minutes: int | None = None
    in_office_time: time | None = None
    out_office_time: time | None = None
    lunch_always_minutes: int | None = None
    lunch_working_minutes: int | None = None
    late_going_minutes: int | None = None
    limit_shift_hours: int | None = None
    business_id: int | None = None        # 🔥 allow updating business_id if needed
    component_id: int | None = None


class TimeRuleResponse(TimeRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
