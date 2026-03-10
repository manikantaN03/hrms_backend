from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class SalaryStructureRuleBase(BaseModel):
    business_id: int = Field(..., gt=0, description="Business ID")
    structure_id: int = Field(..., gt=0, description="Structure ID")
    component_id: int = Field(..., gt=0, description="Component ID")
    calculation_type: str = Field(..., min_length=1, max_length=20, description="Fixed or Percentage")
    value: float = Field(..., ge=0, description="Amount or percentage value")
    sequence: int = Field(default=1, ge=1, description="Display order")

    @field_validator('calculation_type')
    @classmethod
    def validate_calculation_type(cls, v: str) -> str:
        """Ensure calculation type is valid"""
        allowed = ['Fixed', 'Percentage']
        if v not in allowed:
            raise ValueError(f'Calculation type must be one of: {", ".join(allowed)}')
        return v


class SalaryStructureRuleCreate(BaseModel):
    structure_id: int = Field(..., gt=0, description="Structure ID")
    component_id: int = Field(..., gt=0, description="Component ID")
    calculation_type: str = Field(..., min_length=1, max_length=20, description="Fixed or Percentage")
    value: float = Field(..., ge=0, description="Amount or percentage value")
    sequence: int = Field(default=1, ge=1, description="Display order")

    @field_validator('calculation_type')
    @classmethod
    def validate_calculation_type(cls, v: str) -> str:
        """Ensure calculation type is valid"""
        allowed = ['Fixed', 'Percentage']
        if v not in allowed:
            raise ValueError(f'Calculation type must be one of: {", ".join(allowed)}')
        return v


class SalaryStructureRuleUpdate(BaseModel):
    component_id: Optional[int] = Field(None, gt=0)
    calculation_type: Optional[str] = Field(None, min_length=1, max_length=20)
    value: Optional[float] = Field(None, ge=0)
    sequence: Optional[int] = Field(None, ge=1)

    @field_validator('calculation_type')
    @classmethod
    def validate_calculation_type(cls, v: Optional[str]) -> Optional[str]:
        """Ensure calculation type is valid if provided"""
        if v is not None:
            allowed = ['Fixed', 'Percentage']
            if v not in allowed:
                raise ValueError(f'Calculation type must be one of: {", ".join(allowed)}')
        return v


class SalaryStructureRuleResponse(BaseModel):
    id: int
    business_id: int
    structure_id: int
    component_id: int
    calculation_type: str
    value: float
    sequence: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
