"""
Employee Basic Info Schemas with Mandatory Validation
NO EMPTY REQUEST BODIES ALLOWED
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import date, datetime
from fastapi import HTTPException, status


class EmployeeBasicInfoUpdate(BaseModel):
    """
    Schema for updating employee basic information
    🚨 MANDATORY VALIDATION: Empty {} request bodies are NOT allowed
    At least one field must be provided for update
    """
    firstName: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    lastName: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    middleName: Optional[str] = Field(None, max_length=100, description="Middle name")
    dateOfBirth: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    gender: Optional[str] = Field(None, description="Gender (male/female/other)")
    maritalStatus: Optional[str] = Field(None, description="Marital status (single/married/divorced/widowed)")
    bloodGroup: Optional[str] = Field(None, max_length=10, description="Blood group")
    nationality: Optional[str] = Field(None, max_length=100, description="Nationality")
    religion: Optional[str] = Field(None, max_length=100, description="Religion")
    fatherName: Optional[str] = Field(None, max_length=100, description="Father's name")
    motherName: Optional[str] = Field(None, max_length=100, description="Mother's name")
    personalEmail: Optional[EmailStr] = Field(None, description="Personal email - must be valid email format")
    personalPhone: Optional[str] = Field(None, min_length=10, max_length=15, description="Personal phone")
    alternatePhone: Optional[str] = Field(None, min_length=10, max_length=15, description="Alternate phone")
    currentAddress: Optional[str] = Field(None, max_length=500, description="Current address")
    permanentAddress: Optional[str] = Field(None, max_length=500, description="Permanent address")
    panNumber: Optional[str] = Field(None, min_length=10, max_length=10, description="PAN number (10 characters)")
    aadharNumber: Optional[str] = Field(None, min_length=12, max_length=12, description="Aadhar number (12 digits)")
    passportNumber: Optional[str] = Field(None, max_length=20, description="Passport number")
    passportExpiry: Optional[str] = Field(None, description="Passport expiry date in YYYY-MM-DD format")
    drivingLicense: Optional[str] = Field(None, max_length=20, description="Driving license number")
    licenseExpiry: Optional[str] = Field(None, description="License expiry date in YYYY-MM-DD format")
    employeeCode: Optional[str] = Field(None, min_length=1, max_length=50, description="Employee code")
    biometricCode: Optional[str] = Field(None, max_length=20, description="Biometric code")
    emergencyContact: Optional[str] = Field(None, min_length=1, max_length=100, description="Emergency contact name")
    emergencyPhone: Optional[str] = Field(None, min_length=10, max_length=15, description="Emergency contact phone")
    
    @validator('dateOfBirth', 'passportExpiry', 'licenseExpiry')
    def validate_dates(cls, v):
        """Validate date format"""
        if v and v.strip():
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('personalPhone', 'alternatePhone', 'emergencyPhone')
    def validate_phone_numbers(cls, v):
        """Validate phone numbers contain only digits"""
        if v and v.strip():
            # Remove any spaces or special characters for validation
            clean_phone = ''.join(filter(str.isdigit, v))
            if len(clean_phone) < 10:
                raise ValueError('Phone number must be at least 10 digits')
            return v
        return v
    
    @validator('aadharNumber')
    def validate_aadhar(cls, v):
        """Validate Aadhar number format"""
        if v and v.strip():
            clean_aadhar = ''.join(filter(str.isdigit, v))
            if len(clean_aadhar) != 12:
                raise ValueError('Aadhar number must be exactly 12 digits')
            return clean_aadhar
        return v
    
    @validator('panNumber')
    def validate_pan(cls, v):
        """Validate PAN number format"""
        if v and v.strip():
            v = v.upper().strip()
            if len(v) != 10:
                raise ValueError('PAN number must be exactly 10 characters')
            # Basic PAN format validation: 5 letters, 4 digits, 1 letter
            if not (v[:5].isalpha() and v[5:9].isdigit() and v[9].isalpha()):
                raise ValueError('PAN number format is invalid (should be ABCDE1234F)')
            return v
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender values"""
        if v and v.strip():
            valid_genders = ['male', 'female', 'other']
            if v.lower() not in valid_genders:
                raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
            return v.lower()
        return v
    
    @validator('maritalStatus')
    def validate_marital_status(cls, v):
        """Validate marital status values"""
        if v and v.strip():
            valid_statuses = ['single', 'married', 'divorced', 'widowed']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Marital status must be one of: {", ".join(valid_statuses)}')
            return v.lower()
        return v
    
    def validate_non_empty_request(self):
        """
        Custom validation to ensure at least one field is provided
        This prevents empty {} request bodies
        """
        data_dict = self.dict(exclude_unset=True)
        non_none_values = {k: v for k, v in data_dict.items() if v is not None and str(v).strip()}
        
        if not non_none_values:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body cannot be empty. At least one valid field must be provided for update. Empty {} request bodies are not allowed."
            )
        
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "firstName": "John",
                "lastName": "Doe",
                "middleName": "Smith",
                "dateOfBirth": "1990-01-01",
                "gender": "male",
                "maritalStatus": "single",
                "bloodGroup": "O+",
                "nationality": "Indian",
                "religion": "Hindu",
                "personalEmail": "john.doe@example.com",
                "personalPhone": "9876543210",
                "alternatePhone": "9876543211",
                "currentAddress": "123 Main Street, City",
                "permanentAddress": "456 Home Street, Hometown",
                "panNumber": "ABCDE1234F",
                "aadharNumber": "123456789012",
                "employeeCode": "EMP001",
                "biometricCode": "BIO001",
                "emergencyContact": "Jane Doe",
                "emergencyPhone": "9876543212"
            }
        }


class EmployeeBasicInfoResponse(BaseModel):
    """Schema for employee basic info response"""
    success: bool
    message: str
    employee: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Employee basic information updated successfully",
                "employee": {
                    "id": 1,
                    "name": "John Doe",
                    "code": "EMP001",
                    "email": "john.doe@example.com",
                    "mobile": "9876543210"
                }
            }
        }