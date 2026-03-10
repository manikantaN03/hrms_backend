from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class FilterOptionsResponse(BaseModel):
    locations: List[str] = Field(..., description="List of available locations")
    cost_centers: List[str] = Field(..., alias="costCenters", description="List of available cost centers")
    departments: List[str] = Field(..., description="List of available departments")

    model_config = {"populate_by_name": True}


class SendLoginRequest(BaseModel):
    business_id: int = Field(..., alias="businessId", gt=0, description="Business ID")
    location: Optional[str] = Field(None, max_length=100, description="Filter by location")
    cost_center: Optional[str] = Field(None, alias="costCenter", max_length=100, description="Filter by cost center")
    department: Optional[str] = Field(None, max_length=100, description="Filter by department")
    include_logged_in: bool = Field(False, alias="includeLoggedIn", description="Include already logged-in employees")

    @field_validator('location', 'cost_center', 'department')
    @classmethod
    def validate_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            return v.strip()
        return None

    model_config = {"populate_by_name": True}


class SendLoginResponse(BaseModel):
    success: bool
    message: str
    employees_notified: int = Field(..., alias="employeesNotified", ge=0)
    details: str

    model_config = {"populate_by_name": True}


class EmployeeFilterRequest(BaseModel):
    business_id: int = Field(..., alias="businessId", gt=0, description="Business ID")
    location: Optional[str] = Field(None, max_length=100, description="Filter by location")
    cost_center: Optional[str] = Field(None, alias="costCenter", max_length=100, description="Filter by cost center")
    department: Optional[str] = Field(None, max_length=100, description="Filter by department")

    @field_validator('location', 'cost_center', 'department')
    @classmethod
    def validate_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            return v.strip()
        return None

    model_config = {"populate_by_name": True}


class EmployeeCountResponse(BaseModel):
    total_employees: int = Field(..., alias="totalEmployees", ge=0, description="Total number of employees matching filters")
    filters: dict = Field(..., description="Applied filter criteria")

    model_config = {"populate_by_name": True}