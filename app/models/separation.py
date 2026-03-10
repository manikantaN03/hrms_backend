"""
Separation Models
Employee separation and exit management data models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, ForeignKey, Text, Enum
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum
from datetime import datetime


class SeparationType(str, enum.Enum):
    RESIGNATION = "resignation"
    TERMINATION = "termination"
    RETIREMENT = "retirement"
    END_OF_CONTRACT = "end_of_contract"
    LAYOFF = "layoff"
    MUTUAL_SEPARATION = "mutual_separation"


class SeparationStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ClearanceStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"


class SeparationRequest(Base):
    """Main separation request records"""
    __tablename__ = "separation_requests"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Separation details
    separation_type = Column(Enum(SeparationType), nullable=False)
    status = Column(Enum(SeparationStatus), default=SeparationStatus.INITIATED)
    
    # Dates
    request_date = Column(Date, nullable=False)
    last_working_date = Column(Date, nullable=False)
    actual_separation_date = Column(Date)
    notice_period_days = Column(Integer, default=0)
    
    # Reason and details
    reason = Column(Text, nullable=False)
    detailed_reason = Column(Text)
    initiated_by = Column(String(50))  # employee, manager, hr, admin
    
    # Financial details
    final_settlement_amount = Column(Numeric(15, 2))
    pending_dues = Column(Numeric(15, 2))
    recovery_amount = Column(Numeric(15, 2))
    
    # Workflow
    initiated_by_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    rejected_by = Column(Integer, ForeignKey("users.id"))
    
    # Workflow timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Additional fields
    rejection_reason = Column(Text)
    admin_notes = Column(Text)
    hr_notes = Column(Text)
    
    # System fields
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", back_populates="separation_requests")
    initiator = relationship("User", foreign_keys=[initiated_by_user])
    approver = relationship("User", foreign_keys=[approved_by])
    rejector = relationship("User", foreign_keys=[rejected_by])
    
    # Related records
    clearance_items = relationship("SeparationClearance", back_populates="separation")
    exit_interview = relationship("ExitInterview", back_populates="separation", uselist=False)
    documents = relationship("SeparationDocument", back_populates="separation")


class SeparationClearance(Base):
    """Clearance checklist items for separation"""
    __tablename__ = "separation_clearance"

    id = Column(Integer, primary_key=True, index=True)
    separation_id = Column(Integer, ForeignKey("separation_requests.id"), nullable=False)
    
    # Clearance details
    department = Column(String(100), nullable=False)  # IT, HR, Finance, etc.
    item_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Status
    status = Column(Enum(ClearanceStatus), default=ClearanceStatus.PENDING)
    is_mandatory = Column(Boolean, default=True)
    
    # Responsible person
    assigned_to = Column(Integer, ForeignKey("users.id"))
    cleared_by = Column(Integer, ForeignKey("users.id"))
    
    # Dates
    due_date = Column(Date)
    cleared_at = Column(DateTime)
    
    # Additional info
    clearance_notes = Column(Text)
    pending_amount = Column(Numeric(10, 2))  # If any recovery needed
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    separation = relationship("SeparationRequest", back_populates="clearance_items")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    clearer = relationship("User", foreign_keys=[cleared_by])


class ExitInterview(Base):
    """Exit interview data"""
    __tablename__ = "exit_interviews"

    id = Column(Integer, primary_key=True, index=True)
    separation_id = Column(Integer, ForeignKey("separation_requests.id"), nullable=False)
    
    # Interview details
    interview_date = Column(Date)
    interviewer_id = Column(Integer, ForeignKey("users.id"))
    interview_mode = Column(String(50))  # in_person, video_call, phone, written
    
    # Feedback questions and responses
    reason_for_leaving = Column(Text)
    job_satisfaction_rating = Column(Integer)  # 1-10 scale
    manager_feedback = Column(Text)
    company_culture_feedback = Column(Text)
    work_environment_feedback = Column(Text)
    growth_opportunities_feedback = Column(Text)
    compensation_feedback = Column(Text)
    
    # Recommendations
    would_recommend_company = Column(Boolean)
    would_consider_rejoining = Column(Boolean)
    suggestions_for_improvement = Column(Text)
    
    # Additional feedback
    positive_aspects = Column(Text)
    negative_aspects = Column(Text)
    additional_comments = Column(Text)
    
    # Interview status
    is_completed = Column(Boolean, default=False)
    interview_notes = Column(Text)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    separation = relationship("SeparationRequest", back_populates="exit_interview")
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    creator = relationship("User", foreign_keys=[created_by])


class SeparationDocument(Base):
    """Documents related to separation"""
    __tablename__ = "separation_documents"

    id = Column(Integer, primary_key=True, index=True)
    separation_id = Column(Integer, ForeignKey("separation_requests.id"), nullable=False)
    
    # Document details
    document_type = Column(String(100), nullable=False)  # resignation_letter, clearance_form, etc.
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Document metadata
    description = Column(Text)
    is_mandatory = Column(Boolean, default=False)
    is_generated = Column(Boolean, default=False)  # System generated vs uploaded
    
    # System fields
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    separation = relationship("SeparationRequest", back_populates="documents")
    uploader = relationship("User")


class SeparationTemplate(Base):
    """Templates for separation documents"""
    __tablename__ = "separation_templates"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Template details
    name = Column(String(255), nullable=False)
    template_type = Column(String(100), nullable=False)  # clearance_form, experience_letter, etc.
    description = Column(Text)
    template_content = Column(Text, nullable=False)
    
    # Template variables (JSON)
    available_variables = Column(Text)  # JSON array of variable names
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    business = relationship("Business")
    creator = relationship("User")


class SeparationSettings(Base):
    """Separation process configuration settings"""
    __tablename__ = "separation_settings"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Notice period settings
    default_notice_period_days = Column(Integer, default=30)
    allow_notice_period_buyout = Column(Boolean, default=True)
    
    # Approval workflow
    require_manager_approval = Column(Boolean, default=True)
    require_hr_approval = Column(Boolean, default=True)
    require_admin_approval = Column(Boolean, default=False)
    
    # Exit interview settings
    mandatory_exit_interview = Column(Boolean, default=True)
    exit_interview_template = Column(Text)  # JSON template
    
    # Clearance settings
    default_clearance_items = Column(Text)  # JSON array of default items
    auto_create_clearance = Column(Boolean, default=True)
    
    # Notification settings
    notify_manager = Column(Boolean, default=True)
    notify_hr = Column(Boolean, default=True)
    notify_admin = Column(Boolean, default=False)
    
    # Email templates
    separation_request_template = Column(Text)
    approval_notification_template = Column(Text)
    rejection_notification_template = Column(Text)
    clearance_reminder_template = Column(Text)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    business = relationship("Business")
    creator = relationship("User")


class RehireOfferStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class RehireRequest(Base):
    """Rehire requests for ex-employees"""
    __tablename__ = "rehire_requests"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    previous_separation_id = Column(Integer, ForeignKey("separation_requests.id"), nullable=False)
    
    # Position details
    position_offered = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    designation_id = Column(Integer, ForeignKey("designations.id"))
    reporting_manager_id = Column(Integer, ForeignKey("employees.id"))
    work_location = Column(String(200))
    
    # Employment terms
    employment_type = Column(String(50), default="permanent")  # permanent, contract, temporary, internship
    proposed_salary = Column(Numeric(15, 2))
    negotiated_salary = Column(Numeric(15, 2))
    proposed_start_date = Column(Date, nullable=False)
    negotiated_start_date = Column(Date)
    probation_period_months = Column(Integer, default=3)
    notice_period_days = Column(Integer, default=30)
    
    # Offer details
    rehire_reason = Column(Text, nullable=False)
    terms_and_conditions = Column(Text)
    benefits_package = Column(Text)
    offer_status = Column(Enum(RehireOfferStatus), default=RehireOfferStatus.PENDING)
    
    # Response tracking
    employee_response = Column(Text)
    final_terms = Column(Text)
    
    # Workflow
    rehire_initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    offer_sent_at = Column(DateTime)
    offer_expires_at = Column(DateTime)
    employee_responded_at = Column(DateTime)
    offer_accepted_at = Column(DateTime)
    offer_rejected_at = Column(DateTime)
    
    # Processing flags
    send_offer_letter = Column(Boolean, default=True)
    auto_create_onboarding = Column(Boolean, default=True)
    background_verification_required = Column(Boolean, default=True)
    
    # Notes
    hr_notes = Column(Text)
    admin_notes = Column(Text)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", foreign_keys=[employee_id])
    previous_separation = relationship("SeparationRequest")
    department = relationship("Department")
    designation = relationship("Designation")
    reporting_manager = relationship("Employee", foreign_keys=[reporting_manager_id])
    initiator = relationship("User", foreign_keys=[rehire_initiated_by])