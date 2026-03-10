"""
CRM Schemas
Pydantic models for CRM API validation and serialization
"""

from pydantic import BaseModel, EmailStr, Field, validator, computed_field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContactType(str, Enum):
    LEAD = "lead"
    CUSTOMER = "customer"
    PROSPECT = "prospect"
    PARTNER = "partner"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class DealStage(str, Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    NOTE = "note"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Company Schemas
class CRMCompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    phone2: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    ratings: Optional[Decimal] = Field(None, ge=0, le=5)
    owner_id: Optional[int] = None
    tags: Optional[str] = None  # JSON string for tags
    deals_info: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", max_length=10)
    language: str = Field(default="English", max_length=50)
    about: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None  # Company logo (supports base64 images)
    
    # Address fields
    address: Optional[str] = None
    country: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Social media fields
    facebook_url: Optional[str] = Field(None, max_length=255)
    twitter_url: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    skype_handle: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=20)
    instagram_url: Optional[str] = Field(None, max_length=255)
    
    # Access control
    visibility: str = Field(default="private", max_length=20)
    status: str = Field(default="Active", max_length=20)
    
    # Legacy fields for compatibility
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: bool = True


class CRMCompanyCreate(CRMCompanyBase):
    pass


class CRMCompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    phone2: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    ratings: Optional[Decimal] = Field(None, ge=0, le=5)
    owner_id: Optional[int] = None
    tags: Optional[str] = None  # JSON string for tags
    deals_info: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, max_length=10)
    language: Optional[str] = Field(None, max_length=50)
    about: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None  # Company logo (supports base64 images)
    
    # Address fields
    address: Optional[str] = None
    country: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Social media fields
    facebook_url: Optional[str] = Field(None, max_length=255)
    twitter_url: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    skype_handle: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=20)
    instagram_url: Optional[str] = Field(None, max_length=255)
    
    # Access control
    visibility: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    
    # Legacy fields for compatibility
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CRMCompanyResponse(CRMCompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    owner: Optional[Dict] = None  # Owner user information

    class Config:
        from_attributes = True
    
    @field_validator('owner', mode='before')
    @classmethod
    def serialize_owner(cls, v):
        """Convert User object to dictionary"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # Handle SQLAlchemy User object
        if hasattr(v, 'id'):
            return {
                "id": v.id,
                "name": getattr(v, 'name', getattr(v, 'email', 'Unknown')),
                "email": getattr(v, 'email', 'Unknown')
            }
        return None


# Contact Schemas
class CRMContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    contact_type: ContactType = ContactType.LEAD
    is_primary: bool = False
    is_active: bool = True
    company_id: Optional[int] = None
    lead_source: Optional[str] = Field(None, max_length=100)
    lead_status: LeadStatus = LeadStatus.NEW
    
    # Frontend required fields
    rating: int = Field(default=0, ge=0, le=5)
    owner_id: Optional[int] = None
    tags: Optional[str] = None  # JSON string for tags array
    profile_image_url: Optional[str] = None  # No max_length for base64 images
    currency: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[datetime] = None
    industry: Optional[str] = Field(None, max_length=100)
    deals_info: Optional[str] = Field(None, max_length=100)
    visibility: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    
    # Lead specific fields
    value: Optional[Decimal] = Field(None, ge=0)  # Lead value for frontend display
    
    # Address
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    
    # Social media
    linkedin_url: Optional[str] = Field(None, max_length=255)
    twitter_handle: Optional[str] = Field(None, max_length=100)
    facebook_url: Optional[str] = Field(None, max_length=255)
    instagram_url: Optional[str] = Field(None, max_length=255)
    skype_handle: Optional[str] = Field(None, max_length=100)
    
    # Notes
    notes: Optional[str] = None


class CRMContactCreate(CRMContactBase):
    @validator('currency', 'language', 'location', 'profile_image_url', 'visibility', 'status', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for optional fields"""
        if v == '':
            return None
        return v


class CRMContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    contact_type: Optional[ContactType] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    company_id: Optional[int] = None
    lead_source: Optional[str] = Field(None, max_length=100)
    lead_status: Optional[LeadStatus] = None
    
    # Frontend required fields
    rating: Optional[int] = Field(None, ge=0, le=5)
    owner_id: Optional[int] = None
    tags: Optional[str] = None  # JSON string for tags array
    profile_image_url: Optional[str] = None  # No max_length for base64 images
    currency: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[datetime] = None
    industry: Optional[str] = Field(None, max_length=100)
    deals_info: Optional[str] = Field(None, max_length=100)
    visibility: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    
    # Lead specific fields
    value: Optional[Decimal] = Field(None, ge=0)  # Lead value for frontend display
    
    # Address
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    
    # Social media
    linkedin_url: Optional[str] = Field(None, max_length=255)
    twitter_handle: Optional[str] = Field(None, max_length=100)
    facebook_url: Optional[str] = Field(None, max_length=255)
    instagram_url: Optional[str] = Field(None, max_length=255)
    skype_handle: Optional[str] = Field(None, max_length=100)
    
    # Notes
    notes: Optional[str] = None
    
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for all optional string fields"""
        if v == '':
            return None
        return v
    location: Optional[str] = Field(None, max_length=100)
    
    # Social media
    linkedin_url: Optional[str] = Field(None, max_length=255)
    twitter_handle: Optional[str] = Field(None, max_length=100)
    facebook_url: Optional[str] = Field(None, max_length=255)
    instagram_url: Optional[str] = Field(None, max_length=255)
    skype_handle: Optional[str] = Field(None, max_length=100)
    
    # Notes
    notes: Optional[str] = None


class CRMContactResponse(CRMContactBase):
    id: int
    full_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    company: Optional[CRMCompanyResponse] = None
    owner: Optional[Dict] = None  # Owner user information

    class Config:
        from_attributes = True
    
    @field_validator('owner', mode='before')
    @classmethod
    def serialize_owner(cls, v):
        """Convert User object to dictionary"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # Handle SQLAlchemy User object
        if hasattr(v, 'id'):
            return {
                "id": v.id,
                "name": getattr(v, 'name', getattr(v, 'email', 'Unknown')),
                "email": getattr(v, 'email', 'Unknown')
            }
        return None


# Deal Schemas
class CRMDealBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    value: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    stage: DealStage = DealStage.PROSPECTING
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    lead_source: Optional[str] = Field(None, max_length=100)
    competitor: Optional[str] = Field(None, max_length=255)
    next_step: Optional[str] = None
    is_active: bool = True
    
    # Frontend required fields
    pipeline: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    period: Optional[str] = Field(None, max_length=100)
    period_value: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=255)
    due_date: Optional[datetime] = None
    assignee: Optional[str] = Field(None, max_length=255)
    tags: Optional[str] = None  # JSON string for tags
    followup_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, max_length=50)
    
    # Display fields for frontend compatibility
    initials: Optional[str] = Field(None, max_length=10)
    title: Optional[str] = Field(None, max_length=255)
    amount: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    owner_img: Optional[str] = Field(None, max_length=255)
    progress: Optional[str] = Field(None, max_length=10)
    date: Optional[str] = Field(None, max_length=50)


