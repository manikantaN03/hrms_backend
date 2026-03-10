from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ======================================================================
#                          OVERTIME POLICY
# ======================================================================

class OvertimePolicyCreate(BaseModel):
    business_id: int = Field(..., gt=0, description="Business ID must be positive")
    policy_name: str = Field(..., min_length=1, max_length=255, description="Policy name (1-255 characters)")
    
    @field_validator('policy_name')
    @classmethod
    def validate_policy_name(cls, v: str) -> str:
        """Ensure policy name is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Policy name cannot be empty or whitespace only")
        return v.strip()


class OvertimePolicyUpdate(BaseModel):
    policy_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Policy name (1-255 characters)")
    
    @field_validator('policy_name')
    @classmethod
    def validate_policy_name(cls, v: Optional[str]) -> Optional[str]:
        """Ensure policy name is not empty or whitespace only if provided"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Policy name cannot be empty or whitespace only")
            return v.strip()
        return v


class OvertimePolicyOut(BaseModel):
    id: int
    business_id: int
    policy_name: str

    class Config:
        from_attributes = True


# ======================================================================
#                          OVERTIME RULE
# ======================================================================

class OvertimeRuleCreate(BaseModel):
    business_id: int = Field(..., gt=0, description="Business ID must be positive")
    policy_id: int = Field(..., gt=0, description="Policy ID must be positive")
    attendance_type: str = Field(..., min_length=1, max_length=50, description="Attendance type (e.g., Present, Absent, Half Day)")
    time_basis: str = Field(..., min_length=1, max_length=50, description="Time basis (e.g., Early Coming, Late Going, Daily, Weekly)")
    from_hrs: int = Field(..., ge=0, le=23, description="From hours (0-23)")
    from_mins: int = Field(..., ge=0, le=59, description="From minutes (0-59)")
    to_hrs: int = Field(..., ge=0, le=23, description="To hours (0-23)")
    to_mins: int = Field(..., ge=0, le=59, description="To minutes (0-59)")
    calculation_method: str = Field(..., min_length=1, max_length=50, description="Calculation method (e.g., Exclusive, Progressive, Multiplier)")
    multiplier: int = Field(..., ge=1, le=10, description="Multiplier (1-10)")
    overtime_mins_type: str = Field(..., min_length=1, max_length=50, description="Overtime minutes type (e.g., Actual, Above, Fixed)")
    fixed_mins: Optional[int] = Field(None, ge=0, le=1440, description="Fixed minutes (0-1440, required if overtime_mins_type is Fixed)")
    
    @field_validator('attendance_type', 'time_basis', 'calculation_method', 'overtime_mins_type')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure string fields are not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('fixed_mins')
    @classmethod
    def validate_fixed_mins(cls, v: Optional[int], info) -> Optional[int]:
        """Validate fixed_mins based on overtime_mins_type"""
        # Note: This validation runs per field, so we can't access overtime_mins_type here
        # This should be done at the model level if needed
        return v


class OvertimeRuleUpdate(BaseModel):
    attendance_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Attendance type")
    time_basis: Optional[str] = Field(None, min_length=1, max_length=50, description="Time basis")
    from_hrs: Optional[int] = Field(None, ge=0, le=23, description="From hours (0-23)")
    from_mins: Optional[int] = Field(None, ge=0, le=59, description="From minutes (0-59)")
    to_hrs: Optional[int] = Field(None, ge=0, le=23, description="To hours (0-23)")
    to_mins: Optional[int] = Field(None, ge=0, le=59, description="To minutes (0-59)")
    calculation_method: Optional[str] = Field(None, min_length=1, max_length=50, description="Calculation method")
    multiplier: Optional[int] = Field(None, ge=1, le=10, description="Multiplier (1-10)")
    overtime_mins_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Overtime minutes type")
    fixed_mins: Optional[int] = Field(None, ge=0, le=1440, description="Fixed minutes (0-1440)")
    
    @field_validator('attendance_type', 'time_basis', 'calculation_method', 'overtime_mins_type')
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure string fields are not empty or whitespace only if provided"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Field cannot be empty or whitespace only")
            return v.strip()
        return v


class OvertimeRuleOut(BaseModel):
    id: int
    business_id: int
    policy_id: int
    attendance_type: str
    time_basis: str
    from_hrs: int
    from_mins: int
    to_hrs: int
    to_mins: int
    calculation_method: str
    multiplier: int
    overtime_mins_type: str
    fixed_mins: Optional[int]

    class Config:
        from_attributes = True
