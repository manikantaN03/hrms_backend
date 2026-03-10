from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.schemas.setup.salary_and_deductions.salary_structure_rule import (
    SalaryStructureRuleCreate, SalaryStructureRuleUpdate, SalaryStructureRuleResponse
)


# ---------------- SALARY STRUCTURE SCHEMAS ----------------

class SalaryStructureCreate(BaseModel):
    business_id: int = Field(..., gt=0, description="Business ID")
    name: str = Field(..., min_length=1, max_length=120, description="Structure name")
    rules: List[SalaryStructureRuleCreate] = Field(default=[], description="Allocation rules")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError('Structure name cannot be empty or whitespace only')
        return v.strip()


class SalaryStructureUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    rules: Optional[List[SalaryStructureRuleUpdate]] = None
    business_id: Optional[int] = None   # Optional on update but should not be changed

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Ensure name is not empty or whitespace only if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Structure name cannot be empty or whitespace only')
        return v.strip() if v else v


class SalaryStructureResponse(BaseModel):
    id: int
    business_id: int
    name: str
    rules: List[SalaryStructureRuleResponse]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