class CRMDealCreate(CRMDealBase):
    pass


class CRMDealUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    stage: Optional[DealStage] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    lead_source: Optional[str] = Field(None, max_length=100)
    competitor: Optional[str] = Field(None, max_length=255)
    next_step: Optional[str] = None
    is_active: Optional[bool] = None
    is_won: Optional[bool] = None
    is_lost: Optional[bool] = None
    lost_reason: Optional[str] = Field(None, max_length=255)
    
    # Frontend required fields
    pipeline: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    period: Optional[str] = Field(None, max_length=100)
    period_value: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=255)
    due_date: Optional[datetime] = None
    assignee: Optional[str] = Field(None, max_length=255)
    tags: Optional[str] = None  # JSON string for tags
    followup_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, max_length=50)
    
    # Display fields for frontend compatibility
    initials: Optional[str] = Field(None, max_length=10)
    title: Optional[str] = Field(None, max_length=255)
    amount: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    owner_img: Optional[str] = Field(None, max_length=255)
    progress: Optional[str] = Field(None, max_length=10)
    date: Optional[str] = Field(None, max_length=50)


class CRMDealResponse(CRMDealBase):
    id: int
    actual_close_date: Optional[datetime] = None
    is_won: bool = False
    is_lost: bool = False
    lost_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    company: Optional[CRMCompanyResponse] = None
    contact: Optional[CRMContactResponse] = None

    class Config:
        from_attributes = True


# Activity Schemas
class CRMActivityBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: ActivityType
    priority: Priority = Priority.MEDIUM
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=255)
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    
    # Frontend compatibility fields (non-computed)
    owner: Optional[str] = Field(None, max_length=255)  # Owner name for display
    guests: Optional[str] = Field(None, max_length=255)  # Guest names
    time: Optional[str] = Field(None, max_length=10)  # Time in HH:MM format
    remainder: Optional[str] = Field(None, max_length=255)  # Reminder text
    remainder_type: Optional[str] = Field(None, max_length=50)  # Reminder type
    deals: Optional[str] = Field(None, max_length=255)  # Deal names
    contacts: Optional[str] = Field(None, max_length=255)  # Contact names  
    companies: Optional[str] = Field(None, max_length=255)  # Company names


class CRMActivityCreate(CRMActivityBase):
    pass


class CRMActivityUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: Optional[ActivityType] = None
    priority: Optional[Priority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=255)
    outcome: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    
    # Frontend compatibility fields (non-computed)
    owner: Optional[str] = Field(None, max_length=255)  # Owner name for display
    guests: Optional[str] = Field(None, max_length=255)  # Guest names
    time: Optional[str] = Field(None, max_length=10)  # Time in HH:MM format
    remainder: Optional[str] = Field(None, max_length=255)  # Reminder text
    remainder_type: Optional[str] = Field(None, max_length=50)  # Reminder type
    deals: Optional[str] = Field(None, max_length=255)  # Deal names
    contacts: Optional[str] = Field(None, max_length=255)  # Contact names  
    companies: Optional[str] = Field(None, max_length=255)  # Company names


class CRMActivityResponse(CRMActivityBase):
    id: int
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    company: Optional[CRMCompanyResponse] = None
    contact: Optional[CRMContactResponse] = None
    deal: Optional[CRMDealResponse] = None
    
    # Frontend display fields (will be computed)
    checked: bool = False  # For frontend checkbox

    class Config:
        from_attributes = True
    
    @computed_field
    @property
    def title(self) -> str:
        """Computed title from subject"""
        return self.subject
    
    @computed_field
    @property
    def type(self) -> str:
        """Computed type from activity_type"""
        activity_type_value = self.activity_type.value if hasattr(self.activity_type, 'value') else self.activity_type
        type_map = {
            "call": "Call",
            "email": "Email", 
            "meeting": "Meeting",
            "task": "Task",
            "note": "Note"
        }
        return type_map.get(activity_type_value, "Task")
    
    @computed_field
    @property
    def badgeClass(self) -> str:
        """Computed badge class from activity_type"""
        activity_type_value = self.activity_type.value if hasattr(self.activity_type, 'value') else self.activity_type
        badge_map = {
            "call": "badge-purple-transparent",
            "email": "badge-warning-transparent", 
            "meeting": "badge-pink-transparent",
            "task": "badge-info-transparent",
            "note": "badge-success-transparent"
        }
        return badge_map.get(activity_type_value, "badge-info-transparent")
    
    @computed_field
    @property
    def icon(self) -> str:
        """Computed icon from activity_type"""
        activity_type_value = self.activity_type.value if hasattr(self.activity_type, 'value') else self.activity_type
        icon_map = {
            "call": "ti ti-phone",
            "email": "ti ti-mail",
            "meeting": "ti ti-device-computer-camera",
            "task": "ti ti-subtask",
            "note": "ti ti-note"
        }
        return icon_map.get(activity_type_value, "ti ti-subtask")
    
    @computed_field
    @property
    def dueDate(self) -> Optional[str]:
        """Computed formatted due date"""
        if not self.due_date:
            return None
        try:
            if hasattr(self.due_date, 'strftime'):
                return self.due_date.strftime("%d %b %Y")
            else:
                # Handle string dates
                from datetime import datetime
                date_obj = datetime.fromisoformat(str(self.due_date).replace('Z', '+00:00'))
                return date_obj.strftime("%d %b %Y")
        except:
            return None
    
    @computed_field
    @property
    def createdDate(self) -> Optional[str]:
        """Computed formatted created date"""
        if not self.created_at:
            return None
        try:
            if hasattr(self.created_at, 'strftime'):
                return self.created_at.strftime("%d %b %Y")
            else:
                # Handle string dates
                from datetime import datetime
                date_obj = datetime.fromisoformat(str(self.created_at).replace('Z', '+00:00'))
                return date_obj.strftime("%d %b %Y")
        except:
            return None
        logger.debug(f"CRMActivityResponse.__init__ called with data keys: {list(data.keys())}")
        logger.debug(f"activity_type value: {data.get('activity_type')}")
        logger.debug(f"activity_type type: {type(data.get('activity_type'))}")
        
        # Set computed fields before calling parent __init__
        if 'subject' in data and not data.get('title'):
            data['title'] = data['subject']
        
        if 'activity_type' in data:
            activity_type = data['activity_type']
            
            # Handle both enum objects and string values
            if hasattr(activity_type, 'value'):
                activity_type_value = activity_type.value
            else:
                activity_type_value = activity_type
            
            logger.debug(f"activity_type_value: {activity_type_value}")
            
            # Set type based on activity_type value
            type_map = {
                "call": "Call",
                "email": "Email", 
                "meeting": "Meeting",
                "task": "Task",
                "note": "Note"
            }
            data['type'] = type_map.get(activity_type_value, "Task")
            logger.debug(f"Setting type to: {data['type']}")
            
            # Set badge class
            badge_map = {
                "call": "badge-purple-transparent",
                "email": "badge-warning-transparent", 
                "meeting": "badge-pink-transparent",
                "task": "badge-info-transparent",
                "note": "badge-success-transparent"
            }
            data['badgeClass'] = badge_map.get(activity_type_value, "badge-info-transparent")
            logger.debug(f"Setting badgeClass to: {data['badgeClass']}")
            
            # Set icon
            icon_map = {
                "call": "ti ti-phone",
                "email": "ti ti-mail",
                "meeting": "ti ti-device-computer-camera",
                "task": "ti ti-subtask",
                "note": "ti ti-note"
            }
            data['icon'] = icon_map.get(activity_type_value, "ti ti-subtask")
            logger.debug(f"Setting icon to: {data['icon']}")
        
        # Format dates
        if 'due_date' in data and data['due_date']:
            try:
                if hasattr(data['due_date'], 'strftime'):
                    data['dueDate'] = data['due_date'].strftime("%d %b %Y")
                else:
                    # Handle string dates
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(str(data['due_date']).replace('Z', '+00:00'))
                    data['dueDate'] = date_obj.strftime("%d %b %Y")
                logger.debug(f"Setting dueDate to: {data['dueDate']}")
            except Exception as e:
                logger.debug(f"Error formatting due_date: {e}")
                data['dueDate'] = None
        
        if 'created_at' in data and data['created_at']:
            try:
                if hasattr(data['created_at'], 'strftime'):
                    data['createdDate'] = data['created_at'].strftime("%d %b %Y")
                else:
                    # Handle string dates
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(str(data['created_at']).replace('Z', '+00:00'))
                    data['createdDate'] = date_obj.strftime("%d %b %Y")
                logger.debug(f"Setting createdDate to: {data['createdDate']}")
            except Exception as e:
                logger.debug(f"Error formatting created_at: {e}")
                data['createdDate'] = None
        
        super().__init__(**data)


