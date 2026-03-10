"""
HR Management Models
Models for HR communication, policies, and management features
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum as PyEnum
from .base import BaseModel


class NotificationStatus(PyEnum):
    """Notification status enumeration"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NotificationPriority(PyEnum):
    """Notification priority enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class LetterType(PyEnum):
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


class AlertType(PyEnum):
    """Alert type enumeration"""
    SYSTEM = "system"
    POLICY = "policy"
    DEADLINE = "deadline"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    GENERAL = "general"


class GreetingType(PyEnum):
    """Greeting type enumeration"""
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    FESTIVAL = "festival"
    ACHIEVEMENT = "achievement"
    WELCOME = "welcome"
    FAREWELL = "farewell"


class PolicyStatus(PyEnum):
    """Policy status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Notification(BaseModel):
    """HR Notifications model"""
    __tablename__ = "hr_notifications"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Notification Details
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.DRAFT, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    
    # Publishing Details
    publish_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Targeting
    target_all_employees = Column(Boolean, default=True, nullable=False)
    target_departments = Column(Text, nullable=True)  # JSON array of department IDs
    target_employees = Column(Text, nullable=True)    # JSON array of employee IDs
    
    # Engagement
    view_count = Column(Integer, default=0, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    # Attachments
    attachment_url = Column(String(500), nullable=True)
    
    # Relationships
    business = relationship("Business")
    creator = relationship("Employee", foreign_keys=[created_by])


class Letter(BaseModel):
    """HR Letters model"""
    __tablename__ = "hr_letters"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Letter Details
    letter_type = Column(Enum(LetterType), nullable=False)
    letter_number = Column(String(100), nullable=True)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Dates
    letter_date = Column(Date, default=date.today, nullable=False)
    effective_date = Column(Date, nullable=True)
    
    # Status
    is_generated = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_date = Column(DateTime, nullable=True)
    
    # Template and Formatting
    template_id = Column(Integer, nullable=True)
    letterhead_used = Column(Boolean, default=True, nullable=False)
    
    # Digital Signature
    is_digitally_signed = Column(Boolean, default=False, nullable=False)
    signed_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    signature_date = Column(DateTime, nullable=True)
    
    # File Storage
    pdf_url = Column(String(500), nullable=True)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("Employee", foreign_keys=[created_by])
    signer = relationship("Employee", foreign_keys=[signed_by])


class Alert(BaseModel):
    """HR Alerts model"""
    __tablename__ = "hr_alerts"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Alert Details
    alert_type = Column(Enum(AlertType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Timing
    alert_date = Column(DateTime, default=datetime.now, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    
    # Display Settings
    is_popup = Column(Boolean, default=False, nullable=False)
    is_email = Column(Boolean, default=False, nullable=False)
    is_sms = Column(Boolean, default=False, nullable=False)
    
    # Targeting
    target_all_employees = Column(Boolean, default=True, nullable=False)
    target_departments = Column(Text, nullable=True)  # JSON array
    target_employees = Column(Text, nullable=True)    # JSON array
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    acknowledgment_required = Column(Boolean, default=False, nullable=False)
    
    # Attendance-based Alert Settings (for frontend compatibility)
    alert_name = Column(String(255), nullable=True)  # Frontend: alertName
    condition = Column(String(100), nullable=True)   # Frontend: condition (Absent, Late)
    days = Column(Integer, default=1, nullable=True) # Frontend: days
    send_letter = Column(String(100), nullable=True) # Frontend: sendLetter (Warning, Notice)
    check_every = Column(String(50), default="day", nullable=True) # Frontend: checkEvery (day, week, month)
    
    # Relationships
    business = relationship("Business")
    creator = relationship("Employee", foreign_keys=[created_by])


class GreetingConfiguration(BaseModel):
    """HR Greeting Configuration model"""
    __tablename__ = "hr_greeting_configurations"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Configuration Details
    greeting_type = Column(Enum(GreetingType), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Notification Settings
    send_to_managers = Column(Boolean, default=True, nullable=False)
    post_on_org_feed = Column(Boolean, default=True, nullable=False)
    send_email = Column(Boolean, default=True, nullable=False)
    send_push_notification = Column(Boolean, default=True, nullable=False)
    
    # Message Customization
    email_subject = Column(String(500), nullable=True)
    message_template = Column(Text, nullable=False)
    
    # Processing Settings
    process_time = Column(String(10), default="07:00", nullable=False)  # Time to process greetings
    
    # Relationships
    business = relationship("Business")
    creator = relationship("Employee", foreign_keys=[created_by])


class Greeting(BaseModel):
    """HR Greetings model"""
    __tablename__ = "hr_greetings"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # Null for general greetings
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Greeting Details
    greeting_type = Column(Enum(GreetingType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Timing
    greeting_date = Column(Date, default=date.today, nullable=False)
    display_from = Column(DateTime, nullable=True)
    display_until = Column(DateTime, nullable=True)
    
    # Media
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    
    # Display Settings
    is_public = Column(Boolean, default=True, nullable=False)
    show_on_dashboard = Column(Boolean, default=True, nullable=False)
    send_notification = Column(Boolean, default=True, nullable=False)
    
    # Engagement
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("Employee", foreign_keys=[created_by])


class HRPolicy(BaseModel):
    """HR Policies model"""
    __tablename__ = "hr_policies"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)

    # Policy Details
    policy_name = Column(String(255), nullable=False)
    policy_code = Column(String(50), nullable=True)
    category = Column(String(100), nullable=False)  # Leave, Attendance, Code of Conduct, etc.
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    
    # Version Control
    version = Column(String(20), default="1.0", nullable=False)
    previous_version_id = Column(Integer, ForeignKey("hr_policies.id"), nullable=True)
    
    # Status and Dates
    status = Column(Enum(PolicyStatus), default=PolicyStatus.DRAFT, nullable=False)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    # Approval Details
    approval_date = Column(DateTime, nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    # Document Management
    document_url = Column(String(500), nullable=True)
    is_mandatory_reading = Column(Boolean, default=False, nullable=False)
    acknowledgment_required = Column(Boolean, default=False, nullable=False)
    
    # Applicability
    applies_to_all = Column(Boolean, default=True, nullable=False)
    applicable_departments = Column(Text, nullable=True)  # JSON array
    applicable_designations = Column(Text, nullable=True)  # JSON array
    
    # Relationships
    business = relationship("Business")
    creator = relationship("Employee", foreign_keys=[created_by])
    approver = relationship("Employee", foreign_keys=[approved_by])
    previous_version = relationship("HRPolicy", remote_side="HRPolicy.id")


class PolicyAcknowledgment(BaseModel):
    """Policy acknowledgment tracking"""
    __tablename__ = "policy_acknowledgments"

    # Foreign Keys
    policy_id = Column(Integer, ForeignKey("hr_policies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Acknowledgment Details
    acknowledged_date = Column(DateTime, default=datetime.now, nullable=False)
    acknowledgment_method = Column(String(50), default="digital", nullable=False)  # digital, physical
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Status
    is_current_version = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    policy = relationship("HRPolicy")
    employee = relationship("Employee")


class NotificationRead(BaseModel):
    """Notification read tracking"""
    __tablename__ = "notification_reads"

    # Foreign Keys
    notification_id = Column(Integer, ForeignKey("hr_notifications.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Read Details
    read_date = Column(DateTime, default=datetime.now, nullable=False)
    read_duration = Column(Integer, nullable=True)  # seconds
    
    # Relationships
    notification = relationship("Notification")
    employee = relationship("Employee")


class AlertAcknowledgment(BaseModel):
    """Alert acknowledgment tracking"""
    __tablename__ = "alert_acknowledgments"

    # Foreign Keys
    alert_id = Column(Integer, ForeignKey("hr_alerts.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Acknowledgment Details
    acknowledged_date = Column(DateTime, default=datetime.now, nullable=False)
    acknowledgment_comments = Column(Text, nullable=True)
    
    # Relationships
    alert = relationship("Alert")
    employee = relationship("Employee")