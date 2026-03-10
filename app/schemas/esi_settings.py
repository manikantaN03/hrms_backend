"""
ESI Settings Schemas
Pydantic models for ESI configuration
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import date
from enum import Enum


class ESIStatus(str, Enum):
    ENABLED = "Enabled"
    DISABLED = "Disabled"


class CalculationBase(str, Enum):
    GROSS_SALARY = "Gross Salary"
    EARNED_SALARY = "Earned Salary"


# Component Mapping Schemas
class ESIComponentMappingBase(BaseModel):
    component_name: str = Field(..., max_length=100)
    component_code: str = Field(..., max_length=50)
    component_type: str = Field(..., max_length=50)
    is_selected: bool = False


class ESIComponentMappingCreate(ESIComponentMappingBase):
    pass


class ESIComponentMappingUpdate(BaseModel):
    is_selected: Optional[bool] = None


class ESIComponentMappingResponse(ESIComponentMappingBase):
    id: int
    esi_settings_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Rate Change Schemas
class ESIRateChangeBase(BaseModel):
    status: ESIStatus = ESIStatus.ENABLED
    effective_from: date
    employee_rate: float = Field(..., ge=0, le=100, description="Employee contribution rate (%)")
    employer_rate: float = Field(..., ge=0, le=100, description="Employer contribution rate (%)")
    wage_limit: float = Field(..., ge=0, description="ESI wage ceiling limit")


class ESIRateChangeCreate(ESIRateChangeBase):
    pass


class ESIRateChangeUpdate(BaseModel):
    status: Optional[ESIStatus] = None
    effective_from: Optional[date] = None
    employee_rate: Optional[float] = Field(None, ge=0, le=100)
    employer_rate: Optional[float] = Field(None, ge=0, le=100)
    wage_limit: Optional[float] = Field(None, ge=0)


class ESIRateChangeResponse(ESIRateChangeBase):
    id: int
    esi_settings_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Main ESI Settings Schemas
class ESISettingsBase(BaseModel):
    is_enabled: bool = True
    calculation_base: CalculationBase = CalculationBase.GROSS_SALARY


class ESISettingsCreate(ESISettingsBase):
    business_id: int
    component_mappings: Optional[List[ESIComponentMappingCreate]] = []
    rate_changes: Optional[List[ESIRateChangeCreate]] = []


class ESISettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    calculation_base: Optional[CalculationBase] = None


class ESISettingsResponse(ESISettingsBase):
    id: int
    business_id: int
    component_mappings: List[ESIComponentMappingResponse] = []
    rate_changes: List[ESIRateChangeResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# Bulk Component Update
class ESIComponentBulkUpdate(BaseModel):
    component_ids: List[int] = Field(..., description="List of component IDs to update")
    is_selected: bool = Field(..., description="Selection status to apply")