# Pipeline Schemas
class CRMPipelineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    stages_config: Optional[str] = None
    
    # Frontend required fields
    total_deal_value: Optional[Decimal] = Field(None, ge=0)
    deal_count: int = Field(default=0, ge=0)
    current_stage: Optional[str] = Field(None, max_length=100)
    stage_color: str = Field(default="primary", max_length=20)
    status: str = Field(default="Active", max_length=20)


class CRMPipelineCreate(CRMPipelineBase):
    pass


class CRMPipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    stages_config: Optional[str] = None
    
    # Frontend required fields
    total_deal_value: Optional[Decimal] = Field(None, ge=0)
    deal_count: Optional[int] = Field(None, ge=0)
    current_stage: Optional[str] = Field(None, max_length=100)
    stage_color: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)


class CRMPipelineResponse(CRMPipelineBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Computed fields for frontend compatibility
    value: Optional[str] = None  # Formatted currency string
    deals: int = 0  # Alias for deal_count
    stage: Optional[str] = None  # Alias for current_stage
    stageColor: str = "primary"  # Alias for stage_color
    date: Optional[str] = None  # Formatted date string

    class Config:
        from_attributes = True
        
    @validator('value', pre=False, always=True)
    def format_value(cls, v, values):
        total_value = values.get('total_deal_value')
        if total_value:
            return f"${total_value:,.0f}"
        return "$0"
    
    @validator('deals', pre=False, always=True)
    def set_deals(cls, v, values):
        return values.get('deal_count', 0)
    
    @validator('stage', pre=False, always=True)
    def set_stage(cls, v, values):
        return values.get('current_stage', 'Unknown')
    
    @validator('stageColor', pre=False, always=True)
    def set_stage_color(cls, v, values):
        return values.get('stage_color', 'primary')
    
    @validator('date', pre=False, always=True)
    def format_date(cls, v, values):
        created_at = values.get('created_at')
        if created_at:
            return created_at.strftime("%d %b %Y")
        return None


# Analytics Schemas
class CRMAnalyticsResponse(BaseModel):
    contacts: List[Dict[str, Any]]
    deals: List[Dict[str, Any]]
    leads: List[Dict[str, Any]]
    companies: List[Dict[str, Any]]
    deals_by_stage_chart: Dict[str, Any]
    leads_by_source_chart: Dict[str, Any]


# List Response Schemas
class CRMCompanyListResponse(BaseModel):
    items: List[CRMCompanyResponse]
    total: int
    page: int
    size: int
    pages: int


class CRMContactListResponse(BaseModel):
    items: List[CRMContactResponse]
    total: int
    page: int
    size: int
    pages: int


class CRMDealListResponse(BaseModel):
    items: List[CRMDealResponse]
    total: int
    page: int
    size: int
    pages: int


class CRMActivityListResponse(BaseModel):
    items: List[CRMActivityResponse]
    total: int
    page: int
    size: int
    pages: int