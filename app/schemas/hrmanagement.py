"""
HR Management Schemas
Pydantic schemas for HR management API
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class NotificationStatus(str, Enum):
    """Notification status enumeration"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NotificationPriority(str, Enum):
    """Notification priority enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class LetterType(str, Enum):
    """Letter type enumeration"""
    APPOINTMENT = "APPOINTMENT"
    CONFIRMATION = "CONFIRMATION"
    PROMOTION = "PROMOTION"
    TRANSFER = "TRANSFER"
    WARNING = "WARNING"
    TERMINATION = "TERMINATION"
    APPRECIATION = "APPRECIATION"
    SALARY_REVISION = "SALARY_REVISION"
    EXPERIENCE = "EXPERIENCE"
    RELIEVING = "RELIEVING"


class AlertType(str, Enum):
    """Alert type enumeration"""
    SYSTEM = "system"
    POLICY = "policy"
    DEADLINE = "deadline"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    GENERAL = "general"


class GreetingType(str, Enum):
    """Greeting type enumeration"""
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    FESTIVAL = "festival"
    ACHIEVEMENT = "achievement"
    WELCOME = "welcome"
    FAREWELL = "farewell"


class PolicyStatus(str, Enum):
    """Policy status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


# Standard API Response Schemas
class APIResponse(BaseModel):
    """Standard API response schema"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class APIListResponse(BaseModel):
    """Standard API list response schema"""
    success: bool = True
    message: str
    data: List[Dict[str, Any]]
    total: int = 0
    page: int = 1
    size: int = 20
    timestamp: datetime = Field(default_factory=datetime.now)


class APIErrorResponse(BaseModel):
    """Standard API error response schema"""
    success: bool = False
    message: str
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Notification Schemas
class NotificationBase(BaseModel):
    """Base notification schema"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    priority: NotificationPriority = NotificationPriority.MEDIUM
    publish_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    target_all_employees: bool = True
    target_departments: Optional[str] = None
    target_employees: Optional[str] = None
    is_pinned: bool = False
    attachment_url: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Notification creation schema"""
    pass


class NotificationUpdate(BaseModel):
    """Notification update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[NotificationStatus] = None
    priority: Optional[NotificationPriority] = None
    expiry_date: Optional[datetime] = None
    is_pinned: Optional[bool] = None


class NotificationResponse(NotificationBase):
    """Notification response schema"""
    id: int
    business_id: int
    created_by: int
    status: NotificationStatus
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Letter Schemas
class LetterBase(BaseModel):
    """Base letter schema"""
    letter_type: LetterType
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    letter_date: date = Field(default_factory=date.today)
    effective_date: Optional[date] = None
    letterhead_used: bool = True


class LetterCreate(LetterBase):
    """Letter creation schema"""
    employee_id: Optional[int] = None  # Allow null for auto-assignment
    template_id: Optional[int] = None


class LetterUpdate(BaseModel):
    """Letter update schema"""
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    effective_date: Optional[date] = None
    is_generated: Optional[bool] = None
    is_sent: Optional[bool] = None


class LetterResponse(LetterBase):
    """Letter response schema"""
    id: int
    business_id: int
    employee_id: int
    created_by: int
    letter_number: Optional[str] = None
    is_generated: bool
    is_sent: bool
    sent_date: Optional[datetime] = None
    is_digitally_signed: bool
    signed_by: Optional[int] = None
    signature_date: Optional[datetime] = None
    pdf_url: Optional[str] = None
    created_at: datetime
    employee_name: Optional[str] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    """Base alert schema"""
    alert_type: AlertType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    expiry_date: Optional[datetime] = None
    is_popup: bool = False
    is_email: bool = False
    is_sms: bool = False
    target_all_employees: bool = True
    target_departments: Optional[str] = None
    target_employees: Optional[str] = None
    acknowledgment_required: bool = False
    is_active: bool = True  # Add is_active field
    
    # Attendance-based Alert Settings (for frontend compatibility)
    alert_name: Optional[str] = Field(None, max_length=255)
    condition: Optional[str] = Field(None, max_length=100)  # Absent, Late
    days: Optional[int] = Field(1, ge=1)
    send_letter: Optional[str] = Field(None, max_length=100)  # Warning, Notice
    check_every: Optional[str] = Field("day", max_length=50)  # day, week, month


