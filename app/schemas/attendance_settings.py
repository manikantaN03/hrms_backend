from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class AttendanceSettingsBase(BaseModel):
    default_attendance: Optional[str] = Field(default="PRESENT", description="Default attendance status (PRESENT or ABSENT)")
    mark_out_on_punch: Optional[bool] = Field(default=False, description="Mark out on every 2nd punch")
    punch_count: Optional[int] = Field(default=2, ge=1, le=10, description="Number of punches (1-10)")
    enable_manual_attendance: Optional[bool] = Field(default=False, description="Enable manual attendance entry")
    
    # Holiday Sandwich Rules (matching frontend structure)
    no_holiday_if_absent: Optional[bool] = Field(default=False, description="Do not allow holiday if absent on next/previous day")
    apply_holiday_one_side: Optional[bool] = Field(default=False, description="Apply only if absent on BOTH next and previous day")
    apply_holiday_either: Optional[bool] = Field(default=False, description="Restrict to only one day before/after absent")
    
    # Week Off Sandwich Rules (matching frontend structure)
    no_week_off_if_absent: Optional[bool] = Field(default=False, description="Do not allow week off if absent on next/previous day")
    apply_week_off_one_side: Optional[bool] = Field(default=False, description="Apply only if absent on BOTH next and previous day")
    apply_week_off_either: Optional[bool] = Field(default=False, description="Restrict to only one day before/after absent")

    @field_validator("default_attendance")
    @classmethod
    def validate_default_attendance(cls, v):
        """Validate default attendance value"""
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ["PRESENT", "ABSENT"]:
                raise ValueError("default_attendance must be PRESENT or ABSENT")
            return v_upper
        return v
    
    @field_validator("punch_count")
    @classmethod
    def validate_punch_count(cls, v):
        """Validate punch count is within range"""
        if v is not None and (v < 1 or v > 10):
            raise ValueError("punch_count must be between 1 and 10")
        return v


class AttendanceSettingsCreate(AttendanceSettingsBase):
    business_id: int = Field(..., gt=0, description="Business ID must be positive")


class AttendanceSettingsUpdate(BaseModel):
    default_attendance: Optional[str] = Field(None, description="Default attendance status (PRESENT or ABSENT)")
    mark_out_on_punch: Optional[bool] = Field(None, description="Mark out on every 2nd punch")
    punch_count: Optional[int] = Field(None, ge=1, le=10, description="Number of punches (1-10)")
    enable_manual_attendance: Optional[bool] = Field(None, description="Enable manual attendance entry")
    no_holiday_if_absent: Optional[bool] = Field(None, description="Do not allow holiday if absent on next/previous day")
    apply_holiday_one_side: Optional[bool] = Field(None, description="Apply only if absent on BOTH next and previous day")
    apply_holiday_either: Optional[bool] = Field(None, description="Restrict to only one day before/after absent")
    no_week_off_if_absent: Optional[bool] = Field(None, description="Do not allow week off if absent on next/previous day")
    apply_week_off_one_side: Optional[bool] = Field(None, description="Apply only if absent on BOTH next and previous day")
    apply_week_off_either: Optional[bool] = Field(None, description="Restrict to only one day before/after absent")

    @field_validator("default_attendance")
    @classmethod
    def validate_default_attendance(cls, v):
        """Validate default attendance value"""
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ["PRESENT", "ABSENT"]:
                raise ValueError("default_attendance must be PRESENT or ABSENT")
            return v_upper
        return v
    
    @field_validator("punch_count")
    @classmethod
    def validate_punch_count(cls, v):
        """Validate punch count is within range"""
        if v is not None and (v < 1 or v > 10):
            raise ValueError("punch_count must be between 1 and 10")
        return v


class AttendanceSettingsResponse(AttendanceSettingsBase):
    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
