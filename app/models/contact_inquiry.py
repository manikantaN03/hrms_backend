"""
Contact Inquiry Models
Database models for landing page contact/demo requests
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class InquiryStatus(str, enum.Enum):
    """Status of contact inquiry"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    CLOSED = "closed"
    SPAM = "spam"


class InquirySource(str, enum.Enum):
    """Source of inquiry"""
    LANDING_PAGE = "landing_page"
    CONTACT_FORM = "contact_form"
    DEMO_REQUEST = "demo_request"
    PHONE = "phone"
    EMAIL = "email"
    REFERRAL = "referral"


class ContactInquiry(Base):
    """Contact/Demo Request Model"""
    __tablename__ = "contact_inquiries"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contact Information
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    company_name = Column(String(255), nullable=False, index=True)
    
    # Company Details
    number_of_employees = Column(String(50), nullable=False)
    industry = Column(String(100), nullable=True)
    
    # Inquiry Details
    message = Column(Text, nullable=True)
    source = Column(SQLEnum(InquirySource, native_enum=False), nullable=False, default=InquirySource.LANDING_PAGE)
    
    # Status & Assignment
    status = Column(SQLEnum(InquiryStatus, native_enum=False), nullable=False, default=InquiryStatus.NEW)
    assigned_to_id = Column(Integer, nullable=True)  # Sales person ID
    
    # Tracking
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer_url = Column(String(500), nullable=True)
    
    # Follow-up
    contacted_at = Column(DateTime, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Flags
    is_spam = Column(Boolean, default=False)
    is_priority = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ContactInquiry(id={self.id}, name={self.full_name}, company={self.company_name}, status={self.status})>"
