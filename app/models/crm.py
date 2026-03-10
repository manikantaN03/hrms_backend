"""
CRM Models
Database models for Customer Relationship Management
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class ContactType(str, enum.Enum):
    LEAD = "lead"
    CUSTOMER = "customer"
    PROSPECT = "prospect"
    PARTNER = "partner"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class DealStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ActivityType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    NOTE = "note"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CRMCompany(Base):
    """CRM Company/Account model"""
    __tablename__ = "crm_companies"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255))
    phone = Column(String(20))
    phone2 = Column(String(20))  # Phone Number 2
    fax = Column(String(20))
    website = Column(String(255))
    ratings = Column(Numeric(2, 1), default=0.0)  # 1-5 star rating
    owner_id = Column(Integer, ForeignKey("users.id"))  # Company owner
    tags = Column(Text)  # JSON string for tags
    deals_info = Column(String(100))  # Deal information
    industry = Column(String(100))
    source = Column(String(100))  # Lead source
    currency = Column(String(10), default='USD')
    language = Column(String(50), default='English')
    about = Column(Text)  # Company description
    contact_person = Column(String(255))  # Contact person
    logo_url = Column(Text)  # Company logo (supports base64 images)
    
    # Address fields
    address = Column(Text)
    country = Column(String(100))
    state = Column(String(100))
    city = Column(String(100))
    postal_code = Column(String(20))  # zipcode
    
    # Social media fields
    facebook_url = Column(String(255))
    twitter_url = Column(String(255))
    linkedin_url = Column(String(255))
    skype_handle = Column(String(100))
    whatsapp = Column(String(20))
    instagram_url = Column(String(255))
    
    # Access control
    visibility = Column(String(20), default='private')  # public/private/selectPeople
    status = Column(String(20), default='Active')  # Active/Inactive
    
    # Legacy fields for compatibility
    annual_revenue = Column(Numeric(15, 2))
    employee_count = Column(Integer)
    description = Column(Text)  # Alias for about
    is_active = Column(Boolean, default=True)
    
    # Relationships
    business = relationship("Business", foreign_keys=[business_id])
    contacts = relationship("CRMContact", back_populates="company")
    deals = relationship("CRMDeal", back_populates="company")
    activities = relationship("CRMActivity", back_populates="company")
    owner = relationship("User", foreign_keys=[owner_id])
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))


class CRMContact(Base):
    """CRM Contact model"""
    __tablename__ = "crm_contacts"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    mobile = Column(String(20))
    job_title = Column(String(100))
    department = Column(String(100))
    contact_type = Column(Enum(ContactType), default=ContactType.LEAD)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Company relationship
    company_id = Column(Integer, ForeignKey("crm_companies.id"))
    company = relationship("CRMCompany", back_populates="contacts")
    
    # Lead information
    lead_source = Column(String(100))
    lead_status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    
    # Frontend required fields
    rating = Column(Integer, default=0)  # 0-5 star rating
    owner_id = Column(Integer, ForeignKey("users.id"))  # Contact owner
    tags = Column(Text)  # JSON string for tags array
    profile_image_url = Column(Text)  # Text field to support base64 images
    currency = Column(String(50), default='Rupees')
    language = Column(String(50), default='English')
    date_of_birth = Column(DateTime(timezone=True))
    industry = Column(String(100))
    deals_info = Column(String(100))  # Deal information
    visibility = Column(String(20), default='public')  # public/private/selectPeople
    status = Column(String(20), default='Active')  # Active/Inactive
    
    # Lead specific fields
    value = Column(Numeric(15, 2), default=0)  # Lead value for frontend display
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    location = Column(String(100), default='India')
    
    # Social media
    linkedin_url = Column(String(255))
    twitter_handle = Column(String(100))
    facebook_url = Column(String(255))
    instagram_url = Column(String(255))
    skype_handle = Column(String(100))
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    business = relationship("Business", foreign_keys=[business_id])
    deals = relationship("CRMDeal", back_populates="contact")
    activities = relationship("CRMActivity", back_populates="contact")
    owner = relationship("User", foreign_keys=[owner_id])
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class CRMDeal(Base):
    """CRM Deal/Opportunity model"""
    __tablename__ = "crm_deals"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    value = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD")
    stage = Column(Enum(DealStage), default=DealStage.PROSPECTING)
    probability = Column(Integer, default=0)  # 0-100%
    expected_close_date = Column(DateTime(timezone=True))
    actual_close_date = Column(DateTime(timezone=True))
    
    # Frontend required fields
    pipeline = Column(String(100))  # Sales, Marketing, Calls
    status = Column(String(50))  # Open, Won, Lost
    period = Column(String(100))  # Period description
    period_value = Column(String(100))  # Period value
    project = Column(String(255))  # Project name/type
    due_date = Column(DateTime(timezone=True))  # Due date (different from expected_close_date)
    assignee = Column(String(255))  # Assigned person
    tags = Column(Text)  # JSON string for tags
    followup_date = Column(DateTime(timezone=True))  # Follow-up date
    priority = Column(String(50))  # High, Medium, Low
    
    # Display fields for frontend compatibility
    initials = Column(String(10))  # Deal initials for display
    title = Column(String(255))  # Alias for name
    amount = Column(String(100))  # Formatted amount string
    email = Column(String(255))  # Contact email (denormalized)
    phone = Column(String(20))  # Contact phone (denormalized)
    location = Column(String(255))  # Location/project location
    owner = Column(String(255))  # Deal owner name
    owner_img = Column(String(255))  # Owner image URL
    progress = Column(String(10))  # Progress percentage as string
    date = Column(String(50))  # Formatted date string
    
    # Relationships
    business = relationship("Business", foreign_keys=[business_id])
    company_id = Column(Integer, ForeignKey("crm_companies.id"))
    company = relationship("CRMCompany", back_populates="deals")
    
    contact_id = Column(Integer, ForeignKey("crm_contacts.id"))
    contact = relationship("CRMContact", back_populates="deals")
    
    activities = relationship("CRMActivity", back_populates="deal")
    
    # Sales information
    lead_source = Column(String(100))
    competitor = Column(String(255))
    next_step = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_won = Column(Boolean, default=False)
    is_lost = Column(Boolean, default=False)
    lost_reason = Column(String(255))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))


class CRMActivity(Base):
    """CRM Activity model"""
    __tablename__ = "crm_activities"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    activity_type = Column(Enum(ActivityType), nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    
    # Scheduling
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    business = relationship("Business", foreign_keys=[business_id])
    company_id = Column(Integer, ForeignKey("crm_companies.id"))
    company = relationship("CRMCompany", back_populates="activities")
    
    contact_id = Column(Integer, ForeignKey("crm_contacts.id"))
    contact = relationship("CRMContact", back_populates="activities")
    
    deal_id = Column(Integer, ForeignKey("crm_deals.id"))
    deal = relationship("CRMDeal", back_populates="activities")
    
    # Additional fields
    location = Column(String(255))
    outcome = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True))
    
    # Frontend compatibility fields
    owner = Column(String(255))  # Owner name for display
    guests = Column(String(255))  # Guest names
    time = Column(String(10))  # Time in HH:MM format
    remainder = Column(String(255))  # Reminder text
    remainder_type = Column(String(50))  # Reminder type
    deals = Column(String(255))  # Deal names for display
    contacts = Column(String(255))  # Contact names for display
    companies = Column(String(255))  # Company names for display
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    @property
    def title(self):
        """Alias for subject for frontend compatibility"""
        return self.subject


class CRMPipeline(Base):
    """CRM Sales Pipeline model"""
    __tablename__ = "crm_pipelines"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Pipeline stages (JSON or separate table)
    stages_config = Column(Text)  # JSON string of stages configuration
    
    # Frontend required fields
    total_deal_value = Column(Numeric(15, 2), default=0)  # Total value of all deals in pipeline
    deal_count = Column(Integer, default=0)  # Number of deals in pipeline
    current_stage = Column(String(100))  # Current stage name
    stage_color = Column(String(20), default="primary")  # Bootstrap color class
    status = Column(String(20), default="Active")  # Active/Inactive
    
    # Relationships
    business = relationship("Business", foreign_keys=[business_id])
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))