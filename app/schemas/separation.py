"""
Separation Schemas
Pydantic models for separation API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class SeparationTypeEnum(str, Enum):
    RESIGNATION = "resignation"
    TERMINATION = "termination"
    RETIREMENT = "retirement"
    END_OF_CONTRACT = "end_of_contract"
    LAYOFF = "layoff"
    MUTUAL_SEPARATION = "mutual_separation"


class SeparationStatusEnum(str, Enum):
    INITIATED = "initiated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ClearanceStatusEnum(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"


# Base schemas
class SeparationRequestBase(BaseModel):
    employee_id: int = Field(..., gt=0, description="Valid employee ID")
    separation_type: SeparationTypeEnum = Field(..., description="Type of separation")
    request_date: date = Field(..., description="Date when separation was requested")
    last_working_date: date = Field(..., description="Employee's last working day")
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for separation")
    detailed_reason: Optional[str] = Field(None, max_length=2000, description="Detailed explanation")
    initiated_by: str = Field(..., pattern="^(employee|manager|hr|admin)$", description="Who initiated the separation")
    notice_period_days: int = Field(0, ge=0, le=365, description="Notice period in days")
    
    @validator('last_working_date')
    def validate_last_working_date(cls, v, values):
        if 'request_date' in values and v < values['request_date']:
            raise ValueError('Last working date must be after request date')
        return v
    
    @validator('request_date')
    def validate_request_date(cls, v):
        if v > date.today():
            raise ValueError('Request date cannot be in the future')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason cannot be empty')
        return v.strip()


class SeparationRequestCreate(SeparationRequestBase):
    """Schema for creating a new separation request"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "separation_type": "resignation",
                "request_date": "2024-01-15",
                "last_working_date": "2024-02-15",
                "reason": "Better career opportunity with higher compensation and growth prospects in a leading technology company.",
                "detailed_reason": "After careful consideration, I have decided to accept an offer from a technology company that aligns better with my career goals and offers significant growth opportunities in my field of expertise.",
                "initiated_by": "employee",
                "notice_period_days": 30
            }
        }


class SeparationRequestUpdate(BaseModel):
    separation_type: Optional[SeparationTypeEnum] = None
    last_working_date: Optional[date] = None
    reason: Optional[str] = Field(None, min_length=10, max_length=1000)
    detailed_reason: Optional[str] = None
    notice_period_days: Optional[int] = Field(None, ge=0, le=365)
    actual_separation_date: Optional[date] = None
    final_settlement_amount: Optional[Decimal] = None
    pending_dues: Optional[Decimal] = None
    recovery_amount: Optional[Decimal] = None
    admin_notes: Optional[str] = None
    hr_notes: Optional[str] = None


class SeparationRequestResponse(SeparationRequestBase):
    """Schema for separation request response"""
    id: int = Field(..., description="Unique separation request ID")
    business_id: int = Field(..., description="Business ID")
    status: SeparationStatusEnum = Field(..., description="Current status of separation")
    actual_separation_date: Optional[date] = Field(None, description="Actual date of separation")
    final_settlement_amount: Optional[Decimal] = Field(None, description="Final settlement amount")
    pending_dues: Optional[Decimal] = Field(None, description="Pending dues amount")
    recovery_amount: Optional[Decimal] = Field(None, description="Recovery amount")
    initiated_by_user: int = Field(..., description="User ID who initiated the request")
    approved_by: Optional[int] = Field(None, description="User ID who approved")
    rejected_by: Optional[int] = Field(None, description="User ID who rejected")
    created_at: datetime = Field(..., description="Creation timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    admin_notes: Optional[str] = Field(None, description="Admin notes")
    hr_notes: Optional[str] = Field(None, description="HR notes")
    
    # Employee details (joined)
    employee_name: Optional[str] = Field(None, description="Employee full name")
    employee_code: Optional[str] = Field(None, description="Employee code")
    department_name: Optional[str] = Field(None, description="Department name")
    designation_name: Optional[str] = Field(None, description="Designation name")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "business_id": 1,
                "employee_id": 123,
                "separation_type": "resignation",
                "status": "initiated",
                "request_date": "2024-01-15",
                "last_working_date": "2024-02-15",
                "actual_separation_date": None,
                "reason": "Better career opportunity with higher compensation and growth prospects in a leading technology company.",
                "detailed_reason": "After careful consideration, I have decided to accept an offer from a technology company that aligns better with my career goals.",
                "initiated_by": "employee",
                "notice_period_days": 30,
                "final_settlement_amount": None,
                "pending_dues": None,
                "recovery_amount": None,
                "initiated_by_user": 1,
                "approved_by": None,
                "rejected_by": None,
                "created_at": "2024-01-15T10:30:00Z",
                "approved_at": None,
                "rejected_at": None,
                "completed_at": None,
                "rejection_reason": None,
                "admin_notes": None,
                "hr_notes": None,
                "employee_name": "John Doe",
                "employee_code": "EMP001",
                "department_name": "Engineering",
                "designation_name": "Senior Software Engineer"
            }
        }


