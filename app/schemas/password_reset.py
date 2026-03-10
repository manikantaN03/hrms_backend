"""
Password Reset Schemas
Request/Response models for forgot password flow
"""

from pydantic import BaseModel, EmailStr, field_validator
import re


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset"""
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class ForgotPasswordResponse(BaseModel):
    """Response after requesting password reset"""
    message: str
    email: str


class VerifyResetOTPRequest(BaseModel):
    """Request to verify password reset OTP"""
    email: EmailStr
    otp: str
    
    @field_validator('email')
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower().strip()
    
    @field_validator('otp')
    @classmethod
    def otp_must_be_6_digits(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be exactly 6 digits')
        return v


class VerifyResetOTPResponse(BaseModel):
    """Response after verifying OTP"""
    message: str
    email: str
    verified: bool


class ResetPasswordRequest(BaseModel):
    """Request to reset password"""
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str
    
    @field_validator('email')
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower().strip()
    
    @field_validator('otp')
    @classmethod
    def otp_must_be_6_digits(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be exactly 6 digits')
        return v
    
    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ResetPasswordResponse(BaseModel):
    """Response after password reset"""
    message: str
    email: str
    reset_at: str


class ResendResetOTPRequest(BaseModel):
    """Request to resend password reset OTP"""
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower().strip()
