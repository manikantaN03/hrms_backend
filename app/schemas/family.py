"""
Family Member Pydantic Schemas for Employee Family Management
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date
from enum import Enum


class RelationType(str, Enum):
    """Enum for family relationship types"""
    FATHER = "Father"
    MOTHER = "Mother"
    BROTHER = "Brother"
    SISTER = "Sister"
    SPOUSE = "Spouse"
    SON = "Son"
    DAUGHTER = "Daughter"
    GRAND_FATHER = "Grand Father"
    GRAND_MOTHER = "Grand Mother"


class RelationTypeOption(BaseModel):
    """Relation type option for frontend dropdown"""
    value: str
    label: str


class FamilyMemberCreateRequest(BaseModel):
    """Schema for creating a new family member"""
    relation: RelationType = Field(..., description="Relationship type")
    name: str = Field(..., min_length=1, max_length=100, description="Family member name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    is_dependent: bool = Field(default=False, description="Is this person a dependent")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required and cannot be empty')
        return v.strip()

    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.strip()) > 0:
            # Basic phone validation
            phone_clean = v.strip()
            if len(phone_clean) < 10:
                raise ValueError('Phone number must be at least 10 digits')
            return phone_clean
        return v

    @validator('email')
    def validate_email(cls, v):
        if v and len(v.strip()) > 0:
            email_clean = v.strip().lower()
            if '@' not in email_clean or '.' not in email_clean:
                raise ValueError('Invalid email format')
            return email_clean
        return v

    class Config:
        use_enum_values = True


class FamilyMemberUpdateRequest(BaseModel):
    """Schema for updating a family member"""
    relation: RelationType = Field(..., description="Relationship type")
    name: str = Field(..., min_length=1, max_length=100, description="Family member name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    is_dependent: bool = Field(default=False, description="Is this person a dependent")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required and cannot be empty')
        return v.strip()

    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.strip()) > 0:
            phone_clean = v.strip()
            if len(phone_clean) < 10:
                raise ValueError('Phone number must be at least 10 digits')
            return phone_clean
        return v

    @validator('email')
    def validate_email(cls, v):
        if v and len(v.strip()) > 0:
            email_clean = v.strip().lower()
            if '@' not in email_clean or '.' not in email_clean:
                raise ValueError('Invalid email format')
            return email_clean
        return v

    class Config:
        use_enum_values = True


class FamilyMemberResponse(BaseModel):
    """Schema for family member response"""
    id: int
    relation: str
    name: str
    phone: str
    email: str
    notes: str
    date_of_birth: Optional[str] = None
    dob: str = ""
    is_dependent: bool
    created_at: Optional[str] = None


class FamilyMemberCreateResponse(BaseModel):
    """Schema for family member creation response"""
    success: bool
    message: str
    member: FamilyMemberResponse


class FamilyMemberUpdateResponse(BaseModel):
    """Schema for family member update response"""
    success: bool
    message: str
    member: FamilyMemberResponse


class FamilyMemberDeleteResponse(BaseModel):
    """Schema for family member deletion response"""
    success: bool
    message: str


class EmployeeFamilyResponse(BaseModel):
    """Schema for employee family information response"""
    id: int
    name: str
    code: str
    family_members: List[FamilyMemberResponse]
    total_members: int
    relation_types: List[RelationTypeOption]