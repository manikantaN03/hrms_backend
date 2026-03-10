"""
User Schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

from .enums import UserRole, UserStatus


# ============================================================================
# Admin Management Schemas
# ============================================================================

class AdminCreateRequest(BaseModel):
    """Request schema for creating admin accounts."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Company/Admin name")
    email: EmailStr
    account_url: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., min_length=1)
    website: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=8)
    confirm_password: str
    address: Optional[str] = Field(None, max_length=500)
    plan_name: str
    plan_type: str
    currency: str = "USD"
    language: str = "English"
    status: UserStatus = UserStatus.ACTIVE
    profile_image: Optional[str] = None
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value, info):
        """Ensure password and confirm_password match."""
        if 'password' in info.data and value != info.data['password']:
            raise ValueError('Passwords do not match')
        return value
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, value):
        """Ensure phone number is not empty."""
        if not value or not value.strip():
            raise ValueError('Phone number is required')
        return value


class AdminUpdateRequest(BaseModel):
    """Request schema for updating admin accounts."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    account_url: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., min_length=1)
    website: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, description="Leave empty to keep current")
    address: Optional[str] = Field(None, max_length=500)
    plan_name: str
    plan_type: str
    currency: str = "USD"
    language: str = "English"
    status: UserStatus
    profile_image: Optional[str] = None


class AdminResponse(BaseModel):
    """Response schema for admin accounts."""
    
    id: int
    name: str
    email: str
    role: UserRole
    status: UserStatus
    account_url: Optional[str] = None
    phone_number: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    plan_name: Optional[str] = None
    plan_type: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: datetime
    
    # Computed fields for frontend compatibility
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @classmethod
    def from_user(cls, user):
        """Create AdminResponse from User model with computed fields"""
        # Split name into first_name and last_name
        first_name = None
        last_name = None
        if user.name:
            name_parts = user.name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        return cls(
            id=user.id,
            name=user.name or "",
            email=user.email,
            role=user.role,
            status=user.status,
            account_url=user.account_url,
            phone_number=user.phone_number,
            phone=user.phone,
            mobile=user.mobile,
            website=user.website,
            address=user.address,
            country=user.country,
            state=user.state,
            city=user.city,
            postal_code=user.postal_code,
            plan_name=user.plan_name,
            plan_type=user.plan_type,
            currency=user.currency,
            language=user.language,
            profile_image=user.profile_image,
            created_at=user.created_at,
            first_name=first_name,
            last_name=last_name
        )
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Basic user response without sensitive data."""
    
    id: int
    name: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# User Registration Schemas
# ============================================================================

class UnifiedRegistrationRequest(BaseModel):
    """
    Admin registration schema.
    
    Important: Only ADMIN users can register.
    Company details are NOT required during registration.
    """
    
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Admin's first name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Admin's last name"
    )
    email: EmailStr = Field(..., description="Unique email address")
    mobile: str = Field(..., description="10-digit mobile number")
    
    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        """Validate 10-digit mobile number."""
        cleaned = value.replace(" ", "").replace("-", "")
        
        if not cleaned.isdigit():
            raise ValueError('Mobile number must contain only digits')
        
        if len(cleaned) != 10:
            raise ValueError('Mobile number must be exactly 10 digits')
        
        return cleaned
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate names contain only letters and spaces."""
        if not value.replace(" ", "").isalpha():
            raise ValueError('Name must contain only letters and spaces')
        return value.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, value: EmailStr) -> EmailStr:
        """Prevent disposable email domains."""
        forbidden_domains = ['tempmail.com', 'throwaway.email', 'guerrillamail.com']
        domain = value.split('@')[1].lower()
        
        if domain in forbidden_domains:
            raise ValueError(f'Email domain {domain} is not allowed')
        
        return value
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "mobile": "9876543210"
                }
            ]
        }
    )


class ChangeUserRoleRequest(BaseModel):
    """
    Request schema for changing user role.
    
    Note: Since only 2 roles exist (SUPERADMIN, ADMIN),
    role changes are limited.
    """
    new_role: UserRole = Field(..., description="New role (only ADMIN allowed)")
    
    @field_validator('new_role')
    @classmethod
    def validate_role(cls, value: UserRole) -> UserRole:
        """Prevent assigning SUPERADMIN role via API."""
        if value == UserRole.SUPERADMIN:
            raise ValueError('Cannot assign SUPERADMIN role via API')
        return value
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_role": "admin"
            }
        }
    )

class UserRegistrationResponse(BaseModel):
    """Response after successful registration."""
    
    message: str
    user: UserResponse
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# OTP Verification Schemas
# ============================================================================

class VerifyOTPRequest(BaseModel):
    """Request schema for OTP verification."""
    
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit code")
    
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, value: str) -> str:
        """Validate OTP format."""
        if not value.isdigit():
            raise ValueError('OTP must contain only digits')
        if len(value) != 6:
            raise ValueError('OTP must be exactly 6 digits')
        return value
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }
    )


class VerifyOTPResponse(BaseModel):
    """Response after successful OTP verification."""
    
    message: str
    email: str
    email_verified: bool = True
    redirect_to_password_creation: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class ResendOTPRequest(BaseModel):
    """Request schema for resending OTP."""
    
    email: EmailStr
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com"}
        }
    )


# ============================================================================
# Password Creation Schemas
# ============================================================================

class SetPasswordRequest(BaseModel):
    """Request schema for setting password after OTP verification."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm password")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value, info):
        """Ensure passwords match."""
        if 'password' in info.data and value != info.data['password']:
            raise ValueError('Passwords do not match')
        return value
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Enforce strong password requirements."""
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        if not any(c.isupper() for c in value):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in value):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in value):
            raise ValueError('Password must contain at least one number')
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in value):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common passwords
        common_passwords = ['password', '12345678', 'qwerty', 'admin123']
        if value.lower() in common_passwords:
            raise ValueError('Password is too common. Choose a stronger password.')
        
        return value
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass@123",
                "confirm_password": "SecurePass@123"
            }
        }
    )


class SetPasswordResponse(BaseModel):
    """Response after successful password creation."""
    
    message: str
    email: str
    can_login: bool = True
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Role Management Schemas
# ============================================================================

class ChangeUserRoleRequest(BaseModel):
    """Request schema for changing user role (superadmin only)."""
    
    new_role: UserRole = Field(..., description="New role for the user")
    
    @field_validator('new_role')
    @classmethod
    def validate_role(cls, value: UserRole) -> UserRole:
        """Prevent assigning SUPERADMIN role via API."""
        if value == UserRole.SUPERADMIN:
            raise ValueError('Cannot assign SUPERADMIN role via API')
        return value
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"new_role": "admin"}
        }
    )