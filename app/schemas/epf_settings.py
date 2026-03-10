"""
EPF Settings Schemas
Pydantic models for EPF configuration
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import date
from enum import Enum


class EPFStatus(str, Enum):
    ENABLED = "Enabled"
    DISABLED = "Disabled"


class CalculationBase(str, Enum):
    GROSS_SALARY = "Gross Salary"
    EARNED_SALARY = "Earned Salary"


# Component Mapping Schemas
class EPFComponentMappingBase(BaseModel):
    component_name: str = Field(..., max_length=100)
    component_code: str = Field(..., max_length=50)
    component_type: str = Field(..., max_length=50)
    is_selected: bool = False


class EPFComponentMappingCreate(EPFComponentMappingBase):
    pass


class EPFComponentMappingUpdate(BaseModel):
    is_selected: Optional[bool] = None


class EPFComponentMappingResponse(EPFComponentMappingBase):
    id: int
    epf_settings_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Rate Change Schemas
class EPFRateChangeBase(BaseModel):
    status: EPFStatus = EPFStatus.ENABLED
    effective_from: date
    
    # Non-Senior rates
    emp_pf_rate_non_senior: float = Field(12.0, ge=0, le=100, description="Employee PF rate for non-seniors (%)")
    employer_pf_rate_non_senior: float = Field(12.0, ge=0, le=100, description="Employer PF rate for non-seniors (%)")
    pension_rate_non_senior: float = Field(8.33, ge=0, le=100, description="Pension rate for non-seniors (%)")
    
    # Senior rates
    emp_pf_rate_senior: float = Field(12.0, ge=0, le=100, description="Employee PF rate for seniors (%)")
    employer_pf_rate_senior: float = Field(12.0, ge=0, le=100, description="Employer PF rate for seniors (%)")
    pension_rate_senior: float = Field(0.0, ge=0, le=100, description="Pension rate for seniors (%)")
    
    # Other settings
    edli_rate: float = Field(0.5, ge=0, le=100, description="EDLI & Admin charges (%)")
    wage_ceiling: float = Field(15000.0, ge=0, description="PF wage ceiling limit")
    senior_age: int = Field(58, ge=18, le=100, description="Age threshold for senior employees")


class EPFRateChangeCreate(EPFRateChangeBase):
    pass


class EPFRateChangeUpdate(BaseModel):
    status: Optional[EPFStatus] = None
    effective_from: Optional[date] = None
    emp_pf_rate_non_senior: Optional[float] = Field(None, ge=0, le=100)
    employer_pf_rate_non_senior: Optional[float] = Field(None, ge=0, le=100)
    pension_rate_non_senior: Optional[float] = Field(None, ge=0, le=100)
    emp_pf_rate_senior: Optional[float] = Field(None, ge=0, le=100)
    employer_pf_rate_senior: Optional[float] = Field(None, ge=0, le=100)
    pension_rate_senior: Optional[float] = Field(None, ge=0, le=100)
    edli_rate: Optional[float] = Field(None, ge=0, le=100)
    wage_ceiling: Optional[float] = Field(None, ge=0)
    senior_age: Optional[int] = Field(None, ge=18, le=100)


class EPFRateChangeResponse(EPFRateChangeBase):
    id: int
    epf_settings_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Main EPF Settings Schemas
class EPFSettingsBase(BaseModel):
    is_enabled: bool = True
    calculation_base: CalculationBase = CalculationBase.GROSS_SALARY


class EPFSettingsCreate(EPFSettingsBase):
    business_id: int
    component_mappings: Optional[List[EPFComponentMappingCreate]] = []
    rate_changes: Optional[List[EPFRateChangeCreate]] = []


class EPFSettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    calculation_base: Optional[CalculationBase] = None


class EPFSettingsResponse(EPFSettingsBase):
    id: int
    business_id: int
    component_mappings: List[EPFComponentMappingResponse] = []
    rate_changes: List[EPFRateChangeResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# Bulk Component Update
class EPFComponentBulkUpdate(BaseModel):
    component_ids: List[int] = Field(..., description="List of component IDs to update")
    is_selected: bool = Field(..., description="Selection status to apply")