# Clearance schemas
class SeparationClearanceCreate(BaseModel):
    department: str = Field(..., max_length=100)
    item_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_mandatory: bool = True
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    pending_amount: Optional[Decimal] = None


class SeparationClearanceUpdate(BaseModel):
    status: Optional[ClearanceStatusEnum] = None
    clearance_notes: Optional[str] = None
    pending_amount: Optional[Decimal] = None
    cleared_by: Optional[int] = None


class SeparationClearanceResponse(SeparationClearanceCreate):
    id: int
    separation_id: int
    status: ClearanceStatusEnum
    cleared_by: Optional[int] = None
    cleared_at: Optional[datetime] = None
    clearance_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # User details (joined)
    assigned_user_name: Optional[str] = None
    clearer_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Exit interview schemas
class ExitInterviewCreate(BaseModel):
    interview_date: Optional[date] = None
    interviewer_id: Optional[int] = None
    interview_mode: str = Field("in_person", pattern="^(in_person|video_call|phone|written)$")
    reason_for_leaving: Optional[str] = None
    job_satisfaction_rating: Optional[int] = Field(None, ge=1, le=10)
    manager_feedback: Optional[str] = None
    company_culture_feedback: Optional[str] = None
    work_environment_feedback: Optional[str] = None
    growth_opportunities_feedback: Optional[str] = None
    compensation_feedback: Optional[str] = None
    would_recommend_company: Optional[bool] = None
    would_consider_rejoining: Optional[bool] = None
    suggestions_for_improvement: Optional[str] = None
    positive_aspects: Optional[str] = None
    negative_aspects: Optional[str] = None
    additional_comments: Optional[str] = None
    interview_notes: Optional[str] = None


class ExitInterviewUpdate(ExitInterviewCreate):
    is_completed: Optional[bool] = None


class ExitInterviewResponse(ExitInterviewCreate):
    id: int
    separation_id: int
    is_completed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Interviewer details (joined)
    interviewer_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Document schemas
class SeparationDocumentCreate(BaseModel):
    document_type: str = Field(..., max_length=100)
    document_name: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_mandatory: bool = False
    is_generated: bool = False


class SeparationDocumentResponse(SeparationDocumentCreate):
    id: int
    separation_id: int
    uploaded_at: datetime
    uploaded_by: Optional[int] = None
    
    # Uploader details (joined)
    uploader_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Dashboard and statistics schemas
class SeparationDashboardResponse(BaseModel):
    total_separations: int
    pending_approvals: int
    in_progress_separations: int
    completed_separations: int
    pending_clearances: int
    exit_interviews_pending: int
    recent_separations: List[Dict[str, Any]]
    monthly_stats: List[Dict[str, Any]]
    separation_by_type: Dict[str, int]
    average_notice_period: Optional[float] = None


class SeparationStatsResponse(BaseModel):
    total_separations: int
    voluntary_separations: int
    involuntary_separations: int
    turnover_rate: float
    average_tenure: Optional[float] = None
    top_separation_reasons: List[Dict[str, Any]]
    department_wise_stats: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]


# Ex-Employee response schema
class ExEmployeeResponse(BaseModel):
    """Schema for ex-employee response"""
    id: int
    employee_code: str
    full_name: str
    email: Optional[str] = None
    department_name: Optional[str] = None
    designation_name: Optional[str] = None
    date_of_joining: Optional[str] = None
    date_of_termination: Optional[str] = None
    separation_type: str
    separation_reason: Optional[str] = None
    final_settlement_amount: Optional[float] = None
    
    class Config:
        from_attributes = True


# Pagination schemas
class PaginatedSeparationResponse(BaseModel):
    items: List[SeparationRequestResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedExEmployeeResponse(BaseModel):
    items: List[ExEmployeeResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedClearanceResponse(BaseModel):
    items: List[SeparationClearanceResponse]
    total: int
    page: int
    size: int
    pages: int


# Action schemas
class SeparationApprovalRequest(BaseModel):
    """Schema for approving a separation request"""
    notes: Optional[str] = Field(None, max_length=2000, description="Admin notes for approval")
    actual_separation_date: Optional[date] = Field(None, description="Actual separation date (if different from planned)")
    final_settlement_amount: Optional[Decimal] = Field(None, ge=0, description="Final settlement amount")
    pending_dues: Optional[Decimal] = Field(None, ge=0, description="Pending dues amount")
    recovery_amount: Optional[Decimal] = Field(None, ge=0, description="Recovery amount")
    hr_notes: Optional[str] = Field(None, max_length=2000, description="HR notes")
    auto_complete_clearances: bool = Field(False, description="Auto-complete mandatory clearances")
    send_notifications: bool = Field(True, description="Send approval notifications")
    
    @validator('actual_separation_date')
    def validate_actual_separation_date(cls, v):
        if v and v > date.today():
            raise ValueError('Actual separation date cannot be in the future')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "notes": "Approved after reviewing all documentation and clearance requirements.",
                "actual_separation_date": "2024-02-15",
                "final_settlement_amount": 45000.00,
                "pending_dues": 0.00,
                "recovery_amount": 500.00,
                "hr_notes": "All HR processes completed successfully.",
                "auto_complete_clearances": False,
                "send_notifications": True
            }
        }


