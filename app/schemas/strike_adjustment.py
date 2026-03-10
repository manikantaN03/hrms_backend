from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class StrikeAdjustmentBase(BaseModel):
    strike_type: str = Field(..., alias="strikeType", description="Strike type: Green, Blue, or Red")
    strike_range_from: int = Field(..., alias="strikeRangeFrom", ge=0, description="Strike range start (inclusive)")
    strike_range_to: int = Field(..., alias="strikeRangeTo", ge=0, description="Strike range end (inclusive)")
    action: str = Field(..., description="Action: Send Warning Only or Update Attendance")
    business_id: int = Field(..., description="Business ID")

    @field_validator("strike_type")
    @classmethod
    def validate_strike_type(cls, v):
        """Validate strike type is one of allowed values"""
        allowed = ["Green", "Blue", "Red"]
        if v not in allowed:
            raise ValueError(f"strike_type must be one of {allowed}")
        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        """Validate action is one of allowed values"""
        allowed = ["Send Warning Only", "Update Attendance"]
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v

    @field_validator("strike_range_to")
    @classmethod
    def validate_range(cls, v, info):
        """Validate strike_range_to is greater than or equal to strike_range_from"""
        if "strike_range_from" in info.data and v < info.data["strike_range_from"]:
            raise ValueError("strike_range_to must be greater than or equal to strike_range_from")
        return v

    model_config = ConfigDict(populate_by_name=True)


class StrikeAdjustmentCreate(StrikeAdjustmentBase):
    """Schema for creating a new strike adjustment"""
    pass


class StrikeAdjustmentUpdate(StrikeAdjustmentBase):
    """Schema for updating an existing strike adjustment"""
    pass


class StrikeAdjustmentResponse(BaseModel):
    """Schema for strike adjustment response"""
    id: int
    strike_type: str = Field(..., alias="strikeType")
    strike_range_from: int = Field(..., alias="strikeRangeFrom")
    strike_range_to: int = Field(..., alias="strikeRangeTo")
    action: str
    business_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