class AlertCreate(AlertBase):
    """Alert creation schema"""
    pass


class AlertUpdate(BaseModel):
    """Alert update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    acknowledgment_required: Optional[bool] = None
    
    # Attendance-based Alert Settings
    alert_name: Optional[str] = Field(None, max_length=255)
    condition: Optional[str] = Field(None, max_length=100)
    days: Optional[int] = Field(None, ge=1)
    send_letter: Optional[str] = Field(None, max_length=100)
    check_every: Optional[str] = Field(None, max_length=50)


class AlertResponse(AlertBase):
    """Alert response schema"""
    id: int
    business_id: int
    created_by: int
    alert_date: datetime
    is_active: bool
    created_at: datetime
    creator_name: Optional[str] = None
    acknowledgment_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Greeting Configuration Schemas
class GreetingConfigurationBase(BaseModel):
    """Base greeting configuration schema"""
    greeting_type: GreetingType
    is_enabled: bool = True
    send_to_managers: bool = True
    post_on_org_feed: bool = True
    send_email: bool = True
    send_push_notification: bool = True
    email_subject: Optional[str] = None
    message_template: str = Field(..., min_length=1)
    process_time: str = "07:00"


class GreetingConfigurationCreate(GreetingConfigurationBase):
    """Greeting configuration creation schema"""
    pass


class GreetingConfigurationUpdate(BaseModel):
    """Greeting configuration update schema"""
    is_enabled: Optional[bool] = None
    send_to_managers: Optional[bool] = None
    post_on_org_feed: Optional[bool] = None
    send_email: Optional[bool] = None
    send_push_notification: Optional[bool] = None
    email_subject: Optional[str] = None
    message_template: Optional[str] = Field(None, min_length=1)
    process_time: Optional[str] = None


# Greeting Configuration Save Schema (for frontend compatibility)
class GreetingConfigItem(BaseModel):
    """Individual greeting configuration item"""
    enabled: bool = Field(False, description="Whether this greeting type is enabled")
    managerCopy: bool = Field(True, description="Send copy to manager")
    orgFeed: bool = Field(True, description="Post on organization feed")
    subject: Optional[str] = Field("", description="Email subject for the greeting")
    message: Optional[str] = Field("", description="Greeting message template")
    
    class Config:
        # Allow extra fields for future compatibility
        extra = "allow"


class GreetingConfigurationSaveRequest(BaseModel):
    """Request schema for saving greeting configurations"""
    birthday: Optional[GreetingConfigItem] = Field(None, description="Birthday greeting configuration")
    workAnniversary: Optional[GreetingConfigItem] = Field(None, description="Work anniversary greeting configuration")
    weddingAnniversary: Optional[GreetingConfigItem] = Field(None, description="Wedding anniversary greeting configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "birthday": {
                    "enabled": True,
                    "managerCopy": True,
                    "orgFeed": True,
                    "subject": "Happy Birthday!",
                    "message": "Wishing you a wonderful birthday, {{first_name}}!"
                },
                "workAnniversary": {
                    "enabled": True,
                    "managerCopy": True,
                    "orgFeed": True,
                    "subject": "Work Anniversary Celebration",
                    "message": "Congratulations on your work anniversary, {{first_name}}!"
                }
            }
        }


class GreetingConfigurationResponse(GreetingConfigurationBase):
    """Greeting configuration response schema"""
    id: int
    business_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Greeting Schemas
class GreetingBase(BaseModel):
    """Base greeting schema"""
    greeting_type: GreetingType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    greeting_date: date = Field(default_factory=date.today)
    display_from: Optional[datetime] = None
    display_until: Optional[datetime] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_public: bool = True
    show_on_dashboard: bool = True
    send_notification: bool = True


class GreetingCreate(GreetingBase):
    """Greeting creation schema"""
    employee_id: Optional[int] = None


class GreetingUpdate(BaseModel):
    """Greeting update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)
    display_until: Optional[datetime] = None
    is_public: Optional[bool] = None
    show_on_dashboard: Optional[bool] = None


