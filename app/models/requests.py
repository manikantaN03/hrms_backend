"""
Request Management Models
Models for handling various types of employee requests
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum, Date, func
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum as PyEnum
from .base import BaseModel, Base


class RequestStatus(PyEnum):
    """Request status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    IN_REVIEW = "in_review"


class RequestType(PyEnum):
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
    WEEKOFF_ROSTER = "weekoff_roster"


class Request(BaseModel):
    """Base request model"""
    __tablename__ = "requests"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    # Request Details
    request_type = Column(Enum(RequestType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    
    # Dates
    request_date = Column(Date, default=date.today, nullable=False)
    from_date = Column(Date, nullable=True)
    to_date = Column(Date, nullable=True)
    
    # Approval Details
    approved_date = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    # Additional Fields
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, urgent
    amount = Column(DECIMAL(10, 2), nullable=True)  # For claim requests
    attachment_url = Column(String(500), nullable=True)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approver_id])
    approved_by_employee = relationship("Employee", foreign_keys=[approved_by])


class LeaveRequest(BaseModel):
    """Leave request model"""
    __tablename__ = "leave_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    leave_type_id = Column(Integer, nullable=True)  # Reference to leave types
    
    # Leave Details
    leave_type = Column(String(100), nullable=False)  # Annual, Sick, Casual, etc.
    total_days = Column(Integer, nullable=False)
    half_day = Column(Boolean, default=False)
    reason = Column(Text, nullable=False)
    
    # Emergency Contact
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)
    
    # Relationship
    request = relationship("Request", backref="leave_details")


class MissedPunchRequest(BaseModel):
    """Missed punch request model"""
    __tablename__ = "missed_punch_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Punch Details
    missed_date = Column(Date, nullable=False)
    punch_type = Column(String(20), nullable=False)  # in, out, break_in, break_out
    expected_time = Column(String(10), nullable=False)  # HH:MM format
    reason = Column(Text, nullable=False)
    
    # Relationship
    request = relationship("Request", backref="missed_punch_details")


class ClaimRequest(BaseModel):
    """Claim/Expense request model"""
    __tablename__ = "claim_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Claim Details
    claim_type = Column(String(100), nullable=False)  # Travel, Medical, Food, etc.
    claim_amount = Column(DECIMAL(10, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    vendor_name = Column(String(200), nullable=True)
    bill_number = Column(String(100), nullable=True)
    
    # Additional Details
    project_code = Column(String(50), nullable=True)
    client_name = Column(String(200), nullable=True)
    
    # Relationship
    request = relationship("Request", backref="claim_details")


class CompoffRequest(BaseModel):
    """Compensatory off request model"""
    __tablename__ = "compoff_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Compoff Details
    worked_date = Column(Date, nullable=False)
    worked_hours = Column(DECIMAL(4, 2), nullable=False)
    compoff_date = Column(Date, nullable=False)
    reason_for_work = Column(Text, nullable=False)
    
    # Relationship
    request = relationship("Request", backref="compoff_details")


class TimeRelaxationRequest(BaseModel):
    """Time relaxation request model"""
    __tablename__ = "time_relaxation_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Time Details
    relaxation_date = Column(Date, nullable=False)
    requested_in_time = Column(String(10), nullable=True)  # HH:MM
    requested_out_time = Column(String(10), nullable=True)  # HH:MM
    reason = Column(Text, nullable=False)
    
    # Relationship
    request = relationship("Request", backref="time_relaxation_details")


class VisitPunchRequest(BaseModel):
    """Visit punch request model"""
    __tablename__ = "visit_punch_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Visit Details
    visit_date = Column(Date, nullable=False)
    client_name = Column(String(200), nullable=False)
    client_address = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    expected_duration = Column(String(20), nullable=True)  # e.g., "2 hours"
    
    # Relationship
    request = relationship("Request", backref="visit_punch_details")


class WorkflowRequest(BaseModel):
    """Custom workflow request model"""
    __tablename__ = "workflow_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    workflow_type_id = Column(Integer, nullable=True)
    
    # Workflow Details
    workflow_name = Column(String(200), nullable=False)
    current_step = Column(Integer, default=1, nullable=False)
    total_steps = Column(Integer, nullable=False)
    workflow_data = Column(Text, nullable=True)  # JSON data
    
    # Relationship
    request = relationship("Request", backref="workflow_details")


class HelpdeskRequest(BaseModel):
    """Helpdesk ticket model"""
    __tablename__ = "helpdesk_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    category_id = Column(Integer, nullable=True)
    
    # Ticket Details
    category = Column(String(100), nullable=False)  # IT, HR, Admin, etc.
    subcategory = Column(String(100), nullable=True)
    issue_type = Column(String(100), nullable=False)  # Hardware, Software, Access, etc.
    urgency = Column(String(20), default="medium", nullable=False)
    
    # Technical Details
    asset_tag = Column(String(50), nullable=True)
    location = Column(String(200), nullable=True)
    
    # Relationship
    request = relationship("Request", backref="helpdesk_details")


class StrikeExemptionRequest(BaseModel):
    """Strike exemption request model"""
    __tablename__ = "strike_exemption_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Strike Details
    strike_date = Column(Date, nullable=False)
    exemption_reason = Column(Text, nullable=False)
    work_justification = Column(Text, nullable=False)
    department_approval = Column(Boolean, default=False)
    
    # Relationship
    request = relationship("Request", backref="strike_exemption_details")


class ShiftRosterRequest(Base):
    """Shift roster request model"""
    __tablename__ = "shift_roster_requests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Shift Details
    requested_date = Column(Date, nullable=False)
    current_shift_type = Column(String(50), nullable=True)
    requested_shift_type = Column(String(50), nullable=False)
    shift_start_time = Column(String(10), nullable=True)  # HH:MM format
    shift_end_time = Column(String(10), nullable=True)    # HH:MM format
    
    # Request Details
    reason = Column(Text, nullable=False)
    location = Column(String(100), nullable=True)
    is_permanent = Column(Boolean, default=False)  # Permanent or temporary change
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    
    # Approval Details
    manager_approval = Column(Boolean, default=False)
    hr_approval = Column(Boolean, default=False)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    request = relationship("Request", backref="shift_roster_details")


class WeekoffRosterRequest(BaseModel):
    """Weekoff roster request model"""
    __tablename__ = "weekoff_roster_requests"

    # Foreign Keys
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    
    # Weekoff Details
    requested_date = Column(Date, nullable=False)
    current_weekoff_day = Column(String(20), nullable=True)  # Current weekoff day
    requested_weekoff_day = Column(String(20), nullable=False)  # Requested weekoff day
    
    # Request Details
    reason = Column(Text, nullable=False)
    is_permanent = Column(Boolean, default=False)  # Permanent or temporary change
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    
    # Additional Details
    department_approval = Column(Boolean, default=False)
    hr_approval = Column(Boolean, default=False)
    impact_analysis = Column(Text, nullable=True)  # Business impact analysis
    
    # Relationship
    request = relationship("Request", backref="weekoff_roster_details")