"""
Additional Request Schemas
Pydantic models for request API endpoints that were missing proper schemas
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal


# ============================================================================
# Missed Punch Request Update Schema
# ============================================================================

class MissedPunchRequestUpdate(BaseModel):
    """Missed punch request update"""
    punch_time: Optional[str] = Field(None, description="Updated punch time in HH:MM:SS format", example="09:30:00")
    punch_type: Optional[str] = Field(None, description="Punch type: in, out", example="in")
    reason: Optional[str] = Field(None, description="Updated reason", min_length=10, max_length=500, example="Biometric device was not working")
    location: Optional[str] = Field(None, description="Punch location", max_length=255, example="Office Main Gate")
    
    @field_validator('punch_time')
    @classmethod
    def validate_punch_time(cls, v):
        """Validate punch time format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            raise ValueError("punch_time must be in HH:MM:SS format")
    
    @field_validator('punch_type')
    @classmethod
    def validate_punch_type(cls, v):
        """Validate punch type"""
        if v is None:
            return v
        valid_types = ['in', 'out']
        if v.lower() not in valid_types:
            raise ValueError(f"punch_type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "punch_time": "09:30:00",
                "punch_type": "in",
                "reason": "Biometric device was not working",
                "location": "Office Main Gate"
            }
        }


# ============================================================================
# Request Approval/Rejection Schemas
# ============================================================================

class RequestApprovalRequest(BaseModel):
    """Generic request approval"""
    remarks: Optional[str] = Field(None, description="Approval remarks", max_length=500, example="Approved as per company policy")
    approved_by: Optional[int] = Field(None, description="Approver ID", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "remarks": "Approved as per company policy"
            }
        }


class RequestRejectionRequest(BaseModel):
    """Generic request rejection"""
    remarks: str = Field(..., description="Rejection reason (required)", min_length=10, max_length=500, example="Does not meet approval criteria")
    rejected_by: Optional[int] = Field(None, description="Rejector ID", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "remarks": "Does not meet approval criteria"
            }
        }


# ============================================================================
# Strike Exemption Request Schemas
# ============================================================================

class StrikeExemptionRequestCreate(BaseModel):
    """Strike exemption request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    exemption_date: str = Field(..., description="Exemption date in YYYY-MM-DD format", example="2026-02-19")
    reason: str = Field(..., description="Reason for exemption", min_length=10, max_length=500, example="Medical emergency - had to visit hospital")
    supporting_documents: Optional[List[str]] = Field(None, description="Supporting document URLs", example=["medical_certificate.pdf"])
    
    @field_validator('exemption_date')
    @classmethod
    def validate_exemption_date(cls, v):
        """Validate exemption date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("exemption_date must be in YYYY-MM-DD format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "exemption_date": "2026-02-19",
                "reason": "Medical emergency - had to visit hospital",
                "supporting_documents": ["medical_certificate.pdf"]
            }
        }


# ============================================================================
# Week Roster Request Schemas
# ============================================================================

