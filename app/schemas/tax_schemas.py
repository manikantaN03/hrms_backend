from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import date
from enum import Enum


# ----------------------------
# ENUMS
# ----------------------------

class TaxScheme(str, Enum):
    """Tax scheme options"""
    OLD_SCHEME = "Old Scheme"
    NEW_SCHEME = "New Scheme"


class TaxCategory(str, Enum):
    """Tax category options"""
    BELOW_60 = "< 60 Yr."
    ALL = "All"


# ----------------------------
# TDS SETTINGS
# ----------------------------

class TDSSettingResponse(BaseModel):
    deduct_tds: bool = Field(
        ...,
        description="Whether TDS deduction is enabled"
    )

    class Config:
        from_attributes = True


class TDSSettingUpdate(BaseModel):
    deduct_tds: bool = Field(
        ...,
        description="Enable or disable TDS deduction"
    )


# ----------------------------
# FINANCIAL YEAR
# ----------------------------

class FinancialYearBase(BaseModel):
    year: str = Field(
        ...,
        min_length=7,
        max_length=10,
        description="Financial year in format YYYY-YY (e.g., 2025-26)"
    )
    open: bool = Field(
        ...,
        description="Whether the financial year is open for submissions"
    )
    start_date: date = Field(
        ...,
        description="Start date of the financial year"
    )
    end_date: date = Field(
        ...,
        description="End date of the financial year"
    )

    @field_validator('year')
    @classmethod
    def validate_year_format(cls, v: str) -> str:
        """Validate financial year format"""
        if not v or not v.strip():
            raise ValueError("Financial year cannot be empty")
        
        # Check format: YYYY-YY or YYYY-YYYY
        parts = v.strip().split('-')
        if len(parts) != 2:
            raise ValueError("Financial year must be in format YYYY-YY or YYYY-YYYY")
        
        try:
            year1 = int(parts[0])
            year2 = int(parts[1])
            
            # If short format (YY), convert to full year
            if len(parts[1]) == 2:
                year2 = 2000 + year2 if year2 < 50 else 1900 + year2
            
            # Validate year2 is year1 + 1
            if year2 != year1 + 1:
                raise ValueError("Financial year end must be start year + 1")
                
        except ValueError as e:
            raise ValueError(f"Invalid financial year format: {str(e)}")
        
        return v.strip()

    @field_validator('end_date')
    @classmethod
    def validate_end_after_start(cls, v: date, info) -> date:
        """Validate end date is after start date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("End date must be after start date")
        return v


class FinancialYearCreate(FinancialYearBase):
    business_id: int = Field(
        ...,
        gt=0,
        description="Business ID for which financial year is being created"
    )


class FinancialYearUpdate(BaseModel):
    open: Optional[bool] = Field(
        None,
        description="Toggle financial year open/closed status"
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date in ISO format (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date in ISO format (YYYY-MM-DD)"
    )


class FinancialYearResponse(BaseModel):
    id: int = Field(..., gt=0, description="Financial year ID")
    year: str = Field(..., description="Financial year")
    open: bool = Field(..., description="Open status")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    business_id: int = Field(..., gt=0, description="Business ID")

    class Config:
        from_attributes = True


# ----------------------------
# SALARY COMPONENT
# ----------------------------

class SalaryComponentBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Salary component name"
    )
    type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Component type (Fixed, Variable, System, Manual)"
    )
    categories: Dict[str, bool] = Field(
        default_factory=dict,
        description="Tax category mappings"
    )


class SalaryComponentCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Salary component name"
    )
    type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Component type"
    )
    business_id: int = Field(
        ...,
        gt=0,
        description="Business ID"
    )


class SalaryComponentUpdate(BaseModel):
    basic: Optional[bool] = Field(None, description="Mark as Basic salary")
    hra: Optional[bool] = Field(None, description="Mark as HRA")
    profit: Optional[bool] = Field(None, description="Mark as Profit")
    perk: Optional[bool] = Field(None, description="Mark as Perk")
    ent_all: Optional[bool] = Field(None, description="Mark as Entertainment Allowance")
    exempt: Optional[bool] = Field(None, description="Mark as Exempt (Old Regime)")
    exempt_new: Optional[bool] = Field(None, description="Mark as Exempt (New Regime)")


class SalaryComponentResponse(BaseModel):
    id: int = Field(..., gt=0, description="Component ID")
    name: str = Field(..., description="Component name")
    type: str = Field(..., description="Component type")
    business_id: int = Field(..., gt=0, description="Business ID")
    basic: bool = Field(default=False, description="Is Basic salary")
    hra: bool = Field(default=False, description="Is HRA")
    profit: bool = Field(default=False, description="Is Profit")
    perk: bool = Field(default=False, description="Is Perk")
    ent_all: bool = Field(default=False, description="Is Entertainment Allowance")
    exempt: bool = Field(default=False, description="Is Exempt (Old Regime)")
    exempt_new: bool = Field(default=False, description="Is Exempt (New Regime)")

    class Config:
        from_attributes = True


# ----------------------------
# TAX RATE
# ----------------------------

class TaxRateBase(BaseModel):
    financial_year: str = Field(
        ...,
        min_length=7,
        max_length=10,
        description="Financial year (e.g., 2025-26)"
    )
    scheme: TaxScheme = Field(
        ...,
        description="Tax scheme (Old Scheme or New Scheme)"
    )
    category: TaxCategory = Field(
        ...,
        description="Tax category (< 60 Yr. or All)"
    )
    income_from: float = Field(
        ...,
        ge=0,
        le=100000000,
        description="Income threshold from which this rate applies"
    )
    fixed_tax: float = Field(
        ...,
        ge=0,
        le=100000000,
        description="Fixed tax amount up to this slab"
    )
    progressive_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Progressive tax rate percentage"
    )


class TaxRateResponse(TaxRateBase):
    id: int = Field(..., gt=0, description="Tax rate ID")

    class Config:
        from_attributes = True
