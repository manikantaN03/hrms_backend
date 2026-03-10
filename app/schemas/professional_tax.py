"""
Professional Tax Schemas
Pydantic models for Professional Tax configuration
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import date
from enum import Enum


class CalculationBase(str, Enum):
    GROSS_SALARY = "Gross Salary"
    EARNED_SALARY = "Earned Salary"


class PTMonth(str, Enum):
    ALL_MONTHS = "All Months"
    JANUARY = "January"
    FEBRUARY = "February"
    MARCH = "March"
    APRIL = "April"
    MAY = "May"
    JUNE = "June"
    JULY = "July"
    AUGUST = "August"
    SEPTEMBER = "September"
    OCTOBER = "October"
    NOVEMBER = "November"
    DECEMBER = "December"


class PTGender(str, Enum):
    ALL_GENDERS = "All Genders"
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


# Component Mapping Schemas
class PTComponentMappingBase(BaseModel):
    component_name: str = Field(..., max_length=100)
    component_code: str = Field(..., max_length=50)
    component_type: str = Field(..., max_length=50)
    is_selected: bool = False


class PTComponentMappingCreate(PTComponentMappingBase):
    pass


class PTComponentMappingUpdate(BaseModel):
    is_selected: Optional[bool] = None


class PTComponentMappingResponse(PTComponentMappingBase):
    id: int
    pt_settings_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Tax Rate Schemas
class ProfessionalTaxRateBase(BaseModel):
    state: str = Field(..., max_length=100, description="State name")
    effective_from: date = Field(..., description="Effective start date")
    salary_above: float = Field(0.0, ge=0, description="Salary threshold for this slab")
    month: PTMonth = PTMonth.ALL_MONTHS
    gender: PTGender = PTGender.ALL_GENDERS
    tax_amount: float = Field(..., ge=0, description="Tax amount for this slab")


class ProfessionalTaxRateCreate(ProfessionalTaxRateBase):
    pass


class ProfessionalTaxRateUpdate(BaseModel):
    state: Optional[str] = Field(None, max_length=100)
    effective_from: Optional[date] = None
    salary_above: Optional[float] = Field(None, ge=0)
    month: Optional[PTMonth] = None
    gender: Optional[PTGender] = None
    tax_amount: Optional[float] = Field(None, ge=0)


class ProfessionalTaxRateResponse(ProfessionalTaxRateBase):
    id: int
    pt_settings_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Main Professional Tax Settings Schemas
class ProfessionalTaxSettingsBase(BaseModel):
    is_enabled: bool = True
    calculation_base: CalculationBase = CalculationBase.GROSS_SALARY


class ProfessionalTaxSettingsCreate(ProfessionalTaxSettingsBase):
    business_id: int
    component_mappings: Optional[List[PTComponentMappingCreate]] = []
    tax_rates: Optional[List[ProfessionalTaxRateCreate]] = []


class ProfessionalTaxSettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    calculation_base: Optional[CalculationBase] = None


class ProfessionalTaxSettingsResponse(ProfessionalTaxSettingsBase):
    id: int
    business_id: int
    component_mappings: List[PTComponentMappingResponse] = []
    tax_rates: List[ProfessionalTaxRateResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# Bulk Component Update
class PTComponentBulkUpdate(BaseModel):
    component_ids: List[int] = Field(..., description="List of component IDs to update")
    is_selected: bool = Field(..., description="Selection status to apply")


# Query by State
class PTRatesByStateResponse(BaseModel):
    state: str
    rates: List[ProfessionalTaxRateResponse]
