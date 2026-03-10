from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class SalaryDeductionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Deduction name")
    code: str = Field(..., min_length=1, max_length=50, description="Short code/alias")
    type: str = Field(..., min_length=1, max_length=50, description="Deduction type (Fixed/Variable)")
    active: bool = Field(default=True, description="Active status")
    payback_on_exit: bool = Field(default=False, description="Payback on employee exit")

    @field_validator('name', 'code', 'type')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure string fields are not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace only')
        return v.strip()


class SalaryDeductionCreate(SalaryDeductionBase):
    """Used for creating a salary deduction."""
    business_id: int = Field(..., gt=0, description="Business ID")


class SalaryDeductionUpdate(BaseModel):
    """Used for updating fields of a salary deduction."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    active: Optional[bool] = None
    payback_on_exit: Optional[bool] = None
    status: Optional[str] = Field(None, min_length=1, max_length=20)

    @field_validator('name', 'code', 'type', 'status')
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure string fields are not empty or whitespace only if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Field cannot be empty or whitespace only')
        return v.strip() if v else v

    # business_id should never be editable → NOT included


class SalaryDeductionResponse(SalaryDeductionBase):
    id: int
    business_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