class WeekRosterRequestCreate(BaseModel):
    """Week roster request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    week_start_date: str = Field(..., description="Week start date in YYYY-MM-DD format", example="2026-02-17")
    roster_pattern: str = Field(..., description="Roster pattern (e.g., 'MTWRFSS' where M=Monday, etc.)", min_length=7, max_length=7, example="MTWRF--")
    reason: str = Field(..., description="Reason for roster change", min_length=10, max_length=500, example="Need to attend training program")
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500, example="Will work extra hours next week")
    
    @field_validator('week_start_date')
    @classmethod
    def validate_week_start_date(cls, v):
        """Validate week start date format"""
        try:
            parsed_date = datetime.strptime(v, "%Y-%m-%d")
            # Check if it's a Monday
            if parsed_date.weekday() != 0:
                raise ValueError("week_start_date must be a Monday")
            return v
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError("week_start_date must be in YYYY-MM-DD format")
            raise e
    
    @field_validator('roster_pattern')
    @classmethod
    def validate_roster_pattern(cls, v):
        """Validate roster pattern"""
        if len(v) != 7:
            raise ValueError("roster_pattern must be exactly 7 characters")
        
        valid_chars = set('MTWRFSU-')  # M=Mon, T=Tue, W=Wed, R=Thu, F=Fri, S=Sat, U=Sun, -=Off
        if not all(c in valid_chars for c in v.upper()):
            raise ValueError("roster_pattern must contain only M, T, W, R, F, S, U, or - characters")
        
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "week_start_date": "2026-02-16",
                "roster_pattern": "MTWRF--",
                "reason": "Need to attend training program",
                "notes": "Will work extra hours next week"
            }
        }


# ============================================================================
# Workflow Request Schemas
# ============================================================================

class WorkflowRequestCreate(BaseModel):
    """Workflow request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    workflow_type: str = Field(..., description="Workflow type", max_length=100, example="SALARY_ADVANCE")
    request_data: Dict[str, Any] = Field(..., description="Workflow-specific request data")
    reason: str = Field(..., description="Reason for request", min_length=10, max_length=500, example="Need salary advance for medical emergency")
    priority: str = Field(default="NORMAL", description="Request priority: LOW, NORMAL, HIGH, URGENT", example="NORMAL")
    
    @field_validator('workflow_type')
    @classmethod
    def validate_workflow_type(cls, v):
        """Validate workflow type"""
        valid_types = [
            'SALARY_ADVANCE', 'LOAN_REQUEST', 'ASSET_REQUEST', 
            'TRANSFER_REQUEST', 'PROMOTION_REQUEST', 'RESIGNATION',
            'GRIEVANCE', 'POLICY_EXCEPTION', 'OTHER'
        ]
        if v.upper() not in valid_types:
            raise ValueError(f"workflow_type must be one of: {', '.join(valid_types)}")
        return v.upper()
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority"""
        valid_priorities = ['LOW', 'NORMAL', 'HIGH', 'URGENT']
        if v.upper() not in valid_priorities:
            raise ValueError(f"priority must be one of: {', '.join(valid_priorities)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "workflow_type": "SALARY_ADVANCE",
                "request_data": {
                    "amount": 50000,
                    "repayment_months": 3
                },
                "reason": "Need salary advance for medical emergency",
                "priority": "HIGH"
            }
        }


# ============================================================================
# Visit Punch Request Update Schema
# ============================================================================

class VisitPunchRequestUpdate(BaseModel):
    """Visit punch request update"""
    visit_type_id: Optional[int] = Field(None, description="Visit type ID", gt=0, example=1)
    visit_location: Optional[str] = Field(None, description="Visit location", max_length=255, example="Client Office - ABC Corp")
    visit_purpose: Optional[str] = Field(None, description="Visit purpose", max_length=500, example="Client meeting for project discussion")
    punch_in_time: Optional[str] = Field(None, description="Punch in time in HH:MM:SS format", example="10:00:00")
    punch_out_time: Optional[str] = Field(None, description="Punch out time in HH:MM:SS format", example="16:00:00")
    latitude: Optional[float] = Field(None, description="GPS latitude", ge=-90, le=90, example=12.9716)
    longitude: Optional[float] = Field(None, description="GPS longitude", ge=-180, le=180, example=77.5946)
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500, example="Meeting went well")
    
    @field_validator('punch_in_time', 'punch_out_time')
    @classmethod
    def validate_time(cls, v):
        """Validate time format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM:SS format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "visit_type_id": 1,
                "visit_location": "Client Office - ABC Corp",
                "visit_purpose": "Client meeting for project discussion",
                "punch_in_time": "10:00:00",
                "punch_out_time": "16:00:00",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "notes": "Meeting went well"
            }
        }


# ============================================================================
# Helpdesk Request Create Schema
# ============================================================================

