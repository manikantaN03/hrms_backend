from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional

class LeaveTypeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(..., description="Full name of the leave type", min_length=1, max_length=100)
    alias: str = Field(..., description="Short/alias used for this leave type", min_length=1, max_length=10)
    color: str = Field("#e7f3ff", description="Hex color code for UI display")
    paid: bool = True
    track_balance: bool = Field(True, alias="trackBalance")
    probation: str = Field("Allow", description="Probation rule: Allow or Disallow")
    allow_requests: bool = Field(True, alias="allowRequests")
    allow_future_requests: bool = Field(True, alias="allowFutureRequests")
    advance_leaves: int = Field(0, alias="advanceLeaves", ge=0)
    past_days: int = Field(0, alias="pastDays", ge=0)
    monthly_limit: int = Field(0, alias="monthlyLimit", ge=0)

    @field_validator("probation")
    def validate_probation(cls, v):
        if v not in ["Allow", "Disallow"]:
            raise ValueError("Probation must be 'Allow' or 'Disallow'")
        return v

    @field_validator("color")
    def validate_color(cls, v):
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be a valid hex color code (e.g., #FF5722)")
        return v


class LeaveTypeCreate(LeaveTypeBase):
    business_id: Optional[int] = None


class LeaveTypeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    alias: Optional[str] = Field(None, min_length=1, max_length=10)
    color: Optional[str] = None
    paid: Optional[bool] = None
    track_balance: Optional[bool] = Field(None, alias="trackBalance")
    probation: Optional[str] = None
    allow_requests: Optional[bool] = Field(None, alias="allowRequests")
    allow_future_requests: Optional[bool] = Field(None, alias="allowFutureRequests")
    advance_leaves: Optional[int] = Field(None, alias="advanceLeaves", ge=0)
    past_days: Optional[int] = Field(None, alias="pastDays", ge=0)
    monthly_limit: Optional[int] = Field(None, alias="monthlyLimit", ge=0)

    @field_validator("probation")
    def validate_probation(cls, v):
        if v is not None and v not in ["Allow", "Disallow"]:
            raise ValueError("Probation must be 'Allow' or 'Disallow'")
        return v

    @field_validator("color")
    def validate_color(cls, v):
        if v is not None and (not v.startswith("#") or len(v) != 7):
            raise ValueError("Color must be a valid hex color code (e.g., #FF5722)")
        return v


class LeaveTypeResponse(LeaveTypeBase):
    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
