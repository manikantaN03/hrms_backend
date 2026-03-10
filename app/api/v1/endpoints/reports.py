"""
Reports API Endpoints
Updated: Added salary-register/filters endpoint with HYBRID logic
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from app.core.database import get_db
from app.api.v1.deps import get_current_admin, get_current_user
from app.models.user import User
from app.services.reports_service import ReportsService
from app.schemas.reports import (
    AIReportQueryCreate, AIReportQueryResponse, ReportTemplateCreate, ReportTemplateResponse,
    GeneratedReportCreate, GeneratedReportResponse, SalaryReportCreate, SalaryReportResponse,
    IncomeTaxForm16Filters, TDSReturnFilters, AnnualSalarySummaryFilters, AnnualSalaryStatementFilters,
    AnnualAttendanceFilters, ActivityLogFilters,
    AttendanceReportCreate, AttendanceReportResponse, EmployeeReportCreate, EmployeeReportResponse,
    StatutoryReportCreate, StatutoryReportResponse, AnnualReportCreate, AnnualReportResponse,
    ActivityLogCreate, ActivityLogResponse, UserFeedbackCreate, UserFeedbackResponse,
    SystemAlertCreate, SystemAlertResponse, ReportFilters, ReportDashboard, SalaryRegisterFilters,
    SalarySlipFilters, BankTransferLetterFilters, OvertimeRegisterFilters, CostToCompanyFilters,
    PromotionAgeFilters, IncrementAgeingFilters, EmployeeJoiningFilters, EmployeeExitFilters,
    VariableSalaryFilters, TimeSalaryFilters, RateSalaryFilters, LeaveEncashmentReportFilters,
    StatutoryBonusReportFilters, SalaryDeductionsFilters, EmployeeLoansFilters, SAPExportFilters,
    AttendanceRegisterFilters, LeaveRegisterFilters, TimeRegisterFilters, StrikeRegisterFilters,
    TravelRegisterFilters, TimePunchesFilters, RemotePunchFilters, ManualUpdatesFilters,
    EmployeeRegisterFilters, EmployeeRegisterOptions, EmployeeAddressesFilters, EmployeeEventsFilters,
    VaccinationStatusFilters, WorkmanStatusFilters, EmployeeAssetsFilters,
    EmployeeRelativesFilters, InactiveEmployeesFilters, ExportRecordsFilters, ESIDeductionFilters, ESICoverageFilters, PFDeductionFilters, PFCoverageFilters,
    IncomeTaxDeclarationFilters, IncomeTaxComputationFilters, LabourWelfareFundFilters, TDSReturnFilters
)
from app.schemas.reports_additional import (
    UserFeedbackReportFilters,
    SystemAlertsReportFilters,
    SalarySlipPreferences
)

router = APIRouter()


# AI Reporting Endpoints
@router.post("/ai/query", response_model=AIReportQueryResponse)
async def process_ai_query(
    query_data: AIReportQueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process AI report query"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    service = ReportsService(db)
    return await service.process_ai_query(current_user.id, query_data, business_id)


@router.get("/ai/queries", response_model=List[AIReportQueryResponse])
def get_user_ai_queries(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's AI queries"""
    service = ReportsService(db)
    return service.get_user_ai_queries(current_user.id, limit)


# Report Template Endpoints
@router.post("/templates", response_model=ReportTemplateResponse)
def create_report_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new report template"""
    service = ReportsService(db)
    return service.create_report_template(template_data)


@router.get("/templates", response_model=List[ReportTemplateResponse])
def get_report_templates(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get report templates by category"""
    service = ReportsService(db)
    return service.get_report_templates(category)