class GreetingResponse(GreetingBase):
    """Greeting response schema"""
    id: int
    business_id: int
    employee_id: Optional[int] = None
    created_by: int
    like_count: int
    comment_count: int
    created_at: datetime
    employee_name: Optional[str] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# HR Policy Schemas
class HRPolicyBase(BaseModel):
    """Base HR policy schema"""
    policy_name: str = Field(..., min_length=1, max_length=255)
    policy_code: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    version: str = "1.0"
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_mandatory_reading: bool = False
    acknowledgment_required: bool = False
    applies_to_all: bool = True
    applicable_departments: Optional[str] = None
    applicable_designations: Optional[str] = None


class HRPolicyCreateRequest(BaseModel):
    """HR policy creation request schema - Frontend Compatible"""
    policyName: str = Field(..., min_length=1, max_length=255, description="Name of the policy")
    policyType: str = Field(..., pattern="^(online|upload)$", description="Policy type: 'online' or 'upload'")
    policyBody: Optional[str] = Field(None, description="Policy content for online policies")
    policyFile: Optional[str] = Field(None, description="Policy file URL for upload policies")
    type: Optional[str] = Field("General", description="Policy category")
    
    @validator('policyBody')
    def validate_policy_body(cls, v, values):
        """Validate that policyBody is provided for online policies"""
        policy_type = values.get('policyType')
        if policy_type == 'online' and (not v or not v.strip()):
            raise ValueError('Policy body is required for online policies')
        return v
    
    @validator('policyFile')
    def validate_policy_file(cls, v, values):
        """Validate that policyFile is provided for upload policies"""
        policy_type = values.get('policyType')
        if policy_type == 'upload' and not v:
            raise ValueError('Policy file is required for upload policies')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "policyName": "Work From Home Policy",
                "policyType": "online",
                "policyBody": "This policy outlines the guidelines for remote work...",
                "type": "Remote Work"
            }
        }


class HRPolicyCreate(HRPolicyBase):
    """HR policy creation schema"""
    pass


class HRPolicyUpdate(BaseModel):
    """HR policy update schema"""
    policy_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[PolicyStatus] = None
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    expiry_date: Optional[date] = None
    approval_comments: Optional[str] = None


class HRPolicyResponse(HRPolicyBase):
    """HR policy response schema"""
    id: int
    business_id: int
    created_by: int
    approved_by: Optional[int] = None
    status: PolicyStatus
    previous_version_id: Optional[int] = None
    approval_date: Optional[datetime] = None
    approval_comments: Optional[str] = None
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_name: Optional[str] = None
    approver_name: Optional[str] = None
    acknowledgment_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class HRDashboardStats(BaseModel):
    """HR dashboard statistics"""
    total_notifications: int
    active_notifications: int
    total_letters: int
    pending_letters: int
    total_alerts: int
    active_alerts: int
    total_greetings: int
    recent_greetings: int
    total_policies: int
    active_policies: int
    policies_needing_review: int


class HRDashboardResponse(BaseModel):
    """HR dashboard response"""
    statistics: HRDashboardStats
    recent_notifications: List[NotificationResponse]
    active_alerts: List[AlertResponse]
    upcoming_greetings: List[GreetingResponse]
    policies_for_review: List[HRPolicyResponse]


# Acknowledgment Schemas
class PolicyAcknowledgmentCreate(BaseModel):
    """Policy acknowledgment creation schema"""
    policy_id: int
    acknowledgment_method: str = "digital"


class PolicyAcknowledgmentResponse(BaseModel):
    """Policy acknowledgment response schema"""
    id: int
    policy_id: int
    employee_id: int
    acknowledged_date: datetime
    acknowledgment_method: str
    is_current_version: bool
    policy_name: Optional[str] = None
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertAcknowledgmentCreate(BaseModel):
    """Alert acknowledgment creation schema"""
    alert_id: int
    acknowledgment_comments: Optional[str] = None


class AlertAcknowledgmentResponse(BaseModel):
    """Alert acknowledgment response schema"""
    id: int
    alert_id: int
    employee_id: int
    acknowledged_date: datetime
    acknowledgment_comments: Optional[str] = None
    alert_title: Optional[str] = None
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True