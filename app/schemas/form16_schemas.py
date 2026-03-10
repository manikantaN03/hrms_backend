from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

# ---------- PERSON RESPONSIBLE ----------
class PersonResponsibleCreate(BaseModel):
    fullName: str = Field(..., min_length=1, max_length=50, description="Full name of the person responsible")
    designation: str = Field(..., min_length=1, max_length=50, description="Designation of the person")
    fatherName: str = Field(..., min_length=1, max_length=50, description="Father's name")
    signaturePath: Optional[str] = Field(None, max_length=255, description="Path to signature image")
    business_id: Optional[int] = Field(None, gt=0, description="Business ID")

    @field_validator('fullName', 'designation', 'fatherName')
    @classmethod
    def validate_not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace")
        return v.strip()


class PersonResponsibleResponse(BaseModel):
    id: int
    fullName: str
    designation: str
    fatherName: str
    signaturePath: Optional[str] = None
    business_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- EMPLOYER INFO ----------
class EmployerInfoCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Employer name")
    address1: Optional[str] = Field(None, max_length=512, description="Address line 1")
    address2: Optional[str] = Field(None, max_length=512, description="Address line 2")
    address3: Optional[str] = Field(None, max_length=512, description="Address line 3")
    placeOfIssue: Optional[str] = Field(None, max_length=255, description="Place of issue")

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Employer name cannot be empty or whitespace")
        return v.strip()

    @field_validator('address1', 'address2', 'address3', 'placeOfIssue')
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            return v.strip()
        return None


class EmployerInfoResponse(BaseModel):
    id: int
    name: str
    address1: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    placeOfIssue: Optional[str] = None
    business_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- CIT INFO ----------
class CITInfoCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="CIT office name")
    address1: Optional[str] = Field(None, max_length=512, description="Address line 1")
    address2: Optional[str] = Field(None, max_length=512, description="Address line 2")
    address3: Optional[str] = Field(None, max_length=512, description="Address line 3")

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("CIT name cannot be empty or whitespace")
        return v.strip()

    @field_validator('address1', 'address2', 'address3')
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            return v.strip()
        return None


class CITInfoResponse(BaseModel):
    id: int
    name: str
    address1: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    business_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- EMPLOYER (Legacy/Alternate) ----------
class EmployerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Employer name")
    address1: Optional[str] = Field(None, max_length=512, description="Address line 1")
    address2: Optional[str] = Field(None, max_length=512, description="Address line 2")
    address3: Optional[str] = Field(None, max_length=512, description="Address line 3")
    placeOfIssue: Optional[str] = Field(None, max_length=255, description="Place of issue")

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Employer name cannot be empty or whitespace")
        return v.strip()

    @field_validator('address1', 'address2', 'address3', 'placeOfIssue')
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            return v.strip()
        return None


class EmployerResponse(BaseModel):
    id: int
    name: str
    address1: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    placeOfIssue: Optional[str] = None
    business_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