# Generated Report Endpoints
@router.post("/generate", response_model=GeneratedReportResponse)
def generate_report(
    report_data: GeneratedReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Generate a new report"""
    service = ReportsService(db)
    return service.generate_report(current_user.id, report_data)


@router.get("/generated", response_model=List[GeneratedReportResponse])
def get_generated_reports(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get user's generated reports"""
    service = ReportsService(db)
    return service.get_generated_reports(current_user.id, limit)


# Salary Report Endpoints
@router.post("/salary", response_model=SalaryReportResponse)
def create_salary_report(
    report_data: SalaryReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new salary report"""
    service = ReportsService(db)
    return service.create_salary_report(report_data)


@router.get("/salary", response_model=List[SalaryReportResponse])
def get_salary_reports(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_ids: Optional[str] = Query(None, description="Comma-separated employee IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary reports with filters"""
    service = ReportsService(db)
    
    # Parse employee IDs
    employee_id_list = None
    if employee_ids:
        try:
            employee_id_list = [int(id.strip()) for id in employee_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid employee IDs format")
    
    filters = ReportFilters(
        start_date=start_date,
        end_date=end_date,
        employee_ids=employee_id_list
    )
    
    return service.get_salary_reports(filters)


# Salary Summary Endpoint (specific for frontend)
@router.get("/salary-summary")
def get_salary_summary_report(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., SEP-2025)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary summary grouped by cost centers, locations, departments, and grades"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    service = ReportsService(db)
    return service.get_salary_summary_report(month, business_id)


# Bank Transfer Letter Endpoints
@router.get("/bank-transfer-letter/filters")
def get_bank_transfer_letter_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for bank transfer letter with HYBRID business unit logic
    
    Returns:
    - business_units: Businesses for superadmin, Business Units for regular admin
    - locations: All active locations (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    - departments: All active departments (filtered by business)
    """
    try:
        from app.models.location import Location
        from app.models.cost_center import CostCenter
        from app.models.department import Department
        from app.utils.business_unit_utils import get_business_unit_options
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get business units using HYBRID APPROACH
        business_unit_options = get_business_unit_options(db, current_user, business_id)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "business_units": business_unit_options,
            "locations": location_options,
            "cost_centers": cost_center_options,
            "departments": department_options,
            "format_types": [
                {"value": "generic", "label": "Generic"},
                {"value": "hdfc", "label": "HDFC Bank"},
                {"value": "icici", "label": "ICICI Bank"},
                {"value": "axis", "label": "Axis Bank"},
                {"value": "idfc", "label": "IDFC Bank"},
                {"value": "kotak", "label": "Kotak Bank"},
                {"value": "kotak-text", "label": "Kotak Bank (Text Format)"},
                {"value": "razorpay", "label": "RazorPay Payout"},
                {"value": "openmoney", "label": "OpenMoney Payout"}
            ]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching bank transfer letter filters: {str(e)}")
        return {
            "business_units": ["All Business Units"],
            "locations": ["All Locations"],
            "cost_centers": ["All Cost Centers"],
            "departments": ["All Departments"],
            "format_types": [{"value": "generic", "label": "Generic"}]
        }


@router.post("/bank-transfer-letter")
def get_bank_transfer_letter(
    filters: BankTransferLetterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get bank transfer letter with employee bank details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_bank_transfer_letter(filters)


@router.get("/bank-transfer-letter")
def get_bank_transfer_letter_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., OCT-2025)"),
    business_unit: str = Query("All Business Units", description="Business unit filter"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search term"),
    format_type: str = Query("generic", description="Export format type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get bank transfer letter with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = BankTransferLetterFilters(
        period=period,
        business_unit=business_unit,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        format_type=format_type,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_bank_transfer_letter(filters)


# Salary Slip Endpoints
@router.get("/salary-slips/employee-search")
def search_employees_for_salary_slips(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for salary slips autocomplete
    Returns employee code and name for dropdown suggestions
    """
    try:
        from app.models.employee import Employee
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_pattern = f"%{q}%"
        query = db.query(Employee).filter(
            or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_code.ilike(search_pattern)
            )
        )
        
        # Filter by business if not superadmin
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Get results
        employees = query.limit(limit).all()
        
        # Format results
        results = [
            {
                "id": emp.id,
                "code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "display": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip()
            }
            for emp in employees
        ]
        
        return {
            "success": True,
            "count": len(results),
            "employees": results
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees: {str(e)}")
        return {
            "success": False,
            "count": 0,
            "employees": [],
            "error": str(e)
        }


@router.get("/salary-slips/filters")
def get_salary_slip_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for salary slips with HYBRID business unit logic
    (Exact same implementation as salary register filters)
    
    Returns:
    - business_units: Businesses for superadmin, Business Units for regular admin
    - locations: All active locations (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    - departments: All active departments (filtered by business)
    """
    try:
        from app.models.location import Location
        from app.models.cost_center import CostCenter
        from app.models.department import Department
        from app.utils.business_unit_utils import get_business_unit_options
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get business units using HYBRID APPROACH (same as salary register)
        business_unit_options = get_business_unit_options(db, current_user, business_id)
        
        # Get locations (same pattern as salary register)
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments (same pattern as salary register)
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers (same pattern as salary register)
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "business_units": business_unit_options,
            "locations": location_options,
            "cost_centers": cost_center_options,
            "departments": department_options,
            "record_types": ["All", "Active", "Inactive"],
            "amount_rounding_options": ["0 decimals", "2 decimals"],
            "unit_rounding_options": ["0 decimals", "2 decimals"]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching salary slip filters: {str(e)}")
        # Return default values if there's an error
        return {
            "business_units": ["All Business Units"],
            "locations": ["All Locations"],
            "cost_centers": ["All Cost Centers"],
            "departments": ["All Departments"],
            "record_types": ["All", "Active", "Inactive"],
            "amount_rounding_options": ["0 decimals", "2 decimals"],
            "unit_rounding_options": ["0 decimals", "2 decimals"]
        }


@router.post("/salary-slips")
def get_salary_slips(
    filters: SalarySlipFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get comprehensive salary slips with filtering options"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_salary_slips(filters)


@router.post("/salary-slips/save-preferences")
def save_salary_slip_preferences(
    preferences: SalarySlipPreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save user's salary slip report preferences
    
    **Request body:**
    - showGrossSalary: Show gross salary (optional)
    - showDeductions: Show deductions (optional)
    - showNetSalary: Show net salary (optional)
    - showEarnings: Show earnings breakdown (optional)
    - showAttendance: Show attendance summary (optional)
    - showLeaveBalance: Show leave balance (optional)
    - includeCompanyLogo: Include company logo (optional)
    - includeEmployeePhoto: Include employee photo (optional)
    - dateFormat: Date format preference (optional)
    - currency: Currency code (optional)
    
    Note: Currently stores in localStorage on frontend.
    TODO: Add preferences field to User model for database storage.
    """
    try:
        # For now, just return success
        # The frontend will handle localStorage storage
        # In future, add a preferences JSON field to User model
        
        return {
            "success": True,
            "message": "Preferences saved successfully",
            "preferences": preferences,
            "note": "Preferences stored locally in browser"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in save preferences endpoint: {str(e)}")
        return {
            "success": True,  # Return success anyway since localStorage works
            "message": "Preferences saved locally",
            "preferences": preferences
        }


@router.get("/salary-slips/preferences")
def get_salary_slip_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's saved salary slip report preferences
    Note: Currently returns empty, frontend uses localStorage.
    TODO: Add preferences field to User model for database storage.
    """
    try:
        # For now, return empty preferences
        # Frontend will use localStorage as fallback
        
        return {
            "success": True,
            "preferences": {},
            "note": "Using localStorage for preferences"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get preferences endpoint: {str(e)}")
        return {
            "success": False,
            "preferences": {}
        }


@router.get("/salary-slips")
def get_salary_slips_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., SEP-2025)"),
    business_unit: str = Query("All Business Units", description="Business unit filter"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee: str = Query(None, description="Employee search term"),
    records: str = Query("Active", description="Record type: All, Active, Inactive"),
    exclude_hold: bool = Query(True, description="Exclude hold salary"),
    records_per_page: int = Query(1, description="Records per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary slips with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = SalarySlipFilters(
        period=period,
        business_unit=business_unit,
        location=location,
        cost_center=cost_center,
        department=department,
        employee=employee,
        records=records,
        exclude_hold=exclude_hold,
        records_per_page=records_per_page,
        options={},  # Default empty options
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_salary_slips(filters)


# Salary Register Endpoints
@router.get("/salary-register/filters")
def get_salary_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for salary register with HYBRID business unit logic
    
    Returns:
    - business_units: Businesses for superadmin, Business Units for regular admin
    - locations: All active locations
    - cost_centers: All active cost centers
    - departments: All active departments
    """
    from app.models.business import Business
    from app.models.location import Location
    from app.models.department import Department
    from app.models.cost_center import CostCenter
    from app.utils.business_unit_utils import get_business_unit_options
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    try:
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get business units using HYBRID APPROACH
        business_unit_options = get_business_unit_options(db, current_user, business_id)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "success": True,
            "business_units": business_unit_options,
            "locations": location_options,
            "departments": department_options,
            "cost_centers": cost_center_options
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching salary register filters: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching filters: {str(e)}")


@router.post("/salary-register")
def get_salary_register(
    filters: SalaryRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get comprehensive salary register with filtering options"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_salary_register(filters)


@router.get("/salary-register")
def get_salary_register_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUL-2025)"),
    business_unit: str = Query("All Business Units", description="Business unit filter"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee: str = Query(None, description="Employee search term"),
    active_records: bool = Query(True, description="Include active records"),
    inactive_records: bool = Query(False, description="Include inactive records"),
    all_records: bool = Query(False, description="Include all records"),
    exclude_hold: bool = Query(True, description="Exclude hold salary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary register with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = SalaryRegisterFilters(
        period=period,
        business_unit=business_unit,
        location=location,
        cost_center=cost_center,
        department=department,
        employee=employee,
        active_records=active_records,
        inactive_records=inactive_records,
        all_records=all_records,
        exclude_hold=exclude_hold,
        options={},  # Default empty options
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_salary_register(filters)


# Cost to Company Endpoints
@router.get("/cost-to-company/filters")
def get_cost_to_company_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for cost to company report with HYBRID business unit logic
    
    Returns:
    - locations: All active locations (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    - departments: All active departments (filtered by business)
    """
    try:
        from app.models.location import Location
        from app.models.cost_center import CostCenter
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "locations": location_options,
            "cost_centers": cost_center_options,
            "departments": department_options
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching cost to company filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "cost_centers": ["All Cost Centers"],
            "departments": ["All Departments"]
        }


@router.post("/cost-to-company")
def get_cost_to_company_report(
    filters: CostToCompanyFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get cost to company report with detailed salary breakdown"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_cost_to_company_report(filters)


@router.get("/cost-to-company")
def get_cost_to_company_report_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    revision: str = Query("latest", description="Revision type: latest, all, dateSpecific"),
    date_specific: str = Query(None, description="Specific date in YYYY-MM-DD format"),
    employee_search: str = Query(None, description="Employee search term"),
    active_only: bool = Query(True, description="Include only active employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get cost to company report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = CostToCompanyFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        revision=revision,
        date_specific=date_specific,
        employee_search=employee_search,
        active_only=active_only,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_cost_to_company_report(filters)


@router.get("/cost-to-company/employee-search")
def search_employees_for_ctc(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Cost to Company report autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(Employee).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.employee_status == 'ACTIVE'
        )
        
        # Apply business filter if applicable
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "display": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip()
            }
            for emp in employees
        ]
        
        return {"employees": results, "total": len(results)}
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for CTC: {str(e)}")
        return {"employees": [], "total": 0}


@router.post("/cost-to-company/email")
async def email_cost_to_company_report(
    filters: CostToCompanyFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Email Cost to Company report to employee
    
    Sends a professional HTML email with CTC breakdown to the employee's email address
    """
    from app.api.v1.endpoints.master_setup import get_user_business_id
    from app.services.email_service import EmailService
    from app.services.email_template.cost_to_company_template import (
        generate_ctc_email_template,
        generate_ctc_plain_text
    )
    from app.models.employee import Employee
    from app.models.business import Business
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # CRITICAL: Get business_id and inject into filters for security
        business_id = get_user_business_id(current_user, db)
        filters.business_id = business_id
        
        logger.info(f"[CTC EMAIL] Sending email for business_id={business_id}, employee_search={filters.employee_search}")
        
        # Get CTC data
        service = ReportsService(db)
        ctc_response = service.get_cost_to_company_report(filters)
        
        if not ctc_response.employees or len(ctc_response.employees) == 0:
            raise HTTPException(
                status_code=404,
                detail="No employee data found. Please ensure the employee has a salary structure configured."
            )
        
        if len(ctc_response.employees) > 1:
            raise HTTPException(
                status_code=400,
                detail=f"Multiple employees found ({len(ctc_response.employees)}). Please specify a single employee code."
            )
        
        # Get the single employee data
        employee_data = ctc_response.employees[0]
        
        # Get employee email from database
        employee = db.query(Employee).filter(
            Employee.employee_code == employee_data.employee_code,
            Employee.business_id == business_id
        ).first()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        if not employee.email:
            raise HTTPException(
                status_code=400,
                detail=f"Employee {employee.employee_code} does not have an email address configured."
            )
        
        # Get company name
        business = db.query(Business).filter(Business.id == business_id).first()
        company_name = business.business_name if business else "DCM HRMS"
        
        # Convert employee data to dict for template
        employee_dict = {
            'employee_name': employee_data.employee_name,
            'employee_code': employee_data.employee_code,
            'designation': employee_data.designation,
            'department': employee_data.department,
            'location': employee_data.location,
            'cost_center': employee_data.cost_center,
            'basic_salary': employee_data.basic_salary,
            'gross_salary': employee_data.gross_salary,
            'total_ctc': employee_data.total_ctc,
            'total_earnings': employee_data.total_earnings,
            'total_deductions': employee_data.total_deductions,
            'total_employer_contributions': employee_data.total_employer_contributions,
            'net_payable': employee_data.net_payable,
            'effective_from': str(employee_data.effective_from) if employee_data.effective_from else 'N/A',
            'earnings': [
                {
                    'component_name': e.component_name,
                    'amount': float(e.amount)
                }
                for e in employee_data.earnings
            ] if employee_data.earnings else [],
            'deductions': [
                {
                    'component_name': d.component_name,
                    'amount': float(d.amount)
                }
                for d in employee_data.deductions
            ] if employee_data.deductions else [],
            'employer_contributions': [
                {
                    'component_name': c.component_name,
                    'amount': float(c.amount)
                }
                for c in employee_data.employer_contributions
            ] if employee_data.employer_contributions else []
        }
        
        # Generate email content
        html_content = generate_ctc_email_template(employee_dict, company_name)
        text_content = generate_ctc_plain_text(employee_dict, company_name)
        
        # Send email
        email_service = EmailService()
        success = await email_service.send_email(
            to_email=employee.email,
            subject=f"Cost to Company Report - {employee_data.employee_code}",
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            logger.info(f"[CTC EMAIL] Successfully sent email to {employee.email}")
            return {
                "success": True,
                "message": f"Cost to Company report sent successfully to {employee.email}",
                "employee_code": employee_data.employee_code,
                "employee_name": employee_data.employee_name,
                "email": employee.email
            }
        else:
            logger.warning(f"[CTC EMAIL] SMTP not configured, email not sent")
            raise HTTPException(
                status_code=503,
                detail="Email service is not configured. Please contact your administrator to set up SMTP settings."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CTC EMAIL] Error sending email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )


# Overtime Register Endpoints
@router.get("/overtime-register/filters")
def get_overtime_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for overtime register with HYBRID business unit logic
    
    Returns:
    - locations: All active locations (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    - departments: All active departments (filtered by business)
    """
    try:
        from app.models.location import Location
        from app.models.cost_center import CostCenter
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "locations": location_options,
            "cost_centers": cost_center_options,
            "departments": department_options
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching overtime register filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "cost_centers": ["All Cost Centers"],
            "departments": ["All Departments"]
        }


@router.post("/overtime-register")
def get_overtime_register(
    filters: OvertimeRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get overtime register with employee overtime details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_overtime_register(filters)


@router.get("/overtime-register")
def get_overtime_register_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUN-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    payment_date: str = Query(None, description="Payment date in YYYY-MM-DD format"),
    include_inactive_employees: bool = Query(False, description="Include inactive employees"),
    include_zero_records: bool = Query(False, description="Include zero overtime records"),
    detailed_report: bool = Query(False, description="Generate detailed report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get overtime register with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = OvertimeRegisterFilters(
        period=period,
        location=location,
        cost_center=cost_center,
        department=department,
        payment_date=payment_date,
        include_inactive_employees=include_inactive_employees,
        include_zero_records=include_zero_records,
        detailed_report=detailed_report,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_overtime_register(filters)


# Time Salary Endpoints
@router.post("/time-salary")
def get_time_salary_report(
    filters: TimeSalaryFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get time salary report with employee time-based salary details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_time_salary_report(filters)


@router.get("/time-salary")
def get_time_salary_report_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., MAR-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    salary_component: str = Query(None, description="Salary component filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get time salary report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = TimeSalaryFilters(
        period=period,
        location=location,
        department=department,
        salary_component=salary_component,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_time_salary_report(filters)


@router.get("/time-salary/filters")
def get_time_salary_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for Time Salary report
    
    Returns distinct locations, departments, and salary components from database
    """
    try:
        from app.models.employee import Employee
        from app.models.location import Location
        from app.models.department import Department
        from app.models.setup.salary_and_deductions.salary_component import SalaryComponent
        from app.models.setup.salary_and_deductions.time_salary import TimeSalaryRule
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get distinct locations from active employees
        locations_query = db.query(Location.name).join(
            Employee, Employee.location_id == Location.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            locations_query = locations_query.filter(Employee.business_id == business_id)
        
        locations = ["All Locations"] + [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get distinct departments from active employees
        departments_query = db.query(Department.name).join(
            Employee, Employee.department_id == Department.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            departments_query = departments_query.filter(Employee.business_id == business_id)
        
        departments = ["All Departments"] + [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get ALL active salary components (not just those in time salary rules)
        # This gives users the option to filter by any component
        components_query = db.query(SalaryComponent.name).filter(
            SalaryComponent.is_active == True
        ).order_by(SalaryComponent.name)
        
        # Optional: Filter by business_id if needed
        # if business_id:
        #     components_query = components_query.filter(SalaryComponent.business_id == business_id)
        
        salary_components = [comp[0] for comp in components_query.distinct().all() if comp[0]]
        
        return {
            "locations": locations,
            "departments": departments,
            "salary_components": salary_components
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching time salary filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "salary_components": ["Basic Salary"]
        }


@router.get("/time-salary/employee-search")
def search_employees_for_time_salary(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Time Salary report autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(
            Employee.employee_code,
            Employee.first_name,
            Employee.last_name,
            Department.name.label('department_name')
        ).outerjoin(
            Department, Employee.department_id == Department.id
        ).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.employee_status == 'ACTIVE'
        )
        
        # Apply business filter if applicable
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "employee_code": emp.employee_code,
                "full_name": f"{emp.first_name} {emp.last_name}".strip(),
                "department": emp.department_name or "N/A"
            }
            for emp in employees
        ]
        
        return {"employees": results}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for time salary: {str(e)}")
        return {"employees": []}


# Leave Encashment Report Endpoints
@router.post("/leave-encashment")
def get_leave_encashment_report(
    filters: LeaveEncashmentReportFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get leave encashment report with employee leave encashment details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_leave_encashment_report(filters)


@router.get("/leave-encashment")
def get_leave_encashment_report_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., OCT-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get leave encashment report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = LeaveEncashmentReportFilters(
        period=period,
        location=location,
        department=department,
        cost_center=cost_center,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_leave_encashment_report(filters)


@router.get("/leave-encashment/filters")
def get_leave_encashment_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for Leave Encashment report
    
    Returns distinct locations, departments, and cost centers from database
    """
    try:
        from app.models.employee import Employee
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get distinct locations from active employees
        locations_query = db.query(Location.name).join(
            Employee, Employee.location_id == Location.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            locations_query = locations_query.filter(Employee.business_id == business_id)
        
        locations = ["All Locations"] + [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get distinct departments from active employees
        departments_query = db.query(Department.name).join(
            Employee, Employee.department_id == Department.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            departments_query = departments_query.filter(Employee.business_id == business_id)
        
        departments = ["All Departments"] + [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get distinct cost centers from active employees
        cost_centers_query = db.query(CostCenter.name).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            cost_centers_query = cost_centers_query.filter(Employee.business_id == business_id)
        
        cost_centers = ["All Cost Centers"] + [cc[0] for cc in cost_centers_query.distinct().all() if cc[0]]
        
        return {
            "locations": locations,
            "departments": departments,
            "cost_centers": cost_centers
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching leave encashment filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"]
        }


@router.get("/leave-encashment/employee-search")
def search_employees_for_leave_encashment(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Leave Encashment report autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(
            Employee.employee_code,
            Employee.first_name,
            Employee.last_name,
            Department.name.label('department_name')
        ).outerjoin(
            Department, Employee.department_id == Department.id
        ).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.employee_status == 'ACTIVE'
        )
        
        # Apply business filter if applicable
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "employee_code": emp.employee_code,
                "full_name": f"{emp.first_name} {emp.last_name}".strip(),
                "department": emp.department_name or "N/A"
            }
            for emp in employees
        ]
        
        return {"employees": results}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for leave encashment: {str(e)}")
        return {"employees": []}


# Rate Salary Endpoints
@router.post("/rate-salary")
def get_rate_salary_report(
    filters: RateSalaryFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get rate salary report with employee rate-based salary details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_rate_salary_report(filters)


@router.get("/rate-salary")
def get_rate_salary_report_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUN-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    salary_component: str = Query("- Select -", description="Salary component filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get rate salary report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = RateSalaryFilters(
        period=period,
        location=location,
        department=department,
        salary_component=salary_component,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_rate_salary_report(filters)


@router.get("/rate-salary/filters")
def get_rate_salary_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for Rate Salary report
    
    Returns distinct locations, departments, and salary components from database
    """
    try:
        from app.models.employee import Employee
        from app.models.location import Location
        from app.models.department import Department
        from app.models.setup.salary_and_deductions.salary_component import SalaryComponent
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get distinct locations from active employees
        locations_query = db.query(Location.name).join(
            Employee, Employee.location_id == Location.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            locations_query = locations_query.filter(Employee.business_id == business_id)
        
        locations = ["All Locations"] + [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get distinct departments from active employees
        departments_query = db.query(Department.name).join(
            Employee, Employee.department_id == Department.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            departments_query = departments_query.filter(Employee.business_id == business_id)
        
        departments = ["All Departments"] + [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get ALL active salary components
        components_query = db.query(SalaryComponent.name).filter(
            SalaryComponent.is_active == True
        ).order_by(SalaryComponent.name)
        
        salary_components = [comp[0] for comp in components_query.distinct().all() if comp[0]]
        
        return {
            "locations": locations,
            "departments": departments,
            "salary_components": salary_components
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching rate salary filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "salary_components": []
        }


@router.get("/rate-salary/employee-search")
def search_employees_for_rate_salary(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Rate Salary report autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(
            Employee.employee_code,
            Employee.first_name,
            Employee.last_name,
            Department.name.label('department_name')
        ).outerjoin(
            Department, Employee.department_id == Department.id
        ).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.employee_status == 'ACTIVE'
        )
        
        # Apply business filter if applicable
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "employee_code": emp.employee_code,
                "full_name": f"{emp.first_name} {emp.last_name}".strip(),
                "department": emp.department_name or "N/A"
            }
            for emp in employees
        ]
        
        return {"employees": results}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for rate salary: {str(e)}")
        return {"employees": []}


# Variable Salary Endpoints
@router.get("/variable-salary/filters")
def get_variable_salary_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for variable salary report
    
    Returns:
    - locations: All active locations (filtered by business)
    - departments: All active departments (filtered by business)
    - salary_components: All variable salary components actually used in SalaryVariable table
    """
    try:
        from app.models.location import Location
        from app.models.department import Department
        from app.models.datacapture import SalaryVariable
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import func, distinct
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get actual variable names used in SalaryVariable table
        components_query = db.query(SalaryVariable.variable_name).filter(
            SalaryVariable.is_active == True
        ).distinct()
        
        if business_id:
            components_query = components_query.filter(SalaryVariable.business_id == business_id)
        
        components = components_query.order_by(SalaryVariable.variable_name).all()
        component_options = [comp[0] for comp in components if comp[0]]
        
        # Add default options if no components found
        if not component_options:
            component_options = ["Leave Encashment", "Bonus", "Incentive", "Commission"]
        
        return {
            "locations": location_options,
            "departments": department_options,
            "salary_components": component_options
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching variable salary filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "salary_components": ["Leave Encashment", "Bonus", "Incentive"]
        }


@router.get("/variable-salary/employee-search")
def search_employees_for_variable_salary(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Variable Salary report autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(Employee).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.employee_status == 'ACTIVE'
        )
        
        # Apply business filter if applicable
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "display": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip()
            }
            for emp in employees
        ]
        
        return {"employees": results, "total": len(results)}
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for variable salary: {str(e)}")
        return {"employees": [], "total": 0, "error": str(e)}


@router.post("/variable-salary")
def get_variable_salary_report(
    filters: VariableSalaryFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get variable salary report with employee variable salary details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_variable_salary_report(filters)


@router.get("/variable-salary")
def get_variable_salary_report_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUN-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    salary_component: str = Query("Leave Encashment", description="Salary component filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get variable salary report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = VariableSalaryFilters(
        period=period,
        location=location,
        department=department,
        salary_component=salary_component,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_variable_salary_report(filters)


# Statutory Bonus Report Endpoints
@router.get("/statutory-bonus/filters")
def get_statutory_bonus_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for Statutory Bonus report
    
    Returns distinct locations, departments, and cost centers from database
    """
    try:
        from app.models.employee import Employee
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get distinct locations from active employees
        locations_query = db.query(Location.name).join(
            Employee, Employee.location_id == Location.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            locations_query = locations_query.filter(Employee.business_id == business_id)
        
        locations = ["All Locations"] + [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get distinct departments from active employees
        departments_query = db.query(Department.name).join(
            Employee, Employee.department_id == Department.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            departments_query = departments_query.filter(Employee.business_id == business_id)
        
        departments = ["All Departments"] + [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get distinct cost centers from active employees
        cost_centers_query = db.query(CostCenter.name).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            cost_centers_query = cost_centers_query.filter(Employee.business_id == business_id)
        
        cost_centers = ["All Cost Centers"] + [cc[0] for cc in cost_centers_query.distinct().all() if cc[0]]
        
        return {
            "locations": locations,
            "departments": departments,
            "cost_centers": cost_centers
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching statutory bonus filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"]
        }


@router.post("/statutory-bonus")
def get_statutory_bonus_report(
    filters: StatutoryBonusReportFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get statutory bonus report with employee bonus details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_statutory_bonus_report(filters)


@router.get("/statutory-bonus")
def get_statutory_bonus_report_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUL-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get statutory bonus report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = StatutoryBonusReportFilters(
        period=period,
        location=location,
        department=department,
        cost_center=cost_center,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_statutory_bonus_report(filters)


# Salary Deductions Report Endpoints
@router.get("/salary-deductions/filters")
def get_salary_deductions_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for Salary Deductions report
    
    Returns locations, departments, cost centers, and deduction types from database
    """
    try:
        from app.models.employee import Employee
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.models.setup.salary_and_deductions.salary_deduction import SalaryDeduction
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get distinct locations from active employees
        locations_query = db.query(Location.name).join(
            Employee, Employee.location_id == Location.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            locations_query = locations_query.filter(Employee.business_id == business_id)
        
        locations = ["All Locations"] + [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get distinct departments from active employees
        departments_query = db.query(Department.name).join(
            Employee, Employee.department_id == Department.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            departments_query = departments_query.filter(Employee.business_id == business_id)
        
        departments = ["All Departments"] + [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get distinct cost centers from active employees
        cost_centers_query = db.query(CostCenter.name).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            cost_centers_query = cost_centers_query.filter(Employee.business_id == business_id)
        
        cost_centers = ["All Cost Centers"] + [cc[0] for cc in cost_centers_query.distinct().all() if cc[0]]
        
        # Get deduction components (don't filter by business_id as these are setup/master data)
        deductions_query = db.query(SalaryDeduction.name).filter(
            SalaryDeduction.active == True
        ).distinct()
        
        deductions = ["-select-"] + [ded[0] for ded in deductions_query.all() if ded[0]]
        
        return {
            "locations": locations,
            "departments": departments,
            "cost_centers": cost_centers,
            "deductions": deductions
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching salary deductions filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"],
            "deductions": ["-select-"]
        }


@router.get("/salary-deductions/search-employees")
def search_employees_for_salary_deductions(
    search: str = Query(..., min_length=2, description="Search term (min 2 characters)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for salary deductions report autocomplete
    
    Returns list of employees matching search term
    """
    try:
        from app.models.employee import Employee
        from sqlalchemy import or_, func
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        search_term = f"%{search.strip()}%"
        
        query = db.query(Employee).filter(
            Employee.employee_status == 'ACTIVE',
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term),
                func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
            )
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        employees = query.limit(10).all()
        
        return [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": emp.full_name,
                "display": f"{emp.employee_code} - {emp.full_name}"
            }
            for emp in employees
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees: {str(e)}")
        return []


@router.post("/salary-deductions")
def get_salary_deductions_report(
    filters: SalaryDeductionsFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary deductions report with employee deduction details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    from app.services.salary_deductions_service import SalaryDeductionsService
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = SalaryDeductionsService(db)
    return service.get_salary_deductions_report(filters)


@router.get("/salary-deductions")
def get_salary_deductions_report_get(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., MAY-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    deduction: str = Query("-select-", description="Deduction type filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary deductions report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    from app.services.salary_deductions_service import SalaryDeductionsService
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = SalaryDeductionsFilters(
        month=month,
        location=location,
        department=department,
        cost_center=cost_center,
        deduction=deduction,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = SalaryDeductionsService(db)
    return service.get_salary_deductions_report(filters)


# Employee Loans Report Endpoints
@router.get("/employee-loans/filters")
def get_employee_loans_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for Employee Loans report
    
    Returns locations, departments, cost centers from database
    """
    try:
        from app.models.employee import Employee
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get distinct locations from active employees
        locations_query = db.query(Location.name).join(
            Employee, Employee.location_id == Location.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            locations_query = locations_query.filter(Employee.business_id == business_id)
        
        locations = ["All Locations"] + [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get distinct departments from active employees
        departments_query = db.query(Department.name).join(
            Employee, Employee.department_id == Department.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            departments_query = departments_query.filter(Employee.business_id == business_id)
        
        departments = ["All Departments"] + [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get distinct cost centers from active employees
        cost_centers_query = db.query(CostCenter.name).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(
            Employee.employee_status == 'ACTIVE'
        )
        
        if business_id:
            cost_centers_query = cost_centers_query.filter(Employee.business_id == business_id)
        
        cost_centers = ["All Cost Centers"] + [cc[0] for cc in cost_centers_query.distinct().all() if cc[0]]
        
        # Issued during options
        issued_during = ["Last 30 days", "Last 3 months", "Last 6 months", "Last 1 year", "All Time"]
        
        return {
            "locations": locations,
            "departments": departments,
            "cost_centers": cost_centers,
            "issued_during": issued_during
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching employee loans filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"],
            "issued_during": ["Last 30 days", "Last 3 months", "Last 6 months", "Last 1 year", "All Time"]
        }


@router.get("/employee-loans/search-employees")
def search_employees_for_loans(
    search: str = Query(..., min_length=2, description="Search term (min 2 characters)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for loans report autocomplete
    
    Returns list of employees matching search term
    """
    try:
        from app.models.employee import Employee
        from sqlalchemy import or_, func
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        search_term = f"%{search.strip()}%"
        
        query = db.query(Employee).filter(
            Employee.employee_status == 'ACTIVE',
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term),
                func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
            )
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        employees = query.limit(10).all()
        
        return [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": emp.full_name,
                "display": f"{emp.employee_code} - {emp.full_name}"
            }
            for emp in employees
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees: {str(e)}")
        return []


@router.post("/employee-loans")
def get_employee_loans_report(
    filters: EmployeeLoansFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee loans report with loan details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    from app.services.loan_service import LoanService
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = LoanService(db)
    return service.get_employee_loans_report(filters, current_user)


@router.get("/employee-loans")
def get_employee_loans_report_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    issued_during: str = Query("Last 30 days", description="Date range filter"),
    employee_search: str = Query(None, description="Employee search term"),
    report_type: str = Query("Summary Only", description="Report type: Summary Only or With Loan Schedule"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee loans report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeLoansFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        issued_during=issued_during,
        employee_search=employee_search,
        report_type=report_type,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_loans_report(filters)


# Attendance Register Endpoints
@router.get("/attendance-register/filters")
def get_attendance_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for attendance register
    
    Returns:
    - locations: All active locations (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    - departments: All active departments (filtered by business)
    """
    try:
        from app.models.location import Location
        from app.models.cost_center import CostCenter
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "locations": location_options,
            "cost_centers": cost_center_options,
            "departments": department_options,
            "record_types": ["All Records", "Active Records", "Inactive Records"]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching attendance register filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "cost_centers": ["All Cost Centers"],
            "departments": ["All Departments"],
            "record_types": ["All Records", "Active Records", "Inactive Records"]
        }


@router.post("/attendance-register")
def get_attendance_register(
    filters: AttendanceRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get attendance register with employee attendance details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_attendance_register(filters)


@router.get("/attendance-register")
def get_attendance_register_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    from_date: str = Query(None, description="From date in YYYY-MM-DD format"),
    to_date: str = Query(None, description="To date in YYYY-MM-DD format"),
    employee: str = Query(None, description="Employee search term"),
    record_type: str = Query("All Records", description="Record type: All Records, Active Records, Inactive Records"),
    show_time_punches: bool = Query(False, description="Include time punch details"),
    show_strikes: bool = Query(False, description="Include strike information"),
    show_time_summary: bool = Query(False, description="Include time summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get attendance register with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = AttendanceRegisterFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        from_date=from_date,
        to_date=to_date,
        employee=employee,
        record_type=record_type,
        show_time_punches=show_time_punches,
        show_strikes=show_strikes,
        show_time_summary=show_time_summary,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_attendance_register(filters)


@router.get("/attendance-register/employee-search")
def search_employees_for_attendance_register(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Attendance Register autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(Employee).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        )
        
        # Apply business filter (CRITICAL: Business isolation)
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "display": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip(),
                "status": emp.employee_status
            }
            for emp in employees
        ]
        
        return {"employees": results, "total": len(results)}
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for attendance register: {str(e)}")
        return {"employees": [], "total": 0}


# SAP Export Report Endpoints
@router.post("/sap-export")
def get_sap_export_report(
    filters: SAPExportFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get SAP export report with salary data formatted for SAP import"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_sap_export_report(filters)


@router.get("/sap-export")
def get_sap_export_report_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., SEP-2025)"),
    format: str = Query("xlsx", description="Export format: xlsx or txt"),
    business_unit: str = Query("All Business Units", description="Business unit filter"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get SAP export report with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = SAPExportFilters(
        period=period,
        format=format,
        business_unit=business_unit,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_sap_export_report(filters)


@router.get("/salary/summary")
def get_salary_summary(
    period: str = Query(..., pattern=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get salary summary for a period"""
    service = ReportsService(db)
    return service.get_salary_summary(period)


# Attendance Report Endpoints
@router.post("/attendance", response_model=AttendanceReportResponse)
def create_attendance_report(
    report_data: AttendanceReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new attendance report"""
    service = ReportsService(db)
    return service.create_attendance_report(report_data)


@router.get("/attendance", response_model=List[AttendanceReportResponse])
def get_attendance_reports(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_ids: Optional[str] = Query(None, description="Comma-separated employee IDs"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get attendance reports with filters"""
    service = ReportsService(db)
    
    # Parse employee IDs
    employee_id_list = None
    if employee_ids:
        try:
            employee_id_list = [int(id.strip()) for id in employee_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid employee IDs format")
    
    filters = ReportFilters(
        start_date=start_date,
        end_date=end_date,
        employee_ids=employee_id_list,
        status=status
    )
    
    return service.get_attendance_reports(filters)


@router.get("/attendance/summary")
def get_attendance_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get attendance summary for a date range"""
    service = ReportsService(db)
    return service.get_attendance_summary(start_date, end_date)


# Employee Report Endpoints
@router.post("/employee", response_model=EmployeeReportResponse)
def create_employee_report(
    report_data: EmployeeReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new employee report"""
    service = ReportsService(db)
    return service.create_employee_report(report_data)


@router.get("/employee", response_model=List[EmployeeReportResponse])
def get_employee_reports(
    employee_ids: Optional[str] = Query(None, description="Comma-separated employee IDs"),
    report_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee reports with filters"""
    service = ReportsService(db)
    
    # Parse employee IDs
    employee_id_list = None
    if employee_ids:
        try:
            employee_id_list = [int(id.strip()) for id in employee_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid employee IDs format")
    
    filters = ReportFilters(
        employee_ids=employee_id_list,
        report_type=report_type,
        status=status
    )
    
    return service.get_employee_reports(filters)


# Statutory Report Endpoints
@router.post("/statutory", response_model=StatutoryReportResponse)
def create_statutory_report(
    report_data: StatutoryReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new statutory report"""
    service = ReportsService(db)
    return service.create_statutory_report(report_data)


@router.get("/statutory", response_model=List[StatutoryReportResponse])
def get_statutory_reports(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_ids: Optional[str] = Query(None, description="Comma-separated employee IDs"),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get statutory reports with filters"""
    service = ReportsService(db)
    
    # Parse employee IDs
    employee_id_list = None
    if employee_ids:
        try:
            employee_id_list = [int(id.strip()) for id in employee_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid employee IDs format")
    
    filters = ReportFilters(
        start_date=start_date,
        end_date=end_date,
        employee_ids=employee_id_list,
        report_type=report_type
    )
    
    return service.get_statutory_reports(filters)


# Annual Report Endpoints
@router.post("/annual", response_model=AnnualReportResponse)
def create_annual_report(
    report_data: AnnualReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new annual report"""
    service = ReportsService(db)
    return service.create_annual_report(report_data)


@router.get("/annual", response_model=List[AnnualReportResponse])
def get_annual_reports(
    employee_ids: Optional[str] = Query(None, description="Comma-separated employee IDs"),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get annual reports with filters"""
    service = ReportsService(db)
    
    # Parse employee IDs
    employee_id_list = None
    if employee_ids:
        try:
            employee_id_list = [int(id.strip()) for id in employee_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid employee IDs format")
    
    filters = ReportFilters(
        employee_ids=employee_id_list,
        report_type=report_type
    )
    
    return service.get_annual_reports(filters)


# Activity Log Endpoints
@router.post("/activity-logs", response_model=ActivityLogResponse)
def create_activity_log(
    log_data: ActivityLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new activity log"""
    service = ReportsService(db)
    
    # Add IP address and user agent from request
    log_data.ip_address = request.client.host
    log_data.user_agent = request.headers.get("user-agent")
    
    return service.create_activity_log(current_user.id, log_data)


@router.get("/activity-logs", response_model=List[ActivityLogResponse])
def get_activity_logs(
    user_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get activity logs"""
    service = ReportsService(db)
    return service.get_activity_logs(user_id, limit)


# Activity Logs Report Endpoints (Frontend Compatible)
@router.get("/activitylogs")
def get_activity_logs_report_frontend(
    from_date: str = Query(None, description="From date in YYYY-MM-DD format"),
    to_date: str = Query(None, description="To date in YYYY-MM-DD format"),
    user_id: int = Query(None, description="Filter by specific user ID"),
    module: str = Query(None, description="Filter by module"),
    action: str = Query(None, description="Filter by action"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Activity Logs report with query parameters"""
    from app.api.v1.deps import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = ActivityLogFilters(
        from_date=from_date,
        to_date=to_date,
        user_id=user_id,
        module=module,
        action=action,
        limit=limit,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_activity_logs_report(filters)


@router.post("/activitylogs")
def get_activity_logs_report_frontend_post(
    filters: ActivityLogFilters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Activity Logs report with request body"""
    from app.api.v1.deps import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_activity_logs_report(filters)


# User Feedback Endpoints
@router.post("/feedback", response_model=UserFeedbackResponse)
def create_user_feedback(
    feedback_data: UserFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new user feedback"""
    service = ReportsService(db)
    return service.create_user_feedback(current_user.id, feedback_data)


@router.get("/feedback", response_model=List[UserFeedbackResponse])
def get_user_feedback(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get user feedback"""
    service = ReportsService(db)
    return service.get_user_feedback(limit)


@router.put("/feedback/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int,
    status: str = Query(..., pattern="^(open|in_progress|resolved|closed)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update feedback status"""
    service = ReportsService(db)
    updated_feedback = service.update_feedback_status(feedback_id, status, current_user.id)
    if not updated_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return updated_feedback


# User Feedback Report Endpoints (Frontend Compatible)
@router.get("/userfeedback")
def get_user_feedback_report_frontend(
    from_date: str = Query(None, description="From date in YYYY-MM-DD format"),
    to_date: str = Query(None, description="To date in YYYY-MM-DD format"),
    feedback_type: str = Query(None, description="Filter by feedback type"),
    status: str = Query(None, description="Filter by status"),
    rating: int = Query(None, ge=1, le=5, description="Filter by rating"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of feedback to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get User Feedback report with query parameters"""
    from app.api.v1.deps import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = {
        "from_date": from_date,
        "to_date": to_date,
        "feedback_type": feedback_type,
        "status": status,
        "rating": rating,
        "limit": limit,
        "business_id": business_id  # Inject business_id
    }
    
    service = ReportsService(db)
    return service.get_user_feedback_report(filters)


@router.post("/userfeedback")
def get_user_feedback_report_frontend_post(
    filters: UserFeedbackReportFilters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get User Feedback report with request body
    
    **Request body:**
    - startDate: Start date in YYYY-MM-DD format (optional)
    - endDate: End date in YYYY-MM-DD format (optional)
    - status: Feedback status (optional)
    - rating: Feedback rating 1-5 (optional)
    - category: Feedback category (optional)
    - employeeId: Employee ID (optional)
    """
    from app.api.v1.deps import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_user_feedback_report(filters.model_dump())


# System Alert Endpoints
@router.post("/alerts", response_model=SystemAlertResponse)
def create_system_alert(
    alert_data: SystemAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new system alert"""
    service = ReportsService(db)
    return service.create_system_alert(alert_data)


@router.get("/alerts", response_model=List[SystemAlertResponse])
def get_system_alerts(
    is_resolved: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get system alerts"""
    service = ReportsService(db)
    return service.get_system_alerts(is_resolved, limit)


@router.put("/alerts/{alert_id}/resolve")
def resolve_system_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Resolve system alert"""
    service = ReportsService(db)
    resolved_alert = service.resolve_system_alert(alert_id, current_user.id)
    if not resolved_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return resolved_alert


# System Alerts Report Endpoints (Frontend Compatible)
@router.get("/systemalerts")
def get_system_alerts_report_frontend(
    from_date: str = Query(None, description="From date in YYYY-MM-DD format"),
    to_date: str = Query(None, description="To date in YYYY-MM-DD format"),
    alert_type: str = Query(None, description="Filter by alert type"),
    is_resolved: bool = Query(None, description="Filter by resolution status"),
    module: str = Query(None, description="Filter by module"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of alerts to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get System Alerts report with query parameters"""
    from app.api.v1.deps import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = {
        "from_date": from_date,
        "to_date": to_date,
        "alert_type": alert_type,
        "is_resolved": is_resolved,
        "module": module,
        "limit": limit,
        "business_id": business_id  # Inject business_id
    }
    
    service = ReportsService(db)
    return service.get_system_alerts_report(filters)


@router.post("/systemalerts")
def get_system_alerts_report_frontend_post(
    filters: SystemAlertsReportFilters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get System Alerts report with request body
    
    **Request body:**
    - startDate: Start date in YYYY-MM-DD format (optional)
    - endDate: End date in YYYY-MM-DD format (optional)
    - severity: Alert severity - low, medium, high, critical (optional)
    - status: Alert status - active, resolved, dismissed (optional)
    - alertType: Alert type (optional)
    - module: Module name (optional)
    """
    from app.api.v1.deps import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_system_alerts_report(filters.model_dump())


# Dashboard Endpoint
@router.get("/dashboard", response_model=ReportDashboard)
def get_reports_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get reports dashboard data"""
    service = ReportsService(db)
    return service.get_reports_dashboard()


# Export Endpoints
@router.post("/export/{report_type}")
def export_report_data(
    report_type: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_ids: Optional[str] = Query(None, description="Comma-separated employee IDs"),
    format: str = Query("excel", pattern="^(excel|csv|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Export report data in specified format"""
    service = ReportsService(db)
    
    # Parse employee IDs
    employee_id_list = None
    if employee_ids:
        try:
            employee_id_list = [int(id.strip()) for id in employee_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid employee IDs format")
    
    filters = ReportFilters(
        start_date=start_date,
        end_date=end_date,
        employee_ids=employee_id_list
    )
    
    try:
        return service.export_report_data(report_type, filters, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Leave Register Endpoints
@router.get("/leave-register/filters")
def get_leave_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for leave register
    
    Returns:
    - locations: All active locations (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    - departments: All active departments (filtered by business)
    - years: Available years
    - months: Month options
    """
    try:
        from app.models.location import Location
        from app.models.cost_center import CostCenter
        from app.models.department import Department
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from datetime import datetime
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get locations
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get cost centers
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        # Get departments
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Generate year options (current year and previous 2 years)
        current_year = datetime.now().year
        year_options = [str(year) for year in range(current_year - 2, current_year + 2)]
        
        # Month options
        month_options = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        return {
            "locations": location_options,
            "cost_centers": cost_center_options,
            "departments": department_options,
            "years": year_options,
            "months": month_options
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching leave register filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "cost_centers": ["All Cost Centers"],
            "departments": ["All Departments"],
            "years": ["2024", "2025", "2026"],
            "months": ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        }


@router.post("/leave-register")
def get_leave_register(
    filters: LeaveRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get leave register with employee leave details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_leave_register(filters)


@router.get("/leave-register")
def get_leave_register_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    year: str = Query("2025", description="Year filter"),
    month: str = Query("December", description="Month filter (January to selected month)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get leave register with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = LeaveRegisterFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        year=year,
        month=month,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_leave_register(filters)


# Strike Register Endpoints
@router.get("/strike-register/filters")
def get_strike_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for strike register
    
    Returns:
        - locations: List of location names from database
        - departments: List of department names from database
        - cost_centers: List of cost center names from database
        - deductions: List of deduction types from database
    """
    try:
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.models.employee import Employee
        from app.models.datacapture import EmployeeDeduction
        from sqlalchemy import distinct
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # CRITICAL: Get user's business_id for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Base query for active employees - FILTER BY USER'S BUSINESS
        employee_query = db.query(Employee).filter(
            Employee.employee_status == 'ACTIVE',
            Employee.business_id == business_id  # CRITICAL: Business isolation
        )
        employees = employee_query.all()
        employee_ids = [emp.id for emp in employees]
        
        # Get unique locations
        locations = db.query(distinct(Location.name)).join(
            Employee, Employee.location_id == Location.id
        ).filter(Employee.id.in_(employee_ids)).order_by(Location.name).all() if employee_ids else []
        location_list = ["All Locations"] + [loc[0] for loc in locations if loc[0]]
        
        # Get unique departments
        departments = db.query(distinct(Department.name)).join(
            Employee, Employee.department_id == Department.id
        ).filter(Employee.id.in_(employee_ids)).order_by(Department.name).all() if employee_ids else []
        department_list = ["All Departments"] + [dept[0] for dept in departments if dept[0]]
        
        # Get unique cost centers
        cost_centers = db.query(distinct(CostCenter.name)).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(Employee.id.in_(employee_ids)).order_by(CostCenter.name).all() if employee_ids else []
        cost_center_list = ["All Cost Centers"] + [cc[0] for cc in cost_centers if cc[0]]
        
        # Get unique deduction types
        deductions = db.query(distinct(EmployeeDeduction.deduction_name)).filter(
            EmployeeDeduction.is_active == True
        ).order_by(EmployeeDeduction.deduction_name).all()
        deduction_list = [ded[0] for ded in deductions if ded[0]]
        
        return {
            "locations": location_list,
            "departments": department_list,
            "cost_centers": cost_center_list,
            "deductions": deduction_list
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching strike register filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"],
            "deductions": []
        }


@router.post("/strike-register")
def get_strike_register(
    filters: StrikeRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get strike register with employee strike details and deductions"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_strike_register(filters)


@router.get("/strike-register")
def get_strike_register_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUL-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    deduction: str = Query("- Select -", description="Deduction type filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get strike register with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = StrikeRegisterFilters(
        period=period,
        location=location,
        department=department,
        cost_center=cost_center,
        deduction=deduction,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_strike_register(filters)


# Time Register Endpoints
@router.get("/time-register/filters")
def get_time_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for time register with HYBRID business unit logic
    
    Returns:
        - locations: List of location names from database
        - departments: List of department names from database
        - cost_centers: List of cost center names from database
        - employees: List of employee codes and names from database
    """
    try:
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.models.employee import Employee
        from app.models.business import Business
        from app.models.datacapture import SalaryUnit
        from sqlalchemy import distinct
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # CRITICAL: Get user's business_id for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get only the user's business
        user_business = db.query(Business).filter(Business.id == business_id).first()
        business_unit_list = ["All Units"]
        if user_business and user_business.business_name:
            business_unit_list.append(user_business.business_name)
        
        # Get salary components (salary units) from database - DISTINCT by unit_name only
        from sqlalchemy import func
        
        salary_units_distinct = db.query(
            func.distinct(SalaryUnit.unit_name).label('unit_name')
        ).filter(
            SalaryUnit.is_active == True
        ).order_by(
            SalaryUnit.unit_name
        ).all()
        
        # Return only unique unit names (no codes to avoid duplicates)
        salary_component_list = [{"name": su.unit_name, "code": su.unit_name} for su in salary_units_distinct]
        
        # Base query for active employees - FILTER BY USER'S BUSINESS
        employee_query = db.query(Employee).filter(
            Employee.employee_status == 'ACTIVE',
            Employee.business_id == business_id  # CRITICAL: Business isolation
        )
        
        # Execute query once and get employee IDs
        employees = employee_query.all()
        employee_ids = [emp.id for emp in employees]
        
        # Get unique locations using employee IDs
        locations = db.query(distinct(Location.name)).join(
            Employee, Employee.location_id == Location.id
        ).filter(Employee.id.in_(employee_ids)).order_by(Location.name).all() if employee_ids else []
        location_list = ["All Locations"] + [loc[0] for loc in locations if loc[0]]
        
        # Get unique departments using employee IDs
        departments = db.query(distinct(Department.name)).join(
            Employee, Employee.department_id == Department.id
        ).filter(Employee.id.in_(employee_ids)).order_by(Department.name).all() if employee_ids else []
        department_list = ["All Departments"] + [dept[0] for dept in departments if dept[0]]
        
        # Get unique cost centers using employee IDs
        cost_centers = db.query(distinct(CostCenter.name)).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(Employee.id.in_(employee_ids)).order_by(CostCenter.name).all() if employee_ids else []
        cost_center_list = ["All Cost Centers"] + [cc[0] for cc in cost_centers if cc[0]]
        
        # Build employee list from already fetched employees
        employee_list = [
            {
                "code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "id": emp.id
            }
            for emp in employees
        ]
        
        return {
            "business_units": business_unit_list,
            "locations": location_list,
            "departments": department_list,
            "cost_centers": cost_center_list,
            "salary_components": salary_component_list,
            "employees": employee_list
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching time register filters: {str(e)}")
        return {
            "business_units": ["All Units"],
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"],
            "salary_components": [],
            "employees": []
        }


@router.post("/time-register")
def get_time_register(
    filters: TimeRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get time register with employee time breakdown details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_time_register(filters)


@router.get("/time-register")
def get_time_register_get(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., NOV-2025)"),
    business_unit: str = Query("All Business Units", description="Business unit filter"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    salary_component: str = Query(None, description="Salary component filter"),
    show_details: bool = Query(False, description="Show detailed breakdown"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get time register with GET method for easy testing"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = TimeRegisterFilters(
        period=period,
        business_unit=business_unit,
        location=location,
        department=department,
        cost_center=cost_center,
        salary_component=salary_component,
        show_details=show_details,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_time_register(filters)


# Report Categories Endpoint
@router.get("/categories")
def get_report_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get available report categories"""
    return {
        "categories": [
            {
                "key": "ai_reporting",
                "name": "AI Reporting",
                "description": "AI-powered report generation and analysis",
                "icon": "ti ti-brain"
            },
            {
                "key": "salary_reports",
                "name": "Salary Reports",
                "description": "Salary summaries, registers, slips, and payroll reports",
                "icon": "ti ti-currency-rupee"
            },
            {
                "key": "attendance_reports",
                "name": "Attendance Reports",
                "description": "Attendance registers, leave reports, and time tracking",
                "icon": "ti ti-calendar"
            },
            {
                "key": "employee_reports",
                "name": "Employee Reports",
                "description": "Employee registers, events, joinings, and exits",
                "icon": "ti ti-user"
            },
            {
                "key": "statutory_reports",
                "name": "Statutory Reports",
                "description": "ESI, PF, TDS, and other compliance reports",
                "icon": "ti ti-briefcase"
            },
            {
                "key": "annual_reports",
                "name": "Annual Reports",
                "description": "Annual salary, attendance, and leave summaries",
                "icon": "ti ti-chart-bar"
            },
            {
                "key": "other_reports",
                "name": "Other Reports",
                "description": "Activity logs, feedback, and system alerts",
                "icon": "ti ti-file"
            }
        ]
    }


# Travel Register Endpoints
@router.get("/travel-register/filters")
def get_travel_register_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get filter options for travel register"""
    try:
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.models.employee import Employee
        from sqlalchemy import distinct
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # CRITICAL: Get user's business_id for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Base query for active employees - FILTER BY USER'S BUSINESS
        employee_query = db.query(Employee).filter(
            Employee.employee_status == 'ACTIVE',
            Employee.business_id == business_id  # CRITICAL: Business isolation
        )
        employees = employee_query.all()
        employee_ids = [emp.id for emp in employees]
        
        # Get unique locations
        locations = db.query(distinct(Location.name)).join(
            Employee, Employee.location_id == Location.id
        ).filter(Employee.id.in_(employee_ids)).order_by(Location.name).all() if employee_ids else []
        location_list = ["All Locations"] + [loc[0] for loc in locations if loc[0]]
        
        # Get unique departments
        departments = db.query(distinct(Department.name)).join(
            Employee, Employee.department_id == Department.id
        ).filter(Employee.id.in_(employee_ids)).order_by(Department.name).all() if employee_ids else []
        department_list = ["All Departments"] + [dept[0] for dept in departments if dept[0]]
        
        # Get unique cost centers
        cost_centers = db.query(distinct(CostCenter.name)).join(
            Employee, Employee.cost_center_id == CostCenter.id
        ).filter(Employee.id.in_(employee_ids)).order_by(CostCenter.name).all() if employee_ids else []
        cost_center_list = ["All Cost Centers"] + [cc[0] for cc in cost_centers if cc[0]]
        
        return {
            "locations": location_list,
            "departments": department_list,
            "cost_centers": cost_center_list,
            "salary_components": ["- Select -", "Travel Allowance", "Conveyance", "Vehicle Allowance"]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching travel register filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"],
            "salary_components": ["- Select -"]
        }


@router.post("/travel-register")
def get_travel_register(
    filters: TravelRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get travel register with employee travel details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_travel_register(filters)


@router.get("/travel-register")
def get_travel_register_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    salary_component: str = Query("- Select -", description="Salary component filter"),
    date_from: str = Query(None, description="From date in YYYY-MM-DD format"),
    date_to: str = Query(None, description="To date in YYYY-MM-DD format"),
    employee_id: str = Query(None, description="Employee ID or name search"),
    exclude_zero_distance: bool = Query(False, description="Exclude zero distance records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get travel register with GET method for easy testing"""
    from app.schemas.reports import TravelRegisterFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = TravelRegisterFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        salary_component=salary_component,
        date_from=date_from,
        date_to=date_to,
        employee_id=employee_id,
        exclude_zero_distance=exclude_zero_distance,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_travel_register(filters)


@router.get("/travel-register/employee-search")
def search_employees_for_travel_register(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Travel Register autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Build search query
        search_term = f"%{query}%"
        employees_query = db.query(Employee).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        )
        
        # Apply business filter (CRITICAL: Business isolation)
        if business_id:
            employees_query = employees_query.filter(Employee.business_id == business_id)
        
        # Limit results to 10 for autocomplete
        employees = employees_query.limit(10).all()
        
        # Format response
        results = [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "display": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip(),
                "status": emp.employee_status
            }
            for emp in employees
        ]
        
        return {"employees": results, "total": len(results)}
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for travel register: {str(e)}")
        return {"employees": [], "total": 0}


# Time Punches Endpoints
@router.get("/time-punches/filters")
def get_time_punches_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for time punches with HYBRID business unit logic
    
    Returns:
    - business_units: Businesses for superadmin, Business Units for regular admin
    - locations: All active locations (filtered by business)
    - departments: All active departments (filtered by business)
    - cost_centers: All active cost centers (filtered by business)
    """
    try:
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.utils.business_unit_utils import get_business_unit_options
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get business units using HYBRID APPROACH (same as salary register)
        business_unit_options = get_business_unit_options(db, current_user, business_id)
        
        # Get locations (filtered by business if not superadmin)
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments (filtered by business if not superadmin)
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers (filtered by business if not superadmin)
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "business_units": business_unit_options,
            "locations": location_options,
            "departments": department_options,
            "cost_centers": cost_center_options
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching time punches filters: {str(e)}")
        return {
            "business_units": ["All Business Units"],
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"]
        }


@router.get("/time-punches/employee-search")
def search_time_punches_employees(
    search: str = Query(..., min_length=1, description="Search term for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for time punches autocomplete
    Returns employees filtered by business_id for security
    """
    try:
        from app.models.employee import Employee, EmployeeStatus
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # CRITICAL: Get business_id for security
        business_id = get_user_business_id(current_user, db)
        
        if not business_id:
            return {"employees": []}
        
        # Search employees by name or code, filtered by business_id
        search_term = f"%{search}%"
        employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        ).limit(10).all()
        
        return {
            "employees": [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "code": emp.employee_code
                }
                for emp in employees
            ]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching time punches employees: {str(e)}")
        return {"employees": []}


@router.post("/time-punches")
def get_time_punches(
    filters: TimePunchesFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get time punches with employee punch details"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_time_punches(filters)


@router.get("/time-punches")
def get_time_punches_get(
    business_unit: str = Query("All Business Units", description="Business unit filter"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    date_from: str = Query(None, description="From date in YYYY-MM-DD format"),
    date_to: str = Query(None, description="To date in YYYY-MM-DD format"),
    employee: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get time punches with GET method for easy testing"""
    from app.schemas.reports import TimePunchesFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = TimePunchesFilters(
        business_unit=business_unit,
        location=location,
        cost_center=cost_center,
        department=department,
        date_from=date_from,
        date_to=date_to,
        employee=employee,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_time_punches(filters)


# Remote Punch Endpoints
@router.get("/remote-punch/filters")
def get_remote_punch_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get filter options for remote punch report"""
    try:
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        from app.api.v1.endpoints.master_setup import get_user_business_id
        
        # Get business ID for filtering
        business_id = get_user_business_id(current_user, db)
        
        # Get locations (filtered by business if not superadmin)
        locations_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = locations_query.all()
        location_options = ["All Locations"] + [loc.name for loc in locations]
        
        # Get departments (filtered by business if not superadmin)
        departments_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = departments_query.all()
        department_options = ["All Departments"] + [dept.name for dept in departments]
        
        # Get cost centers (filtered by business if not superadmin)
        cost_centers_query = db.query(CostCenter).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = cost_centers_query.all()
        cost_center_options = ["All Cost Centers"] + [cc.name for cc in cost_centers]
        
        return {
            "locations": location_options,
            "departments": department_options,
            "cost_centers": cost_center_options
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching remote punch filters: {str(e)}")
        return {
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"]
        }


@router.get("/remote-punch/employee-search")
def search_remote_punch_employees(
    search: str = Query(..., min_length=1, description="Search term for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for remote punch autocomplete
    Returns employees filtered by business_id for security
    """
    try:
        from app.models.employee import Employee, EmployeeStatus
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # CRITICAL: Get business_id for security
        business_id = get_user_business_id(current_user, db)
        
        if not business_id:
            return {"employees": []}
        
        # Search employees by name or code, filtered by business_id
        search_term = f"%{search}%"
        employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        ).limit(10).all()
        
        return {
            "employees": [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "code": emp.employee_code
                }
                for emp in employees
            ]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching remote punch employees: {str(e)}")
        return {"employees": []}


@router.post("/remote-punch")
def get_remote_punch_report(
    filters: 'RemotePunchFilters',
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get remote punch report with employee remote punch details"""
    from app.schemas.reports import RemotePunchFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_remote_punch(filters)


@router.get("/remote-punch")
def get_remote_punch_report_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    date_from: str = Query(None, description="From date in YYYY-MM-DD format"),
    date_to: str = Query(None, description="To date in YYYY-MM-DD format"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get remote punch report with GET method for easy testing"""
    from app.schemas.reports import RemotePunchFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = RemotePunchFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        date_from=date_from,
        date_to=date_to,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_remote_punch(filters)


# Manual Updates Filters Endpoint
@router.get("/manual-updates/filters")
def get_manual_updates_filters(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get filter options for manual updates report"""
    from app.models.location import Location
    from app.models.department import Department
    from app.models.cost_center import CostCenter
    from app.models.business import Business
    from app.models.business_unit import BusinessUnit
    from app.api.v1.endpoints.master_setup import get_user_business_id
    from sqlalchemy import distinct
    
    try:
        # CRITICAL: Get business_id for security
        business_id = get_user_business_id(current_user, db)
        
        # Get locations (filtered by business)
        locations_query = db.query(Location.name).filter(Location.is_active == True)
        if business_id:
            locations_query = locations_query.filter(Location.business_id == business_id)
        locations = [loc[0] for loc in locations_query.distinct().all() if loc[0]]
        
        # Get departments (filtered by business)
        departments_query = db.query(Department.name).filter(Department.is_active == True)
        if business_id:
            departments_query = departments_query.filter(Department.business_id == business_id)
        departments = [dept[0] for dept in departments_query.distinct().all() if dept[0]]
        
        # Get cost centers (filtered by business)
        cost_centers_query = db.query(CostCenter.name).filter(CostCenter.is_active == True)
        if business_id:
            cost_centers_query = cost_centers_query.filter(CostCenter.business_id == business_id)
        cost_centers = [cc[0] for cc in cost_centers_query.distinct().all() if cc[0]]
        
        return {
            "locations": sorted(locations),
            "departments": sorted(departments),
            "cost_centers": sorted(cost_centers)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filters: {str(e)}")


@router.get("/manual-updates/employee-search")
def search_manual_updates_employees(
    search: str = Query(..., min_length=1, description="Search term for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for manual updates autocomplete
    Returns employees filtered by business_id for security
    """
    try:
        from app.models.employee import Employee, EmployeeStatus
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # CRITICAL: Get business_id for security
        business_id = get_user_business_id(current_user, db)
        
        if not business_id:
            return {"employees": []}
        
        # Search employees by name or code, filtered by business_id
        search_term = f"%{search}%"
        employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        ).limit(10).all()
        
        return {
            "employees": [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "code": emp.employee_code
                }
                for emp in employees
            ]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching manual updates employees: {str(e)}")
        return {"employees": []}


# Manual Updates Endpoints
@router.post("/manual-updates")
def get_manual_updates_report(
    filters: 'ManualUpdatesFilters',
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get manual updates report with attendance corrections and manual entries"""
    from app.schemas.reports import ManualUpdatesFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_manual_updates(filters)


@router.get("/manual-updates")
def get_manual_updates_report_get(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    month: str = Query(None, description="Month filter (e.g., 'August 2025' or 'AUG-2025')"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get manual updates report with GET method for easy testing"""
    from app.schemas.reports import ManualUpdatesFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = ManualUpdatesFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        month=month,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_manual_updates(filters)


# Employee Register Options Endpoints
@router.post("/employee-register-options")
def get_employee_register_options_report(
    filters: 'EmployeeRegisterFilters',
    options: 'EmployeeRegisterOptions',
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee register report with configurable field options"""
    from app.schemas.reports import EmployeeRegisterFilters, EmployeeRegisterOptions
    from app.api.v1.endpoints.master_setup import get_user_business_id
    from fastapi.responses import JSONResponse
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    result = service.get_employee_register(filters, options)
    
    # Convert to dict with proper field filtering
    response_dict = {
        "total_employees": result.total_employees,
        "employees": [emp.model_dump(exclude_none=True) for emp in result.employees],
        "filters_applied": result.filters_applied.model_dump(),
        "options_applied": result.options_applied.model_dump(),
        "summary": result.summary
    }
    
    return JSONResponse(content=response_dict)


@router.get("/employee-register-options")
def get_employee_register_options_report_get(
    location: str = Query(None, description="Location filter"),
    cost_center: str = Query(None, description="Cost center filter"),
    department: str = Query(None, description="Department filter"),
    selected_date: str = Query(None, description="Selected date in YYYY-MM-DD format"),
    records_per_page: int = Query(20, description="Records per page (1-1000)"),
    # Basic Details options
    employee_code: bool = Query(False, description="Include employee code"),
    employee_name: bool = Query(True, description="Include employee name"),
    gender: bool = Query(False, description="Include gender"),
    dob: bool = Query(False, description="Include date of birth"),
    doj: bool = Query(False, description="Include date of joining"),
    doe: bool = Query(True, description="Include date of exit"),
    # Work Profile options
    location_field: bool = Query(True, description="Include location"),
    cost_center_field: bool = Query(False, description="Include cost center"),
    department_field: bool = Query(True, description="Include department"),
    grade: bool = Query(True, description="Include grade"),
    designation: bool = Query(True, description="Include designation"),
    pan: bool = Query(True, description="Include PAN"),
    esi: bool = Query(False, description="Include ESI"),
    pf_uan: bool = Query(True, description="Include PF UAN"),
    # Personal Details options
    aadhaar: bool = Query(True, description="Include Aadhaar"),
    office_email: bool = Query(False, description="Include office email"),
    office_phone: bool = Query(False, description="Include office phone"),
    mobile: bool = Query(True, description="Include mobile"),
    bank_name: bool = Query(True, description="Include bank name"),
    bank_ifsc: bool = Query(True, description="Include bank IFSC"),
    bank_account: bool = Query(False, description="Include bank account"),
    # Extra Info options
    home_phone: bool = Query(True, description="Include home phone"),
    personal_email: bool = Query(True, description="Include personal email"),
    other_info1: bool = Query(True, description="Include other info 1"),
    other_info2: bool = Query(True, description="Include other info 2"),
    other_info3: bool = Query(True, description="Include other info 3"),
    other_info4: bool = Query(True, description="Include other info 4"),
    other_info5: bool = Query(True, description="Include other info 5"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee register report with GET method for easy testing"""
    from app.schemas.reports import EmployeeRegisterFilters, EmployeeRegisterOptions
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeRegisterFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        selected_date=selected_date,
        records_per_page=records_per_page,
        business_id=business_id  # Inject business_id
    )
    
    options = EmployeeRegisterOptions(
        employee_code=employee_code,
        employee_name=employee_name,
        gender=gender,
        dob=dob,
        doj=doj,
        doe=doe,
        location=location_field,
        cost_center=cost_center_field,
        department=department_field,
        grade=grade,
        designation=designation,
        pan=pan,
        esi=esi,
        pf_uan=pf_uan,
        aadhaar=aadhaar,
        office_email=office_email,
        office_phone=office_phone,
        mobile=mobile,
        bank_name=bank_name,
        bank_ifsc=bank_ifsc,
        bank_account=bank_account,
        home_phone=home_phone,
        personal_email=personal_email,
        other_info1=other_info1,
        other_info2=other_info2,
        other_info3=other_info3,
        other_info4=other_info4,
        other_info5=other_info5
    )
    
    service = ReportsService(db)
    result = service.get_employee_register(filters, options)
    
    # Convert to dict with proper field filtering
    from fastapi.responses import JSONResponse
    response_dict = {
        "total_employees": result.total_employees,
        "employees": [emp.model_dump(exclude_none=True) for emp in result.employees],
        "filters_applied": result.filters_applied.model_dump(),
        "options_applied": result.options_applied.model_dump(),
        "summary": result.summary
    }
    
    return JSONResponse(content=response_dict)


# Add endpoint that matches frontend URL pattern
@router.get("/employeeregisteroptions")
def get_employee_register_options_frontend(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    selected_date: str = Query(None, description="Selected date filter"),
    records_per_page: int = Query(20, description="Records per page"),
    
    # Basic Details
    employee_code: bool = Query(False, description="Include employee code"),
    employee_name: bool = Query(True, description="Include employee name"),
    gender: bool = Query(False, description="Include gender"),
    dob: bool = Query(False, description="Include date of birth"),
    doj: bool = Query(False, description="Include date of joining"),
    doe: bool = Query(True, description="Include date of exit"),
    
    # Work Profile
    location_field: bool = Query(True, description="Include location"),
    cost_center_field: bool = Query(False, description="Include cost center"),
    department_field: bool = Query(True, description="Include department"),
    grade: bool = Query(True, description="Include grade"),
    designation: bool = Query(True, description="Include designation"),
    pan: bool = Query(True, description="Include PAN"),
    esi: bool = Query(False, description="Include ESI"),
    pf_uan: bool = Query(True, description="Include PF UAN"),
    
    # Personal Details
    aadhaar: bool = Query(True, description="Include Aadhaar"),
    office_email: bool = Query(False, description="Include office email"),
    office_phone: bool = Query(False, description="Include office phone"),
    mobile: bool = Query(True, description="Include mobile"),
    bank_name: bool = Query(True, description="Include bank name"),
    bank_ifsc: bool = Query(True, description="Include bank IFSC"),
    bank_account: bool = Query(False, description="Include bank account"),
    
    # Extra Info
    home_phone: bool = Query(True, description="Include home phone"),
    personal_email: bool = Query(True, description="Include personal email"),
    other_info1: bool = Query(True, description="Include other info 1"),
    other_info2: bool = Query(True, description="Include other info 2"),
    other_info3: bool = Query(True, description="Include other info 3"),
    other_info4: bool = Query(True, description="Include other info 4"),
    other_info5: bool = Query(True, description="Include other info 5"),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee register report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeRegisterFilters, EmployeeRegisterOptions
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeRegisterFilters(
        location=location if location != "All Locations" else None,
        cost_center=cost_center if cost_center != "All Cost Centers" else None,
        department=department if department != "All Departments" else None,
        selected_date=selected_date,
        records_per_page=records_per_page,
        business_id=business_id  # Inject business_id
    )
    
    options = EmployeeRegisterOptions(
        employee_code=employee_code,
        employee_name=employee_name,
        gender=gender,
        dob=dob,
        doj=doj,
        doe=doe,
        location=location_field,
        cost_center=cost_center_field,
        department=department_field,
        grade=grade,
        designation=designation,
        pan=pan,
        esi=esi,
        pf_uan=pf_uan,
        aadhaar=aadhaar,
        office_email=office_email,
        office_phone=office_phone,
        mobile=mobile,
        bank_name=bank_name,
        bank_ifsc=bank_ifsc,
        bank_account=bank_account,
        home_phone=home_phone,
        personal_email=personal_email,
        other_info1=other_info1,
        other_info2=other_info2,
        other_info3=other_info3,
        other_info4=other_info4,
        other_info5=other_info5
    )
    
    service = ReportsService(db)
    result = service.get_employee_register(filters, options)
    
    # Convert to dict with proper field filtering
    from fastapi.responses import JSONResponse
    response_dict = {
        "total_employees": result.total_employees,
        "employees": [emp.model_dump(exclude_none=True) for emp in result.employees],
        "filters_applied": result.filters_applied.model_dump(),
        "options_applied": result.options_applied.model_dump(),
        "summary": result.summary
    }
    
    return JSONResponse(content=response_dict)

# Employee Addresses Endpoints
@router.get("/employeeaddresses/employee-search")
def search_employee_addresses_employees(
    search: str = Query(..., min_length=1, description="Search term for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for employee addresses autocomplete
    Returns employees filtered by business_id for security
    """
    try:
        from app.models.employee import Employee, EmployeeStatus
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # CRITICAL: Get business_id for security
        business_id = get_user_business_id(current_user, db)
        
        if not business_id:
            return {"employees": []}
        
        # Search employees by name or code, filtered by business_id
        search_term = f"%{search}%"
        employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        ).limit(10).all()
        
        return {
            "employees": [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "code": emp.employee_code
                }
                for emp in employees
            ]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employee addresses employees: {str(e)}")
        return {"employees": []}


@router.get("/employeeaddresses")
def get_employee_addresses_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee addresses report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeAddressesFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeAddressesFilters(
        location=location if location != "All Locations" else None,
        cost_center=cost_center if cost_center != "All Cost Centers" else None,
        department=department if department != "All Departments" else None,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_addresses(filters)


# Employee Events Endpoints
@router.get("/employeevents")
def get_employee_events_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    show_birthdays: bool = Query(True, description="Show birthdays"),
    show_work_anniversaries: bool = Query(True, description="Show work anniversaries"),
    show_wedding_anniversaries: bool = Query(True, description="Show wedding anniversaries"),
    from_month: str = Query("January", description="From month"),
    to_month: str = Query("December", description="To month"),
    employee_search: str = Query(None, description="Employee search filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee events report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeEventsFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeEventsFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        show_birthdays=show_birthdays,
        show_work_anniversaries=show_work_anniversaries,
        show_wedding_anniversaries=show_wedding_anniversaries,
        from_month=from_month,
        to_month=to_month,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_events(filters)


# Promotion Age Endpoints
@router.get("/promotionage")
def get_promotion_age_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    ageing: str = Query("All Employees", description="Ageing filter"),
    grade: str = Query("All Grades", description="Grade filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get promotion age report - frontend compatible endpoint"""
    from app.schemas.reports import PromotionAgeFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = PromotionAgeFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        ageing=ageing,
        grade=grade,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_promotion_age_report(filters)


@router.post("/promotionage")
def get_promotion_age_report_post(
    filters: PromotionAgeFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get promotion age report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_promotion_age_report(filters)


# Increment Ageing Endpoints
@router.get("/incrementageing")
def get_increment_ageing_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    ageing: str = Query("All Employees", description="Ageing filter"),
    grade: str = Query("All Grades", description="Grade filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get increment ageing report - frontend compatible endpoint"""
    from app.schemas.reports import IncrementAgeingFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = IncrementAgeingFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        ageing=ageing,
        grade=grade,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_increment_ageing_report(filters)


@router.post("/incrementageing")
def get_increment_ageing_report_post(
    filters: IncrementAgeingFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get increment ageing report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_increment_ageing_report(filters)


# Employee Joinings Endpoints
@router.get("/employeejoinings")
def get_employee_joinings_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    grade: str = Query("All Grades", description="Grade filter"),
    from_date: str = Query(None, description="From date in YYYY-MM-DD format"),
    to_date: str = Query(None, description="To date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee joinings report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeJoiningFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeJoiningFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        grade=grade,
        from_date=from_date,
        to_date=to_date,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_joinings_report(filters)


@router.post("/employeejoinings")
def get_employee_joinings_report_post(
    filters: EmployeeJoiningFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee joinings report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_employee_joinings_report(filters)


# Employee Exits Endpoints
@router.get("/employeeexits")
def get_employee_exits_report(
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    exit_reason: str = Query("All Reasons", description="Exit reason filter"),
    from_date: str = Query(None, description="From date in YYYY-MM-DD format"),
    to_date: str = Query(None, description="To date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee exits report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeExitFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeExitFilters(
        location=location,
        department=department,
        cost_center=cost_center,
        exit_reason=exit_reason,
        from_date=from_date,
        to_date=to_date,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_exits_report(filters)


@router.post("/employeeexits")
def get_employee_exits_report_post(
    filters: EmployeeExitFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee exits report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_employee_exits_report(filters)


# Vaccination Status Endpoints
@router.get("/vaccinationstatus")
def get_vaccination_status_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    status: str = Query("Vaccinated", description="Vaccination status filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get vaccination status report - frontend compatible endpoint"""
    from app.schemas.reports import VaccinationStatusFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = VaccinationStatusFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        status=status,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_vaccination_status_report(filters)


@router.post("/vaccinationstatus")
def get_vaccination_status_report_post(
    filters: VaccinationStatusFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get vaccination status report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_vaccination_status_report(filters)


# Workman Status Endpoints
@router.get("/workmanstatus")
def get_workman_status_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    inactive_only: bool = Query(False, description="Show only inactive workman installations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get workman status report - frontend compatible endpoint"""
    from app.schemas.reports import WorkmanStatusFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = WorkmanStatusFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        inactive_only=inactive_only,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_workman_status_report(filters)


@router.post("/workmanstatus")
def get_workman_status_report_post(
    filters: WorkmanStatusFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get workman status report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_workman_status_report(filters)


# Employee Assets Endpoints
@router.get("/employeeassets/employee-search")
def search_employee_assets_employees(
    search: str = Query(..., min_length=1, description="Search term for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for employee assets autocomplete
    Returns employees filtered by business_id for security
    """
    try:
        from app.models.employee import Employee, EmployeeStatus
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from sqlalchemy import or_
        
        # CRITICAL: Get business_id for security
        business_id = get_user_business_id(current_user, db)
        
        if not business_id:
            return {"employees": []}
        
        # Search employees by name or code, filtered by business_id
        search_term = f"%{search}%"
        employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            )
        ).limit(10).all()
        
        return {
            "employees": [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "code": emp.employee_code
                }
                for emp in employees
            ]
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employee assets employees: {str(e)}")
        return {"employees": []}


@router.get("/employeeassets")
def get_employee_assets_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    search: str = Query(None, description="Employee name search"),
    warranty_only: bool = Query(False, description="Show only expired warranties"),
    active_only: bool = Query(True, description="Show only active employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee assets report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeAssetsFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeAssetsFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        search=search,
        warranty_only=warranty_only,
        active_only=active_only,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_assets_report(filters)


@router.post("/employeeassets")
def get_employee_assets_report_post(
    filters: EmployeeAssetsFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee assets report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_employee_assets_report(filters)


# Employee Relatives Endpoints
@router.get("/employeerelatives")
def get_employee_relatives_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    active_only: bool = Query(False, description="Include only active employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee relatives report - frontend compatible endpoint"""
    from app.schemas.reports import EmployeeRelativesFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = EmployeeRelativesFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        active_only=active_only,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_employee_relatives_report(filters)


@router.post("/employeerelatives")
def get_employee_relatives_report_post(
    filters: EmployeeRelativesFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get employee relatives report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_employee_relatives_report(filters)


# Inactive Employees Endpoints
@router.get("/inactiveemployees")
def get_inactive_employees_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get inactive employees report - frontend compatible endpoint"""
    from app.schemas.reports import InactiveEmployeesFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = InactiveEmployeesFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_inactive_employees_report(filters)


@router.post("/inactiveemployees")
def get_inactive_employees_report_post(
    filters: InactiveEmployeesFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get inactive employees report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_inactive_employees_report(filters)

# Export Records Endpoints
@router.get("/exportrecords")
def get_export_records_report(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    record_type: str = Query("all", description="Record type: all, active, inactive"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get export records report - frontend compatible endpoint for CSV download"""
    from app.schemas.reports import ExportRecordsFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = ExportRecordsFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        record_type=record_type,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_export_records_report(filters)


@router.post("/exportrecords")
def get_export_records_report_post(
    filters: ExportRecordsFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get export records report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_export_records_report(filters)
# ESI Deduction Endpoints
@router.get("/esideduction")
def get_esi_deduction_report(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., NOV-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    report_type: str = Query("ESI Return", description="Report type: ESI Return, ESI Summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get ESI deduction report - frontend compatible endpoint"""
    from app.schemas.reports import ESIDeductionFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = ESIDeductionFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        report_type=report_type,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_esi_deduction_report(filters)


@router.post("/esideduction")
def get_esi_deduction_report_post(
    filters: ESIDeductionFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get ESI deduction report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_esi_deduction_report(filters)
# ESI Coverage Endpoints
@router.get("/esicoverage")
def get_esi_coverage_report(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., NOV-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get ESI coverage report - frontend compatible endpoint"""
    from app.schemas.reports import ESICoverageFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = ESICoverageFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_esi_coverage_report(filters)


@router.post("/esicoverage")
def get_esi_coverage_report_post(
    filters: ESICoverageFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get ESI coverage report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_esi_coverage_report(filters)
# PF Deduction Endpoints
@router.get("/pfdeduction")
def get_pf_deduction_report(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., AUG-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    ignore_ncp_days: bool = Query(False, description="Ignore NCP (Non-Contributing Period) Days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get PF deduction report - frontend compatible endpoint"""
    from app.schemas.reports import PFDeductionFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = PFDeductionFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        ignore_ncp_days=ignore_ncp_days,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_pf_deduction_report(filters)


@router.post("/pfdeduction")
def get_pf_deduction_report_post(
    filters: PFDeductionFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get PF deduction report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_pf_deduction_report(filters)
# PF Coverage Endpoints
@router.get("/pfcoverage")
def get_pf_coverage_report(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., NOV-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get PF coverage report - frontend compatible endpoint"""
    from app.schemas.reports import PFCoverageFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = PFCoverageFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_pf_coverage_report(filters)


@router.post("/pfcoverage")
def get_pf_coverage_report_post(
    filters: PFCoverageFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get PF coverage report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_pf_coverage_report(filters)
# Overtime Register Endpoints (Frontend Compatible)
@router.get("/overtimeregister")
def get_overtime_register_frontend(
    period: str = Query(..., description="Period in format MMM-YYYY (e.g., JUN-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    payment_date: str = Query(None, description="Payment date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get overtime register report - frontend compatible endpoint"""
    from app.schemas.reports import OvertimeRegisterFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = OvertimeRegisterFilters(
        period=period,
        location=location,
        cost_center=cost_center,
        department=department,
        payment_date=payment_date,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_overtime_register(filters)


@router.post("/overtimeregister")
def get_overtime_register_frontend_post(
    filters: OvertimeRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get overtime register report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_overtime_register(filters)
# Register of Leaves Endpoints (Frontend Compatible)
@router.get("/registerofleaves")
def get_register_of_leaves_frontend(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    year: str = Query("2025", description="Year filter"),
    month: str = Query("December", description="End month (Jan to specified month)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get register of leaves report - frontend compatible endpoint"""
    from app.schemas.reports import LeaveRegisterFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = LeaveRegisterFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        year=year,
        month=month,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_leave_register(filters)


@router.post("/registerofleaves")
def get_register_of_leaves_frontend_post(
    filters: LeaveRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get register of leaves report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_leave_register(filters)


# Annual Leave Register Endpoints (Alias for Register of Leaves)
@router.get("/annualleave")
def get_annual_leave_register_frontend(
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    year: str = Query("2025", description="Year filter"),
    month: str = Query("December", description="End month (Jan to specified month)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get annual leave register report - alias for register of leaves"""
    from app.schemas.reports import LeaveRegisterFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    
    filters = LeaveRegisterFilters(
        location=location,
        cost_center=cost_center,
        department=department,
        year=year,
        month=month,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_leave_register(filters)


@router.post("/annualleave")
def get_annual_leave_register_frontend_post(
    filters: LeaveRegisterFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get annual leave register report - POST endpoint"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_leave_register(filters)


# Income Tax Declaration Report Endpoints (Frontend Compatible)
@router.get("/incometaxdec")
def get_income_tax_declaration_report_frontend(
    location: str = Query("All Locations", description="Location filter"),
    financial_year: str = Query("2025-26", description="Financial year filter"),
    active_employees_only: bool = Query(False, description="Include only active employees"),
    exclude_no_declarations: bool = Query(False, description="Exclude employees with no declarations"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get income tax declaration report - GET endpoint for frontend compatibility"""
    from app.schemas.reports import IncomeTaxDeclarationFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = IncomeTaxDeclarationFilters(
        location=location,
        financial_year=financial_year,
        active_employees_only=active_employees_only,
        exclude_no_declarations=exclude_no_declarations,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_income_tax_declaration_report(filters)


@router.post("/incometaxdec")
def get_income_tax_declaration_report_frontend_post(
    filters: IncomeTaxDeclarationFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get income tax declaration report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_income_tax_declaration_report(filters)

# Income Tax Computation Report Endpoints (Frontend Compatible)
@router.get("/incometaxcom")
def get_income_tax_computation_report_frontend(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., JAN-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get income tax computation report - GET endpoint for frontend compatibility"""
    from app.schemas.reports import IncomeTaxComputationFilters
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = IncomeTaxComputationFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        business_id=business_id  # Inject business_id
    )
    
    service = ReportsService(db)
    return service.get_income_tax_computation_report(filters)


@router.post("/incometaxcom")
def get_income_tax_computation_report_frontend_post(
    filters: IncomeTaxComputationFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get income tax computation report - POST endpoint for complex filters"""
    from app.api.v1.endpoints.master_setup import get_user_business_id
    
    # CRITICAL: Get business_id and inject into filters for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_income_tax_computation_report(filters)


@router.get("/incometaxcom/employee-search")
def search_employees_for_income_tax_computation(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees by name or code for Income Tax Computation report autocomplete
    
    Returns list of employees matching the search query
    """
    try:
        from app.models.employee import Employee, EmployeeStatus
        from app.models.business import Business
        from sqlalchemy import or_
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get user's business
        business = db.query(Business).filter(Business.owner_id == current_user.id).first()
        if not business:
            return {"employees": [], "total": 0}
        
        business_id = business.id
        logger.info(f"[INCOME TAX COMPUTATION SEARCH] Searching for query='{query}', business_id={business_id}")
        
        # Search pattern
        search_term = f"%{query}%"
        
        # Query employees
        employees_query = db.query(Employee).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.business_id == business_id,  # CRITICAL: Business isolation
            Employee.employee_status == EmployeeStatus.ACTIVE
        ).limit(10)
        
        employees = employees_query.all()
        
        # Format results
        results = [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "label": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip()
            }
            for emp in employees
        ]
        
        logger.info(f"[INCOME TAX COMPUTATION SEARCH] Found {len(results)} employees")
        
        return {
            "employees": results,
            "total": len(results)
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching employees for income tax computation: {str(e)}")
        return {"employees": [], "total": 0}


@router.get("/incometaxcom/download/{month}")
def download_income_tax_computation_report(
    month: str,
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Download income tax computation report as CSV"""
    from fastapi.responses import StreamingResponse
    from io import StringIO
    import csv
    
    # Create filters
    filters = IncomeTaxComputationFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search
    )
    
    # Get report data
    service = ReportsService(db)
    report_data = service.get_income_tax_computation_report(filters)
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        "Employee Code",
        "Employee Name",
        "Department",
        "Designation",
        "Location",
        "Gross Salary (Monthly)",
        "Basic Salary (Monthly)",
        "Taxable Income (Annual)",
        "80C Deductions",
        "80D Deductions",
        "HRA Exemption",
        "Other Deductions",
        "Total Deductions",
        "Total Exemptions",
        "Tax Slab Rate (%)",
        "Annual Tax Liability",
        "Monthly TDS",
        "Months Remaining",
        "TDS Deducted YTD",
        "TDS Current Month"
    ])
    
    # Write employee data
    for emp in report_data.employees:
        writer.writerow([
            emp.employee_code or "",
            emp.employee_name,
            emp.department or "",
            emp.designation or "",
            emp.location or "",
            float(emp.gross_salary),
            float(emp.basic_salary),
            float(emp.taxable_income),
            float(emp.deductions_80c),
            float(emp.deductions_80d),
            float(emp.hra_exemption),
            float(emp.other_deductions),
            float(emp.total_deductions),
            float(emp.exemptions),
            float(emp.tax_slab_rate),
            float(emp.annual_tax_liability),
            float(emp.monthly_tds),
            emp.months_remaining,
            float(emp.tds_deducted_ytd),
            float(emp.tds_current_month)
        ])
    
    # Add summary row
    writer.writerow([])
    writer.writerow(["SUMMARY"])
    writer.writerow(["Total Employees", report_data.total_employees])
    writer.writerow(["Total Tax Liability", float(report_data.summary.get("total_tax_liability", 0))])
    writer.writerow(["Total TDS Amount", float(report_data.summary.get("total_tds_amount", 0))])
    writer.writerow(["Total Gross Salary", float(report_data.summary.get("total_gross_salary", 0))])
    writer.writerow(["Average Tax Liability", float(report_data.summary.get("average_tax_liability", 0))])
    writer.writerow(["Average Monthly TDS", float(report_data.summary.get("average_monthly_tds", 0))])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=Income_Tax_Computation_{month}.csv"
        }
    )

# Labour Welfare Fund Report Endpoints (Frontend Compatible)
@router.get("/labourWelfarefund")
def get_labour_welfare_fund_report_frontend(
    month: str = Query(..., description="Month in format MMM-YYYY (e.g., JAN-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get Labour Welfare Fund report - GET endpoint for frontend compatibility"""
    from app.schemas.reports import LabourWelfareFundFilters
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = LabourWelfareFundFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        business_id=business_id
    )
    
    service = ReportsService(db)
    return service.get_labour_welfare_fund_report(filters)


@router.post("/labourWelfarefund")
def get_labour_welfare_fund_report_frontend_post(
    filters: LabourWelfareFundFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get Labour Welfare Fund report - POST endpoint for complex filters"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_labour_welfare_fund_report(filters)


@router.get("/labourWelfarefund/download/{month}")
def download_labour_welfare_fund_report(
    month: str,
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Download Labour Welfare Fund report as CSV"""
    from fastapi.responses import StreamingResponse
    from io import StringIO
    import csv
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    # Create filters
    filters = LabourWelfareFundFilters(
        month=month,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        business_id=business_id
    )
    
    # Get report data
    service = ReportsService(db)
    report_data = service.get_labour_welfare_fund_report(filters)
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        "SN",
        "Employee Code",
        "Employee Name",
        "Department",
        "Designation",
        "Location",
        "State",
        "Salary",
        "Employee Deduction",
        "Employer Contribution",
        "Total LWF",
        "LWF Applicable"
    ])
    
    # Write employee data
    for emp in report_data.employees:
        total_lwf = float(emp.deduction) + float(emp.contribution)
        writer.writerow([
            emp.sn,
            emp.employee_code or "",
            emp.employee_name,
            emp.department or "",
            emp.designation or "",
            emp.location or "",
            emp.state or "",
            float(emp.salary),
            float(emp.deduction),
            float(emp.contribution),
            total_lwf,
            "Yes" if emp.lwf_applicable else "No"
        ])
    
    # Add summary row
    writer.writerow([])
    writer.writerow(["SUMMARY"])
    writer.writerow(["Total Employees", report_data.total_employees])
    writer.writerow(["Total Salary", float(report_data.total_salary)])
    writer.writerow(["Total Employee Deduction", float(report_data.total_deduction)])
    writer.writerow(["Total Employer Contribution", float(report_data.total_contribution)])
    writer.writerow(["Total LWF Amount", float(report_data.total_deduction + report_data.total_contribution)])
    writer.writerow(["LWF Applicable Employees", report_data.summary.get("lwf_applicable_employees", 0)])
    writer.writerow(["Average Salary", report_data.summary.get("average_salary", 0)])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=Labour_Welfare_Fund_{month}.csv"
        }
    )

# Income Tax Form 16 Report Endpoints (Frontend Compatible)
# NOTE: More specific routes must come BEFORE general routes in FastAPI
@router.get("/incometaxform16/download")
def download_income_tax_form16_report(
    financial_year: str = Query(..., description="Financial year in format YYYY-YY (e.g., 2024-25)"),
    employee_id: Optional[int] = Query(None, description="Specific employee ID (optional)"),
    employee_code: Optional[str] = Query(None, description="Specific employee code (optional)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download Income Tax Form 16 report as CSV in readable format"""
    from fastapi.responses import StreamingResponse
    from io import StringIO
    import csv
    from decimal import Decimal
    import logging
    from app.api.v1.deps import get_user_business_id
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Form 16 download requested for FY {financial_year}, employee_code: {employee_code}")
        
        # Get user's business_id for security
        business_id = get_user_business_id(current_user, db)
        
        # Create filters
        filters = IncomeTaxForm16Filters(
            financial_year=financial_year,
            employee_id=employee_id,
            employee_code=employee_code,
            location=location,
            department=department,
            cost_center=cost_center,
            business_id=business_id
        )
        
        # Get report data
        service = ReportsService(db)
        report_data = service.get_income_tax_form16_report(filters)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write title
        writer.writerow(["INCOME TAX FORM 16 - CERTIFICATE UNDER SECTION 203"])
        writer.writerow(["Financial Year:", financial_year])
        writer.writerow([])
        
        # Process each certificate
        for idx, cert in enumerate(report_data.certificates, 1):
            # Certificate header
            writer.writerow([f"=== CERTIFICATE {idx} OF {len(report_data.certificates)} ==="])
            writer.writerow(["Certificate Number:", cert.certificate_number])
            writer.writerow(["Issue Date:", str(cert.issue_date)])
            writer.writerow(["Place of Issue:", cert.place_of_issue or ""])
            writer.writerow([])
            
            # Employer details
            writer.writerow(["EMPLOYER DETAILS"])
            writer.writerow(["Name:", cert.employer.name])
            writer.writerow(["Address:", cert.employer.address_line1 or ""])
            if cert.employer.address_line2:
                writer.writerow(["", cert.employer.address_line2])
            if cert.employer.address_line3:
                writer.writerow(["", cert.employer.address_line3])
            writer.writerow(["TAN Number:", cert.employer.tan_number or ""])
            writer.writerow(["PAN Number:", cert.employer.pan_number or ""])
            writer.writerow([])
            
            # Employee details
            writer.writerow(["EMPLOYEE DETAILS"])
            writer.writerow(["Employee Code:", cert.employee.employee_code])
            writer.writerow(["Employee Name:", cert.employee.employee_name])
            writer.writerow(["Designation:", cert.employee.designation or ""])
            writer.writerow(["Department:", cert.employee.department or ""])
            writer.writerow(["Location:", cert.employee.location or ""])
            writer.writerow(["PAN Number:", cert.employee.pan_number or ""])
            writer.writerow(["Date of Joining:", str(cert.employee.date_of_joining) if cert.employee.date_of_joining else ""])
            writer.writerow([])
            
            # Salary details
            writer.writerow(["PART A - DETAILS OF SALARY PAID AND TAX DEDUCTED"])
            writer.writerow(["Description", "Amount (₹)"])
            writer.writerow(["Gross Salary", f"{float(cert.salary_details.gross_salary):,.2f}"])
            writer.writerow(["  Basic Salary", f"{float(cert.salary_details.basic_salary):,.2f}"])
            writer.writerow(["  House Rent Allowance (HRA)", f"{float(cert.salary_details.hra):,.2f}"])
            writer.writerow(["  Special Allowance", f"{float(cert.salary_details.special_allowance):,.2f}"])
            writer.writerow(["Less: Deductions", ""])
            writer.writerow(["  Employee PF Contribution", f"{float(cert.salary_details.pf_employee):,.2f}"])
            writer.writerow(["Net Salary", f"{float(cert.salary_details.net_salary):,.2f}"])
            writer.writerow([])
            
            # Tax computation
            writer.writerow(["PART B - DETAILS OF TAX DEDUCTED AND DEPOSITED"])
            writer.writerow(["Description", "Amount (₹)"])
            writer.writerow(["Gross Total Income", f"{float(cert.tax_details.gross_total_income):,.2f}"])
            writer.writerow(["Income Chargeable Under Head 'Salaries'", f"{float(cert.tax_details.income_chargeable_under_head_salary):,.2f}"])
            writer.writerow([])
            writer.writerow(["Deductions under Chapter VI-A:", ""])
            writer.writerow(["  Section 80C (LIC, PPF, ELSS, etc.)", f"{float(cert.tax_details.section_80c):,.2f}"])
            writer.writerow(["  Section 80D (Medical Insurance)", f"{float(cert.tax_details.section_80d):,.2f}"])
            writer.writerow(["Total Deductions", f"{float(cert.tax_details.total_deductions):,.2f}"])
            writer.writerow([])
            writer.writerow(["Total Taxable Income", f"{float(cert.tax_details.total_income):,.2f}"])
            writer.writerow(["Tax on Total Income", f"{float(cert.tax_details.tax_on_total_income):,.2f}"])
            writer.writerow(["Education Cess @ 4%", f"{float(cert.tax_details.education_cess):,.2f}"])
            writer.writerow(["Total Tax Payable", f"{float(cert.tax_details.total_tax_payable):,.2f}"])
            writer.writerow([])
            writer.writerow(["TDS Deducted (Total)", f"{float(cert.tax_details.tds_deducted):,.2f}"])
            writer.writerow(["Balance Tax Payable/(Refundable)", f"{float(cert.tax_details.balance_tax):,.2f}"])
            writer.writerow([])
            
            # Quarterly TDS details
            if cert.quarterly_tds and len(cert.quarterly_tds) > 0:
                writer.writerow(["QUARTERLY TDS DETAILS"])
                writer.writerow(["Quarter", "Period", "TDS Amount (₹)", "Challan Number", "Deposit Date"])
                for qtds in cert.quarterly_tds:
                    writer.writerow([
                        qtds.quarter,
                        qtds.period,
                        f"{float(qtds.tds_amount):,.2f}",
                        qtds.challan_number or "",
                        str(qtds.deposit_date) if qtds.deposit_date else ""
                    ])
                writer.writerow([])
            
            # Person responsible
            writer.writerow(["VERIFICATION"])
            writer.writerow(["Full Name:", cert.person_responsible.full_name])
            writer.writerow(["Designation:", cert.person_responsible.designation])
            writer.writerow([])
            writer.writerow(["=" * 80])
            writer.writerow([])
        
        # Summary section
        writer.writerow([])
        writer.writerow(["=" * 80])
        writer.writerow(["SUMMARY REPORT"])
        writer.writerow(["=" * 80])
        writer.writerow(["Financial Year:", report_data.summary.get("financial_year", "")])
        writer.writerow(["Total Employees:", report_data.summary.get("total_employees", 0)])
        writer.writerow(["Total Certificates Generated:", report_data.summary.get("total_certificates", 0)])
        writer.writerow(["Total Gross Salary:", f"₹{report_data.summary.get('total_gross_salary', 0):,.2f}"])
        writer.writerow(["Total TDS Deducted:", f"₹{report_data.summary.get('total_tds_deducted', 0):,.2f}"])
        writer.writerow([])
        writer.writerow(["Filters Applied:"])
        filters_summary = report_data.summary.get("filters_summary", {})
        writer.writerow(["  Location:", filters_summary.get("location", "All Locations")])
        writer.writerow(["  Department:", filters_summary.get("department", "All Departments")])
        writer.writerow(["  Cost Center:", filters_summary.get("cost_center", "All Cost Centers")])
        writer.writerow(["  Employee Filter:", filters_summary.get("employee_filter", "All Employees")])
        writer.writerow([])
        writer.writerow(["Generated On:", str(report_data.summary.get("generated_on", ""))])
        writer.writerow([])
        writer.writerow(["Note: This is a system-generated certificate. For official Form 16, please visit TRACES portal."])
        
        # Prepare response
        output.seek(0)
        filename = f"Form16_{financial_year}_{employee_code or 'All_Employees'}.csv"
        
        logger.info(f"Form 16 CSV generated successfully. Size: {len(output.getvalue())} bytes")
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating Form 16 download: {str(e)}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error generating Form 16: {str(e)}")


@router.get("/incometaxform16")
def get_income_tax_form16_report_frontend(
    financial_year: str = Query(..., description="Financial year in format YYYY-YY (e.g., 2024-25)"),
    employee_id: Optional[int] = Query(None, description="Specific employee ID (optional)"),
    employee_code: Optional[str] = Query(None, description="Specific employee code (optional)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Income Tax Form 16 report with query parameters"""
    from app.schemas.reports import IncomeTaxForm16Filters
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = IncomeTaxForm16Filters(
        financial_year=financial_year,
        employee_id=employee_id,
        employee_code=employee_code,
        location=location,
        department=department,
        cost_center=cost_center,
        business_id=business_id
    )
    
    service = ReportsService(db)
    return service.get_income_tax_form16_report(filters)


@router.post("/incometaxform16")
def get_income_tax_form16_report_frontend_post(
    filters: IncomeTaxForm16Filters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Income Tax Form 16 report with request body"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_income_tax_form16_report(filters)


@router.get("/incometaxform16/employee-search")
def search_employees_for_form16(
    query: str = Query(..., min_length=1, description="Search query for employee name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Search employees for Form-16 report autocomplete.
    Returns employees matching the search query from the user's business only.
    """
    from app.models.employee import Employee
    from app.api.v1.deps import get_user_business_id
    from sqlalchemy import or_
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get user's business_id for security
        business_id = get_user_business_id(current_user, db)
        
        logger.info(f"Employee search for Form-16: query='{query}', business_id={business_id}")
        
        # Search employees by name or code, filtered by business_id
        search_pattern = f"%{query}%"
        employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_code.ilike(search_pattern)
            )
        ).limit(10).all()
        
        # Format results for autocomplete
        results = [
            {
                "id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "label": f"{emp.employee_code} - {emp.first_name} {emp.last_name}".strip()
            }
            for emp in employees
        ]
        
        logger.info(f"Found {len(results)} employees for query '{query}'")
        
        return {"employees": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Error searching employees for Form-16: {str(e)}")
        return {"employees": [], "total": 0, "error": str(e)}


# Annual Salary Summary Report Endpoints (Frontend Compatible)
@router.get("/annualsalarysummary")
def get_annual_salary_summary_report_frontend(
    financial_year: str = Query(..., description="Financial year in format YYYY-YY (e.g., 2024-25)"),
    location: str = Query("All Locations", description="Location filter"),
    department: str = Query("All Departments", description="Department filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    employee_grade: str = Query("All Grades", description="Employee grade filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Annual Salary Summary report with query parameters"""
    from app.schemas.reports import AnnualSalarySummaryFilters
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = AnnualSalarySummaryFilters(
        financial_year=financial_year,
        location=location,
        department=department,
        cost_center=cost_center,
        employee_grade=employee_grade,
        business_id=business_id
    )
    
    service = ReportsService(db)
    return service.get_annual_salary_summary_report(filters)


@router.post("/annualsalarysummary")
def get_annual_salary_summary_report_frontend_post(
    filters: AnnualSalarySummaryFilters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Annual Salary Summary report with request body"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_annual_salary_summary_report(filters)

# TDS Return Report Endpoints (Frontend Compatible)
@router.get("/tdsretrun")
def get_tds_return_report_frontend(
    financial_year: str = Query(..., description="Financial year in format YYYY-YY (e.g., 2024-25)"),
    quarter: str = Query(None, description="Quarter filter (Q1, Q2, Q3, Q4)"),
    return_type: str = Query("24Q", description="Return type (24Q, 26Q, 27Q)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get TDS Return report - GET endpoint for frontend compatibility"""
    from app.schemas.reports import TDSReturnFilters
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    filters = TDSReturnFilters(
        financial_year=financial_year,
        quarter=quarter,
        return_type=return_type,
        business_id=business_id
    )
    
    service = ReportsService(db)
    return service.get_tds_return_report(filters)


@router.post("/tdsretrun")
def get_tds_return_report_frontend_post(
    filters: TDSReturnFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get TDS Return report - POST endpoint for complex filters"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_tds_return_report(filters)


# Annual Salary Statement Report Endpoints (Frontend Compatible)
@router.get("/annualsalaries")
def get_annual_salary_statement_report_frontend(
    periods: str = Query(..., description="Comma-separated periods in format MMM-YYYY (e.g., JUL-2025,OCT-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee name or code search"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Annual Salary Statement report with query parameters"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    # Parse periods from comma-separated string
    periods_list = [p.strip() for p in periods.split(",") if p.strip()]
    
    filters = AnnualSalaryStatementFilters(
        periods=periods_list,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        business_id=business_id
    )
    
    service = ReportsService(db)
    return service.get_annual_salary_statement_report(filters)


@router.post("/annualsalaries")
def get_annual_salary_statement_report_frontend_post(
    filters: AnnualSalaryStatementFilters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Annual Salary Statement report with request body"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_annual_salary_statement_report(filters)


# Annual Attendance Report Endpoints (Frontend Compatible)
@router.get("/annualattendance")
def get_annual_attendance_report_frontend(
    periods: str = Query(..., description="Comma-separated periods in format MMM-YYYY (e.g., JAN-2025,DEC-2025)"),
    location: str = Query("All Locations", description="Location filter"),
    cost_center: str = Query("All Cost Centers", description="Cost center filter"),
    department: str = Query("All Departments", description="Department filter"),
    employee_search: str = Query(None, description="Employee name or code search"),
    record_type: str = Query("All Records", description="Record type: All Records, Active Records, Inactive Records"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Annual Attendance report with query parameters"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    
    # Parse periods from comma-separated string
    periods_list = [p.strip() for p in periods.split(",") if p.strip()]
    
    filters = AnnualAttendanceFilters(
        periods=periods_list,
        location=location,
        cost_center=cost_center,
        department=department,
        employee_search=employee_search,
        record_type=record_type,
        business_id=business_id
    )
    
    service = ReportsService(db)
    return service.get_annual_attendance_report(filters)


@router.post("/annualattendance")
def get_annual_attendance_report_frontend_post(
    filters: AnnualAttendanceFilters,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Annual Attendance report with request body"""
    from app.api.v1.deps import get_user_business_id
    
    # Get user's business_id for security
    business_id = get_user_business_id(current_user, db)
    filters.business_id = business_id
    
    service = ReportsService(db)
    return service.get_annual_attendance_report(filters)