class SeparationRejectionRequest(BaseModel):
    """Schema for rejecting a separation request"""
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for rejection")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional admin notes")
    send_notifications: bool = Field(True, description="Send rejection notifications")
    
    @validator('reason')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Rejection reason cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Insufficient notice period provided. Company policy requires minimum 30 days notice for this position level.",
                "notes": "Employee needs to provide proper notice period as per company policy.",
                "send_notifications": True
            }
        }


class SeparationActionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|complete|cancel)$")
    reason: Optional[str] = None
    notes: Optional[str] = None
    actual_separation_date: Optional[date] = None
    final_settlement_amount: Optional[Decimal] = None


class SeparationActionResponse(BaseModel):
    """Schema for separation action response"""
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Success or error message")
    separation_id: int = Field(..., description="Separation request ID")
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(..., description="Action timestamp")
    updated_status: Optional[str] = Field(None, description="New status after action")
    next_steps: Optional[List[str]] = Field(None, description="Next steps in the process")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Separation request approved successfully",
                "separation_id": 1,
                "action": "approve",
                "timestamp": "2024-01-15T10:30:00Z",
                "updated_status": "approved",
                "next_steps": [
                    "Employee will be notified of approval",
                    "Clearance process will begin",
                    "Final settlement calculation will be initiated",
                    "Exit interview will be scheduled"
                ]
            }
        }


# Settings schemas
class SeparationSettingsUpdate(BaseModel):
    default_notice_period_days: Optional[int] = Field(None, ge=0, le=365)
    allow_notice_period_buyout: Optional[bool] = None
    require_manager_approval: Optional[bool] = None
    require_hr_approval: Optional[bool] = None
    require_admin_approval: Optional[bool] = None
    mandatory_exit_interview: Optional[bool] = None
    exit_interview_template: Optional[str] = None
    default_clearance_items: Optional[str] = None
    auto_create_clearance: Optional[bool] = None
    notify_manager: Optional[bool] = None
    notify_hr: Optional[bool] = None
    notify_admin: Optional[bool] = None
    separation_request_template: Optional[str] = None
    approval_notification_template: Optional[str] = None
    rejection_notification_template: Optional[str] = None
    clearance_reminder_template: Optional[str] = None


class SeparationSettingsResponse(SeparationSettingsUpdate):
    id: int
    business_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# Template schemas
class SeparationTemplateCreate(BaseModel):
    name: str = Field(..., max_length=255)
    template_type: str = Field(..., max_length=100)
    description: Optional[str] = None
    template_content: str
    available_variables: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class SeparationTemplateResponse(SeparationTemplateCreate):
    id: int
    business_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# Search and filter schemas
class SeparationSearchRequest(BaseModel):
    query: Optional[str] = None
    status: Optional[SeparationStatusEnum] = None
    separation_type: Optional[SeparationTypeEnum] = None
    department_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    initiated_by: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


