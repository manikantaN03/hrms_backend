from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class EmployeeCodeBase(BaseModel):
    autoCode: bool = Field(default=True, description="Enable automatic employee code generation")
    prefix: str = Field(default="", max_length=10, description="Prefix for employee codes")
    length: int = Field(..., ge=1, le=10, description="Length of numeric part")
    suffix: str = Field(default="", max_length=10, description="Suffix for employee codes")


class EmployeeCodeCreate(EmployeeCodeBase):
    business_id: int = Field(..., gt=0, description="Business ID")
    prefix: str = Field(..., min_length=1, max_length=10, description="Prefix for employee codes (required for creation)")


class EmployeeCodeUpdate(BaseModel):
    autoCode: Optional[bool] = Field(None, description="Enable automatic employee code generation")
    prefix: Optional[str] = Field(None, min_length=1, max_length=10, description="Prefix for employee codes")
    length: Optional[int] = Field(None, ge=1, le=10, description="Length of numeric part")
    suffix: Optional[str] = Field(None, max_length=10, description="Suffix for employee codes")


class EmployeeCodeResponse(EmployeeCodeBase):
    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)


class RegenerateCodesRequest(BaseModel):
    sort_by: str = Field(default="dateJoining", description="Sort employees by: dateJoining or employeeName")
