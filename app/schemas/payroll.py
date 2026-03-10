"""
Payroll Management Schemas
Pydantic schemas for payroll management API
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PayrollPeriodStatus(str, Enum):
    """Payroll period status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PROCESSING = "processing"


class PayrollRunStatus(str, Enum):
    """Payroll run status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Payroll Period Schemas
class PayrollPeriodBase(BaseModel):
    """Base payroll period schema"""
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    custom_days_enabled: bool = False
    custom_days: Optional[int] = None
    different_month: bool = False
    calendar_month: Optional[str] = None
    calendar_year: Optional[int] = None
    reporting_enabled: bool = False


class PayrollPeriodCreate(PayrollPeriodBase):
    """Payroll period creation schema"""
    
    @validator('end_date')
    def validate_dates(cls, v, values, **kwargs):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    @validator('custom_days')
    def validate_custom_days(cls, v, values, **kwargs):
        if values.get('custom_days_enabled') and (v is None or v <= 0):
            raise ValueError('custom_days must be positive when custom_days_enabled is True')
        return v


class PayrollPeriodUpdate(BaseModel):
    """Payroll period update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[PayrollPeriodStatus] = None
    custom_days_enabled: Optional[bool] = None
    custom_days: Optional[int] = None
    different_month: Optional[bool] = None
    calendar_month: Optional[str] = None
    calendar_year: Optional[int] = None
    reporting_enabled: Optional[bool] = None


class PayrollPeriodResponse(PayrollPeriodBase):
    """Payroll period response schema"""
    id: int
    business_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Payroll Run Request Schemas
class PayrollRunRequest(BaseModel):
    """Payroll run request schema"""
    period: Optional[str] = Field(None, min_length=1, max_length=50, description="Period name (e.g., 'SEP-2025')")
    period_id: Optional[int] = Field(None, gt=0, description="Period ID")
    notes: Optional[str] = Field(None, max_length=1000, description="Run notes")
    all_employees: bool = Field(True, description="Include all employees")
    employee_filter: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Employee filter criteria")
    
    @validator('notes')
    def validate_notes(cls, v):
        """Validate notes field"""
        if v is not None and len(v.strip()) == 0:
            return None
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_period_info(cls, values):
        """Ensure either period or period_id is provided"""
        period = values.get('period')
        period_id = values.get('period_id')
        
        if not period and not period_id:
            raise ValueError('Either period name or period_id must be provided')
        
        return values


class PayrollRunStatusResponse(BaseModel):
    """Payroll run status response schema"""
    id: int
    status: str
    progress: int = Field(..., ge=0, le=100)
    message: str
    runtime: Optional[str] = None
    total_employees: int = Field(default=0, ge=0)
    processed_employees: int = Field(default=0, ge=0)
    failed_employees: int = Field(default=0, ge=0)
    error_message: Optional[str] = None
    period_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PayrollRunLogsResponse(BaseModel):
    """Payroll run logs response schema"""
    run_id: int
    period: str
    log_file_path: str
    log_content: str
    file_size: int = Field(..., ge=0)
    generated_at: str
    status: str
    runtime: Optional[str] = None


class PayrollEligibilityResponse(BaseModel):
    """Payroll eligibility check response schema"""
    success: bool = True
    can_run: bool
    reason: str
    runs_today: Optional[int] = None
    running_runs: Optional[int] = None


# Payroll Run Schemas
class PayrollRunBase(BaseModel):
    """Base payroll run schema"""
    notes: Optional[str] = None


class PayrollRunCreate(PayrollRunBase):
    """Payroll run creation schema"""
    period_id: int


class PayrollRunResponse(PayrollRunBase):
    """Payroll run response schema"""
    id: int
    business_id: int
    period_id: int
    created_by: int
    run_date: datetime
    status: str
    runtime_seconds: Optional[int] = None
    total_employees: int
    processed_employees: int
    failed_employees: int
    total_gross_salary: Decimal
    total_deductions: Decimal
    total_net_salary: Decimal
    log_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Leave Encashment Schemas
class LeaveEncashmentBase(BaseModel):
    """Base leave encashment schema"""
    leave_type: str = Field(..., min_length=1, max_length=100)
    payment_period: date
    balance_as_on: date
    balance_above: Decimal = Field(default=0, ge=0)
    salary_components: Optional[List[str]] = None