# Rehire schemas
class RehireRequestCreate(BaseModel):
    """Schema for initiating rehire process"""
    position_offered: str = Field(..., min_length=2, max_length=200, description="Position being offered")
    department_id: Optional[int] = Field(None, gt=0, description="Department ID for new position")
    designation_id: Optional[int] = Field(None, gt=0, description="Designation ID for new position")
    proposed_salary: Optional[Decimal] = Field(None, gt=0, description="Proposed salary amount")
    proposed_start_date: date = Field(..., description="Proposed start date")
    employment_type: str = Field("permanent", pattern="^(permanent|contract|temporary|internship)$", description="Type of employment")
    work_location: Optional[str] = Field(None, max_length=200, description="Work location")
    reporting_manager_id: Optional[int] = Field(None, gt=0, description="Reporting manager ID")
    rehire_reason: str = Field(..., min_length=10, max_length=1000, description="Reason for rehiring")
    terms_and_conditions: Optional[str] = Field(None, max_length=2000, description="Special terms and conditions")
    probation_period_months: int = Field(3, ge=0, le=12, description="Probation period in months")
    notice_period_days: int = Field(30, ge=0, le=90, description="Notice period in days")
    benefits_package: Optional[str] = Field(None, max_length=1000, description="Benefits package details")
    hr_notes: Optional[str] = Field(None, max_length=2000, description="HR notes")
    send_offer_letter: bool = Field(True, description="Send offer letter to ex-employee")
    auto_create_onboarding: bool = Field(True, description="Auto-create onboarding record")
    
    @validator('proposed_start_date')
    def validate_start_date(cls, v):
        if v <= date.today():
            raise ValueError('Proposed start date must be in the future')
        return v
    
    @validator('rehire_reason')
    def validate_rehire_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Rehire reason cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "position_offered": "Senior Software Engineer",
                "department_id": 1,
                "designation_id": 5,
                "proposed_salary": 75000.00,
                "proposed_start_date": "2024-03-01",
                "employment_type": "permanent",
                "work_location": "Bangalore Office",
                "reporting_manager_id": 10,
                "rehire_reason": "Excellent past performance and strong technical skills. Company needs experienced developers for new project.",
                "terms_and_conditions": "Standard employment terms apply. Previous experience will be considered for benefits calculation.",
                "probation_period_months": 3,
                "notice_period_days": 30,
                "benefits_package": "Health insurance, provident fund, performance bonus, flexible working hours",
                "hr_notes": "Previous employee with good track record. Recommended by department head.",
                "send_offer_letter": True,
                "auto_create_onboarding": True
            }
        }


class RehireOfferUpdate(BaseModel):
    """Schema for updating rehire offer"""
    offer_status: str = Field(..., pattern="^(pending|accepted|rejected|withdrawn|expired)$", description="Offer status")
    employee_response: Optional[str] = Field(None, max_length=1000, description="Employee response/feedback")
    negotiated_salary: Optional[Decimal] = Field(None, gt=0, description="Negotiated salary amount")
    negotiated_start_date: Optional[date] = Field(None, description="Negotiated start date")
    final_terms: Optional[str] = Field(None, max_length=2000, description="Final agreed terms")
    hr_notes: Optional[str] = Field(None, max_length=2000, description="Additional HR notes")
    
    @validator('negotiated_start_date')
    def validate_negotiated_start_date(cls, v):
        if v and v <= date.today():
            raise ValueError('Negotiated start date must be in the future')
        return v


class RehireResponse(BaseModel):
    """Schema for rehire response"""
    success: bool = Field(..., description="Whether rehire initiation was successful")
    message: str = Field(..., description="Success or error message")
    rehire_id: int = Field(..., description="Unique rehire request ID")
    employee_id: int = Field(..., description="Employee ID")
    employee_name: str = Field(..., description="Employee full name")
    employee_code: str = Field(..., description="Employee code")
    position_offered: str = Field(..., description="Position offered")
    proposed_salary: Optional[Decimal] = Field(None, description="Proposed salary")
    proposed_start_date: date = Field(..., description="Proposed start date")
    employment_type: str = Field(..., description="Employment type")
    offer_status: str = Field(..., description="Current offer status")
    previous_separation_id: int = Field(..., description="Previous separation request ID")
    rehire_initiated_by: int = Field(..., description="User who initiated rehire")
    rehire_initiated_at: datetime = Field(..., description="Rehire initiation timestamp")
    offer_expires_at: Optional[datetime] = Field(None, description="Offer expiration timestamp")
    next_steps: List[str] = Field(..., description="Next steps in rehire process")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Rehire process initiated successfully for John Doe",
                "rehire_id": 1,
                "employee_id": 123,
                "employee_name": "John Doe",
                "employee_code": "EMP001",
                "position_offered": "Senior Software Engineer",
                "proposed_salary": 75000.00,
                "proposed_start_date": "2024-03-01",
                "employment_type": "permanent",
                "offer_status": "pending",
                "previous_separation_id": 5,
                "rehire_initiated_by": 1,
                "rehire_initiated_at": "2024-01-15T10:30:00Z",
                "offer_expires_at": "2024-02-15T23:59:59Z",
                "next_steps": [
                    "Offer letter will be sent to employee",
                    "Employee has 30 days to respond",
                    "HR will schedule discussion call",
                    "Background verification will be initiated",
                    "Onboarding process will begin upon acceptance"
                ]
            }
        }


class RehireListResponse(BaseModel):
    """Schema for rehire list response"""
    rehire_id: int
    employee_id: int
    employee_name: str
    employee_code: str
    position_offered: str
    proposed_salary: Optional[Decimal]
    proposed_start_date: date
    offer_status: str
    rehire_initiated_at: datetime
    offer_expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True