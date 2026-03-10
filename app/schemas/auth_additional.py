"""
Additional Pydantic schemas for Auth endpoints
Replaces dict with proper typed schemas for Swagger/OpenAPI documentation
"""

from pydantic import BaseModel, Field, EmailStr


class SendOTPRequest(BaseModel):
    """Schema for sending OTP to user's email"""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="user@example.com"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }
