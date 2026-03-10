"""
Request Management Schemas
Pydantic schemas for request management API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class RequestStatus(str, Enum):
    """Request status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    IN_REVIEW = "in_review"


class RequestType(str, Enum):
    """Request type enumeration"""
    LEAVE = "leave"
    MISSED_PUNCH = "missed_punch"
    CLAIM = "claim"
    COMPOFF = "compoff"
    TIME_RELAXATION = "time_relaxation"
    VISIT_PUNCH = "visit_punch"
    WORKFLOW = "workflow"
    HELPDESK = "helpdesk"
    STRIKE_EXEMPTION = "strike_exemption"
    SHIFT_ROSTER = "shift_roster"
    WEEKOFF_ROSTER = "weekoff_roster"  # Added for week roster requests


# Base Request Schemas
class RequestBase(BaseModel):
    """Base request schema with comprehensive validation"""
    request_type: RequestType
    title: str = Field(..., min_length=1, max_length=255, description="Request title")
    description: Optional[str] = Field(None, max_length=2000, description="Request description")
    from_date: Optional[date] = Field(None, description="Start date for request")
    to_date: Optional[date] = Field(None, description="End date for request")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$", description="Request priority")
    amount: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="Amount for claim requests")
    attachment_url: Optional[str] = Field(None, max_length=500, description="Attachment URL")
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if v and 'from_date' in values and values['from_date'] and v < values['from_date']:
            raise ValueError('to_date must be after or equal to from_date')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()


class RequestCreate(RequestBase):
    """Request creation schema with mandatory fields"""
    # All fields inherited from RequestBase with proper validation
    pass


class RequestUpdate(BaseModel):
    """Request update schema with optional fields"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[RequestStatus] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    approval_comments: Optional[str] = Field(None, max_length=1000)
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip() if v else v


class RequestResponse(RequestBase):
    """Request response schema"""
    id: int
    business_id: int
    employee_id: int
    approver_id: Optional[int] = None
    status: RequestStatus
    request_date: date
    approved_date: Optional[datetime] = None
    approved_by: Optional[int] = None
    approval_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Leave Request Schemas
class LeaveRequestBase(BaseModel):
    """Base leave request schema with comprehensive validation"""
    leave_type: str = Field(..., min_length=1, max_length=100, description="Type of leave")
    total_days: int = Field(..., ge=1, le=365, description="Total days of leave")
    half_day: bool = Field(default=False, description="Is this a half day leave")
    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for leave")
    emergency_contact: Optional[str] = Field(None, max_length=100, description="Emergency contact person")
    emergency_phone: Optional[str] = Field(None, pattern="^[+]?[0-9]{10,15}$", description="Emergency contact phone")
    
    @validator('reason')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason cannot be empty or whitespace only')
        if len(v.strip()) < 5:
            raise ValueError('Reason must be at least 5 characters long')
        return v.strip()
    
    @validator('leave_type')
    def validate_leave_type(cls, v):
        allowed_types = ['Casual Leave', 'Sick Leave', 'Annual Leave', 'Maternity Leave', 'Paternity Leave', 'Emergency Leave']
        if v not in allowed_types:
            raise ValueError(f'Leave type must be one of: {", ".join(allowed_types)}')
        return v


class LeaveRequestCreate(LeaveRequestBase):
    """Leave request creation schema with date validation"""
    from_date: date = Field(..., description="Leave start date")
    to_date: date = Field(..., description="Leave end date")
    
    @validator('from_date')
    def validate_from_date(cls, v):
        from datetime import date
        if v < date.today():
            raise ValueError('Leave start date cannot be in the past')
        return v
    
    @validator('to_date')
    def validate_dates(cls, v, values):
        if 'from_date' in values and v < values['from_date']:
            raise ValueError('Leave end date must be after or equal to start date')
        return v
    
    @validator('total_days')
    def validate_total_days_with_dates(cls, v, values):
        if 'from_date' in values and 'to_date' in values:
            calculated_days = (values['to_date'] - values['from_date']).days + 1
            if v != calculated_days:
                raise ValueError(f'Total days ({v}) does not match date range ({calculated_days} days)')
        return v


class LeaveRequestResponse(LeaveRequestBase):
    """Leave request response schema"""
    id: int
    request_id: int
    leave_type_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Missed Punch Request Schemas
class MissedPunchRequestBase(BaseModel):
    """Base missed punch request schema with comprehensive validation"""
    missed_date: date = Field(..., description="Date of missed punch")
    punch_type: str = Field(..., pattern="^(in|out|break_in|break_out)$", description="Type of punch missed")
    expected_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Expected punch time (HH:MM)")
    reason: str = Field(..., min_length=5, max_length=500, description="Reason for missed punch")
    
    @validator('missed_date')
    def validate_missed_date(cls, v):
        from datetime import date, timedelta
        if v > date.today():
            raise ValueError('Missed punch date cannot be in the future')
        if v < date.today() - timedelta(days=30):
            raise ValueError('Missed punch date cannot be more than 30 days old')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason cannot be empty or whitespace only')
        return v.strip()


class MissedPunchRequestCreate(MissedPunchRequestBase):
    """Missed punch request creation schema"""
    pass


class MissedPunchRequestResponse(MissedPunchRequestBase):
    """Missed punch request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Claim Request Schemas
class ClaimRequestBase(BaseModel):
    """Base claim request schema with comprehensive validation"""
    claim_type: str = Field(..., min_length=1, max_length=100, description="Type of claim")
    claim_amount: Decimal = Field(..., gt=0, le=999999.99, description="Claim amount")
    expense_date: date = Field(..., description="Date of expense")
    vendor_name: Optional[str] = Field(None, max_length=200, description="Vendor name")
    bill_number: Optional[str] = Field(None, max_length=100, description="Bill/Invoice number")
    project_code: Optional[str] = Field(None, max_length=50, description="Project code")
    client_name: Optional[str] = Field(None, max_length=200, description="Client name")
    
    @validator('claim_type')
    def validate_claim_type(cls, v):
        allowed_types = ['Travel', 'Medical', 'Food', 'Accommodation', 'Communication', 'Fuel', 'Stationery', 'Other']
        if v not in allowed_types:
            raise ValueError(f'Claim type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('expense_date')
    def validate_expense_date(cls, v):
        from datetime import date, timedelta
        if v > date.today():
            raise ValueError('Expense date cannot be in the future')
        if v < date.today() - timedelta(days=90):
            raise ValueError('Expense date cannot be more than 90 days old')
        return v
    
    @validator('claim_amount')
    def validate_claim_amount(cls, v):
        if v <= 0:
            raise ValueError('Claim amount must be greater than 0')
        # Round to 2 decimal places
        return round(v, 2)


class ClaimRequestCreate(ClaimRequestBase):
    """Claim request creation schema"""
    employee_id: Optional[int] = Field(None, description="Employee ID (optional, for admin use)")
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Employee ID must be a positive integer')
        return v


class ClaimRequestResponse(ClaimRequestBase):
    """Claim request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Compoff Request Schemas
class CompoffRequestBase(BaseModel):
    """Base compoff request schema with comprehensive validation"""
    worked_date: date = Field(..., description="Date when extra work was done")
    worked_hours: Decimal = Field(..., gt=0, le=24, description="Hours worked")
    compoff_date: date = Field(..., description="Date when comp-off will be taken")
    reason_for_work: str = Field(..., min_length=5, max_length=500, description="Reason for working extra hours")
    
    @validator('worked_date')
    def validate_worked_date(cls, v):
        from datetime import date, timedelta
        if v > date.today():
            raise ValueError('Worked date cannot be in the future')
        if v < date.today() - timedelta(days=30):
            raise ValueError('Worked date cannot be more than 30 days old')
        return v
    
    @validator('compoff_date')
    def validate_compoff_date(cls, v, values):
        from datetime import date, timedelta
        if v < date.today():
            raise ValueError('Comp-off date cannot be in the past')
        if 'worked_date' in values and v <= values['worked_date']:
            raise ValueError('Comp-off date must be after worked date')
        return v
    
    @validator('reason_for_work')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason for work cannot be empty or whitespace only')
        return v.strip()


class CompoffRequestCreate(CompoffRequestBase):
    """Compoff request creation schema"""
    pass


class CompoffRequestResponse(CompoffRequestBase):
    """Compoff request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Time Relaxation Request Schemas
class TimeRelaxationRequestBase(BaseModel):
    """Base time relaxation request schema"""
    relaxation_date: date
    requested_in_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    requested_out_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    reason: str = Field(..., min_length=1)


class TimeRelaxationRequestCreate(TimeRelaxationRequestBase):
    """Time relaxation request creation schema"""
    pass


class TimeRelaxationRequestResponse(TimeRelaxationRequestBase):
    """Time relaxation request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Visit Punch Request Schemas
class VisitPunchRequestBase(BaseModel):
    """Base visit punch request schema with comprehensive validation"""
    visit_date: date = Field(..., description="Date of the visit")
    client_name: str = Field(..., min_length=1, max_length=200, description="Name of client/company")
    client_address: str = Field(..., min_length=1, max_length=1000, description="Address of visit location")
    purpose: str = Field(..., min_length=1, max_length=1000, description="Purpose of the visit")
    expected_duration: Optional[str] = Field(None, max_length=20, description="Expected duration (e.g., '2 hours')")
    
    @validator('visit_date')
    def validate_visit_date(cls, v):
        from datetime import date, timedelta
        if v < date.today():
            raise ValueError('Visit date cannot be in the past')
        if v > date.today() + timedelta(days=90):
            raise ValueError('Visit date cannot be more than 90 days in the future')
        return v
    
    @validator('client_name')
    def validate_client_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Client name cannot be empty or whitespace only')
        return v.strip()
    
    @validator('client_address')
    def validate_client_address(cls, v):
        if not v or not v.strip():
            raise ValueError('Client address cannot be empty or whitespace only')
        return v.strip()
    
    @validator('purpose')
    def validate_purpose(cls, v):
        if not v or not v.strip():
            raise ValueError('Purpose cannot be empty or whitespace only')
        if len(v.strip()) < 5:
            raise ValueError('Purpose must be at least 5 characters long')
        return v.strip()
    
    @validator('expected_duration')
    def validate_expected_duration(cls, v):
        if v is not None and not v.strip():
            return None  # Convert empty string to None
        return v.strip() if v else v


class VisitPunchRequestCreate(VisitPunchRequestBase):
    """Visit punch request creation schema"""
    employee_id: Optional[int] = Field(None, description="Employee ID (optional, for admin use)")
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Employee ID must be a positive integer')
        return v


class VisitPunchRequestResponse(VisitPunchRequestBase):
    """Visit punch request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Helpdesk Request Schemas
class HelpdeskRequestBase(BaseModel):
    """Base helpdesk request schema"""
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = None
    issue_type: str = Field(..., min_length=1, max_length=100)
    urgency: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    asset_tag: Optional[str] = None
    location: Optional[str] = None


class HelpdeskRequestCreate(HelpdeskRequestBase):
    """Helpdesk request creation schema"""
    pass


class HelpdeskRequestResponse(HelpdeskRequestBase):
    """Helpdesk request response schema"""
    id: int
    request_id: int
    category_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Strike Exemption Request Schemas
class StrikeExemptionRequestBase(BaseModel):
    """Base strike exemption request schema with comprehensive validation"""
    strike_date: date = Field(..., description="Date of strike")
    exemption_reason: str = Field(..., min_length=10, max_length=1000, description="Reason for exemption")
    work_justification: str = Field(..., min_length=10, max_length=1000, description="Justification for working during strike")
    employee_id: Optional[int] = Field(None, description="Employee ID (optional, for admin use)")
    department_approval: bool = Field(default=False, description="Department approval status")
    
    @validator('strike_date')
    def validate_strike_date(cls, v):
        from datetime import date, timedelta
        if v < date.today() - timedelta(days=7):
            raise ValueError('Strike date cannot be more than 7 days old')
        return v
    
    @validator('exemption_reason', 'work_justification')
    def validate_text_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace only')
        return v.strip()


class StrikeExemptionRequestCreate(StrikeExemptionRequestBase):
    """Strike exemption request creation schema"""
    pass


class StrikeExemptionRequestResponse(StrikeExemptionRequestBase):
    """Strike exemption request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True
    
    class Config:
        from_attributes = True


# Week Roster Request Schemas
class WeekRosterRequestBase(BaseModel):
    """Base week roster request schema"""
    employee_id: int = Field(..., description="Employee ID requesting the change")
    week_start_date: date = Field(..., description="Start date of the week")
    week_end_date: date = Field(..., description="End date of the week")
    roster_type: str = Field(..., min_length=1, max_length=100, description="Type of roster")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('week_end_date')
    def validate_week_dates(cls, v, values):
        if 'week_start_date' in values and v < values['week_start_date']:
            raise ValueError('week_end_date must be after week_start_date')
        return v


class WeekRosterRequestCreate(WeekRosterRequestBase):
    """Week roster request creation schema"""
    pass


class WeekRosterRequestResponse(WeekRosterRequestBase):
    """Week roster request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Workflow Request Schemas
class WorkflowRequestBase(BaseModel):
    """Base workflow request schema"""
    workflow_type: str = Field(..., min_length=1, max_length=100, description="Type of workflow")
    title: str = Field(..., min_length=1, max_length=255, description="Workflow title")
    description: str = Field(..., min_length=1, description="Workflow description")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    due_date: Optional[date] = Field(None, description="Due date for workflow completion")


class WorkflowRequestCreate(WorkflowRequestBase):
    """Workflow request creation schema"""
    pass


class WorkflowRequestResponse(WorkflowRequestBase):
    """Workflow request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Shift Roster Request Schemas
class ShiftRosterRequestBase(BaseModel):
    """Base shift roster request schema with comprehensive validation"""
    employee_id: int = Field(..., description="Employee ID requesting shift change")
    date_range: str = Field(..., description="Date for shift change (format: 'Oct 27, 2025 18:00:00')")
    shift_type: str = Field(..., description="Requested shift type")
    note: str = Field(..., min_length=10, max_length=500, description="Reason for shift change")
    location: Optional[str] = Field(default="Hyderabad", description="Employee location")
    
    @validator('shift_type')
    def validate_shift_type(cls, v):
        allowed_types = ["General", "Regular", "Night", "Morning", "Evening"]
        if v not in allowed_types:
            raise ValueError(f'Shift type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('note')
    def validate_note(cls, v):
        if not v or not v.strip():
            raise ValueError('Note cannot be empty or whitespace only')
        if len(v.strip()) < 10:
            raise ValueError('Note must be at least 10 characters long')
        return v.strip()


class ShiftRosterRequestCreate(ShiftRosterRequestBase):
    """Shift roster request creation schema"""
    pass


class ShiftRosterRequestUpdate(BaseModel):
    """Update shift roster request schema"""
    status: str = Field(..., pattern="^(Approved|Rejected)$")
    rejection_reason: Optional[str] = None


class ShiftRosterRequestResponse(BaseModel):
    """Shift roster request response schema matching frontend expectations"""
    id: int
    employee_id: int
    employee_name: str
    employee_code: str
    date_range: str
    shift_type: str
    note: str
    status: str = "Open"  # Open, Pending, Processing, Completed, Approved, Rejected
    location: str
    last_updated: datetime
    requested_at: datetime
    
    class Config:
        from_attributes = True


# Shift Roster Schemas
class ShiftRosterBase(BaseModel):
    """Base shift roster schema"""
    roster_date: date
    shift_name: str = Field(..., min_length=1, max_length=100)
    start_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    break_duration: int = Field(default=60, ge=0, le=480)
    roster_type: str = Field(default="regular", pattern="^(regular|overtime|holiday)$")


class ShiftRosterCreate(ShiftRosterBase):
    """Shift roster creation schema"""
    employee_id: int


class ShiftRosterUpdate(BaseModel):
    """Shift roster update schema"""
    shift_name: Optional[str] = None
    start_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    break_duration: Optional[int] = Field(None, ge=0, le=480)
    roster_type: Optional[str] = Field(None, pattern="^(regular|overtime|holiday)$")
    is_active: Optional[bool] = None


class ShiftRosterResponse(ShiftRosterBase):
    """Shift roster response schema"""
    id: int
    business_id: int
    employee_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Combined Request Schemas
class RequestWithDetails(RequestResponse):
    """Request with detailed information"""
    employee_name: Optional[str] = None
    approver_name: Optional[str] = None
    leave_details: Optional[LeaveRequestResponse] = None
    missed_punch_details: Optional[MissedPunchRequestResponse] = None
    claim_details: Optional[ClaimRequestResponse] = None
    compoff_details: Optional[CompoffRequestResponse] = None
    time_relaxation_details: Optional[TimeRelaxationRequestResponse] = None
    visit_punch_details: Optional[VisitPunchRequestResponse] = None
    helpdesk_details: Optional[HelpdeskRequestResponse] = None


# Request Statistics
class RequestStatistics(BaseModel):
    """Request statistics schema"""
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    requests_by_type: Dict[str, int]
    requests_by_status: Dict[str, int]
    average_approval_time: Optional[float] = None  # in days


# Approval Schema
class RequestApproval(BaseModel):
    """Request approval schema"""
    status: RequestStatus
    approval_comments: Optional[str] = None


# Approval/Rejection Action Schemas
class ApprovalActionRequest(BaseModel):
    """Schema for approval action"""
    comments: Optional[str] = Field(None, max_length=500, description="Approval comments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comments": "Approved as per company policy"
            }
        }


class RejectionActionRequest(BaseModel):
    """Schema for rejection action"""
    comments: str = Field(..., min_length=1, max_length=500, description="Rejection reason (required)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comments": "Insufficient documentation provided"
            }
        }


# Standardized API Response Schemas
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
    total: Optional[int] = None
    page: Optional[int] = None
    size: Optional[int] = None
    pages: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class APIErrorResponse(BaseModel):
    """Standard API error response schema"""
    success: bool = False
    message: str
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Shift Roster Request Schemas
class ShiftRosterRequestBase(BaseModel):
    """Base shift roster request schema with comprehensive validation"""
    requested_date: date = Field(..., description="Date for shift change")
    current_shift_type: str = Field(..., min_length=1, max_length=50, description="Current shift type")
    requested_shift_type: str = Field(..., min_length=1, max_length=50, description="Requested shift type")
    shift_start_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Shift start time")
    shift_end_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Shift end time")
    is_permanent: bool = Field(default=False, description="Is this a permanent shift change")
    manager_approval: bool = Field(default=False, description="Manager approval status")
    hr_approval: bool = Field(default=False, description="HR approval status")
    
    @validator('requested_date')
    def validate_requested_date(cls, v):
        from datetime import date, timedelta
        if v < date.today():
            raise ValueError('Requested date cannot be in the past')
        if v > date.today() + timedelta(days=90):
            raise ValueError('Requested date cannot be more than 90 days in the future')
        return v
    
    @validator('requested_shift_type')
    def validate_shift_types(cls, v, values):
        if 'current_shift_type' in values and v == values['current_shift_type']:
            raise ValueError('Requested shift type must be different from current shift type')
        return v





# Workflow Request Schemas
class WorkflowRequestBase(BaseModel):
    """Base workflow request schema with comprehensive validation"""
    workflow_name: str = Field(..., min_length=1, max_length=200, description="Name of the workflow")
    current_step: int = Field(default=1, ge=1, description="Current workflow step")
    total_steps: int = Field(..., ge=1, le=20, description="Total workflow steps")
    workflow_data: Optional[Dict[str, Any]] = Field(default={}, description="Workflow data as JSON")
    
    @validator('current_step')
    def validate_current_step(cls, v, values):
        if 'total_steps' in values and v > values['total_steps']:
            raise ValueError('Current step cannot be greater than total steps')
        return v
    
    @validator('workflow_name')
    def validate_workflow_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Workflow name cannot be empty or whitespace only')
        return v.strip()


class WorkflowRequestCreate(WorkflowRequestBase):
    """Workflow request creation schema"""
    pass


class WorkflowRequestResponse(WorkflowRequestBase):
    """Workflow request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Helpdesk Request Schemas
class HelpdeskRequestBase(BaseModel):
    """Base helpdesk request schema with comprehensive validation"""
    category: str = Field(..., min_length=1, max_length=100, description="Issue category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Issue subcategory")
    issue_type: str = Field(..., min_length=1, max_length=100, description="Type of issue")
    urgency: str = Field(..., pattern="^(low|medium|high|critical)$", description="Issue urgency")
    asset_tag: Optional[str] = Field(None, max_length=50, description="Asset tag if applicable")
    location: Optional[str] = Field(None, max_length=200, description="Location of issue")
    
    @validator('category')
    def validate_category(cls, v):
        # Allow any non-empty category since categories are dynamic from database
        if not v or not v.strip():
            raise ValueError('Category cannot be empty')
        return v.strip()
    
    @validator('issue_type')
    def validate_issue_type(cls, v):
        if not v or not v.strip():
            raise ValueError('Issue type cannot be empty or whitespace only')
        return v.strip()


class HelpdeskRequestCreate(HelpdeskRequestBase):
    """Helpdesk request creation schema"""
    employee_id: Optional[int] = Field(None, description="Employee ID (for admin users creating requests on behalf of others)")
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Employee ID must be a positive integer')
        return v


class HelpdeskRequestResponse(HelpdeskRequestBase):
    """Helpdesk request response schema"""
    id: int
    request_id: int
    
    class Config:
        from_attributes = True


# Visit Punch Request Schemas (Complete)
class VisitPunchRequestCreate(VisitPunchRequestBase):
    """Visit punch request creation schema"""
    purpose: str = Field(..., min_length=5, max_length=500, description="Purpose of visit")
    expected_duration: Optional[str] = Field(None, description="Expected duration of visit")
    
    @validator('visit_date')
    def validate_visit_date(cls, v):
        from datetime import date, timedelta
        if v < date.today():
            raise ValueError('Visit date cannot be in the past')
        if v > date.today() + timedelta(days=30):
            raise ValueError('Visit date cannot be more than 30 days in the future')
        return v
    
    @validator('purpose')
    def validate_purpose(cls, v):
        if not v or not v.strip():
            raise ValueError('Purpose cannot be empty or whitespace only')
        return v.strip()


class VisitPunchRequestResponse(VisitPunchRequestBase):
    """Visit punch request response schema"""
    id: int
    request_id: int
    purpose: str
    expected_duration: Optional[str] = None
    
    class Config:
        from_attributes = True


# Approval Action Schemas
class ApprovalActionRequest(BaseModel):
    """Schema for approval actions"""
    approval_comments: Optional[str] = Field(None, max_length=1000, description="Optional approval comments")
    
    @validator('approval_comments')
    def validate_comments(cls, v):
        if v is not None and not v.strip():
            return None  # Convert empty string to None
        return v.strip() if v else v


class RejectionActionRequest(BaseModel):
    """Schema for rejection actions"""
    approval_comments: str = Field(..., min_length=5, max_length=1000, description="Required rejection reason")
    
    @validator('approval_comments')
    def validate_rejection_comments(cls, v):
        if not v or not v.strip():
            raise ValueError('Rejection reason is required and cannot be empty')
        if len(v.strip()) < 5:
            raise ValueError('Rejection reason must be at least 5 characters long')
        return v.strip()


# API Response Schemas
class APIResponse(BaseModel):
    """Standard API response schema"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class APIListResponse(BaseModel):
    """API list response with pagination"""
    success: bool = True
    message: str = "Data retrieved successfully"
    data: List[Any] = []
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)


class APIErrorResponse(BaseModel):
    """API error response schema"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Request Statistics Schema
class RequestStatistics(BaseModel):
    """Request statistics schema"""
    total_requests: int = 0
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    in_review_requests: int = 0
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    recent_requests: List[Dict[str, Any]] = []


# Request with Details Schema
class RequestWithDetails(RequestResponse):
    """Request with nested details based on type"""
    leave_details: Optional[LeaveRequestResponse] = None
    missed_punch_details: Optional[MissedPunchRequestResponse] = None
    claim_details: Optional[ClaimRequestResponse] = None
    compoff_details: Optional[CompoffRequestResponse] = None
    time_relaxation_details: Optional[TimeRelaxationRequestResponse] = None
    visit_punch_details: Optional[VisitPunchRequestResponse] = None
    workflow_details: Optional[WorkflowRequestResponse] = None
    helpdesk_details: Optional[HelpdeskRequestResponse] = None
    strike_exemption_details: Optional[StrikeExemptionRequestResponse] = None
    shift_roster_details: Optional[ShiftRosterRequestResponse] = None
    week_roster_details: Optional[WeekRosterRequestResponse] = None