class HelpdeskRequestCreate(BaseModel):
    """Helpdesk request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    category_id: int = Field(..., description="Helpdesk category ID", gt=0, example=1)
    subject: str = Field(..., description="Request subject", min_length=5, max_length=200, example="Laptop not working")
    description: str = Field(..., description="Detailed description", min_length=20, max_length=2000, example="My laptop is not turning on. I tried charging it but still no response. Need urgent replacement.")
    priority: str = Field(default="NORMAL", description="Request priority: LOW, NORMAL, HIGH, URGENT", example="HIGH")
    attachments: Optional[List[str]] = Field(None, description="Attachment URLs", example=["laptop_issue.jpg"])
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority"""
        valid_priorities = ['LOW', 'NORMAL', 'HIGH', 'URGENT']
        if v.upper() not in valid_priorities:
            raise ValueError(f"priority must be one of: {', '.join(valid_priorities)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "category_id": 1,
                "subject": "Laptop not working",
                "description": "My laptop is not turning on. I tried charging it but still no response. Need urgent replacement.",
                "priority": "HIGH",
                "attachments": ["laptop_issue.jpg"]
            }
        }


# ============================================================================
# Claim Request Create Schema
# ============================================================================

class ClaimRequestCreate(BaseModel):
    """Claim request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    claim_type: str = Field(..., description="Claim type", max_length=100, example="TRAVEL")
    claim_date: str = Field(..., description="Claim date in YYYY-MM-DD format", example="2026-02-19")
    amount: float = Field(..., description="Claim amount", gt=0, example=5000.00)
    description: str = Field(..., description="Claim description", min_length=20, max_length=1000, example="Travel expenses for client visit to Mumbai")
    bill_number: Optional[str] = Field(None, description="Bill/invoice number", max_length=100, example="INV-2026-001")
    vendor_name: Optional[str] = Field(None, description="Vendor name", max_length=200, example="ABC Travels")
    attachments: Optional[List[str]] = Field(None, description="Bill/receipt attachments", example=["bill1.pdf", "bill2.pdf"])
    
    @field_validator('claim_date')
    @classmethod
    def validate_claim_date(cls, v):
        """Validate claim date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("claim_date must be in YYYY-MM-DD format")
    
    @field_validator('claim_type')
    @classmethod
    def validate_claim_type(cls, v):
        """Validate claim type"""
        valid_types = [
            'TRAVEL', 'MEDICAL', 'FOOD', 'ACCOMMODATION', 
            'COMMUNICATION', 'FUEL', 'ENTERTAINMENT', 'OTHER'
        ]
        if v.upper() not in valid_types:
            raise ValueError(f"claim_type must be one of: {', '.join(valid_types)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "claim_type": "TRAVEL",
                "claim_date": "2026-02-19",
                "amount": 5000.00,
                "description": "Travel expenses for client visit to Mumbai",
                "bill_number": "INV-2026-001",
                "vendor_name": "ABC Travels",
                "attachments": ["bill1.pdf", "bill2.pdf"]
            }
        }


# ============================================================================
# Leave Request Create Schema
# ============================================================================

class LeaveRequestCreate(BaseModel):
    """Leave request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    leave_type_id: int = Field(..., description="Leave type ID", gt=0, example=1)
    from_date: str = Field(..., description="Leave start date in YYYY-MM-DD format", example="2026-02-20")
    to_date: str = Field(..., description="Leave end date in YYYY-MM-DD format", example="2026-02-22")
    is_half_day: bool = Field(default=False, description="Is half day leave", example=False)
    half_day_session: Optional[str] = Field(None, description="Half day session: FIRST_HALF, SECOND_HALF", example="FIRST_HALF")
    reason: str = Field(..., description="Leave reason", min_length=10, max_length=500, example="Going for family vacation")
    contact_number: Optional[str] = Field(None, description="Contact number during leave", max_length=20, example="+91-9876543210")
    contact_address: Optional[str] = Field(None, description="Contact address during leave", max_length=500, example="123 Beach Road, Goa")
    
    @field_validator('from_date', 'to_date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
    
    @field_validator('half_day_session')
    @classmethod
    def validate_half_day_session(cls, v):
        """Validate half day session"""
        if v is None:
            return v
        valid_sessions = ['FIRST_HALF', 'SECOND_HALF']
        if v.upper() not in valid_sessions:
            raise ValueError(f"half_day_session must be one of: {', '.join(valid_sessions)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "leave_type_id": 1,
                "from_date": "2026-02-20",
                "to_date": "2026-02-22",
                "is_half_day": False,
                "reason": "Going for family vacation",
                "contact_number": "+91-9876543210",
                "contact_address": "123 Beach Road, Goa"
            }
        }


# ============================================================================
# Comp-Off Request Create Schema
# ============================================================================

class CompOffRequestCreate(BaseModel):
    """Comp-off request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    worked_date: str = Field(..., description="Date worked on holiday/weekend in YYYY-MM-DD format", example="2026-02-16")
    comp_off_date: str = Field(..., description="Date to take comp-off in YYYY-MM-DD format", example="2026-02-25")
    hours_worked: float = Field(..., description="Hours worked", gt=0, le=24, example=8.0)
    reason: str = Field(..., description="Reason for working on holiday", min_length=10, max_length=500, example="Had to complete urgent project delivery")
    supporting_documents: Optional[List[str]] = Field(None, description="Supporting documents", example=["work_proof.pdf"])
    
    @field_validator('worked_date', 'comp_off_date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "worked_date": "2026-02-16",
                "comp_off_date": "2026-02-25",
                "hours_worked": 8.0,
                "reason": "Had to complete urgent project delivery",
                "supporting_documents": ["work_proof.pdf"]
            }
        }


