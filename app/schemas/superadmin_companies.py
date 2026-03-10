"""
SuperAdmin Companies Schemas
Pydantic models for companies management in superadmin panel
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PlanType(str, Enum):
    """Available plan types"""
    MONTHLY = "Monthly"
    YEARLY = "Yearly"


class PlanName(str, Enum):
    """Available plan names"""
    BASIC = "Basic"
    ADVANCED = "Advanced"
    PREMIUM = "Premium"
    ENTERPRISE = "Enterprise"
    PROFESSIONAL = "Professional"


class CompanyStatus(str, Enum):
    """Company status options"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    INR = "INR"


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "English"
    ARABIC = "Arabic"
    SPANISH = "Spanish"
    FRENCH = "French"


class CompanyCreateRequest(BaseModel):
    """Request schema for creating a new company"""
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    phone: str
    url: Optional[str] = None
    website: Optional[str] = None
    address: str
    plan_name: PlanName
    plan_type: PlanType
    currency: Currency = Currency.USD
    language: Language = Language.ENGLISH
    status: CompanyStatus = CompanyStatus.ACTIVE

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()

    @validator('phone')
    def phone_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Phone number is required')
        return v.strip()

    @validator('address')
    def address_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Address is required')
        return v.strip()

    class Config:
        use_enum_values = True


class CompanyUpdateRequest(BaseModel):
    """Request schema for updating a company"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    plan_name: Optional[PlanName] = None
    plan_type: Optional[PlanType] = None
    currency: Optional[Currency] = None
    language: Optional[Language] = None
    status: Optional[CompanyStatus] = None

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Company name cannot be empty')
        return v.strip() if v else v

    @validator('phone')
    def phone_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Phone number cannot be empty')
        return v.strip() if v else v

    @validator('address')
    def address_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Address cannot be empty')
        return v.strip() if v else v

    class Config:
        use_enum_values = True


class CompanyResponse(BaseModel):
    """Response schema for company data"""
    id: int
    name: str
    email: str
    url: str
    phone: str
    website: str
    address: str
    plan: str
    date: str
    status: str
    img: Optional[str] = None
    currency: str
    language: str
    plan_name: str
    plan_type: str

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Response schema for companies list with pagination"""
    companies: List[CompanyResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class CompanyStatsResponse(BaseModel):
    """Response schema for company statistics"""
    total_companies: int
    active_companies: int
    inactive_companies: int
    company_locations: int
    total_companies_growth: float
    active_companies_growth: float
    inactive_companies_growth: float
    company_locations_growth: float


class CompanyFilters(BaseModel):
    """Filters for companies list"""
    search: Optional[str] = None
    plan: Optional[PlanName] = None
    status: Optional[CompanyStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    per_page: int = 20

    @validator('per_page')
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError('per_page must be between 1 and 100')
        return v

    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('page must be greater than 0')
        return v

    class Config:
        use_enum_values = True