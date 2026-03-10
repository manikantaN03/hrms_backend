from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class TDS24QCreate(BaseModel):
    # General Info
    deductorType: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        alias="deductorType",
        description="Type of deductor (Company, Government, etc.)"
    )
    sectionCode: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        alias="sectionCode",
        description="TDS section code (92A, 92B, 92C)"
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State (mandatory for State Govt bodies)"
    )
    ministry: Optional[str] = Field(
        None,
        max_length=100,
        description="Ministry (mandatory for Central Govt bodies)"
    )
    ministryName: Optional[str] = Field(
        None, 
        max_length=200,
        alias="ministryName",
        description="Ministry name if 'Others' selected"
    )
    AINNumber: Optional[str] = Field(
        None, 
        max_length=50,
        alias="AINNumber",
        description="AIN Number for government bodies"
    )
    PAOCode: Optional[str] = Field(
        None, 
        max_length=50,
        alias="PAOCode",
        description="PAO Code for government bodies"
    )
    PAORegistration: Optional[str] = Field(
        None, 
        max_length=100,
        alias="PAORegistration",
        description="PAO Registration number"
    )
    DDOCode: Optional[str] = Field(
        None, 
        max_length=50,
        alias="DDOCode",
        description="DDO Code for government bodies"
    )
    DDORegistration: Optional[str] = Field(
        None, 
        max_length=100,
        alias="DDORegistration",
        description="DDO Registration number"
    )
    
    # Employer Details
    employerName: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        alias="employerName",
        description="Employer/Company name"
    )
    branch: str = Field(
        ..., 
        min_length=1,
        max_length=200,
        description="Branch or division name"
    )
    address1: str = Field(
        ..., 
        min_length=1,
        max_length=200,
        description="Address line 1"
    )
    address2: Optional[str] = Field(None, max_length=200)
    address3: Optional[str] = Field(None, max_length=200)
    address4: Optional[str] = Field(None, max_length=200)
    address5: Optional[str] = Field(None, max_length=200)
    employerState: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        alias="employerState",
        description="Employer state"
    )
    pin: str = Field(
        ..., 
        min_length=6,
        max_length=10,
        description="PIN code"
    )
    pan: str = Field(
        ..., 
        min_length=10, 
        max_length=10,
        description="PAN number (10 characters)"
    )
    tan: str = Field(
        ..., 
        min_length=10, 
        max_length=10,
        description="TAN number (10 characters)"
    )
    email: EmailStr = Field(..., description="Primary email address")
    stdCode: Optional[str] = Field(
        None, 
        max_length=10,
        alias="stdCode",
        description="STD code"
    )
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    altEmail: Optional[EmailStr] = Field(
        None, 
        alias="altEmail",
        description="Alternate email address"
    )
    altStdCode: Optional[str] = Field(
        None, 
        max_length=10,
        alias="altStdCode",
        description="Alternate STD code"
    )
    altPhone: Optional[str] = Field(None, max_length=20, alias="altPhone")
    gst: Optional[str] = Field(
        None, 
        max_length=15,
        description="GST number (15 characters)"
    )
    
    # Responsible Person Details
    name: str = Field(
        ..., 
        min_length=1,
        max_length=200,
        description="Responsible person name"
    )
    designation: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="Designation"
    )
    resAddress1: str = Field(
        ..., 
        min_length=1,
        max_length=200,
        alias="resAddress1",
        description="Responsible person address line 1"
    )
    resAddress2: Optional[str] = Field(None, max_length=200, alias="resAddress2")
    resAddress3: Optional[str] = Field(None, max_length=200, alias="resAddress3")
    resAddress4: Optional[str] = Field(None, max_length=200, alias="resAddress4")
    resAddress5: Optional[str] = Field(None, max_length=200, alias="resAddress5")
    resState: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        alias="resState",
        description="Responsible person state"
    )
    resPin: str = Field(
        ..., 
        min_length=6,
        max_length=10,
        alias="resPin",
        description="Responsible person PIN code"
    )
    resPan: str = Field(
        ..., 
        min_length=10, 
        max_length=10, 
        alias="resPan",
        description="Responsible person PAN (10 characters)"
    )
    resMobile: str = Field(
        ..., 
        min_length=10,
        max_length=15,
        alias="resMobile",
        description="Responsible person mobile number"
    )
    resEmail: EmailStr = Field(
        ..., 
        alias="resEmail",
        description="Responsible person email"
    )
    resStdCode: Optional[str] = Field(
        None, 
        max_length=10,
        alias="resStdCode",
        description="Responsible person STD code"
    )
    resPhone: Optional[str] = Field(None, max_length=20, alias="resPhone")
    resAltEmail: Optional[EmailStr] = Field(None, alias="resAltEmail")
    resAltStdCode: Optional[str] = Field(None, max_length=10, alias="resAltStdCode")
    resAltPhone: Optional[str] = Field(None, max_length=20, alias="resAltPhone")
    
    @field_validator('pan', 'resPan')
    @classmethod
    def validate_pan(cls, v: str) -> str:
        """Validate PAN format: 5 letters, 4 digits, 1 letter"""
        if not v:
            raise ValueError("PAN cannot be empty")
        
        v = v.upper().strip()
        
        if len(v) != 10:
            raise ValueError("PAN must be exactly 10 characters")
        
        # PAN format: AAAAA9999A
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', v):
            raise ValueError("Invalid PAN format. Expected: 5 letters, 4 digits, 1 letter")
        
        return v
    
    @field_validator('tan')
    @classmethod
    def validate_tan(cls, v: str) -> str:
        """Validate TAN format: 4 letters, 5 digits, 1 letter"""
        if not v:
            raise ValueError("TAN cannot be empty")
        
        v = v.upper().strip()
        
        if len(v) != 10:
            raise ValueError("TAN must be exactly 10 characters")
        
        # TAN format: AAAA99999A
        if not re.match(r'^[A-Z]{4}[0-9]{5}[A-Z]$', v):
            raise ValueError("Invalid TAN format. Expected: 4 letters, 5 digits, 1 letter")
        
        return v
    
    @field_validator('gst')
    @classmethod
    def validate_gst(cls, v: Optional[str]) -> Optional[str]:
        """Validate GST format if provided"""
        if not v:
            return v
        
        v = v.upper().strip()
        
        if len(v) != 15:
            raise ValueError("GST must be exactly 15 characters")
        
        # GST format: 2 digits (state code) + 10 char PAN + 1 digit + 1 letter + 1 digit/letter
        if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]{3}$', v):
            raise ValueError("Invalid GST format")
        
        return v
    
    @field_validator('pin', 'resPin')
    @classmethod
    def validate_pin(cls, v: str) -> str:
        """Validate PIN code format"""
        if not v:
            raise ValueError("PIN code cannot be empty")
        
        v = v.strip()
        
        if not re.match(r'^[0-9]{6}$', v):
            raise ValueError("PIN code must be 6 digits")
        
        return v
    
    @field_validator('resMobile')
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        """Validate mobile number format"""
        if not v:
            raise ValueError("Mobile number cannot be empty")
        
        v = v.strip()
        
        if not re.match(r'^[0-9]{10,15}$', v):
            raise ValueError("Mobile number must be 10-15 digits")
        
        return v
    
    class Config:
        populate_by_name = True