# ============================================================================
# Time Relaxation Request Create Schema
# ============================================================================

class TimeRelaxationRequestCreate(BaseModel):
    """Time relaxation request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    relaxation_date: str = Field(..., description="Date for time relaxation in YYYY-MM-DD format", example="2026-02-19")
    relaxation_minutes: int = Field(..., description="Relaxation time in minutes", gt=0, le=480, example=30)
    relaxation_type: str = Field(..., description="Relaxation type: LATE_COMING, EARLY_GOING", example="LATE_COMING")
    reason: str = Field(..., description="Reason for time relaxation", min_length=10, max_length=500, example="Had to drop child at school due to spouse being unwell")
    
    @field_validator('relaxation_date')
    @classmethod
    def validate_relaxation_date(cls, v):
        """Validate relaxation date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("relaxation_date must be in YYYY-MM-DD format")
    
    @field_validator('relaxation_type')
    @classmethod
    def validate_relaxation_type(cls, v):
        """Validate relaxation type"""
        valid_types = ['LATE_COMING', 'EARLY_GOING', 'EXTENDED_BREAK']
        if v.upper() not in valid_types:
            raise ValueError(f"relaxation_type must be one of: {', '.join(valid_types)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "relaxation_date": "2026-02-19",
                "relaxation_minutes": 30,
                "relaxation_type": "LATE_COMING",
                "reason": "Had to drop child at school due to spouse being unwell"
            }
        }


# ============================================================================
# Missed Punch Request Create Schema
# ============================================================================

class MissedPunchRequestCreate(BaseModel):
    """Missed punch request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    punch_date: str = Field(..., description="Punch date in YYYY-MM-DD format", example="2026-02-19")
    punch_time: str = Field(..., description="Punch time in HH:MM:SS format", example="09:30:00")
    punch_type: str = Field(..., description="Punch type: in, out", example="in")
    reason: str = Field(..., description="Reason for missed punch", min_length=10, max_length=500, example="Biometric device was not working")
    location: Optional[str] = Field(None, description="Punch location", max_length=255, example="Office Main Gate")
    
    @field_validator('punch_date')
    @classmethod
    def validate_punch_date(cls, v):
        """Validate punch date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("punch_date must be in YYYY-MM-DD format")
    
    @field_validator('punch_time')
    @classmethod
    def validate_punch_time(cls, v):
        """Validate punch time format"""
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            raise ValueError("punch_time must be in HH:MM:SS format")
    
    @field_validator('punch_type')
    @classmethod
    def validate_punch_type(cls, v):
        """Validate punch type"""
        valid_types = ['in', 'out']
        if v.lower() not in valid_types:
            raise ValueError(f"punch_type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "punch_date": "2026-02-19",
                "punch_time": "09:30:00",
                "punch_type": "in",
                "reason": "Biometric device was not working",
                "location": "Office Main Gate"
            }
        }
