"""
Reports Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal


# AI Reporting Schemas
class AIReportQueryCreate(BaseModel):
    query_text: str = Field(..., min_length=10, max_length=1000)


class AIReportQueryResponse(BaseModel):
    id: int
    query_text: str
    response_data: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Report Template Schemas
class ReportTemplateCreate(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field(..., max_length=100)
    description: Optional[str] = None
    template_config: Dict[str, Any]


class ReportTemplateResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    template_config: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Generated Report Schemas
class GeneratedReportCreate(BaseModel):
    template_id: Optional[int] = None
    report_name: str = Field(..., max_length=200)
    report_type: str = Field(..., max_length=100)
    parameters: Optional[Dict[str, Any]] = None


class GeneratedReportResponse(BaseModel):
    id: int
    report_name: str
    report_type: str
    parameters: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Salary Report Schemas
class SalaryReportCreate(BaseModel):
    employee_id: int
    report_period: str = Field(..., pattern=r'^\d{4}-\d{2}$')
    basic_salary: Decimal = Field(default=0, ge=0)
    gross_salary: Decimal = Field(default=0, ge=0)
    net_salary: Decimal = Field(default=0, ge=0)
    total_deductions: Decimal = Field(default=0, ge=0)
    overtime_amount: Decimal = Field(default=0, ge=0)
    bonus_amount: Decimal = Field(default=0, ge=0)
    allowances: Optional[Dict[str, Any]] = None
    deductions: Optional[Dict[str, Any]] = None


class SalaryReportResponse(BaseModel):
    id: int
    employee_id: int
    report_period: str
    basic_salary: Decimal
    gross_salary: Decimal
    net_salary: Decimal
    total_deductions: Decimal
    overtime_amount: Decimal
    bonus_amount: Decimal
    allowances: Optional[Dict[str, Any]] = None
    deductions: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Attendance Report Schemas
class AttendanceReportCreate(BaseModel):
    employee_id: int
    report_date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: Decimal = Field(default=0, ge=0)
    overtime_hours: Decimal = Field(default=0, ge=0)
    status: str = Field(default="present")
    location: Optional[str] = None
    is_remote: bool = Field(default=False)


class AttendanceReportResponse(BaseModel):
    id: int
    employee_id: int
    report_date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: Decimal
    overtime_hours: Decimal
    status: str
    location: Optional[str] = None
    is_remote: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Employee Report Schemas
class EmployeeReportCreate(BaseModel):
    employee_id: int
    report_type: str = Field(..., max_length=100)
    report_data: Dict[str, Any]
    effective_date: Optional[date] = None
    status: str = Field(default="active")


class EmployeeReportResponse(BaseModel):
    id: int
    employee_id: int
    report_type: str
    report_data: Dict[str, Any]
    effective_date: Optional[date] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Statutory Report Schemas
class StatutoryReportCreate(BaseModel):
    employee_id: int
    report_period: str = Field(..., pattern=r'^\d{4}-\d{2}$')
    report_type: str = Field(..., max_length=100)
    employee_contribution: Decimal = Field(default=0, ge=0)
    employer_contribution: Decimal = Field(default=0, ge=0)
    total_contribution: Decimal = Field(default=0, ge=0)
    statutory_data: Optional[Dict[str, Any]] = None


class StatutoryReportResponse(BaseModel):
    id: int
    employee_id: int
    report_period: str
    report_type: str
    employee_contribution: Decimal
    employer_contribution: Decimal
    total_contribution: Decimal
    statutory_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Annual Report Schemas
class AnnualReportCreate(BaseModel):
    employee_id: int
    report_year: int = Field(..., ge=2020, le=2030)
    report_type: str = Field(..., max_length=100)
    annual_data: Dict[str, Any]
    total_amount: Decimal = Field(default=0, ge=0)
    total_days: int = Field(default=0, ge=0)


class AnnualReportResponse(BaseModel):
    id: int
    employee_id: int
    report_year: int
    report_type: str
    annual_data: Dict[str, Any]
    total_amount: Decimal
    total_days: int
    created_at: datetime

    class Config:
        from_attributes = True


# Activity Log Schemas
class ActivityLogCreate(BaseModel):
    action: str = Field(..., max_length=200)
    module: str = Field(..., max_length=100)
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ActivityLogFilters(BaseModel):
    """Filters for Activity Logs report"""
    from_date: Optional[str] = Field(None, description="From date in YYYY-MM-DD format")
    to_date: Optional[str] = Field(None, description="To date in YYYY-MM-DD format")
    user_id: Optional[int] = Field(None, description="Filter by specific user ID")
    module: Optional[str] = Field(None, description="Filter by module")
    action: Optional[str] = Field(None, description="Filter by action")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of logs to return")
    business_id: Optional[int] = None  # SECURITY: Filter by business_id


class ActivityLogData(BaseModel):
    """Activity log data for frontend display"""
    id: int
    description: str  # Formatted activity description
    user: str  # User name who performed the action
    datetime: str  # Formatted datetime string (DD-MMM-YYYY HH:MM AM/PM)
    action: str
    module: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    module: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogsReportResponse(BaseModel):
    """Response for Activity Logs report"""
    logs: List[ActivityLogData]
    total_logs: int
    filters_applied: ActivityLogFilters
    date_range: Dict[str, str]  # from_date, to_date
    message: Optional[str] = None


# User Feedback Schemas
class UserFeedbackCreate(BaseModel):
    feedback_type: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=200)
    description: str = Field(..., min_length=10)
    rating: Optional[int] = Field(None, ge=1, le=5)


class UserFeedbackResponse(BaseModel):
    id: int
    user_id: int
    feedback_type: str
    subject: str
    description: str
    rating: Optional[int] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserFeedbackFilters(BaseModel):
    """Filters for User Feedback report"""
    from_date: Optional[str] = Field(None, description="From date in YYYY-MM-DD format")
    to_date: Optional[str] = Field(None, description="To date in YYYY-MM-DD format")
    feedback_type: Optional[str] = Field(None, description="Filter by feedback type")
    status: Optional[str] = Field(None, description="Filter by status")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Filter by rating")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of feedback to return")


class UserFeedbackData(BaseModel):
    """User feedback data for frontend display"""
    id: int
    user_name: str  # Name of the user who submitted feedback
    feedback_type: str
    subject: str
    description: str
    rating: Optional[int] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    datetime: str  # Formatted datetime string (DD-MMM-YYYY HH:MM AM/PM)
    status_badge: str  # Status with appropriate styling class


class UserFeedbackReportResponse(BaseModel):
    """Response for User Feedback report"""
    feedback: List[UserFeedbackData]
    total_feedback: int
    filters_applied: UserFeedbackFilters
    date_range: Dict[str, str]  # from_date, to_date
    summary: Dict[str, Any]  # Statistics summary
    message: Optional[str] = None


# System Alert Schemas
class SystemAlertCreate(BaseModel):
    alert_type: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    message: str = Field(..., min_length=10)
    module: Optional[str] = None


class SystemAlertResponse(BaseModel):
    id: int
    alert_type: str
    title: str
    message: str
    module: Optional[str] = None
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None

    class Config:
        from_attributes = True


# System Alert Report Schemas
class SystemAlertFilters(BaseModel):
    """Filters for System Alerts report"""
    from_date: Optional[str] = Field(None, description="From date in YYYY-MM-DD format")
    to_date: Optional[str] = Field(None, description="To date in YYYY-MM-DD format")
    alert_type: Optional[str] = Field(None, description="Filter by alert type")
    is_resolved: Optional[bool] = Field(None, description="Filter by resolution status")
    module: Optional[str] = Field(None, description="Filter by module")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of alerts to return")


class SystemAlertData(BaseModel):
    """System alert data for frontend display"""
    id: int
    alert_type: str
    title: str
    message: str
    module: Optional[str] = None
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolver_name: Optional[str] = None  # Name of the user who resolved it
    datetime: str  # Formatted datetime string (DD-MMM-YYYY HH:MM AM/PM)
    status_badge: str  # Status with appropriate styling class
    alert_type_badge: str  # Alert type with appropriate styling class


class SystemAlertsReportResponse(BaseModel):
    """Response for System Alerts report"""
    alerts: List[SystemAlertData]
    total_alerts: int
    filters_applied: SystemAlertFilters
    date_range: Dict[str, str]  # from_date, to_date
    summary: Dict[str, Any]  # Statistics summary
    message: Optional[str] = None


# Report Filter Schemas
class ReportFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    employee_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None
    location_ids: Optional[List[int]] = None
    report_type: Optional[str] = None
    status: Optional[str] = None


# Bank Transfer Letter Schemas
class BankTransferLetterFilters(BaseModel):
    period: str = Field(..., description="Period in format MMM-YYYY")
    business_unit: Optional[str] = "All Business Units"
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    employee_search: Optional[str] = None
    format_type: Optional[str] = "generic"  # generic, hdfc, icici, axis, etc.
    business_id: Optional[int] = None  # Added for business isolation


class BankTransferEmployee(BaseModel):
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    bank_ifsc: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None  # Masked account number
    bank_account_full: Optional[str] = None  # Full account number for export
    net_amount: Decimal = Field(default=0)
    gross_amount: Decimal = Field(default=0)
    deductions: Decimal = Field(default=0)
    
    # Additional bank details
    bank_branch: Optional[str] = None
    account_type: Optional[str] = None
    
    # Employee details for verification
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None


class BankTransferLetterResponse(BaseModel):
    period: str
    total_employees: int
    total_amount: Decimal
    employees: List[BankTransferEmployee]
    filters_applied: BankTransferLetterFilters
    summary: Dict[str, Any]
    bank_wise_summary: Dict[str, Any]
    format_type: str = "generic"


# Salary Slip Schemas
class SalarySlipFilters(BaseModel):
    period: str = Field(..., description="Period in format MMM-YYYY")
    business_unit: Optional[str] = "All Business Units"
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    employee: Optional[str] = None
    records: str = "Active"  # All, Active, Inactive
    exclude_hold: bool = True
    amount_rounding: str = "0 decimals"
    unit_rounding: str = "0 decimals"
    records_per_page: int = 1
    options: Dict[str, bool] = Field(default_factory=dict)
    business_id: Optional[int] = None  # Added for business isolation


class SalarySlipEmployee(BaseModel):
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_joining: Optional[date] = None
    date_of_exit: Optional[date] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Personal Details
    esi_ip_number: Optional[str] = None
    pf_uan_number: Optional[str] = None
    income_tax_pan: Optional[str] = None
    aadhar_number: Optional[str] = None
    office_email: Optional[str] = None
    mobile_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    
    # Attendance Data
    presents: int = 0
    absents: int = 0
    week_offs: int = 0
    holidays: int = 0
    paid_leaves: int = 0
    unpaid_leaves: int = 0
    total_days: int = 0
    extra_days: int = 0
    arrear_days: int = 0
    overtime_days: int = 0
    payable_days: int = 0
    unpaid_days: int = 0
    
    # Salary Data
    basic_salary: Decimal = Field(default=0)
    gross_salary: Decimal = Field(default=0)
    net_salary: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    total_earnings: Decimal = Field(default=0)
    
    # Detailed Salary Components
    earnings: Dict[str, Decimal] = Field(default_factory=dict)
    deductions: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Additional Info
    salary_units: Optional[str] = None
    other_info_1: Optional[str] = None
    other_info_2: Optional[str] = None
    other_info_3: Optional[str] = None
    other_info_4: Optional[str] = None
    other_info_5: Optional[str] = None
    
    # Slip Specific Data
    is_provisional: bool = True
    leave_summary: Optional[Dict[str, Any]] = None
    loan_summary: Optional[Dict[str, Any]] = None
    tax_summary: Optional[Dict[str, Any]] = None
    period_date: Optional[str] = None


class SalarySlipResponse(BaseModel):
    period: str
    total_employees: int
    employees: List[SalarySlipEmployee]
    filters_applied: SalarySlipFilters
    summary: Dict[str, Any]
    is_period_closed: bool = False
    disclaimer: str = "This is a system-generated payslip, no signature required."


# Salary Register Schemas
class SalaryRegisterFilters(BaseModel):
    period: str = Field(..., description="Period in format YYYY-MM")
    business_unit: Optional[str] = "All Business Units"
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    employee: Optional[str] = None
    active_records: bool = True
    inactive_records: bool = False
    all_records: bool = False
    exclude_hold: bool = True
    amount_rounding: str = "0 decimals"
    unit_rounding: str = "0 decimals"
    records_per_page: int = 6
    options: Dict[str, bool] = Field(default_factory=dict)
    business_id: Optional[int] = None  # Added for business isolation


class SalaryRegisterEmployee(BaseModel):
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_joining: Optional[date] = None
    date_of_exit: Optional[date] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Personal Details
    esi_ip_number: Optional[str] = None
    pf_uan_number: Optional[str] = None
    income_tax_pan: Optional[str] = None
    aadhar_number: Optional[str] = None
    office_email: Optional[str] = None
    mobile_phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    
    # Attendance Data
    total_days: int = 0
    presents: int = 0
    absents: int = 0
    week_offs: int = 0
    holidays: int = 0
    extra_days: int = 0
    arrear_days: int = 0
    overtime_days: int = 0
    paid_leaves: int = 0
    unpaid_leaves: int = 0
    payable_days: int = 0
    unpaid_days: int = 0
    
    # Salary Data
    basic_salary: Decimal = Field(default=0)
    gross_salary: Decimal = Field(default=0)
    net_salary: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    allowances: Optional[Dict[str, Any]] = None
    deductions: Optional[Dict[str, Any]] = None
    
    # Additional Info
    salary_units: Optional[str] = None
    other_info_1: Optional[str] = None
    other_info_2: Optional[str] = None
    other_info_3: Optional[str] = None
    other_info_4: Optional[str] = None
    other_info_5: Optional[str] = None


class SalaryRegisterResponse(BaseModel):
    period: str
    total_employees: int
    employees: List[SalaryRegisterEmployee]
    filters_applied: SalaryRegisterFilters
    summary: Dict[str, Any]


# Overtime Register Schemas
class OvertimeRegisterFilters(BaseModel):
    """Schema for overtime register filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    payment_date: Optional[str] = None  # YYYY-MM-DD format
    include_inactive_employees: Optional[bool] = False
    include_zero_records: Optional[bool] = False
    detailed_report: Optional[bool] = False
    business_id: Optional[int] = None  # Added for business isolation