class TDS24QUpdate(BaseModel):
    deductorType: Optional[str] = Field(None, max_length=100)
    sectionCode: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    ministry: Optional[str] = Field(None, max_length=100)
    ministryName: Optional[str] = Field(None, max_length=200)
    AINNumber: Optional[str] = Field(None, max_length=50)
    PAOCode: Optional[str] = Field(None, max_length=50)
    PAORegistration: Optional[str] = Field(None, max_length=100)
    DDOCode: Optional[str] = Field(None, max_length=50)
    DDORegistration: Optional[str] = Field(None, max_length=100)
    employerName: Optional[str] = Field(None, max_length=200)
    branch: Optional[str] = Field(None, max_length=200)
    address1: Optional[str] = Field(None, max_length=200)
    address2: Optional[str] = Field(None, max_length=200)
    address3: Optional[str] = Field(None, max_length=200)
    address4: Optional[str] = Field(None, max_length=200)
    address5: Optional[str] = Field(None, max_length=200)
    employerState: Optional[str] = Field(None, max_length=100)
    pin: Optional[str] = Field(None, max_length=10)
    pan: Optional[str] = Field(None, max_length=10)
    tan: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=100)
    stdCode: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    altEmail: Optional[str] = Field(None, max_length=100)
    altStdCode: Optional[str] = Field(None, max_length=10)
    altPhone: Optional[str] = Field(None, max_length=20)
    gst: Optional[str] = Field(None, max_length=15)
    name: Optional[str] = Field(None, max_length=200)
    designation: Optional[str] = Field(None, max_length=100)
    resAddress1: Optional[str] = Field(None, max_length=200)
    resAddress2: Optional[str] = Field(None, max_length=200)
    resAddress3: Optional[str] = Field(None, max_length=200)
    resAddress4: Optional[str] = Field(None, max_length=200)
    resAddress5: Optional[str] = Field(None, max_length=200)
    resState: Optional[str] = Field(None, max_length=100)
    resPin: Optional[str] = Field(None, max_length=10)
    resPan: Optional[str] = Field(None, max_length=10)
    resMobile: Optional[str] = Field(None, max_length=15)
    resEmail: Optional[str] = Field(None, max_length=100)
    resStdCode: Optional[str] = Field(None, max_length=10)
    resPhone: Optional[str] = Field(None, max_length=20)
    resAltEmail: Optional[str] = Field(None, max_length=100)
    resAltStdCode: Optional[str] = Field(None, max_length=10)
    resAltPhone: Optional[str] = Field(None, max_length=20)
    
    class Config:
        populate_by_name = True


class TDS24QResponse(BaseModel):
    id: int = Field(..., gt=0, description="TDS 24Q record ID")
    business_id: int = Field(..., gt=0, description="Business ID")
    
    # General Info
    deductorType: str
    sectionCode: str
    state: Optional[str]
    ministry: Optional[str]
    ministryName: Optional[str]
    AINNumber: Optional[str]
    PAOCode: Optional[str]
    PAORegistration: Optional[str]
    DDOCode: Optional[str]
    DDORegistration: Optional[str]
    
    # Employer Details
    employerName: str
    branch: str
    address1: str
    address2: Optional[str]
    address3: Optional[str]
    address4: Optional[str]
    address5: Optional[str]
    employerState: str
    pin: str
    pan: str
    tan: str
    email: str
    stdCode: Optional[str]
    phone: Optional[str]
    altEmail: Optional[str]
    altStdCode: Optional[str]
    altPhone: Optional[str]
    gst: Optional[str]
    
    # Responsible Person Details
    name: str
    designation: str
    resAddress1: str
    resAddress2: Optional[str]
    resAddress3: Optional[str]
    resAddress4: Optional[str]
    resAddress5: Optional[str]
    resState: str
    resPin: str
    resPan: str
    resMobile: str
    resEmail: str
    resStdCode: Optional[str]
    resPhone: Optional[str]
    resAltEmail: Optional[str]
    resAltStdCode: Optional[str]
    resAltPhone: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