class LeaveEncashmentCreate(LeaveEncashmentBase):
    """Leave encashment creation schema"""
    period_id: int
    employee_ids: Optional[List[int]] = None  # If None, applies to all employees


class LeaveEncashmentResponse(LeaveEncashmentBase):
    """Leave encashment response schema"""
    id: int
    business_id: int
    period_id: int
    employee_id: int
    created_by: int
    leave_balance: Decimal
    encashment_days: Decimal
    daily_salary: Decimal
    encashment_amount: Decimal
    is_processed: bool
    processed_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Payroll Recalculation Schemas
class PayrollRecalculationBase(BaseModel):
    """Base payroll recalculation schema"""
    date_from: date
    date_to: date
    all_employees: bool = True
    selected_employees: Optional[List[int]] = None


class PayrollRecalculationCreate(PayrollRecalculationBase):
    """Payroll recalculation creation schema"""
    period_id: int
    
    @validator('date_to')
    def validate_dates(cls, v, values, **kwargs):
        if 'date_from' in values and v <= values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v


class PayrollRecalculationResponse(PayrollRecalculationBase):
    """Payroll recalculation response schema"""
    id: int
    business_id: int
    period_id: int
    created_by: int
    status: str
    progress_percentage: int
    total_employees: int
    processed_employees: int
    failed_employees: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Statutory Bonus Schemas
class StatutoryBonusBase(BaseModel):
    """Base statutory bonus schema"""
    bonus_rate: Decimal = Field(default=8.33, ge=0, le=100)
    eligibility_cutoff: Decimal = Field(default=21000, ge=0)
    min_wages: Decimal = Field(default=7000, ge=0)
    min_bonus: Decimal = Field(default=100, ge=0)
    max_bonus: Decimal = Field(default=0, ge=0)
    salary_components: Optional[List[str]] = None


class StatutoryBonusCreate(StatutoryBonusBase):
    """Statutory bonus creation schema"""
    period_id: int
    employee_ids: Optional[List[int]] = None  # If None, applies to all employees


class StatutoryBonusResponse(StatutoryBonusBase):
    """Statutory bonus response schema"""
    id: int
    business_id: int
    period_id: int
    employee_id: int
    created_by: int
    base_salary: Decimal
    bonus_amount: Decimal
    is_processed: bool
    processed_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Gratuity Schemas
class GratuityBase(BaseModel):
    """Base gratuity schema"""
    min_years: int = Field(default=5, ge=0)
    payable_days: int = Field(default=15, ge=1, le=30)
    month_days: int = Field(default=26, ge=1, le=31)
    exit_only: bool = False
    year_rounding: str = Field(default="round_down", pattern="^(round_up|round_down)$")
    salary_components: Optional[List[str]] = None


class GratuityCreate(GratuityBase):
    """Gratuity creation schema"""
    period_id: int
    employee_ids: Optional[List[int]] = None  # If None, applies to all employees


class GratuityResponse(GratuityBase):
    """Gratuity response schema"""
    id: int
    business_id: int
    period_id: int
    employee_id: int
    created_by: int
    years_of_service: Decimal
    base_salary: Decimal
    gratuity_amount: Decimal
    is_processed: bool
    processed_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Hold Salary Schemas
class HoldSalaryBase(BaseModel):
    """Base hold salary schema"""
    hold_start_date: date
    hold_end_date: Optional[date] = None
    reason: str = Field(..., min_length=1)
    notes: Optional[str] = None


class HoldSalaryCreate(HoldSalaryBase):
    """Hold salary creation schema"""
    employee_id: int


class HoldSalaryUpdate(BaseModel):
    """Hold salary update schema"""
    hold_start_date: Optional[date] = None
    hold_end_date: Optional[date] = None
    reason: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class HoldSalaryResponse(HoldSalaryBase):
    """Hold salary response schema"""
    id: int
    business_id: int
    employee_id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Dashboard and Statistics Schemas
class PayrollDashboardStats(BaseModel):
    """Payroll dashboard statistics schema"""
    total_periods: int
    open_periods: int
    closed_periods: int
    processing_periods: int
    total_employees: int
    active_employees: int
    on_hold_employees: int
    current_period_gross: Decimal
    current_period_net: Decimal
    last_run_date: Optional[datetime] = None
    last_run_status: Optional[str] = None