class OvertimeRegisterEmployee(BaseModel):
    """Schema for overtime register employee data"""
    id: int
    employee_code: Optional[str] = None
    name: str
    father_name: Optional[str] = None
    sex: Optional[str] = None
    designation: Optional[str] = None
    date: str  # Work date
    overtime_hrs: float = 0.0
    fixed_gross: Decimal = Field(default=0)
    normal_rate: Decimal = Field(default=0)
    overtime_rate: Decimal = Field(default=0)
    overtime_earnings: Decimal = Field(default=0)
    payment_date: Optional[str] = None
    remarks: Optional[str] = None
    
    # Additional details
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None


class OvertimeRegisterResponse(BaseModel):
    """Schema for overtime register response"""
    period: str
    total_employees: int
    total_overtime_hours: float
    total_overtime_earnings: Decimal
    employees: List[OvertimeRegisterEmployee]
    filters_applied: OvertimeRegisterFilters
    summary: Dict[str, Any]


# Cost to Company Report Schemas
class CostToCompanyFilters(BaseModel):
    """Schema for cost to company report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    revision: str = "latest"  # latest, all, dateSpecific
    date_specific: Optional[str] = None  # YYYY-MM-DD format
    employee_search: Optional[str] = None
    active_only: bool = True
    business_id: Optional[int] = None  # Added for business isolation


class CostToCompanySalaryComponent(BaseModel):
    """Schema for individual salary component in CTC"""
    component_name: str
    component_alias: str
    component_type: str  # Fixed, Variable, Deduction
    amount: Decimal = Field(default=0)
    is_employer_contribution: bool = False
    is_payable: bool = True
    percentage_of_basic: Optional[float] = None


class CostToCompanyEmployee(BaseModel):
    """Schema for cost to company employee data"""
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    date_of_joining: Optional[date] = None
    
    # Salary Structure Info
    salary_structure_name: Optional[str] = None
    effective_from: Optional[date] = None
    revision_number: int = 1
    
    # Basic Salary Components
    basic_salary: Decimal = Field(default=0)
    gross_salary: Decimal = Field(default=0)
    total_ctc: Decimal = Field(default=0)
    
    # Detailed Components
    earnings: List[CostToCompanySalaryComponent] = Field(default_factory=list)
    deductions: List[CostToCompanySalaryComponent] = Field(default_factory=list)
    employer_contributions: List[CostToCompanySalaryComponent] = Field(default_factory=list)
    
    # Summary Totals
    total_earnings: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    total_employer_contributions: Decimal = Field(default=0)
    net_payable: Decimal = Field(default=0)


class CostToCompanyResponse(BaseModel):
    """Schema for cost to company response"""
    total_employees: int
    employees: List[CostToCompanyEmployee]
    filters_applied: CostToCompanyFilters
    summary: Dict[str, Any]


# Time Salary Report Schemas
class TimeSalaryFilters(BaseModel):
    """Schema for time salary report filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    salary_component: Optional[str] = None  # Basic, Bonus, etc.
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class TimeSalaryEmployee(BaseModel):
    """Schema for time salary employee data"""
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    
    # Time-based salary details
    payment_type: str  # Hourly, Daily, Monthly
    hourly_rate: Decimal = Field(default=0)
    daily_rate: Decimal = Field(default=0)
    monthly_rate: Decimal = Field(default=0)
    
    # Time calculations
    total_hours: float = 0.0
    total_days: int = 0
    overtime_hours: float = 0.0
    
    # Amount calculations
    regular_amount: Decimal = Field(default=0)
    overtime_amount: Decimal = Field(default=0)
    total_amount: Decimal = Field(default=0)
    
    # Additional details
    shift_name: Optional[str] = None
    attendance_percentage: Optional[float] = None


class TimeSalaryResponse(BaseModel):
    """Schema for time salary response"""
    period: str
    total_employees: int
    total_amount: Decimal
    total_hours: float
    employees: List[TimeSalaryEmployee]
    filters_applied: TimeSalaryFilters
    summary: Dict[str, Any]


# Variable Salary Report Schemas
class VariableSalaryFilters(BaseModel):
    """Schema for variable salary report filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    salary_component: Optional[str] = "Leave Encashment"  # Leave Encashment, Bonus, Gratuity
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class VariableSalaryEmployee(BaseModel):
    """Schema for variable salary employee data"""
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    salary_component: str
    amount: Decimal = Field(default=0)
    
    # Additional details for export
    variable_type: Optional[str] = None
    effective_date: Optional[date] = None
    description: Optional[str] = None


class VariableSalaryResponse(BaseModel):
    """Schema for variable salary response"""
    period: str
    total_employees: int
    total_amount: Decimal
    employees: List[VariableSalaryEmployee]
    filters_applied: VariableSalaryFilters
    summary: Dict[str, Any]


# Statutory Bonus Report Schemas
class StatutoryBonusReportFilters(BaseModel):
    """Schema for statutory bonus report filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    cost_center: Optional[str] = "All Cost Centers"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class StatutoryBonusReportEmployee(BaseModel):
    """Schema for statutory bonus report employee data"""
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    comments: str
    bonus_amount: Decimal = Field(default=0)
    base_salary: Optional[Decimal] = None
    bonus_rate: Optional[float] = None
    eligibility_status: Optional[str] = None
    payment_date: Optional[date] = None
    is_processed: bool = False


