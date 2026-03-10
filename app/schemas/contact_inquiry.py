"""
Contact Inquiry Schemas
Pydantic schemas for contact/demo request validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.contact_inquiry import InquiryStatus, InquirySource


class ContactInquiryCreate(BaseModel):
    """Schema for creating a contact inquiry"""
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of the person")
    email: EmailStr = Field(..., description="Valid email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    number_of_employees: str = Field(..., description="Number of employees range")
    industry: Optional[str] = Field(None, max_length=100, description="Industry type")
    message: Optional[str] = Field(None, max_length=2000, description="Message or requirement")
    source: Optional[InquirySource] = Field(InquirySource.LANDING_PAGE, description="Source of inquiry")
    
    # Tracking fields (optional, set by backend)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer_url: Optional[str] = None

    @validator('full_name')
    def validate_full_name(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Full name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        return v.strip()

    @validator('company_name')
    def validate_company_name(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Company name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters')
        return v.strip()

    @validator('number_of_employees')
    def validate_employees(cls, v):
        valid_ranges = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+']
        if v not in valid_ranges:
            raise ValueError(f'Invalid employee range. Must be one of: {", ".join(valid_ranges)}')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Remove common phone formatting characters
            cleaned = v.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if len(cleaned) < 10:
                raise ValueError('Phone number must be at least 10 digits')
        return v

    @validator('message')
    def validate_message(cls, v):
        if v and len(v.strip()) > 2000:
            raise ValueError('Message cannot exceed 2000 characters')
        return v.strip() if v else None

    class Config:
        from_attributes = True


class ContactInquiryUpdate(BaseModel):
    """Schema for updating a contact inquiry"""
    status: Optional[InquiryStatus] = None
    assigned_to_id: Optional[int] = None
    contacted_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=5000)
    is_spam: Optional[bool] = None
    is_priority: Optional[bool] = None

    class Config:
        from_attributes = True


class ContactInquiryResponse(BaseModel):
    """Schema for contact inquiry response"""
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    company_name: str
    number_of_employees: str
    industry: Optional[str]
    message: Optional[str]
    source: InquirySource
    status: InquiryStatus
    assigned_to_id: Optional[int]
    ip_address: Optional[str]
    contacted_at: Optional[datetime]
    follow_up_date: Optional[datetime]
    notes: Optional[str]
    is_spam: bool
    is_priority: bool
    email_sent: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactInquiryList(BaseModel):
    """Schema for listing contact inquiries"""
    total: int
    items: list[ContactInquiryResponse]

    class Config:
        from_attributes = True


class ContactInquiryStats(BaseModel):
    """Schema for contact inquiry statistics"""
    total_inquiries: int
    new_inquiries: int
    contacted_inquiries: int
    qualified_inquiries: int
    converted_inquiries: int
    spam_inquiries: int
    priority_inquiries: int
    today_inquiries: int
    this_week_inquiries: int
    this_month_inquiries: int

    class Config:
        from_attributes = True