class PayrollPeriodStats(BaseModel):
    """Payroll period statistics schema"""
    period_id: int
    period_name: str
    total_employees: int
    processed_employees: int
    total_gross_salary: Decimal
    total_deductions: Decimal
    total_net_salary: Decimal
    average_salary: Decimal
    total_runs: int
    successful_runs: int
    failed_runs: int
    last_run_date: Optional[datetime] = None


class PayrollChartData(BaseModel):
    """Payroll chart data schema"""
    labels: List[str]
    gross_salary: List[float]
    net_salary: List[float]
    deductions: List[float]


class PayrollDashboardResponse(BaseModel):
    """Payroll dashboard response schema"""
    stats: PayrollDashboardStats
    recent_runs: List[PayrollRunResponse]
    chart_data: PayrollChartData
    active_periods: List[PayrollPeriodResponse]


# Leave Encashment Generate Request Schema
class LeaveEncashmentGenerateRequest(BaseModel):
    """Leave encashment generate request schema"""
    location: str = Field(default="all", min_length=1)
    costCenter: str = Field(default="all", min_length=1) 
    department: str = Field(default="all", min_length=1)
    paymentPeriod: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    leaveType: str = Field(..., min_length=1, max_length=100)
    employee: str = Field(default="all", min_length=1)
    balanceAsOn: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    balanceAbove: Decimal = Field(default=0, ge=0)
    salaryComponents: List[str] = Field(..., min_items=1)
    
    @validator('leaveType')
    def validate_leave_type(cls, v):
        if v == "- Select -" or v.strip() == "":
            raise ValueError('Please select a valid leave type')
        return v
    
    @validator('salaryComponents')
    def validate_salary_components(cls, v):
        valid_components = [
            'basicSalary', 'houseRentAllowance', 'specialAllowance',
            'medicalAllowance', 'conveyanceAllowance', 'telephoneAllowance'
        ]
        invalid_components = [comp for comp in v if comp not in valid_components]
        if invalid_components:
            raise ValueError(f'Invalid salary components: {invalid_components}')
        return v


# Leave Encashment Process Request Schema  
class LeaveEncashmentProcessRequest(BaseModel):
    """Leave encashment process request schema"""
    encashmentSummary: List[Dict[str, Any]] = Field(..., min_items=1)
    filters: Dict[str, Any] = Field(...)
    
    @validator('encashmentSummary')
    def validate_encashment_summary(cls, v):
        required_fields = ['employee_code', 'leave_balance', 'daily_salary', 'encashment_days', 'encashment_amount']
        for item in v:
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                raise ValueError(f'Missing required fields in encashment summary: {missing_fields}')
        return v


# Summary Schemas
class EncashmentSummaryItem(BaseModel):
    """Leave encashment summary item"""
    employee_id: int
    employee_name: str
    employee_code: str
    leave_balance: Decimal
    daily_salary: Decimal
    encashment_days: Decimal
    encashment_amount: Decimal


class EncashmentSummary(BaseModel):
    """Leave encashment summary"""
    eligible_employees: int
    total_payable: Decimal
    items: List[EncashmentSummaryItem]


class BonusSummaryItem(BaseModel):
    """Statutory bonus summary item"""
    employee_id: int
    employee_code: str
    employee_name: str
    base_salary: Decimal
    bonus_amount: Decimal


class BonusSummary(BaseModel):
    """Statutory bonus summary"""
    eligible_employees: int
    total_payable: Decimal
    items: List[BonusSummaryItem]


class GratuitySummaryItem(BaseModel):
    """Gratuity summary item"""
    employee_id: int
    employee_name: str
    employee_code: str
    base_salary: Decimal
    years_of_service: Decimal
    gratuity_amount: Decimal


class GratuitySummary(BaseModel):
    """Gratuity summary"""
    eligible_employees: int
    total_payable: Decimal
    items: List[GratuitySummaryItem]


# Processing Schemas
class ProcessingRequest(BaseModel):
    """Processing request schema"""
    confirm: bool = True
    notes: Optional[str] = None


class ProcessingResponse(BaseModel):
    """Processing response schema"""
    success: bool
    message: str
    processed_count: int
    total_amount: Decimal
    processing_id: Optional[int] = None