class StatutoryBonusReportResponse(BaseModel):
    """Schema for statutory bonus report response"""
    period: str
    total_employees: int
    total_bonus_amount: Decimal
    employees: List[StatutoryBonusReportEmployee]
    filters_applied: StatutoryBonusReportFilters
    summary: Dict[str, Any]


# Leave Encashment Report Schemas
class LeaveEncashmentReportFilters(BaseModel):
    """Schema for leave encashment report filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    cost_center: Optional[str] = "All Cost Centers"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class LeaveEncashmentReportEmployee(BaseModel):
    """Schema for leave encashment report employee data"""
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    position: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    description: str
    leave_type: Optional[str] = None
    leave_balance: Decimal = Field(default=0)
    encashment_days: Decimal = Field(default=0)
    daily_salary: Decimal = Field(default=0)
    encashment_amount: Decimal = Field(default=0)
    payment_period: Optional[date] = None
    balance_as_on: Optional[date] = None
    is_processed: bool = False
    processed_date: Optional[datetime] = None


class LeaveEncashmentReportResponse(BaseModel):
    """Schema for leave encashment report response"""
    period: str
    total_employees: int
    total_amount: Decimal
    employees: List[LeaveEncashmentReportEmployee]
    filters_applied: LeaveEncashmentReportFilters
    summary: Dict[str, Any]


# Rate Salary Report Schemas
class RateSalaryFilters(BaseModel):
    """Schema for rate salary report filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    salary_component: Optional[str] = "- Select -"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class RateSalaryEmployee(BaseModel):
    """Schema for rate salary employee data"""
    id: int
    employee_code: Optional[str] = None
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    salary_component: str
    rate: Decimal = Field(default=0)
    unit: str = "Days"
    amount: Decimal = Field(default=0)
    
    # Additional details for calculations
    basic_salary: Optional[Decimal] = None
    working_days: Optional[int] = None
    component_type: Optional[str] = None


class RateSalaryResponse(BaseModel):
    """Schema for rate salary response"""
    period: str
    total_employees: int
    total_amount: Decimal
    employees: List[RateSalaryEmployee]
    filters_applied: RateSalaryFilters
    summary: Dict[str, Any]


# Report Summary Schemas
class SalarySummary(BaseModel):
    total_employees: int
    total_gross_salary: Decimal
    total_net_salary: Decimal
    total_deductions: Decimal
    average_salary: Decimal


