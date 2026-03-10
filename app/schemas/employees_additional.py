"""
Additional Pydantic schemas for Employees endpoints
Replaces dict with proper typed schemas for Swagger/OpenAPI documentation
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date


class EmployeeBasicInfoUpdateRequest(BaseModel):
    """Schema for updating employee basic information"""
    
    firstName: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Employee's first name",
        example="John"
    )
    lastName: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Employee's last name",
        example="Doe"
    )
    middleName: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Employee's middle name",
        example="Michael"
    )
    dateOfBirth: Optional[str] = Field(
        default=None,
        description="Date of birth in YYYY-MM-DD format",
        example="1990-01-15"
    )
    gender: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Gender (male/female/other)",
        example="male"
    )
    maritalStatus: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Marital status (single/married/divorced/widowed)",
        example="married"
    )
    bloodGroup: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Blood group",
        example="O+"
    )
    nationality: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Nationality",
        example="Indian"
    )
    religion: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Religion",
        example="Hindu"
    )
    personalEmail: Optional[EmailStr] = Field(
        default=None,
        description="Personal email address",
        example="john.doe@personal.com"
    )
    personalPhone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Personal phone number",
        example="+91-9876543210"
    )
    alternatePhone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Alternate phone number",
        example="+91-9876543211"
    )
    employeeCode: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Employee code",
        example="EMP001"
    )
    biometricCode: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Biometric code",
        example="BIO001"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "firstName": "John",
                "lastName": "Doe",
                "middleName": "Michael",
                "dateOfBirth": "1990-01-15",
                "gender": "male",
                "maritalStatus": "married",
                "bloodGroup": "O+",
                "nationality": "Indian",
                "religion": "Hindu",
                "personalEmail": "john.doe@personal.com",
                "personalPhone": "+91-9876543210",
                "alternatePhone": "+91-9876543211",
                "employeeCode": "EMP001",
                "biometricCode": "BIO001"
            }
        }
