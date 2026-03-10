"""
Business Schemas
Pydantic models for request/response validation
Includes business_id logic in responses
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field
from typing import Optional
from datetime import datetime
import re


# ============================================================================
# Base Schema
# ============================================================================

class BusinessBase(BaseModel):
    """Base schema with common fields"""
    
    business_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Name of the business/company"
    )
    gstin: Optional[str] = Field(
        None, 
        max_length=15,
        description="15-digit GSTIN (optional)"
    )
    is_authorized: bool = Field(
        default=False,
        description="Confirmation that user is authorized for GSTIN"
    )
    
    pan: str = Field(
        ..., 
        min_length=10, 
        max_length=10,
        description="10-character PAN number"
    )
    address: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Full business address"
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="City name"
    )
    pincode: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit pincode"
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="State name"
    )
    constitution: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Business constitution type"
    )
    
    product: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Product/service offering"
    )
    plan: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Subscription plan"
    )
    employee_count: int = Field(
        ..., 
        ge=1,
        description="Number of employees"
    )
    billing_frequency: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Billing cycle"
    )
    
    business_url: Optional[str] = Field(
        None,
        max_length=255,
        description="Custom business URL (subdomain)"
    )


# ============================================================================
# Create Schema
# ============================================================================

class BusinessCreate(BusinessBase):
    """
    Schema for creating a new business.
    Matches the data collected from React 3-step wizard.
    """
    
    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, value):
        """Validate GSTIN format if provided"""
        if value:
            # GSTIN format: 22AAAAA0000A1Z5
            if len(value) != 15:
                raise ValueError('GSTIN must be exactly 15 characters')
            
            if not value.isalnum():
                raise ValueError('GSTIN must be alphanumeric')
            
            # First 2 chars = state code (numbers)
            if not value[:2].isdigit():
                raise ValueError('GSTIN must start with 2-digit state code')
            
            # Last char should be alphanumeric
            if not value[-1].isalnum():
                raise ValueError('Invalid GSTIN format')
        
        return value.upper() if value else None
    
    @field_validator('pan')
    @classmethod
    def validate_pan(cls, value):
        """Validate PAN format"""
        # PAN format: AAAAA9999A
        if len(value) != 10:
            raise ValueError('PAN must be exactly 10 characters')
        
        if not value.isalnum():
            raise ValueError('PAN must be alphanumeric')
        
        # First 5 chars = letters
        if not value[:5].isalpha():
            raise ValueError('First 5 characters of PAN must be letters')
        
        # Next 4 chars = numbers
        if not value[5:9].isdigit():
            raise ValueError('Characters 6-9 of PAN must be digits')
        
        # Last char = letter
        if not value[9].isalpha():
            raise ValueError('Last character of PAN must be a letter')
        
        return value.upper()
    
    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, value):
        """Validate pincode format"""
        if len(value) != 6:
            raise ValueError('Pincode must be exactly 6 digits')
        
        if not value.isdigit():
            raise ValueError('Pincode must contain only digits')
        
        return value
    
    @field_validator('business_url')
    @classmethod
    def validate_business_url(cls, value):
        """Validate business URL format"""
        if value:
            # Only lowercase alphanumeric and hyphens
            if not re.match(r'^[a-z0-9-]+$', value):
                raise ValueError(
                    'Business URL can only contain lowercase letters, '
                    'numbers, and hyphens'
                )
            
            # Cannot start or end with hyphen
            if value.startswith('-') or value.endswith('-'):
                raise ValueError('Business URL cannot start or end with hyphen')
            
            # Min/max length
            if len(value) < 3 or len(value) > 50:
                raise ValueError('Business URL must be 3-50 characters')
        
        return value.lower() if value else None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "business_name": "Acme Corporation",
                "gstin": "22AAAAA0000A1Z5",
                "is_authorized": True,
                "pan": "ABCDE1234F",
                "address": "123 Business Park, Tech City",
                "city": "Bangalore",
                "pincode": "560001",
                "state": "Karnataka",
                "constitution": "Private Limited Company",
                "product": "Runtime HRMS Suite",
                "plan": "Professional",
                "employee_count": 50,
                "billing_frequency": "Monthly (1 month)",
                "business_url": "acme-corp"
            }
        }
    )


# ============================================================================
# Update Schema
# ============================================================================

class BusinessUpdate(BaseModel):
    """
    Schema for updating an existing business.
    All fields are optional.
    """
    
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    gstin: Optional[str] = Field(None, max_length=15)
    is_authorized: Optional[bool] = None
    
    pan: Optional[str] = Field(None, min_length=10, max_length=10)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    constitution: Optional[str] = Field(None, min_length=2, max_length=100)
    
    product: Optional[str] = Field(None, min_length=2, max_length=100)
    plan: Optional[str] = Field(None, min_length=2, max_length=50)
    employee_count: Optional[int] = Field(None, ge=1)
    billing_frequency: Optional[str] = Field(None, min_length=2, max_length=50)
    
    business_url: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    
    # Same validators as BusinessCreate
    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, value):
        if value:
            if len(value) != 15:
                raise ValueError('GSTIN must be exactly 15 characters')
            if not value.isalnum():
                raise ValueError('GSTIN must be alphanumeric')
            if not value[:2].isdigit():
                raise ValueError('GSTIN must start with 2-digit state code')
        return value.upper() if value else None
    
    @field_validator('pan')
    @classmethod
    def validate_pan(cls, value):
        if value:
            if len(value) != 10:
                raise ValueError('PAN must be exactly 10 characters')
            if not value.isalnum():
                raise ValueError('PAN must be alphanumeric')
            if not value[:5].isalpha():
                raise ValueError('First 5 characters of PAN must be letters')
            if not value[5:9].isdigit():
                raise ValueError('Characters 6-9 of PAN must be digits')
            if not value[9].isalpha():
                raise ValueError('Last character of PAN must be a letter')
        return value.upper() if value else None
    
    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, value):
        if value:
            if len(value) != 6:
                raise ValueError('Pincode must be exactly 6 digits')
            if not value.isdigit():
                raise ValueError('Pincode must contain only digits')
        return value
    
    @field_validator('business_url')
    @classmethod
    def validate_business_url(cls, value):
        if value:
            if not re.match(r'^[a-z0-9-]+$', value):
                raise ValueError(
                    'Business URL can only contain lowercase letters, '
                    'numbers, and hyphens'
                )
            if value.startswith('-') or value.endswith('-'):
                raise ValueError('Business URL cannot start or end with hyphen')
            if len(value) < 3 or len(value) > 50:
                raise ValueError('Business URL must be 3-50 characters')
        return value.lower() if value else None


# ============================================================================
# Response Schema (With business_id logic)
# ============================================================================

class BusinessResponse(BusinessBase):
    """
    Schema for business responses.
    Includes all fields plus auto-generated ones.
    Also exposes business_id explicity.
    """
    
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    def business_id(self) -> int:
        """Expose primary key as business_id"""
        return self.id
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary Schema (for lists)
# ============================================================================

class BusinessSummary(BaseModel):
    """
    Lightweight schema for business lists.
    Includes business_id for list views.
    """
    
    id: int
    business_name: str
    gstin: Optional[str]
    state: str
    product: str
    plan: str
    employee_count: int
    is_active: bool
    created_at: datetime
    
    @computed_field
    def business_id(self) -> int:
        """Expose primary key as business_id"""
        return self.id
    
    model_config = ConfigDict(from_attributes=True)