# Salary Deductions Report Schemas
class SalaryDeductionsFilters(BaseModel):
    """Schema for salary deductions report filters"""
    month: str = Field(..., description="Month in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    cost_center: Optional[str] = "All Cost Centers"
    deduction: Optional[str] = "-select-"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class SalaryDeductionsEmployee(BaseModel):
    """Schema for salary deductions employee data"""
    sn: int
    code: Optional[str] = None
    name: str
    dept: Optional[str] = None
    designation: Optional[str] = None
    amount: Decimal = Field(default=0)
    
    # Additional details for backend processing
    employee_id: int
    deduction_type: Optional[str] = None
    deduction_description: Optional[str] = None


class SalaryDeductionsResponse(BaseModel):
    """Schema for salary deductions response"""
    month: str
    total_employees: int
    total_deductions: Decimal
    data: List[SalaryDeductionsEmployee]
    filters_applied: SalaryDeductionsFilters
    summary: Dict[str, Any]


# Employee Loans Report Schemas
class EmployeeLoansFilters(BaseModel):
    """Schema for employee loans report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    issued_during: Optional[str] = "Last 30 days"
    employee_search: Optional[str] = None
    report_type: Optional[str] = "Summary Only"  # "Summary Only" or "With Loan Schedule"
    business_id: Optional[int] = None  # Added for business isolation


class EmployeeLoanData(BaseModel):
    """Schema for employee loan data"""
    id: int
    employee: str
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    loan_type: str
    loan_amount: Decimal = Field(default=0)
    issue_date: str
    interest_method: str
    emi_amount: Decimal = Field(default=0)
    outstanding_amount: Decimal = Field(default=0)
    status: str
    tenure_months: int
    paid_emis: int
    remaining_emis: int
    
    # Additional details for loan schedule
    purpose: Optional[str] = None
    guarantor_name: Optional[str] = None
    guarantor_relation: Optional[str] = None
    first_emi_date: Optional[str] = None
    last_emi_date: Optional[str] = None


class LoanEMISchedule(BaseModel):
    """Schema for loan EMI schedule"""
    emi_number: int
    due_date: str
    paid_date: Optional[str] = None
    emi_amount: Decimal = Field(default=0)
    principal_amount: Decimal = Field(default=0)
    interest_amount: Decimal = Field(default=0)
    is_paid: bool = False
    payment_method: Optional[str] = None
    remarks: Optional[str] = None


class EmployeeLoansResponse(BaseModel):
    """Schema for employee loans response"""
    total_loans: int
    total_loan_amount: Decimal
    total_outstanding_amount: Decimal
    loans: List[EmployeeLoanData]
    filters_applied: EmployeeLoansFilters
    summary: Dict[str, Any]
    loan_schedules: Optional[Dict[int, List[LoanEMISchedule]]] = None  # Only when report_type is "With Loan Schedule"


# SAP Export Report Schemas
class SAPExportFilters(BaseModel):
    """Schema for SAP export filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    format: str = Field(default="xlsx", description="Export format: xlsx or txt")
    business_unit: Optional[str] = "All Business Units"
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class SAPExportEmployee(BaseModel):
    """Schema for SAP export employee data"""
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Bank Details
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_name: Optional[str] = None
    
    # Attendance Data
    total_days: int = 30
    payable_days: int = 22
    presents: int = 22
    absents: int = 0
    overtime_hours: float = 0.0
    
    # Salary Components with SAP Mapping
    basic_salary: Decimal = Field(default=0)
    hra: Decimal = Field(default=0)
    special_allowance: Decimal = Field(default=0)
    medical_allowance: Decimal = Field(default=0)
    conveyance: Decimal = Field(default=0)
    telephone: Decimal = Field(default=0)
    bonus: Decimal = Field(default=0)
    gratuity: Decimal = Field(default=0)
    leave_encashment: Decimal = Field(default=0)
    loan_amount: Decimal = Field(default=0)
    overtime_hours_amount: Decimal = Field(default=0)
    overtime_days_amount: Decimal = Field(default=0)
    retention_bonus: Decimal = Field(default=0)
    
    # Deductions with SAP Mapping
    esi: Decimal = Field(default=0)
    pf: Decimal = Field(default=0)
    voluntary_pf: Decimal = Field(default=0)
    professional_tax: Decimal = Field(default=0)
    income_tax: Decimal = Field(default=0)
    loan_repayment: Decimal = Field(default=0)
    loan_interest: Decimal = Field(default=0)
    group_insurance: Decimal = Field(default=0)
    pf_extra_contribution: Decimal = Field(default=0)
    labour_welfare: Decimal = Field(default=0)
    gratuity_deduction: Decimal = Field(default=0)
    
    # Totals
    gross_salary: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    net_salary: Decimal = Field(default=0)


class SAPExportResponse(BaseModel):
    """Schema for SAP export response"""
    period: str
    total_employees: int
    total_gross_salary: Decimal
    total_net_salary: Decimal
    total_deductions: Decimal
    employees: List[SAPExportEmployee]
    filters_applied: SAPExportFilters
    summary: Dict[str, Any]
    sap_mapping: Optional[Dict[str, Any]] = None
    export_format: str = "xlsx"


# Attendance Register Report Schemas
class AttendanceRegisterFilters(BaseModel):
    """Schema for attendance register filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    from_date: Optional[str] = None  # YYYY-MM-DD format
    to_date: Optional[str] = None    # YYYY-MM-DD format
    employee: Optional[str] = None
    record_type: Optional[str] = "All Records"  # All Records, Active Records, Inactive Records
    show_time_punches: bool = False
    show_strikes: bool = False
    show_time_summary: bool = False
    business_id: Optional[int] = None  # Added for business isolation


class AttendanceDayData(BaseModel):
    """Schema for individual day attendance data"""
    date: int
    day: str  # Mon, Tue, Wed, etc
    status: str  # P, A, W, -
    punch_in: Optional[str] = None  # HH:MM format
    punch_out: Optional[str] = None  # HH:MM format
    total_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    strike_info: Optional[str] = None


class AttendanceRegisterEmployee(BaseModel):
    """Schema for attendance register employee data"""
    sn: int
    name: str
    id: str  # employee code
    des: str  # designation
    employee_id: int
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    days: List[AttendanceDayData]
    presents: int
    absents: int
    week_offs: int
    paid_days: float
    total_hours: Optional[float] = None
    overtime_hours: Optional[float] = None


class AttendanceRegisterResponse(BaseModel):
    """Schema for attendance register response"""
    records: List[AttendanceRegisterEmployee]
    month: str  # NOV-2025 format
    total_records: int
    filters_applied: AttendanceRegisterFilters
    summary: Dict[str, Any]
    date_range: Dict[str, str]  # from_date, to_date


class AttendanceSummary(BaseModel):
    total_employees: int
    present_count: int
    absent_count: int
    leave_count: int
    attendance_percentage: float


# Leave Register Report Schemas
class LeaveRegisterFilters(BaseModel):
    """Schema for leave register filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    year: str = "2025"
    month: str = "December"
    business_id: Optional[int] = None  # Added for business isolation


class LeaveRegisterEmployee(BaseModel):
    """Schema for leave register employee data"""
    employee_name: str
    employee_code: Optional[str] = None
    month: str
    days_worked: str
    maternity: str = "0"
    unpaid_leaves: str
    paid_leaves: str
    wages: str
    
    # Additional fields for backend processing
    employee_id: int
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None


class LeaveRegisterResponse(BaseModel):
    """Schema for leave register response"""
    total_employees: int
    total_records: int
    employees: List[LeaveRegisterEmployee]
    filters_applied: LeaveRegisterFilters
    summary: Dict[str, Any]
    year_range: str
    month_range: str


# Travel Register Report Schemas
class TravelRegisterFilters(BaseModel):
    """Schema for travel register filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    salary_component: Optional[str] = "- Select -"
    date_from: Optional[str] = None  # YYYY-MM-DD format
    date_to: Optional[str] = None    # YYYY-MM-DD format
    employee_id: Optional[str] = None
    exclude_zero_distance: bool = False
    business_id: Optional[int] = None  # Added for business isolation


class TravelRegisterRecord(BaseModel):
    """Schema for individual travel record"""
    id: int
    employee_id: int
    employee_name: str
    employee_code: str
    location: str
    department: str
    calculated_distance: float = 0.0
    approved_distance: float = 0.0
    status: str = "Pending"  # Approved, Pending, Rejected
    travel_date: Optional[date] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    purpose: Optional[str] = None
    travel_allowance: Optional[Decimal] = None

    class Config:
        from_attributes = True


class TravelRegisterResponse(BaseModel):
    """Schema for travel register response"""
    total_records: int
    records: List[TravelRegisterRecord]
    filters_applied: TravelRegisterFilters
    summary: Dict[str, Any]


# Time Punches Report Schemas
class TimePunchesFilters(BaseModel):
    """Schema for time punches filters"""
    business_unit: Optional[str] = "All Business Units"
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    date_from: Optional[str] = None  # YYYY-MM-DD format
    date_to: Optional[str] = None    # YYYY-MM-DD format
    employee: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class TimePunchRecord(BaseModel):
    """Schema for individual punch record"""
    punch_time: str
    punch_type: str
    location: Optional[str] = None
    device_info: Optional[str] = None
    punch_method: Optional[str] = None  # Selfie, Remote, Web/Chat, etc.


class TimePunchesEmployee(BaseModel):
    """Schema for employee time punches data"""
    id: int
    name: str
    code: str
    location: str
    department: str
    role: str
    date: str
    status: str
    in_time: Optional[str] = None
    out_time: Optional[str] = None
    total_hours: str
    punch_type: str
    progress_color: str = "#377dff"
    punches: List[TimePunchRecord] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class TimePunchesResponse(BaseModel):
    """Schema for time punches response"""
    total_employees: int
    employees: List[TimePunchesEmployee]
    filters_applied: TimePunchesFilters
    summary: Dict[str, Any]
    pagination: Dict[str, Any]


# Strike Register Report Schemas
class StrikeRegisterFilters(BaseModel):
    """Schema for strike register filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    cost_center: Optional[str] = "All Cost Centers"
    deduction: Optional[str] = "- Select -"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class StrikeRegisterStrike(BaseModel):
    """Schema for individual strike data"""
    date: str
    shift: str
    strike: str
    strike_count: int
    base_amount: Decimal = Field(default=0)
    deduction_type: Optional[str] = None
    deduction: Decimal = Field(default=0)


class StrikeRegisterEmployee(BaseModel):
    """Schema for strike register employee data"""
    employee_name: str
    employee_code: str
    employee_id: int
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    strikes: List[StrikeRegisterStrike] = Field(default_factory=list)
    total_strikes: int = 0
    total_deductions: Decimal = Field(default=0)


class StrikeRegisterResponse(BaseModel):
    """Schema for strike register response"""
    period: str
    total_employees: int
    employees: List[StrikeRegisterEmployee]
    filters_applied: StrikeRegisterFilters
    summary: Dict[str, Any]


# Time Register Report Schemas
class TimeRegisterFilters(BaseModel):
    """Schema for time register filters"""
    period: str = Field(..., description="Period in format MMM-YYYY")
    business_unit: Optional[str] = "All Business Units"
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    cost_center: Optional[str] = "All Cost Centers"
    salary_component: Optional[str] = None
    show_details: bool = False
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class TimeRegisterEmployee(BaseModel):
    """Schema for time register employee data"""
    id: int
    employee: str
    employee_code: Optional[str] = None
    shift_hrs: str = "0:00"
    early_in: str = "0:00"
    late_in: str = "0:00"
    in_hrs: str = "0:00"
    lunch: str = "0:00"
    out_hrs: str = "0:00"
    early_out: str = "0:00"
    late_out: str = "0:00"
    paid_hrs: str = "-"
    
    # Additional details for backend processing
    employee_id: int
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Time calculations in minutes for processing
    shift_minutes: int = 0
    early_in_minutes: int = 0
    late_in_minutes: int = 0
    in_minutes: int = 0
    lunch_minutes: int = 0
    out_minutes: int = 0
    early_out_minutes: int = 0
    late_out_minutes: int = 0
    paid_minutes: int = 0


class TimeRegisterResponse(BaseModel):
    """Schema for time register response"""
    period: str
    total_employees: int
    employees: List[TimeRegisterEmployee]
    filters_applied: TimeRegisterFilters
    summary: Dict[str, Any]


# Remote Punch Report Schemas
class RemotePunchFilters(BaseModel):
    """Schema for remote punch filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    date_from: Optional[str] = None  # YYYY-MM-DD format
    date_to: Optional[str] = None    # YYYY-MM-DD format
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class RemotePunchRecord(BaseModel):
    """Schema for individual remote punch record"""
    datetime: str
    coords: str
    address: str = "Address Not Fetched"
    punch_type: Optional[str] = "IN"
    device_info: Optional[str] = None
    location_accuracy: Optional[float] = None


class RemotePunchEmployee(BaseModel):
    """Schema for remote punch employee data"""
    id: int
    name: str
    employee_code: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    punches: List[RemotePunchRecord] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class RemotePunchResponse(BaseModel):
    """Schema for remote punch response"""
    total_employees: int
    employees: List[RemotePunchEmployee]
    filters_applied: RemotePunchFilters
    summary: Dict[str, Any]
    date_range: Dict[str, str]


# Manual Updates Report Schemas
class ManualUpdatesFilters(BaseModel):
    """Schema for manual updates filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    month: Optional[str] = None  # Format: "August 2025" or "AUG-2025"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class ManualUpdateRecord(BaseModel):
    """Schema for individual manual update record"""
    employee_code: str
    employee_name: str
    date: str  # YYYY-MM-DD format
    original_status: str
    updated_status: str
    updated_by: str
    reason: str
    update_time: Optional[str] = None  # HH:MM format
    
    class Config:
        from_attributes = True


class ManualUpdatesResponse(BaseModel):
    """Schema for manual updates response"""
    total_records: int
    records: List[ManualUpdateRecord]
    filters_applied: ManualUpdatesFilters
    summary: Dict[str, Any]
    month_info: Dict[str, str]


# Employee Register Options Schemas
class EmployeeRegisterFilters(BaseModel):
    """Schema for employee register filters"""
    location: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    selected_date: Optional[str] = None  # YYYY-MM-DD format
    records_per_page: Optional[int] = 20
    business_id: Optional[int] = None  # Added for business isolation


class EmployeeRegisterOptions(BaseModel):
    """Schema for employee register field options"""
    # Basic Details
    employee_code: bool = False
    employee_name: bool = True
    gender: bool = False
    dob: bool = False
    doj: bool = False
    doe: bool = True
    
    # Work Profile
    location: bool = True
    cost_center: bool = False
    department: bool = True
    grade: bool = True
    designation: bool = True
    pan: bool = True
    esi: bool = False
    pf_uan: bool = True
    
    # Personal Details
    aadhaar: bool = True
    office_email: bool = False
    office_phone: bool = False
    mobile: bool = True
    bank_name: bool = True
    bank_ifsc: bool = True
    bank_account: bool = False
    
    # Extra Info
    home_phone: bool = True
    personal_email: bool = True
    other_info1: bool = True
    other_info2: bool = True
    other_info3: bool = True
    other_info4: bool = True
    other_info5: bool = True


class EmployeeRegisterRecord(BaseModel):
    """Schema for individual employee register record - dynamically includes only selected fields"""
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None  # YYYY-MM-DD format
    doj: Optional[str] = None  # YYYY-MM-DD format
    doe: Optional[str] = None  # YYYY-MM-DD format
    location: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    grade: Optional[str] = None
    designation: Optional[str] = None
    pan: Optional[str] = None
    esi: Optional[str] = None
    pf_uan: Optional[str] = None
    aadhaar: Optional[str] = None
    office_email: Optional[str] = None
    office_phone: Optional[str] = None
    mobile: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    home_phone: Optional[str] = None
    personal_email: Optional[str] = None
    other_info1: Optional[str] = None
    other_info2: Optional[str] = None
    other_info3: Optional[str] = None
    other_info4: Optional[str] = None
    other_info5: Optional[str] = None
    
    class Config:
        from_attributes = True


class EmployeeRegisterResponse(BaseModel):
    """Schema for employee register response"""
    total_employees: int
    employees: List[EmployeeRegisterRecord]
    filters_applied: EmployeeRegisterFilters
    options_applied: EmployeeRegisterOptions
    summary: Dict[str, Any]


class ReportDashboard(BaseModel):
    salary_summary: SalarySummary
    attendance_summary: AttendanceSummary
    total_reports_generated: int
    pending_reports: int


# Employee Addresses Report Schemas
class EmployeeAddressesFilters(BaseModel):
    """Schema for employee addresses report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class EmployeeAddressRecord(BaseModel):
    """Schema for individual employee address record"""
    id: int
    name: str
    code: str
    type: str  # "Present" or "Permanent"
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    class Config:
        from_attributes = True


class EmployeeAddressesResponse(BaseModel):
    """Schema for employee addresses response"""
    total_employees: int
    total_addresses: int
    addresses: List[EmployeeAddressRecord]
    filters_applied: EmployeeAddressesFilters
    summary: Dict[str, Any]


# Employee Events Report Schemas
class EmployeeEventsFilters(BaseModel):
    """Schema for employee events report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    show_birthdays: bool = True
    show_work_anniversaries: bool = True
    show_wedding_anniversaries: bool = True
    from_month: Optional[str] = "January"
    to_month: Optional[str] = "December"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class EmployeeEventRecord(BaseModel):
    """Schema for individual employee event record"""
    date: str  # Format: "Aug 01,2002"
    type: str  # "Birthday", "Work Anniversary", "Wedding Anniversary"
    icon: str  # "bi bi-cake-fill", "bi bi-briefcase-fill", "bi bi-heart-fill"
    iconColor: str  # "aqua", "green", "red"
    employee: str  # Full name
    code: str  # Employee code
    location: str
    department: str
    designation: str
    
    class Config:
        from_attributes = True


class EmployeeEventsResponse(BaseModel):
    """Schema for employee events response"""
    total_events: int
    events: List[EmployeeEventRecord]
    filters_applied: EmployeeEventsFilters
    summary: Dict[str, Any]


# Promotion Age Report Schemas
class PromotionAgeFilters(BaseModel):
    """Schema for promotion age report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    ageing: Optional[str] = "All Employees"
    grade: Optional[str] = "All Grades"
    business_id: Optional[int] = None  # Added for business isolation


class PromotionAgeEmployee(BaseModel):
    """Schema for individual promotion age employee record"""
    sn: int
    name: str
    designation: str
    department: str
    location: str
    costCenter: str
    grade: str
    lastPromoted: str  # Format: "YYYY-MM-DD"
    ageing: str  # Format: "2 Years 5 Months"
    
    class Config:
        from_attributes = True


class PromotionAgeResponse(BaseModel):
    """Schema for promotion age response"""
    employees: List[PromotionAgeEmployee]
    filters_applied: PromotionAgeFilters
    summary: Dict[str, Any]


# Increment Ageing Report Schemas
class IncrementAgeingFilters(BaseModel):
    """Schema for increment ageing report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    ageing: Optional[str] = "All Employees"
    grade: Optional[str] = "All Grades"
    business_id: Optional[int] = None  # Added for business isolation


class IncrementAgeingEmployee(BaseModel):
    """Schema for individual increment ageing employee record"""
    id: int
    name: str
    code: str
    designation: str
    department: str
    lastIncrement: str  # Format: "Jan 2023" or "Never"
    lastIncrementDate: Optional[str]  # Format: "YYYY-MM-DD" or null
    location: str
    costCenter: str
    grade: str
    ageing: str  # Format: "2 Years 5 Months ago" or "Never"
    
    class Config:
        from_attributes = True


class IncrementAgeingResponse(BaseModel):
    """Schema for increment ageing response"""
    employees: List[IncrementAgeingEmployee]
    filters_applied: IncrementAgeingFilters
    summary: Dict[str, Any]


# Employee Joinings Report Schemas
class EmployeeJoiningFilters(BaseModel):
    """Schema for employee joinings report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    grade: Optional[str] = "All Grades"
    from_date: Optional[str] = None  # YYYY-MM-DD format
    to_date: Optional[str] = None    # YYYY-MM-DD format
    business_id: Optional[int] = None  # Added for business isolation


class EmployeeJoiningEmployee(BaseModel):
    """Schema for individual employee joining record"""
    id: int
    name: str
    code: str
    joining: str  # Format: "YYYY-MM-DD"
    confirmation: str  # Format: "YYYY-MM-DD" 
    location: str
    department: str
    designation: str
    grade: str
    cost_center: str
    
    class Config:
        from_attributes = True


class EmployeeJoiningResponse(BaseModel):
    """Schema for employee joinings response"""
    employees: List[EmployeeJoiningEmployee]
    filters_applied: EmployeeJoiningFilters
    summary: Dict[str, Any]


# Employee Exits Report Schemas
class EmployeeExitFilters(BaseModel):
    """Schema for employee exits report filters"""
    location: Optional[str] = "All Locations"
    department: Optional[str] = "All Departments"
    cost_center: Optional[str] = "All Cost Centers"
    exit_reason: Optional[str] = "All Reasons"
    from_date: Optional[str] = None  # YYYY-MM-DD format
    to_date: Optional[str] = None    # YYYY-MM-DD format
    business_id: Optional[int] = None  # Added for business isolation


class EmployeeExitEmployee(BaseModel):
    """Schema for individual employee exit record"""
    id: int
    name: str
    code: str
    location: str
    department: str
    designation: str
    joining: str  # Format: "YYYY-MM-DD"
    exit: str     # Format: "YYYY-MM-DD"
    reason: str
    
    class Config:
        from_attributes = True


class EmployeeExitResponse(BaseModel):
    """Schema for employee exits response"""
    employees: List[EmployeeExitEmployee]
    filters_applied: EmployeeExitFilters
    summary: Dict[str, Any]


# Vaccination Status Report Schemas
class VaccinationStatusFilters(BaseModel):
    """Schema for vaccination status report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    status: Optional[str] = "Vaccinated"  # Vaccinated or Not Vaccinated
    business_id: Optional[int] = None  # Added for business isolation


class VaccinationStatusEmployee(BaseModel):
    """Schema for vaccination status employee record"""
    id: int
    emp_code: str = Field(alias="empCode")
    name: str
    location: str
    department: str
    status: str  # Vaccinated or Not Vaccinated
    
    class Config:
        populate_by_name = True


class VaccinationStatusResponse(BaseModel):
    """Schema for vaccination status response"""
    employees: List[VaccinationStatusEmployee]
    filters_applied: VaccinationStatusFilters
    summary: Dict[str, Any]


# Workman Status Report Schemas
class WorkmanStatusFilters(BaseModel):
    """Schema for workman status report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    inactive_only: Optional[bool] = False
    business_id: Optional[int] = None  # Added for business isolation


class WorkmanStatusEmployee(BaseModel):
    """Schema for workman status employee record"""
    id: int
    emp_id: str  # Employee ID like LEV098
    name: str
    location: str
    dept: str  # Department
    installed: bool
    version: str
    last_seen: str
    
    class Config:
        populate_by_name = True


class WorkmanStatusResponse(BaseModel):
    """Schema for workman status response"""
    employees: List[WorkmanStatusEmployee]
    filters_applied: WorkmanStatusFilters
    summary: Dict[str, Any]


# Employee Assets Report Schemas
class EmployeeAssetsFilters(BaseModel):
    """Schema for employee assets report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    search: Optional[str] = None
    warranty_only: Optional[bool] = False
    active_only: Optional[bool] = True
    business_id: Optional[int] = None  # Added for business isolation


class AssetDetail(BaseModel):
    """Schema for asset detail"""
    id: int
    type: str
    name: str
    serial_number: str = Field(alias="serialNumber")
    issued_date: str = Field(alias="issuedDate")
    warranty_expiry_date: str = Field(alias="warrantyExpiryDate")
    estimated_value: float = Field(alias="estimatedValue")
    icon: str
    warranty_status: str
    
    class Config:
        populate_by_name = True


class EmployeeAssetsEmployee(BaseModel):
    """Schema for employee assets employee record"""
    id: int
    employee_code: str = Field(alias="employeeCode")
    employee_name: str = Field(alias="employeeName")
    department: str
    location: str
    assets: List[AssetDetail]
    
    class Config:
        populate_by_name = True


class EmployeeAssetsResponse(BaseModel):
    """Schema for employee assets response"""
    employees: List[EmployeeAssetsEmployee]
    filters_applied: EmployeeAssetsFilters
    summary: Dict[str, Any]


# Employee Relatives Report Schemas
class EmployeeRelativesFilters(BaseModel):
    """Schema for employee relatives report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    active_only: Optional[bool] = False
    business_id: Optional[int] = None  # Added for business isolation


class RelativeDetail(BaseModel):
    """Schema for relative detail"""
    relation: str
    relativeName: str
    dob: str
    dependent: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    notes: Optional[str] = ""


class EmployeeRelativesEmployee(BaseModel):
    """Schema for employee relatives employee record"""
    sn: int
    code: str
    name: str
    location: str
    costCenter: str
    department: str
    active: bool
    relatives: List[RelativeDetail]


class EmployeeRelativesResponse(BaseModel):
    """Schema for employee relatives response"""
    employees: List[EmployeeRelativesEmployee]
    filters_applied: EmployeeRelativesFilters
    summary: Dict[str, Any]


# Inactive Employees Report Schemas
class InactiveEmployeesFilters(BaseModel):
    """Schema for inactive employees report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    business_id: Optional[int] = None  # Added for business isolation


class InactiveEmployee(BaseModel):
    """Schema for inactive employee data"""
    photo: str
    name: str
    code: str
    joiningDate: str
    location: str
    costCenter: str
    department: str
    designation: str


class InactiveEmployeesResponse(BaseModel):
    """Schema for inactive employees response"""
    employees: List[InactiveEmployee]
    filters_applied: InactiveEmployeesFilters
    summary: Dict[str, Any]


# Export Records Schemas
class ExportRecordsFilters(BaseModel):
    """Schema for export records filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    record_type: Optional[str] = "all"  # all, active, inactive
    business_id: Optional[int] = None  # Added for business isolation


class ExportRecordEmployee(BaseModel):
    """Schema for export record employee data"""
    name: str
    location: str
    department: str
    costCenter: str
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    date_of_joining: Optional[str] = None
    employee_status: Optional[str] = None


class ExportRecordsResponse(BaseModel):
    """Schema for export records response"""
    employees: List[ExportRecordEmployee]
    filters_applied: ExportRecordsFilters
    summary: Dict[str, Any]
    total_records: int

# ESI Deduction Report Schemas
class ESIDeductionFilters(BaseModel):
    """Schema for ESI deduction report filters"""
    month: str = Field(..., description="Month in format MMM-YYYY (e.g., NOV-2025)")
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    report_type: Optional[str] = "ESI Return"  # ESI Return, ESI Summary
    business_id: Optional[int] = None  # Added for business isolation


class ESIDeductionEmployee(BaseModel):
    """Schema for ESI deduction employee data"""
    id: int
    name: str
    ip: str  # ESI IP Number
    days: int
    wages: Decimal = Field(default=0)
    employee: Decimal = Field(default=0)  # Employee contribution
    employer: Decimal = Field(default=0)  # Employer contribution
    reason: str = "-"  # Reason for 0 days
    lastWorking: str  # Last working date in DD/MM/YYYY format
    
    # Additional fields for backend processing
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None


class ESIDeductionResponse(BaseModel):
    """Schema for ESI deduction response"""
    employees: List[ESIDeductionEmployee]
    filters_applied: ESIDeductionFilters
    summary: Dict[str, Any]
    total_employees: int
    total_wages: Decimal = Field(default=0)
    total_employee_contribution: Decimal = Field(default=0)
    total_employer_contribution: Decimal = Field(default=0)
    total_employee_contribution: Decimal = Field(default=0)
    total_employer_contribution: Decimal = Field(default=0)
    total_employee_contribution: Decimal = Field(default=0)
    total_employer_contribution: Decimal = Field(default=0)
# ESI Coverage Report Schemas
class ESICoverageFilters(BaseModel):
    """Schema for ESI coverage report filters"""
    month: str = Field(..., description="Month in format MMM-YYYY (e.g., NOV-2025)")
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    business_id: Optional[int] = None  # Added for business isolation


class ESICoverageStats(BaseModel):
    """Schema for ESI coverage statistics"""
    total_employees: int = 0
    esi_deducted: int = 0
    esi_eligible: int = 0
    esi_not_eligible: int = 0
    total_esi_amount: Decimal = Field(default=0)
    average_esi_per_employee: Decimal = Field(default=0)


class ESICoverageResponse(BaseModel):
    """Schema for ESI coverage response"""
    stats: ESICoverageStats
    filters_applied: ESICoverageFilters
    summary: Dict[str, Any]
    period: str
# PF Deduction Report Schemas
class PFDeductionFilters(BaseModel):
    """Schema for PF deduction report filters"""
    month: str = Field(..., description="Month in format MMM-YYYY (e.g., AUG-2025)")
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    ignore_ncp_days: Optional[bool] = False  # Ignore NCP (Non-Contributing Period) Days
    business_id: Optional[int] = None  # Added for business isolation
    
    @field_validator('month')
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        """Validate month is in MMM-YYYY format"""
        if not v:
            raise ValueError("Month is required")
        
        # Check format: MMM-YYYY (e.g., FEB-2026)
        parts = v.split('-')
        if len(parts) != 2:
            raise ValueError("Month must be in format MMM-YYYY (e.g., FEB-2026)")
        
        month_abbr, year = parts
        
        # Validate month abbreviation (3 letters)
        if len(month_abbr) != 3 or not month_abbr.isalpha():
            raise ValueError("Month abbreviation must be 3 letters (e.g., JAN, FEB, MAR)")
        
        # Validate year (4 digits)
        if len(year) != 4 or not year.isdigit():
            raise ValueError("Year must be 4 digits (e.g., 2026)")
        
        # Validate month is valid by trying to parse it
        try:
            datetime.strptime(v, "%b-%Y")
        except ValueError:
            raise ValueError(f"Invalid month abbreviation: {month_abbr}. Use JAN, FEB, MAR, etc.")
        
        return v.upper()  # Ensure uppercase


class PFDeductionEmployee(BaseModel):
    """Schema for PF deduction employee data"""
    sn: int
    employee: str  # Employee name
    uan_number: str  # UAN Number
    gross_wages: Decimal = Field(default=0)
    wages: Decimal = Field(default=0)
    pf_wages: Decimal = Field(default=0)
    pension_wages: Decimal = Field(default=0)
    employee_cont: Decimal = Field(default=0)  # Employee contribution
    pension_cont: Decimal = Field(default=0)   # Pension contribution
    employer_cont: Decimal = Field(default=0)  # Employer contribution
    
    # Additional fields for backend processing
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None


class PFDeductionResponse(BaseModel):
    """Schema for PF deduction response"""
    employees: List[PFDeductionEmployee]
    filters_applied: PFDeductionFilters
    summary: Dict[str, Any]
    total_employees: int
    total_gross_wages: Decimal = Field(default=0)
    total_pf_wages: Decimal = Field(default=0)
    total_employee_contribution: Decimal = Field(default=0)
    total_employer_contribution: Decimal = Field(default=0)
    total_pension_contribution: Decimal = Field(default=0)
# PF Coverage Report Schemas
class PFCoverageFilters(BaseModel):
    """Schema for PF coverage report filters"""
    month: str = Field(..., description="Month in format MMM-YYYY (e.g., NOV-2025)")
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    business_id: Optional[int] = None  # Added for business isolation
    
    @field_validator('month')
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        """Validate month is in MMM-YYYY format"""
        if not v:
            raise ValueError("Month is required")
        
        # Check format: MMM-YYYY (e.g., FEB-2026)
        parts = v.split('-')
        if len(parts) != 2:
            raise ValueError("Month must be in format MMM-YYYY (e.g., NOV-2025)")
        
        month_abbr, year = parts
        
        # Validate month abbreviation (3 letters)
        if len(month_abbr) != 3 or not month_abbr.isalpha():
            raise ValueError("Month abbreviation must be 3 letters (e.g., JAN, FEB, MAR)")
        
        # Validate year (4 digits)
        if len(year) != 4 or not year.isdigit():
            raise ValueError("Year must be 4 digits (e.g., 2025)")
        
        # Try to parse to ensure it's a valid month
        from datetime import datetime
        try:
            datetime.strptime(v, "%b-%Y")
        except ValueError:
            raise ValueError(f"Invalid month: {v}. Must be in format MMM-YYYY (e.g., NOV-2025)")
        
        return v.upper()  # Ensure uppercase




class PFCoverageStats(BaseModel):
    """Schema for PF coverage statistics"""
    total_employees: int = 0
    pf_deducted: int = 0
    pf_eligible: int = 0
    pf_not_eligible: int = 0
    total_pf_amount: Decimal = Field(default=0)
    average_pf_per_employee: Decimal = Field(default=0)


class PFCoverageResponse(BaseModel):
    """Schema for PF coverage response"""
    stats: PFCoverageStats
    filters_applied: PFCoverageFilters
    summary: Dict[str, Any]
    period: str


# Income Tax Declaration Report Schemas
class IncomeTaxDeclarationFilters(BaseModel):
    """Schema for income tax declaration report filters"""
    location: Optional[str] = "All Locations"
    financial_year: Optional[str] = "2025-26"
    active_employees_only: bool = False
    exclude_no_declarations: bool = False
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class IncomeTaxDeclarationEmployee(BaseModel):
    """Schema for income tax declaration employee data"""
    id: int
    name: str
    employee_code: Optional[str] = None
    pan: Optional[str] = None
    updated: Optional[str] = None  # Last updated date
    chapter_via: str = ""  # Chapter VI-A deductions summary
    rent: str = "₹0"  # Rent paid
    regime: str = "Old"  # Tax regime (Old/New)
    
    # Additional backend fields
    employee_id: int
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    financial_year: str
    status: str = "draft"
    
    # Detailed deduction amounts
    total_80c: Decimal = Field(default=0)
    pf_amount: Decimal = Field(default=0)
    life_insurance: Decimal = Field(default=0)
    elss_mutual_funds: Decimal = Field(default=0)
    home_loan_principal: Decimal = Field(default=0)
    tuition_fees: Decimal = Field(default=0)
    other_80c: Decimal = Field(default=0)
    section_80d_medical: Decimal = Field(default=0)
    section_24_home_loan_interest: Decimal = Field(default=0)
    section_80g_donations: Decimal = Field(default=0)
    hra_exemption: Decimal = Field(default=0)
    rent_paid: Decimal = Field(default=0)
    landlord_name: Optional[str] = None
    landlord_pan: Optional[str] = None
    
    # Timestamps
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IncomeTaxDeclarationResponse(BaseModel):
    """Schema for income tax declaration response"""
    total_employees: int
    employees: List[IncomeTaxDeclarationEmployee]
    filters_applied: IncomeTaxDeclarationFilters
    summary: Dict[str, Any]
    financial_year: str

# Income Tax Computation Report Schemas
class IncomeTaxComputationFilters(BaseModel):
    """Schema for income tax computation report filters"""
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    month: str = "AUG-2025"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None  # Added for business isolation


class IncomeTaxComputationReport(BaseModel):
    """Schema for income tax computation report data"""
    id: int
    description: str
    requested_on: str  # Formatted datetime
    status: str = "ready"  # ready, loading, failed
    download_url: Optional[str] = None
    employee_count: int = 0
    month: str
    
    # Additional backend fields
    total_tax_liability: Decimal = Field(default=0)
    total_tds_amount: Decimal = Field(default=0)
    total_gross_salary: Decimal = Field(default=0)
    created_at: Optional[datetime] = None


class IncomeTaxComputationEmployee(BaseModel):
    """Schema for individual employee tax computation"""
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    
    # Salary details
    gross_salary: Decimal = Field(default=0)
    basic_salary: Decimal = Field(default=0)
    
    # Tax computation
    taxable_income: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    exemptions: Decimal = Field(default=0)
    
    # From IT declarations
    deductions_80c: Decimal = Field(default=0)
    deductions_80d: Decimal = Field(default=0)
    other_deductions: Decimal = Field(default=0)
    hra_exemption: Decimal = Field(default=0)
    
    # Tax calculation
    tax_slab_rate: Decimal = Field(default=0)
    annual_tax_liability: Decimal = Field(default=0)
    monthly_tds: Decimal = Field(default=0)
    months_remaining: int = 12
    
    # TDS details
    tds_deducted_ytd: Decimal = Field(default=0)
    tds_current_month: Decimal = Field(default=0)


class IncomeTaxComputationResponse(BaseModel):
    """Schema for income tax computation response"""
    total_employees: int
    month: str
    reports: List[IncomeTaxComputationReport]
    filters_applied: IncomeTaxComputationFilters
    summary: Dict[str, Any]
    employees: Optional[List[IncomeTaxComputationEmployee]] = None


# Labour Welfare Fund Report Schemas
class LabourWelfareFundFilters(BaseModel):
    """Schema for Labour Welfare Fund report filters"""
    month: str = Field(..., description="Month in format MMM-YYYY")
    location: Optional[str] = "All Locations"
    cost_center: Optional[str] = "All Cost Centers"
    department: Optional[str] = "All Departments"
    employee_search: Optional[str] = None
    business_id: Optional[int] = None


class LabourWelfareFundEmployee(BaseModel):
    """Schema for Labour Welfare Fund employee data"""
    sn: int
    employee_code: Optional[str] = None
    employee_name: str
    location: Optional[str] = None
    state: Optional[str] = None
    salary: Decimal = Field(default=0)
    deduction: Decimal = Field(default=0)
    contribution: Decimal = Field(default=0)
    
    # Additional details for backend processing
    employee_id: int
    department: Optional[str] = None
    designation: Optional[str] = None
    lwf_applicable: bool = True


class LabourWelfareFundResponse(BaseModel):
    """Schema for Labour Welfare Fund response"""
    month: str
    total_employees: int
    total_salary: Decimal
    total_deduction: Decimal
    total_contribution: Decimal
    employees: List[LabourWelfareFundEmployee]
    filters_applied: LabourWelfareFundFilters
    summary: Dict[str, Any]


# Annual Salary Summary Report Schemas
class AnnualSalarySummaryFilters(BaseModel):
    """Filters for Annual Salary Summary report"""
    financial_year: str = Field(..., description="Financial year in format YYYY-YY (e.g., 2024-25)")
    location: Optional[str] = Field("All Locations", description="Location filter")
    department: Optional[str] = Field("All Departments", description="Department filter")
    cost_center: Optional[str] = Field("All Cost Centers", description="Cost center filter")
    employee_grade: Optional[str] = Field("All Grades", description="Employee grade filter")
    business_id: Optional[int] = None

class AnnualSalarySummaryEmployee(BaseModel):
    """Employee details for Annual Salary Summary"""
    employee_id: int
    employee_code: str
    employee_name: str
    designation: str
    department: str
    location: str
    cost_center: Optional[str] = None
    grade: Optional[str] = None
    date_of_joining: Optional[date] = None
    
    # Annual salary breakdown
    annual_basic: Decimal = Field(default=0)
    annual_hra: Decimal = Field(default=0)
    annual_special_allowance: Decimal = Field(default=0)
    annual_other_allowances: Decimal = Field(default=0)
    annual_gross_salary: Decimal = Field(default=0)
    
    # Annual deductions
    annual_pf: Decimal = Field(default=0)
    annual_esi: Decimal = Field(default=0)
    annual_professional_tax: Decimal = Field(default=0)
    annual_tds: Decimal = Field(default=0)
    annual_other_deductions: Decimal = Field(default=0)
    annual_total_deductions: Decimal = Field(default=0)
    
    # Net salary
    annual_net_salary: Decimal = Field(default=0)
    
    # Additional details
    months_worked: int = Field(default=12)
    average_monthly_gross: Decimal = Field(default=0)
    average_monthly_net: Decimal = Field(default=0)

class AnnualSalarySummaryDepartment(BaseModel):
    """Department-wise summary for Annual Salary Summary"""
    department_name: str
    employee_count: int
    total_annual_gross: Decimal = Field(default=0)
    total_annual_net: Decimal = Field(default=0)
    total_annual_deductions: Decimal = Field(default=0)
    average_annual_gross: Decimal = Field(default=0)
    average_annual_net: Decimal = Field(default=0)

class AnnualSalarySummaryLocation(BaseModel):
    """Location-wise summary for Annual Salary Summary"""
    location_name: str
    employee_count: int
    total_annual_gross: Decimal = Field(default=0)
    total_annual_net: Decimal = Field(default=0)
    total_annual_deductions: Decimal = Field(default=0)
    average_annual_gross: Decimal = Field(default=0)
    average_annual_net: Decimal = Field(default=0)

class AnnualSalarySummaryGrade(BaseModel):
    """Grade-wise summary for Annual Salary Summary"""
    grade_name: str
    employee_count: int
    total_annual_gross: Decimal = Field(default=0)
    total_annual_net: Decimal = Field(default=0)
    total_annual_deductions: Decimal = Field(default=0)
    average_annual_gross: Decimal = Field(default=0)
    average_annual_net: Decimal = Field(default=0)

class AnnualSalarySummaryOverall(BaseModel):
    """Overall summary for Annual Salary Summary"""
    total_employees: int
    total_annual_gross: Decimal = Field(default=0)
    total_annual_net: Decimal = Field(default=0)
    total_annual_deductions: Decimal = Field(default=0)
    average_annual_gross: Decimal = Field(default=0)
    average_annual_net: Decimal = Field(default=0)
    
    # Breakdown by components
    total_annual_basic: Decimal = Field(default=0)
    total_annual_hra: Decimal = Field(default=0)
    total_annual_allowances: Decimal = Field(default=0)
    total_annual_pf: Decimal = Field(default=0)
    total_annual_esi: Decimal = Field(default=0)
    total_annual_tds: Decimal = Field(default=0)

class AnnualSalarySummaryResponse(BaseModel):
    """Response for Annual Salary Summary report"""
    financial_year: str
    employees: List[AnnualSalarySummaryEmployee]
    department_summary: List[AnnualSalarySummaryDepartment]
    location_summary: List[AnnualSalarySummaryLocation]
    grade_summary: List[AnnualSalarySummaryGrade]
    overall_summary: AnnualSalarySummaryOverall
    filters_applied: AnnualSalarySummaryFilters
    summary: Dict[str, Any]

# Income Tax Form 16 Report Schemas
class IncomeTaxForm16Filters(BaseModel):
    """Filters for Income Tax Form 16 report"""
    financial_year: str = Field(..., description="Financial year in format YYYY-YY (e.g., 2024-25)")
    employee_id: Optional[int] = Field(None, description="Specific employee ID (optional)")
    employee_code: Optional[str] = Field(None, description="Specific employee code (optional)")
    location: Optional[str] = Field("All Locations", description="Location filter")
    department: Optional[str] = Field("All Departments", description="Department filter")
    cost_center: Optional[str] = Field("All Cost Centers", description="Cost center filter")
    business_id: Optional[int] = None

class IncomeTaxForm16Employee(BaseModel):
    """Employee details for Form 16"""
    employee_id: int
    employee_code: str
    employee_name: str
    designation: str
    department: str
    location: str
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    date_of_joining: Optional[date] = None
    
    # Address details
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class IncomeTaxForm16Salary(BaseModel):
    """Salary details for Form 16"""
    gross_salary: Decimal = Field(default=Decimal('0'))
    basic_salary: Decimal = Field(default=Decimal('0'))
    hra: Decimal = Field(default=Decimal('0'))
    special_allowance: Decimal = Field(default=Decimal('0'))
    other_allowances: Decimal = Field(default=Decimal('0'))
    
    # Deductions
    pf_employee: Decimal = Field(default=Decimal('0'))
    esi_employee: Decimal = Field(default=Decimal('0'))
    professional_tax: Decimal = Field(default=Decimal('0'))
    other_deductions: Decimal = Field(default=Decimal('0'))
    
    # Net salary
    net_salary: Decimal = Field(default=Decimal('0'))

class IncomeTaxForm16TaxDetails(BaseModel):
    """Tax computation details for Form 16"""
    # Income details
    gross_total_income: Decimal = Field(default=Decimal('0'))
    income_chargeable_under_head_salary: Decimal = Field(default=Decimal('0'))
    
    # Deductions under Chapter VI-A
    section_80c: Decimal = Field(default=Decimal('0'))
    section_80d: Decimal = Field(default=Decimal('0'))
    section_80e: Decimal = Field(default=Decimal('0'))
    section_80g: Decimal = Field(default=Decimal('0'))
    other_deductions: Decimal = Field(default=Decimal('0'))
    total_deductions: Decimal = Field(default=Decimal('0'))
    
    # Tax computation
    total_income: Decimal = Field(default=Decimal('0'))
    tax_on_total_income: Decimal = Field(default=Decimal('0'))
    education_cess: Decimal = Field(default=Decimal('0'))
    total_tax_payable: Decimal = Field(default=Decimal('0'))
    
    # Tax deducted
    tds_deducted: Decimal = Field(default=Decimal('0'))
    balance_tax: Decimal = Field(default=Decimal('0'))

class IncomeTaxForm16Quarter(BaseModel):
    """Quarterly TDS details for Form 16"""
    quarter: str
    period: str
    tds_amount: Decimal = Field(default=Decimal('0'))
    challan_number: Optional[str] = None
    deposit_date: Optional[date] = None
    
class IncomeTaxForm16Employer(BaseModel):
    """Employer details for Form 16"""
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    place_of_issue: Optional[str] = None
    tan_number: Optional[str] = None
    pan_number: Optional[str] = None

class IncomeTaxForm16PersonResponsible(BaseModel):
    """Person responsible details for Form 16"""
    full_name: str
    designation: str
    father_name: str
    signature_path: Optional[str] = None

class IncomeTaxForm16Certificate(BaseModel):
    """Complete Form 16 certificate"""
    financial_year: str
    employee: IncomeTaxForm16Employee
    employer: IncomeTaxForm16Employer
    person_responsible: IncomeTaxForm16PersonResponsible
    salary_details: IncomeTaxForm16Salary
    tax_details: IncomeTaxForm16TaxDetails
    quarterly_tds: List[IncomeTaxForm16Quarter]
    
    # Certificate details
    certificate_number: Optional[str] = None
    issue_date: date
    place_of_issue: Optional[str] = None

class IncomeTaxForm16Response(BaseModel):
    """Response for Income Tax Form 16 report"""
    financial_year: str
    certificates: List[IncomeTaxForm16Certificate]
    filters_applied: IncomeTaxForm16Filters
    summary: Dict[str, Any]

# TDS Return Report Schemas
class TDSReturnFilters(BaseModel):
    """Schema for TDS Return report filters"""
    financial_year: str = Field(..., description="Financial year in format YYYY-YY (e.g., 2024-25)")
    quarter: Optional[str] = None  # Q1, Q2, Q3, Q4 or None for all quarters
    return_type: Optional[str] = "24Q"  # 24Q, 26Q, 27Q, etc.
    business_id: Optional[int] = None


class TDSReturnChallanDetail(BaseModel):
    """Schema for TDS Return challan details"""
    month: str
    period: Optional[str] = None
    nil_return: bool = False
    book_entry: str = "No"  # Yes/No
    challan_serial_no: Optional[str] = None
    minor_head: str = "200"  # 200 = TDS payable by taxpayer, 400 = TDS regular assessment
    branch_code: Optional[str] = None
    challan_date: Optional[date] = None
    payment_date: Optional[date] = None
    deposit_date: Optional[date] = None
    
    # Tax amounts
    income_tax: Decimal = Field(default=0)
    surcharge: Decimal = Field(default=0)
    cess: Decimal = Field(default=0)
    interest: Decimal = Field(default=0)
    others: Decimal = Field(default=0)
    fee: Decimal = Field(default=0)
    
    # Payroll amounts for comparison
    payroll_income_tax: Decimal = Field(default=0)
    payroll_surcharge: Decimal = Field(default=0)
    payroll_cess: Decimal = Field(default=0)


class TDSReturnQuarter(BaseModel):
    """Schema for TDS Return quarterly data"""
    quarter: str  # Q1, Q2, Q3, Q4
    financial_year: str
    return_type: str = "24Q"
    
    # Return details
    regular_24q: str = "Y"  # Y/N
    token_no: Optional[str] = None
    employer_address_change: str = "N"  # Y/N
    responsible_address_change: str = "N"  # Y/N
    
    # Challan details (3 months per quarter)
    challans: List[TDSReturnChallanDetail] = Field(default_factory=list)
    
    # Filing details
    acknowledgment_number: Optional[str] = None
    filing_date: Optional[date] = None
    is_filed: bool = False
    
    # Summary totals
    total_deductees: int = 0
    total_tds_amount: Decimal = Field(default=0)
    total_deposited: Decimal = Field(default=0)


class TDSReturnResponse(BaseModel):
    """Schema for TDS Return response"""
    financial_year: str
    return_type: str
    quarters: List[TDSReturnQuarter]
    filters_applied: TDSReturnFilters
    summary: Dict[str, Any]


# Annual Salary Statement Report Schemas
class AnnualSalaryStatementFilters(BaseModel):
    """Filters for Annual Salary Statement report"""
    periods: List[str] = Field(..., description="List of periods in format MMM-YYYY (e.g., ['JUL-2025', 'OCT-2025'])")
    employee_search: Optional[str] = Field(None, description="Employee name or code search")
    location: Optional[str] = Field("All Locations", description="Location filter")
    cost_center: Optional[str] = Field("All Cost Centers", description="Cost center filter")
    department: Optional[str] = Field("All Departments", description="Department filter")
    business_id: Optional[int] = None

class AnnualSalaryStatementPeriodData(BaseModel):
    """Salary data for a specific period"""
    period: str
    basic_salary: Decimal = Field(default=0)
    hra: Decimal = Field(default=0)
    special_allowance: Decimal = Field(default=0)
    transport_allowance: Decimal = Field(default=0)
    medical_allowance: Decimal = Field(default=0)
    other_allowances: Decimal = Field(default=0)
    total_earnings: Decimal = Field(default=0)
    
    pf_deduction: Decimal = Field(default=0)
    esi_deduction: Decimal = Field(default=0)
    professional_tax: Decimal = Field(default=0)
    tds: Decimal = Field(default=0)
    other_deductions: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    
    net_earnings: Decimal = Field(default=0)

class AnnualSalaryStatementSummaryRow(BaseModel):
    """Summary row for salary statement (earnings/deductions breakdown)"""
    label: str
    type: str = Field(default="normal")  # "normal" or "highlight"
    period_values: Dict[str, Decimal] = Field(default_factory=dict)  # period -> amount
    total: Decimal = Field(default=0)

class AnnualSalaryStatementEmployee(BaseModel):
    """Employee details for Annual Salary Statement"""
    employee_id: int
    employee_code: str
    employee_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    date_of_joining: Optional[date] = None
    
    # Salary breakdown by periods
    period_data: List[AnnualSalaryStatementPeriodData] = Field(default_factory=list)
    
    # Summary rows for display (earnings breakdown)
    salary_details: List[AnnualSalaryStatementSummaryRow] = Field(default_factory=list)
    
    # Totals across all periods
    total_earnings: Decimal = Field(default=0)
    total_deductions: Decimal = Field(default=0)
    total_net_earnings: Decimal = Field(default=0)

class AnnualSalaryStatementResponse(BaseModel):
    """Response for Annual Salary Statement report"""
    periods: List[str]
    employee: Optional[AnnualSalaryStatementEmployee] = None
    filters_applied: AnnualSalaryStatementFilters
    summary: Dict[str, Any]
    message: Optional[str] = None


class AnnualSalaryStatementSalaryDetail(BaseModel):
    """Salary detail for a specific component across periods"""
    type: str = Field(default="normal", description="Type: normal, highlight, header")
    label: str = Field(..., description="Salary component label")
    period_values: Dict[str, str] = Field(default_factory=dict, description="Values for each period (period -> amount)")
    total: str = Field(default="0.00", description="Total across all periods")


class AnnualSalaryStatementEmployee(BaseModel):
    """Employee details for Annual Salary Statement"""
    employee_id: int
    employee_name: str
    employee_code: Optional[str] = None
    date_of_joining: Optional[date] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Salary details organized by component
    salary_details: List[AnnualSalaryStatementSalaryDetail] = Field(default_factory=list)
    
    # Summary totals
    total_earnings_across_periods: Decimal = Field(default=0)
    total_deductions_across_periods: Decimal = Field(default=0)
    net_earnings_across_periods: Decimal = Field(default=0)


class AnnualSalaryStatementResponse(BaseModel):
    """Response for Annual Salary Statement report"""
    periods: List[str] = Field(..., description="Selected periods")
    employee: Optional[AnnualSalaryStatementEmployee] = None
    filters_applied: AnnualSalaryStatementFilters
    summary: Dict[str, Any]
    message: Optional[str] = None


# Annual Attendance Report Schemas
class AnnualAttendanceFilters(BaseModel):
    """Filters for Annual Attendance report"""
    periods: List[str] = Field(..., description="List of periods in format MMM-YYYY (e.g., ['JAN-2025', 'DEC-2025'])")
    location: Optional[str] = Field("All Locations", description="Location filter")
    cost_center: Optional[str] = Field("All Cost Centers", description="Cost center filter")
    department: Optional[str] = Field("All Departments", description="Department filter")
    employee_search: Optional[str] = Field(None, description="Employee name or code search")
    record_type: Optional[str] = Field("All Records", description="Record type: All Records, Active Records, Inactive Records")
    business_id: Optional[int] = None

class AnnualAttendanceEmployeeData(BaseModel):
    """Annual attendance data for a single employee"""
    employee_id: int
    employee_name: str
    employee_code: str
    location: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    designation: Optional[str] = None
    
    # Attendance metrics
    presents: int = Field(default=0)
    absents: int = Field(default=0)
    week_offs: int = Field(default=0)
    holidays: int = Field(default=0)
    paid_leaves: int = Field(default=0)
    unpaid_leaves: int = Field(default=0)
    paid_days: int = Field(default=0)
    total_days: int = Field(default=0)
    extra_days: int = Field(default=0)
    ot_days: int = Field(default=0)
    
    # Additional metrics
    total_hours: Optional[float] = Field(default=0.0)
    overtime_hours: Optional[float] = Field(default=0.0)

class AnnualAttendanceResponse(BaseModel):
    """Response for Annual Attendance report"""
    employees: List[AnnualAttendanceEmployeeData]
    periods: List[str]
    total_employees: int
    filters_applied: AnnualAttendanceFilters
    summary: Dict[str, Any]
    date_range: Dict[str, str]  # from_date, to_date
    message: Optional[str] = None