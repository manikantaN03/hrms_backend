"""
Data Capture Schemas
Pydantic models for data capture API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class SalaryVariableTypeEnum(str, Enum):
    ALLOWANCE = "allowance"
    BONUS = "bonus"
    INCENTIVE = "incentive"
    COMMISSION = "commission"
    OVERTIME = "overtime"
    OTHER = "other"


class DeductionTypeEnum(str, Enum):
    TAX = "tax"
    INSURANCE = "insurance"
    LOAN = "loan"
    ADVANCE = "advance"
    FINE = "fine"
    OTHER = "other"


class LoanStatusEnum(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class ITDeclarationStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


# Salary Variable Schemas
class SalaryVariableCreate(BaseModel):
    employee_id: int
    variable_name: str = Field(..., max_length=255)
    variable_type: SalaryVariableTypeEnum
    amount: Decimal = Field(..., gt=0)
    effective_date: date
    end_date: Optional[date] = None
    is_recurring: bool = False
    frequency: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_taxable: bool = True


class SalaryVariableUpdate(BaseModel):
    variable_name: Optional[str] = Field(None, max_length=255)
    variable_type: Optional[SalaryVariableTypeEnum] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_taxable: Optional[bool] = None
    is_active: Optional[bool] = None


class SalaryVariableResponse(SalaryVariableCreate):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Employee details (joined)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    
    class Config:
        from_attributes = True


# Salary Unit Schemas
class SalaryUnitCreate(BaseModel):
    unit_name: str = Field(..., max_length=255, min_length=1)
    unit_code: str = Field(..., max_length=50, min_length=1)
    unit_type: str = Field(..., max_length=100, min_length=1)
    base_rate: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    is_overtime_applicable: bool = False
    overtime_multiplier: Decimal = Field(1.5, gt=0)


class SalaryUnitUpdate(BaseModel):
    unit_name: Optional[str] = Field(None, max_length=255, min_length=1)
    unit_code: Optional[str] = Field(None, max_length=50, min_length=1)
    unit_type: Optional[str] = Field(None, max_length=100, min_length=1)
    base_rate: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    is_overtime_applicable: Optional[bool] = None
    overtime_multiplier: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None


class SalaryUnitResponse(SalaryUnitCreate):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# Employee Salary Unit Schemas
class EmployeeSalaryUnitCreate(BaseModel):
    employee_id: int = Field(..., gt=0)
    unit_name: str = Field(..., max_length=255, min_length=1)
    unit_type: str = Field(..., max_length=100, min_length=1)
    amount: Decimal = Field(..., ge=0)
    effective_date: date
    end_date: Optional[date] = None
    comments: Optional[str] = Field(None, max_length=1000)
    is_arrear: bool = False

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'effective_date' in values and v <= values['effective_date']:
            raise ValueError('End date must be after effective date')
        return v


class EmployeeSalaryUnitUpdate(BaseModel):
    unit_name: Optional[str] = Field(None, max_length=255, min_length=1)
    unit_type: Optional[str] = Field(None, max_length=100, min_length=1)
    amount: Optional[Decimal] = Field(None, ge=0)
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    comments: Optional[str] = Field(None, max_length=1000)
    is_arrear: Optional[bool] = None
    is_active: Optional[bool] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'effective_date' in values and values['effective_date'] and v <= values['effective_date']:
            raise ValueError('End date must be after effective date')
        return v


class EmployeeSalaryUnitResponse(EmployeeSalaryUnitCreate):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# Salary Units API Schemas
class SalaryUnitsEmployeeResponse(BaseModel):
    sn: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    id: str = Field(..., min_length=1)  # Employee code
    location: str = Field(..., min_length=1)
    department: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)
    comments: str = ""
    total: float = Field(..., ge=0)


class SalaryUnitsUpdateRequest(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=50)
    month: str = Field(..., min_length=1)  # Format: "October 2025"
    amount: float = Field(..., ge=0)
    comments: str = Field("", max_length=1000)
    component: str = Field(..., min_length=1, max_length=255)
    arrear: bool = False

    @validator('month')
    def validate_month_format(cls, v):
        try:
            parts = v.split()
            if len(parts) != 2:
                raise ValueError('Month must be in format "Month Year" (e.g., "October 2025")')
            
            month_name = parts[0]
            year = int(parts[1])
            
            valid_months = ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
            
            if month_name not in valid_months:
                raise ValueError(f'Invalid month name. Must be one of: {", ".join(valid_months)}')
            
            if year < 2020 or year > 2030:
                raise ValueError('Year must be between 2020 and 2030')
                
            return v
        except (ValueError, IndexError) as e:
            raise ValueError('Month must be in format "Month Year" (e.g., "October 2025")')


class ImportTravelKmsRequest(BaseModel):
    period: str = Field(..., min_length=1)  # Format: "OCT-2025"
    location: str = Field(..., min_length=1, max_length=255)
    department: str = Field(..., min_length=1, max_length=255)
    component: str = Field(..., min_length=1, max_length=255)
    distance_type: str = Field(..., min_length=1, max_length=100)
    comments: str = Field("", max_length=1000)
    overwrite_existing: bool = False

    @validator('period')
    def validate_period_format(cls, v):
        try:
            parts = v.split('-')
            if len(parts) != 2:
                raise ValueError('Period must be in format "MON-YYYY" (e.g., "OCT-2025")')
            
            month_abbr = parts[0].upper()
            year = int(parts[1])
            
            valid_months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            
            if month_abbr not in valid_months:
                raise ValueError(f'Invalid month abbreviation. Must be one of: {", ".join(valid_months)}')
            
            if year < 2020 or year > 2030:
                raise ValueError('Year must be between 2020 and 2030')
                
            # Return uppercase format
            return f"{month_abbr}-{year}"
        except (ValueError, IndexError) as e:
            raise ValueError('Period must be in format "MON-YYYY" (e.g., "OCT-2025")')

    @validator('location')
    def validate_location(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Location is required')
        return v.strip()

    @validator('department')
    def validate_department(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Department is required')
        return v.strip()

    @validator('component')
    def validate_component(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Component is required')
        return v.strip()

    @validator('distance_type')
    def validate_distance_type(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Distance type is required')
        
        valid_types = ["Calculated", "Approved"]
        if v not in valid_types:
            raise ValueError(f'Distance type must be one of: {", ".join(valid_types)}')
        
        return v


class SalaryUnitsFiltersResponse(BaseModel):
    businessUnits: List[str]
    locations: List[str]
    departments: List[str]
    components: List[str]


# Employee Deduction Schemas
class EmployeeDeductionCreate(BaseModel):
    employee_id: int
    deduction_name: str = Field(..., max_length=255)
    deduction_type: DeductionTypeEnum
    amount: Decimal = Field(..., gt=0)
    effective_date: date
    end_date: Optional[date] = None
    is_recurring: bool = True
    frequency: str = Field("monthly", max_length=50)
    description: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)


class EmployeeDeductionUpdate(BaseModel):
    deduction_name: Optional[str] = Field(None, max_length=255)
    deduction_type: Optional[DeductionTypeEnum] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class EmployeeDeductionResponse(EmployeeDeductionCreate):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Employee details (joined)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    
    class Config:
        from_attributes = True


# Deduction Employee Response for Frontend Table
class DeductionEmployeeResponse(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)  # Employee code
    location: str = Field(..., min_length=1)
    dept: str = Field(..., min_length=1)  # Department
    position: str = Field("Software Engineer", min_length=1)
    grosssalary: float = Field(..., ge=0)
    calculatedexemptions: float = Field(0, ge=0)
    additionalexemptions: float = Field(0, ge=0)
    netsalary: float = Field(..., ge=0)
    amount: float = Field(0, ge=0)
    comments: str = ""
    total: float = Field(0, ge=0)


# Deduction Update Request
class DeductionUpdateRequest(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=50)
    month: str = Field(..., min_length=1)  # Format: "AUG-2025"
    amount: float = Field(..., ge=0)
    comments: str = Field("", max_length=1000)
    deduction_type: str = Field(..., min_length=1, max_length=255)

    @validator('month')
    def validate_month_format(cls, v):
        try:
            parts = v.split('-')
            if len(parts) != 2:
                raise ValueError('Month must be in format "AUG-2025"')
            
            month_name = parts[0]
            year = int(parts[1])
            
            valid_months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            if month_name not in valid_months:
                raise ValueError(f'Month must be one of: {", ".join(valid_months)}')
            
            if year < 2020 or year > 2030:
                raise ValueError('Year must be between 2020 and 2030')
            
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError('Invalid year format in month')
            raise e


# Copy From Previous Period Request
class CopyFromPreviousPeriodRequest(BaseModel):
    source_period: str = Field(..., min_length=1)
    target_period: str = Field(..., min_length=1)
    deduction_type: str = Field(..., min_length=1)
    overwrite_existing: bool = False

    @validator('source_period', 'target_period')
    def validate_period_format(cls, v):
        try:
            parts = v.split('-')
            if len(parts) != 2:
                raise ValueError('Period must be in format "AUG-2025"')
            
            month_name = parts[0]
            year = int(parts[1])
            
            valid_months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            if month_name not in valid_months:
                raise ValueError(f'Month must be one of: {", ".join(valid_months)}')
            
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError('Invalid year format in period')
            raise e


# Deduction Filters Response
class DeductionFiltersResponse(BaseModel):
    businessUnits: List[str]
    locations: List[str]
    departments: List[str]
    deductionTypes: List[str]


# Income Tax TDS Schemas
class IncomeTaxTDSCreate(BaseModel):
    employee_id: int
    financial_year: str = Field(..., max_length=10)
    quarter: str = Field(..., max_length=10)
    gross_salary: Decimal = Field(..., ge=0)
    taxable_income: Decimal = Field(..., ge=0)
    tds_amount: Decimal = Field(..., ge=0)
    tax_slab_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    exemptions: Decimal = Field(0, ge=0)
    deductions_80c: Decimal = Field(0, ge=0)
    other_deductions: Decimal = Field(0, ge=0)
    challan_number: Optional[str] = Field(None, max_length=100)
    deposit_date: Optional[date] = None
    remarks: Optional[str] = None


class IncomeTaxTDSResponse(IncomeTaxTDSCreate):
    id: int
    business_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Employee details (joined)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    
    class Config:
        from_attributes = True


# Extra Day Schemas
class ExtraDayCreate(BaseModel):
    employee_id: int
    work_date: date
    hours_worked: Decimal = Field(..., gt=0, le=24)
    hourly_rate: Decimal = Field(..., gt=0)
    work_description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)


class ExtraDayUpdate(BaseModel):
    hours_worked: Optional[Decimal] = Field(None, gt=0, le=24)
    hourly_rate: Optional[Decimal] = Field(None, gt=0)
    work_description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    is_approved: Optional[bool] = None
    is_paid: Optional[bool] = None


class ExtraDayResponse(ExtraDayCreate):
    id: int
    business_id: int
    total_amount: Decimal
    is_approved: bool
    is_paid: bool
    approved_by: Optional[int] = None
    approval_date: Optional[date] = None
    payment_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Employee details (joined)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    approver_name: Optional[str] = None
    
    class Config:
        from_attributes = True


from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class ExtraHoursEmployeeResponse(BaseModel):
    """Response model for extra hours employee data"""
    id: str = Field(..., description="Employee code")
    name: str = Field(..., description="Employee full name")
    designation: str = Field(..., description="Employee designation")
    total_extra_hours: float = Field(0.0, ge=0, description="Total extra hours for the month")
    total_amount: float = Field(0.0, ge=0, description="Total amount for extra hours")
    
    class Config:
        from_attributes = True


class ExtraHoursFiltersResponse(BaseModel):
    """Response model for filter options"""
    businessUnits: List[str] = Field(..., description="List of business units")
    locations: List[str] = Field(..., description="List of locations")
    departments: List[str] = Field(..., description="List of departments")
    
    class Config:
        from_attributes = True


class ExtraHoursSearchResponse(BaseModel):
    """Response model for employee search"""
    id: str = Field(..., description="Employee code")
    name: str = Field(..., description="Employee full name")
    
    class Config:
        from_attributes = True


class ExtraHoursCreateRequest(BaseModel):
    """Request model for creating extra hours record"""
    employee_code: str = Field(..., min_length=1, max_length=50, description="Employee code")
    work_date: date = Field(..., description="Work date")
    extra_hours: float = Field(..., gt=0, le=24, description="Extra hours worked")
    hourly_rate: float = Field(500.0, gt=0, le=10000, description="Hourly rate")
    reason: str = Field("", max_length=500, description="Reason for extra hours")
    
    @validator('work_date')
    def validate_work_date(cls, v):
        if v > date.today():
            raise ValueError('Work date cannot be in the future')
        return v
    
    @validator('employee_code')
    def validate_employee_code(cls, v):
        if not v.strip():
            raise ValueError('Employee code cannot be empty')
        return v.strip().upper()
    
    class Config:
        from_attributes = True


class ExtraHoursCreateResponse(BaseModel):
    """Response model for extra hours creation"""
    message: str = Field(..., description="Success message")
    employee_code: str = Field(..., description="Employee code")
    work_date: str = Field(..., description="Work date")
    extra_hours: str = Field(..., description="Extra hours")
    hourly_rate: str = Field(..., description="Hourly rate")
    total_amount: str = Field(..., description="Total amount")
    created_at: str = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ExtraHoursImportRequest(BaseModel):
    """Request model for importing extra hours data"""
    month: str = Field("AUG-2025", pattern=r"^[A-Z]{3}-\d{4}$", description="Month in format 'AUG-2025'")
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing records")
    csv_data: str = Field(..., min_length=1, description="CSV content as string")
    
    @validator('csv_data')
    def validate_csv_data(cls, v):
        if not v.strip():
            raise ValueError('CSV data cannot be empty')
        return v.strip()
    
    class Config:
        from_attributes = True


class ExtraHoursImportResponse(BaseModel):
    """Response model for extra hours import"""
    message: str = Field(..., description="Import result message")
    imported_records: int = Field(..., ge=0, description="Number of imported records")
    errors: List[str] = Field(..., description="List of import errors")
    total_errors: int = Field(..., ge=0, description="Total number of errors")
    overwrite_existing: bool = Field(..., description="Whether existing records were overwritten")
    
    class Config:
        from_attributes = True


# Employee Loan Schemas
class EmployeeLoanCreate(BaseModel):
    employee_id: int
    loan_type: str = Field(..., max_length=100)
    loan_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(0, ge=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)
    loan_date: date
    first_emi_date: date
    purpose: Optional[str] = None
    guarantor_name: Optional[str] = Field(None, max_length=255)
    guarantor_relation: Optional[str] = Field(None, max_length=100)


class EmployeeLoanUpdate(BaseModel):
    loan_type: Optional[str] = Field(None, max_length=100)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    status: Optional[LoanStatusEnum] = None
    purpose: Optional[str] = None
    guarantor_name: Optional[str] = Field(None, max_length=255)
    guarantor_relation: Optional[str] = Field(None, max_length=100)


class EmployeeLoanResponse(EmployeeLoanCreate):
    id: int
    business_id: int
    emi_amount: Decimal
    status: LoanStatusEnum
    outstanding_amount: Decimal
    paid_amount: Decimal
    paid_emis: int
    remaining_emis: int
    last_emi_date: Optional[date] = None
    approved_by: Optional[int] = None
    approval_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Employee details (joined)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    approver_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# IT Declaration Schemas
class ITDeclarationCreate(BaseModel):
    employee_id: int
    financial_year: str = Field(..., max_length=10)
    pf_amount: Decimal = Field(0, ge=0)
    life_insurance: Decimal = Field(0, ge=0)
    elss_mutual_funds: Decimal = Field(0, ge=0)
    home_loan_principal: Decimal = Field(0, ge=0)
    tuition_fees: Decimal = Field(0, ge=0)
    other_80c: Decimal = Field(0, ge=0)
    section_80d_medical: Decimal = Field(0, ge=0)
    section_24_home_loan_interest: Decimal = Field(0, ge=0)
    section_80g_donations: Decimal = Field(0, ge=0)
    hra_exemption: Decimal = Field(0, ge=0)
    rent_paid: Decimal = Field(0, ge=0)
    landlord_name: Optional[str] = Field(None, max_length=255)
    landlord_pan: Optional[str] = Field(None, max_length=20)


class ITDeclarationUpdate(BaseModel):
    pf_amount: Optional[Decimal] = Field(None, ge=0)
    life_insurance: Optional[Decimal] = Field(None, ge=0)
    elss_mutual_funds: Optional[Decimal] = Field(None, ge=0)
    home_loan_principal: Optional[Decimal] = Field(None, ge=0)
    tuition_fees: Optional[Decimal] = Field(None, ge=0)
    other_80c: Optional[Decimal] = Field(None, ge=0)
    section_80d_medical: Optional[Decimal] = Field(None, ge=0)
    section_24_home_loan_interest: Optional[Decimal] = Field(None, ge=0)
    section_80g_donations: Optional[Decimal] = Field(None, ge=0)
    hra_exemption: Optional[Decimal] = Field(None, ge=0)
    rent_paid: Optional[Decimal] = Field(None, ge=0)
    landlord_name: Optional[str] = Field(None, max_length=255)
    landlord_pan: Optional[str] = Field(None, max_length=20)
    status: Optional[ITDeclarationStatusEnum] = None


class ITDeclarationResponse(ITDeclarationCreate):
    id: int
    business_id: int
    status: ITDeclarationStatusEnum
    total_80c: Decimal
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Employee details (joined)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    approver_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# TDS Challan Schemas
class TDSChallanCreate(BaseModel):
    challan_number: str = Field(..., max_length=100)
    financial_year: str = Field(..., max_length=10)
    quarter: str = Field(..., max_length=10)
    deposit_date: date
    tds_amount: Decimal = Field(..., gt=0)
    interest: Decimal = Field(0, ge=0)
    penalty: Decimal = Field(0, ge=0)
    bank_name: Optional[str] = Field(None, max_length=255)
    branch_code: Optional[str] = Field(None, max_length=20)
    remarks: Optional[str] = None


class TDSChallanResponse(TDSChallanCreate):
    id: int
    business_id: int
    total_amount: Decimal
    uploaded_file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# TDS Challan Frontend Compatible Schemas
class TDSChallanSaveRequest(BaseModel):
    """TDS challan save request for frontend"""
    financial_year: str = Field(..., max_length=10, description="Financial year in format '2024-25'")
    month: str = Field(..., max_length=10, description="Month in format 'APR-2024'")
    bsrcode: str = Field("", max_length=50, description="BSR code")
    date: str = Field("", description="Deposit date in YYYY-MM-DD format")
    challan: str = Field("", max_length=100, description="Challan serial number")


class TDSChallanMonthResponse(BaseModel):
    """TDS challan month response for frontend"""
    month: str = Field(..., description="Month in format 'APR-2024'")
    bsrcode: str = Field("", description="BSR code")
    date: str = Field("", description="Deposit date in YYYY-MM-DD format")
    challan: str = Field("", description="Challan serial number")
    id: Optional[int] = Field(None, description="Database ID if exists")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")


class TDSChallanYearResponse(BaseModel):
    """TDS challan year response for frontend"""
    financial_year: str = Field(..., description="Financial year in format '2024-25'")
    total_months: int = Field(12, description="Total months in financial year")
    challans: List[TDSChallanMonthResponse] = Field(..., description="List of 12 months data")


class TDSChallanSummaryResponse(BaseModel):
    """TDS challan summary response for frontend"""
    financial_year: str = Field(..., description="Financial year")
    total_months: int = Field(12, description="Total months")
    completed_months: int = Field(..., description="Months with data")
    completion_percentage: float = Field(..., description="Completion percentage")
    total_amount: Optional[Decimal] = Field(None, description="Total TDS amount")
    total_challans: int = Field(..., description="Total number of challans")


# Extra Days Frontend Compatible Schemas
class ExtraDaysEmployeeResponse(BaseModel):
    """Extra days employee response matching frontend expectations"""
    id: int
    name: str
    code: str  # Employee code
    designation: str
    joining: str  # Joining date formatted
    extra: float = 0.0
    arrear: float = 0.0
    ot: float = 0.0  # Overtime
    comments: str = ""


class ExtraDaysUpdateRequest(BaseModel):
    """Extra days update request"""
    employee_id: int
    month: str  # Format: "AUG-2025"
    extra: float = 0.0
    arrear: float = 0.0
    ot: float = 0.0
    comments: str = ""


class ExtraDaysFiltersResponse(BaseModel):
    """Extra days filters response"""
    businessUnits: List[str]
    locations: List[str]
    departments: List[str]
    costCenters: List[str]


class ExtraDaysSearchResponse(BaseModel):
    """Extra days search response"""
    id: int
    name: str


class ExtraDaysExportResponse(BaseModel):
    """Extra days export response"""
    employee_name: str
    employee_code: str
    designation: str
    joining_date: str
    extra_days: float
    arrear: float
    ot: float
    comments: str
    month: str


class ExtraDaysExportAllResponse(BaseModel):
    """Extra days export all response"""
    employees: List[ExtraDaysExportResponse]
    month: str
    total_employees: int


class ExtraDaysImportResponse(BaseModel):
    """Extra days import response"""
    message: str
    imported_records: int
    errors: List[str]
    total_errors: int
    overwrite_existing: bool


# Pagination schemas
class PaginatedSalaryVariableResponse(BaseModel):
    items: List[SalaryVariableResponse]
    total: int
    page: int
    size: int
    pages: int


# Salary Variable Frontend Compatible Schemas
class SalaryVariableEmployeeResponse(BaseModel):
    """Salary variable employee response matching frontend expectations"""
    employee_id: int
    employee_name: str
    employee_code: str
    location: str
    department: str
    amount: float = 0.0
    comments: str = ""
    total: float = 0.0


class SalaryVariableEmployeesResponse(BaseModel):
    """Paginated salary variable employees response"""
    employees: List[SalaryVariableEmployeeResponse]
    total_pages: int
    current_page: int
    total_employees: int


class SalaryVariableUpdateRequest(BaseModel):
    """Salary variable update request"""
    employee_code: str
    month: str  # Format: "October 2025"
    amount: float = 0.0
    comments: str = ""
    variable_type: str = "Leave Encashment"
    arrear: bool = False


class AddNonCashSalaryRequest(BaseModel):
    """Add non-cash salary request"""
    source_component: str
    target_component: str
    start_date: date
    end_date: date
    employee_ids: List[int] = []
    overwrite_existing: bool = False


class SalaryVariableFiltersResponse(BaseModel):
    """Salary variable filters response"""
    business_units: List[str]
    locations: List[str]
    departments: List[str]
    cost_centers: List[str]
    leave_options: List[str]


class PaginatedEmployeeDeductionResponse(BaseModel):
    items: List[EmployeeDeductionResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedEmployeeLoanResponse(BaseModel):
    items: List[EmployeeLoanResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedITDeclarationResponse(BaseModel):
    items: List[ITDeclarationResponse]
    total: int
    page: int
    size: int
    pages: int


# TDS Return Frontend Compatible Schemas
class TDSReturnSaveRequest(BaseModel):
    """TDS return save request for frontend"""
    financial_year: str = Field(..., max_length=10, description="Financial year in format '2024-25'")
    quarter: str = Field(..., max_length=10, description="Quarter in format 'Q1', 'Q2', 'Q3', 'Q4'")
    receipt_number: str = Field("", max_length=50, description="Receipt number")
    filing_date: Optional[str] = Field(None, description="Filing date in format 'YYYY-MM-DD'")
    tds_amount: Optional[Decimal] = Field(None, description="TDS amount")


class TDSReturnRequest(BaseModel):
    """TDS return request"""
    return_type: str = Field(..., description="Return type")
    financial_year: str = Field(..., description="Financial year")
    quarter: str = Field(..., description="Quarter")
    receipt_number: str = Field("", description="Receipt number")
    filing_date: Optional[str] = Field(None, description="Filing date")
    tds_amount: Optional[Decimal] = Field(None, description="TDS amount")