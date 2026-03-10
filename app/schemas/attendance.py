"""
Attendance Schemas
Pydantic models for attendance API requests and responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum


class AttendanceStatusEnum(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    LATE = "LATE"
    ON_LEAVE = "ON_LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"
    COMP_OFF = "COMP_OFF"
    LEAVE_WITHOUT_PAY = "LEAVE_WITHOUT_PAY"


class PunchTypeEnum(str, Enum):
    IN = "in"
    OUT = "out"
    BREAK_OUT = "break_out"
    BREAK_IN = "break_in"


# ============================================================================
# Punch Schemas
# ============================================================================

class PunchCreate(BaseModel):
    """Create punch request"""
    employee_id: int
    punch_type: PunchTypeEnum
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_remote: bool = False
    device_info: Optional[str] = None


class PunchResponse(BaseModel):
    """Punch response"""
    id: int
    employee_id: int
    punch_time: datetime
    punch_type: str
    location: Optional[str] = None
    is_remote: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Attendance Record Schemas
# ============================================================================

class AttendanceRecordCreate(BaseModel):
    """Create attendance record"""
    employee_id: int
    attendance_date: date
    punch_in_time: Optional[datetime] = None
    punch_out_time: Optional[datetime] = None
    attendance_status: AttendanceStatusEnum = AttendanceStatusEnum.PRESENT
    is_manual_entry: bool = False
    manual_entry_reason: Optional[str] = None


class AttendanceRecordUpdate(BaseModel):
    """Update attendance record"""
    punch_in_time: Optional[datetime] = None
    punch_out_time: Optional[datetime] = None
    attendance_status: Optional[AttendanceStatusEnum] = None
    manual_entry_reason: Optional[str] = None


class AttendanceRecordResponse(BaseModel):
    """Attendance record response"""
    id: int
    employee_id: int
    employee_name: str
    employee_code: str
    attendance_date: date
    punch_in_time: Optional[datetime] = None
    punch_out_time: Optional[datetime] = None
    total_hours: Optional[float] = None
    attendance_status: str
    is_late: bool = False
    is_early_out: bool = False
    is_manual_entry: bool = False
    manual_entry_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Dashboard Schemas
# ============================================================================

class AttendanceDashboardResponse(BaseModel):
    """Attendance dashboard response"""
    daily_summary: Dict[str, int]
    weekly_trends: List[Dict[str, Any]]
    recent_activities: List[Dict[str, str]]


class DailyAttendanceSummary(BaseModel):
    """Daily attendance summary"""
    date: date
    total_employees: int
    present: int
    absent: int
    late: int
    on_leave: int
    half_day: int


# ============================================================================
# Daily Punch Schemas
# ============================================================================

class EmployeePunchInfo(BaseModel):
    """Employee punch information"""
    employee_id: int
    employee_name: str
    employee_code: str
    department: Optional[str] = None
    designation: Optional[str] = None
    punch_in_time: Optional[str] = None
    punch_out_time: Optional[str] = None
    total_hours: Optional[str] = None
    status: str
    location: Optional[str] = None
    punches: List[Dict[str, Any]] = []


class DailyPunchResponse(BaseModel):
    """Daily punch records response"""
    date: date
    employee_punches: List[EmployeePunchInfo]
    summary: Dict[str, int]


# ============================================================================
# Daily Attendance Card Schemas
# ============================================================================

class DailyAttendanceCard(BaseModel):
    """Daily attendance card response matching frontend expectations"""
    id: int
    name: str
    code: str
    date: str
    status: str
    note: str
    location: str
    designation: str
    department: str
    punchIn: Optional[str] = None
    punchOut: Optional[str] = None
    punchType: str
    timeline: Dict[str, str]
    totalHours: str
    punches: List[Dict[str, Any]]


class DailyAttendanceCardsResponse(BaseModel):
    """Daily attendance cards response"""
    date: date
    cards: List[DailyAttendanceCard]
    summary: Dict[str, int]


# ============================================================================
# Manual Attendance Schemas
# ============================================================================

class ManualAttendanceRequest(BaseModel):
    """Manual attendance entry request"""
    employee_id: int
    attendance_date: date
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    attendance_status: AttendanceStatusEnum
    reason: Optional[str] = None


class ManualAttendanceResponse(BaseModel):
    """Manual attendance entry response"""
    id: int
    employee_id: int
    employee_name: str
    attendance_date: date
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    attendance_status: str
    total_hours: Optional[float] = None
    reason: Optional[str] = None
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ManualAttendanceSummary(BaseModel):
    """Manual attendance summary for table view"""
    id: int
    name: str
    code: str
    P: int = 0   # Present days
    A: int = 0   # Absent days  
    H: int = 0   # Holiday days
    W: int = 0   # Week off days
    CO: int = 0  # Comp off days
    CL: int = 0  # Casual leave days
    LW: int = 0  # Leave without pay days


class ManualAttendanceUpdate(BaseModel):
    """Manual attendance bulk update request"""
    employee_id: int = Field(..., gt=0, description="Employee ID must be positive")
    month: str = Field(..., description="Month in format 'SEP-2025'")
    present_days: int = Field(default=0, ge=0, le=31, description="Present days (0-31)")
    absent_days: int = Field(default=0, ge=0, le=31, description="Absent days (0-31)")
    holiday_days: int = Field(default=0, ge=0, le=31, description="Holiday days (0-31)")
    weekend_days: int = Field(default=0, ge=0, le=31, description="Weekend days (0-31)")
    comp_off_days: int = Field(default=0, ge=0, le=31, description="Comp off days (0-31)")
    casual_leave_days: int = Field(default=0, ge=0, le=31, description="Casual leave days (0-31)")
    leave_without_pay_days: int = Field(default=0, ge=0, le=31, description="Leave without pay days (0-31)")
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not v:
            raise ValueError("Month is required")
        
        try:
            month_str, year_str = v.split('-')
            year = int(year_str)
            
            valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            if month_str not in valid_months:
                raise ValueError(f"Invalid month. Must be one of: {', '.join(valid_months)}")
            
            if year < 2020 or year > 2030:
                raise ValueError("Year must be between 2020 and 2030")
                
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid month format. Use format like 'SEP-2025'")
            raise e


class ManualAttendanceFilters(BaseModel):
    """Manual attendance filters"""
    month: Optional[str] = Field(None, description="Month in format 'SEP-2025'")
    department_id: Optional[int] = Field(None, gt=0, description="Department ID")
    location_id: Optional[int] = Field(None, gt=0, description="Location ID")
    cost_center_id: Optional[int] = Field(None, gt=0, description="Cost center ID")
    business_unit_id: Optional[int] = Field(None, gt=0, description="Business unit ID")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search term")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=50, ge=1, le=100, description="Records per page")


class ManualAttendanceDownloadRequest(BaseModel):
    """Manual attendance download request"""
    month: str = Field(..., description="Month in format 'SEP-2025'")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not v:
            raise ValueError("Month is required")
        
        try:
            month_str, year_str = v.split('-')
            year = int(year_str)
            
            valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            if month_str not in valid_months:
                raise ValueError(f"Invalid month. Must be one of: {', '.join(valid_months)}")
            
            if year < 2020 or year > 2030:
                raise ValueError("Year must be between 2020 and 2030")
                
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid month format. Use format like 'SEP-2025'")
            raise e


# ============================================================================
# Leave Balance Schemas
# ============================================================================

class LeaveBalanceResponse(BaseModel):
    """Leave balance response"""
    employee_id: int
    employee_name: str
    employee_code: str
    designation: str
    opening_balance: float = 0.0
    activity: float = 0.0
    correction: float = 0.0
    closing_balance: float = 0.0
    
    class Config:
        from_attributes = True


class LeaveBalanceRequest(BaseModel):
    """Leave balance update request"""
    employee_id: int
    correction: float
    reason: Optional[str] = None


# ============================================================================
# Leave Correction Schemas
# ============================================================================

class LeaveCorrectionSaveRequest(BaseModel):
    """Save leave corrections request"""
    month: str = Field(..., pattern=r"^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)-\d{4}$")
    corrections: List[Dict[str, Any]] = Field(..., min_length=1)
    
    @field_validator('corrections')
    @classmethod
    def validate_corrections(cls, v):
        for correction in v:
            if 'employee_id' not in correction:
                raise ValueError('employee_id is required for each correction')
            if 'correction_amount' not in correction:
                raise ValueError('correction_amount is required for each correction')
            if not isinstance(correction['employee_id'], int):
                raise ValueError('employee_id must be an integer')
            try:
                float(correction['correction_amount'])
            except (ValueError, TypeError):
                raise ValueError('correction_amount must be a valid number')
        return v


class LeaveCorrectionSaveResponse(BaseModel):
    """Save leave corrections response - Enhanced"""
    success: bool
    message: str
    saved_count: int
    errors: List[str]
    warnings: Optional[List[str]] = []  # ✅ ADDED: Warnings for non-critical issues
    total_processed: int  # ✅ ADDED: Total number of corrections processed
    month: Optional[str] = None
    year: Optional[int] = None


class LeaveCorrectionResponse(BaseModel):
    """Leave correction response"""
    id: int
    employee_id: int
    employee_name: str
    correction_date: date
    original_status: str
    corrected_status: str
    reason: str
    status: str  # pending, approved, rejected
    requested_by: int
    approved_by: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Shift Roster Schemas
# ============================================================================

class ShiftRosterCreate(BaseModel):
    """Create shift roster request"""
    employee_id: int
    roster_date: date
    shift_id: int
    custom_start_time: Optional[time] = None
    custom_end_time: Optional[time] = None
    notes: Optional[str] = None


class ShiftRosterUpdate(BaseModel):
    """Update shift roster request"""
    shift_id: Optional[int] = None
    custom_start_time: Optional[time] = None
    custom_end_time: Optional[time] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ShiftRosterResponse(BaseModel):
    """Shift roster response"""
    id: int
    employee_id: int
    employee_name: str
    employee_code: str
    roster_date: date
    shift_name: str
    start_time: time
    end_time: time
    is_active: bool
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Employee Attendance Summary Schemas
# ============================================================================

class EmployeeAttendanceSummary(BaseModel):
    """Employee attendance summary"""
    employee_id: int
    employee_name: str
    employee_code: str
    department: Optional[str] = None
    designation: Optional[str] = None
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    leave_days: int
    attendance_percentage: float
    
    class Config:
        from_attributes = True


# ============================================================================
# Attendance Report Schemas
# ============================================================================

class AttendanceReportRequest(BaseModel):
    """Attendance report request"""
    start_date: date
    end_date: date
    employee_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None
    location_ids: Optional[List[int]] = None
    report_type: str = "summary"  # summary, detailed, monthly


class AttendanceReportResponse(BaseModel):
    """Attendance report response"""
    report_type: str
    period: Dict[str, str]
    summary: Dict[str, Any]
    data: List[Dict[str, Any]]
    generated_at: datetime
    generated_by: str


# ============================================================================
# Attendance Recalculate Schemas
# ============================================================================

class AttendanceRecalculateRequest(BaseModel):
    """Attendance recalculate request"""
    employee_id: int = Field(..., description="Employee ID", gt=0)
    month: str = Field(..., description="Month in format 'MMM-YYYY' (e.g., 'JAN-2026')")
    action: str = Field(default="recalculate", description="Action to perform: 'recalculate' or 'replace'")
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not v:
            raise ValueError("Month is required")
        
        try:
            month_str, year_str = v.split('-')
            year = int(year_str)
            
            valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            if month_str not in valid_months:
                raise ValueError(f"Invalid month. Must be one of: {', '.join(valid_months)}")
            
            if year < 2020 or year > 2030:
                raise ValueError("Year must be between 2020 and 2030")
                
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid month format. Use format like 'JAN-2026'")
            raise e
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action"""
        valid_actions = ['recalculate', 'replace']
        if v not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")
        return v


class AttendanceRecalculateResponse(BaseModel):
    """Attendance recalculate response"""
    success: bool
    message: str
    processed_records: int
    employee_id: int
    month: str
    action: str
    date_range: Dict[str, str]