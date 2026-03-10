from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class CompOffRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Rule name")
    max_days: int = Field(default=0, ge=0, description="Maximum comp off days allowed")
    expiry_days: int = Field(default=0, ge=0, description="Days until comp off expires")
    is_active: bool = Field(default=True, description="Whether rule is active")


class CompOffRuleCreate(CompOffRuleBase):
    rule_type: Optional[str] = Field(None, description="Rule type: weekly_offs, holidays, or custom")
    auto_grant_enabled: bool = Field(default=False, description="Auto-grant comp off when conditions met")
    half_day_hours: int = Field(default=0, ge=0, le=23, description="Hours threshold for half day comp off")
    half_day_mins: int = Field(default=0, ge=0, le=59, description="Minutes threshold for half day comp off")
    full_day_hours: int = Field(default=0, ge=0, le=23, description="Hours threshold for full day comp off")
    full_day_mins: int = Field(default=0, ge=0, le=59, description="Minutes threshold for full day comp off")
    grant_type: str = Field(default="grant_comp_off", description="Grant type: grant_comp_off or add_to_extra_days")
    business_id: Optional[int] = Field(None, description="Business ID")

    @field_validator("grant_type")
    @classmethod
    def validate_grant_type(cls, v):
        """Validate grant type is one of allowed values"""
        allowed = ["grant_comp_off", "add_to_extra_days"]
        if v not in allowed:
            raise ValueError(f"grant_type must be one of {allowed}")
        return v

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v):
        """Validate rule type if provided"""
        if v is not None:
            allowed = ["weekly_offs", "holidays", "custom"]
            if v not in allowed:
                raise ValueError(f"rule_type must be one of {allowed}")
        return v


class CompOffRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Rule name")
    max_days: Optional[int] = Field(None, ge=0, description="Maximum comp off days allowed")
    expiry_days: Optional[int] = Field(None, ge=0, description="Days until comp off expires")
    is_active: Optional[bool] = Field(None, description="Whether rule is active")
    auto_grant_enabled: Optional[bool] = Field(None, description="Auto-grant comp off when conditions met")
    half_day_hours: Optional[int] = Field(None, ge=0, le=23, description="Hours threshold for half day comp off")
    half_day_mins: Optional[int] = Field(None, ge=0, le=59, description="Minutes threshold for half day comp off")
    full_day_hours: Optional[int] = Field(None, ge=0, le=23, description="Hours threshold for full day comp off")
    full_day_mins: Optional[int] = Field(None, ge=0, le=59, description="Minutes threshold for full day comp off")
    grant_type: Optional[str] = Field(None, description="Grant type: grant_comp_off or add_to_extra_days")

    @field_validator("grant_type")
    @classmethod
    def validate_grant_type(cls, v):
        """Validate grant type is one of allowed values"""
        if v is not None:
            allowed = ["grant_comp_off", "add_to_extra_days"]
            if v not in allowed:
                raise ValueError(f"grant_type must be one of {allowed}")
        return v


class CompOffRuleResponse(CompOffRuleBase):
    id: int
    business_id: int
    rule_type: Optional[str] = None
    auto_grant_enabled: bool
    half_day_hours: int
    half_day_mins: int
    full_day_hours: int
    full_day_mins: int
    grant_type: str
    created_at: datetime

    class Config:
        from_attributes = True

