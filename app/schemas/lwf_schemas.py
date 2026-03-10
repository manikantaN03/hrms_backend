from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from typing import List, Optional
from enum import Enum


# ----------------------------
# ENUMS
# ----------------------------

class LWFFrequency(str, Enum):
    """LWF deduction frequency options"""
    MONTHLY = "Monthly"
    HALF_YEARLY = "Half-Yearly"
    YEARLY = "Yearly"


# ----------------------------
# LWF SETTINGS
# ----------------------------

class LWFSettingsBase(BaseModel):
    is_enabled: bool = Field(
        default=False,
        description="Whether LWF deduction is enabled for the business"
    )


class LWFSettingsCreate(LWFSettingsBase):
    business_id: int = Field(
        ...,
        gt=0,
        description="Business ID for which LWF settings are being created"
    )


class LWFSettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = Field(
        None,
        description="Toggle LWF deduction on/off"
    )


class LWFSettingsResponse(LWFSettingsBase):
    id: int = Field(..., gt=0, description="LWF settings ID")
    business_id: int = Field(..., gt=0, description="Business ID")
    rates: List['LWFRateOut'] = Field(
        default=[],
        description="List of LWF rates configured for different states"
    )
    
    model_config = ConfigDict(from_attributes=True)


# ----------------------------
# LWF RATE
# ----------------------------

class LWFRateCreate(BaseModel):
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="State name for which LWF rate applies"
    )
    effective_from: date = Field(
        ...,
        description="Date from which this LWF rate is effective"
    )
    employee_contribution: float = Field(
        ...,
        ge=0,
        le=10000,
        description="Employee contribution amount in rupees"
    )
    employer_contribution: float = Field(
        ...,
        ge=0,
        le=10000,
        description="Employer contribution amount in rupees"
    )
    frequency: LWFFrequency = Field(
        default=LWFFrequency.MONTHLY,
        description="Frequency of LWF deduction"
    )
    lwf_settings_id: int = Field(
        ...,
        gt=0,
        description="LWF settings ID this rate belongs to"
    )
    business_id: int = Field(
        ...,
        gt=0,
        description="Business ID this rate belongs to"
    )

    @field_validator('state')
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Validate and normalize state name"""
        if not v or not v.strip():
            raise ValueError("State name cannot be empty")
        return v.strip()

    @field_validator('effective_from')
    @classmethod
    def validate_effective_from(cls, v: date) -> date:
        """Validate effective_from date"""
        if v > date.today():
            # Allow future dates for planning purposes
            pass
        return v


class LWFRateOut(LWFRateCreate):
    id: int = Field(..., gt=0, description="LWF rate ID")
    model_config = ConfigDict(from_attributes=True)


# ----------------------------
# TOGGLE LWF COMPONENT
# ----------------------------

class LWFComponentToggle(BaseModel):
    is_lwf_applicable: bool = Field(
        ...,
        description="Whether this salary component is applicable for LWF calculation"
    )
    business_id: int = Field(
        ...,
        gt=0,
        description="Business ID to validate component ownership"
    )

 
