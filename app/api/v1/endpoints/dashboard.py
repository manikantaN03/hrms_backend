"""
Dashboard API Endpoints
Analytics and overview data for dashboards
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.api.v1.endpoints.master_setup import get_user_business_id
from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import AttendanceRecord, AttendanceSummary, AttendanceStatus
from app.models.business import Business
from app.models.department import Department
from app.models.location import Location
from app.models.subscription import Subscription
from app.models.employee_access import EmployeeLoginSession
from app.models.requests import (
    Request, LeaveRequest, MissedPunchRequest, ClaimRequest, CompoffRequest,
    TimeRelaxationRequest, HelpdeskRequest, StrikeExemptionRequest,
    ShiftRosterRequest, WeekoffRosterRequest, WorkflowRequest, RequestStatus, RequestType
)
from app.models.designations import Designation
from pydantic import BaseModel

router = APIRouter()


class DashboardOverviewResponse(BaseModel):
    """Dashboard overview statistics"""
    total_employees: int
    active_employees: int
    new_joinings_this_month: int
    terminations_this_month: int
    attendance_today: Dict[str, int]
    pending_approvals: int
    upcoming_birthdays: int
    employees_on_leave: int
    recent_activities: List[Dict[str, Any]]


class DashboardMainResponse(BaseModel):
    """Dashboard main response"""
    employee_stats: Dict[str, int]
    attendance_summary: Dict[str, int]
    recent_activities: List[Dict[str, str]]
    kpis: Dict[str, int]


class AttendanceDashboardResponse(BaseModel):
    """Attendance dashboard statistics"""
    today_attendance: Dict[str, int]
    weekly_attendance: List[Dict[str, Any]]
    monthly_attendance: Dict[str, int]
    late_arrivals_today: int
    early_departures_today: int
    overtime_hours_today: float
    average_working_hours: float
    attendance_trends: List[Dict[str, Any]]


class FlightRiskResponse(BaseModel):
    """Flight risk analytics matching frontend expectations"""
    # Frontend compatibility fields
    untracked: List[Dict[str, Any]] = []
    uncalculated: List[Dict[str, Any]] = []
    noRisk: List[Dict[str, Any]] = []
    moderate: List[Dict[str, Any]] = []
    high: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    
    # Legacy fields for backward compatibility
    high_risk_employees: Optional[List[Dict[str, Any]]] = []
    medium_risk_employees: Optional[List[Dict[str, Any]]] = []
    risk_factors: Optional[Dict[str, int]] = {}
    retention_rate: Optional[float] = 0.0
    turnover_rate: Optional[float] = 0.0
    risk_trends: Optional[List[Dict[str, Any]]] = []


class OrgChartNode(BaseModel):
    """Organization chart node matching frontend expectations"""
    id: str  # Changed to string to match frontend
    name: str
    level: str  # Employee code (frontend expects 'level')
    title: str
    children: Optional[List['OrgChartNode']] = []  # Changed from 'subordinates' to 'children'
    
    # Additional fields for backend compatibility
    department: Optional[str] = None
    email: Optional[str] = None
    profile_image: Optional[str] = None
    manager_id: Optional[int] = None


class OrgChartResponse(BaseModel):
    """Organization chart response matching frontend expectations"""
    # Main data structure that frontend expects
    data: OrgChartNode  # Single root node instead of multiple root_nodes
    
    # Additional metadata
    total_employees: Optional[int] = 0
    total_departments: Optional[int] = 0
    organization_depth: Optional[int] = 0


class OrgChartSearchResponse(BaseModel):
    """Organization chart search response"""
    found: bool
    node: Optional[OrgChartNode] = None
    message: Optional[str] = None


class AttendanceEmployeeRecord(BaseModel):
    """Individual employee attendance record"""
    id: int
    name: str
    employee_code: str
    department: str
    designation: str
    profile_image: Optional[str]
    shift_start: str
    shift_end: str
    time_in: Optional[str]
    time_out: Optional[str]
    status: str
    hours_worked: Optional[float]
    late_minutes: Optional[int]
    early_departure_minutes: Optional[int]


class AttendanceEmployeeListResponse(BaseModel):
    """Employee attendance list response"""
    employees: List[AttendanceEmployeeRecord]
    total: int
    date: str
    filters: Dict[str, Any]


# ============================================================================
# NEW ENDPOINTS FOR FRONTEND COMPATIBILITY
# ============================================================================

class OverviewStatsResponse(BaseModel):
    """Overview statistics matching frontend expectations"""
    total_employees: int
    active_employees: int
    inactive_employees: int
    active_mobile_users: int
    subscription_validity: Dict[str, Any]


class AttendanceTrendResponse(BaseModel):
    """Attendance trend data for charts"""
    months: List[str]
    presents: List[int]
    absents: List[int]
    leaves: List[int]


class OpenRequestsResponse(BaseModel):
    """Open requests data"""
    requests: List[Dict[str, Any]]


class BirthdaysResponse(BaseModel):
    """Birthdays data"""
    today: List[Dict[str, Any]]
    tomorrow: List[Dict[str, Any]]
    upcoming: List[Dict[str, Any]]


class SendBirthdayWishResponse(BaseModel):
    """Send birthday wish response"""
    success: bool
    message: str
    employee_name: str


@router.get("/overview-stats", response_model=OverviewStatsResponse)
async def get_overview_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get overview statistics for dashboard cards
    Matches frontend expectations for the three main cards
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Employee statistics
        employee_query = db.query(Employee)
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        total_employees = employee_query.count()
        active_employees = employee_query.filter(Employee.employee_status == "active").count()
        inactive_employees = total_employees - active_employees
        
        # REAL MOBILE USERS DATA - Count unique active mobile sessions in last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        mobile_users_query = db.query(EmployeeLoginSession).filter(
            EmployeeLoginSession.device_type == "mobile",
            EmployeeLoginSession.is_active == True,
            EmployeeLoginSession.last_activity >= thirty_days_ago
        )
        
        if business_id:
            mobile_users_query = mobile_users_query.join(Employee).filter(
                Employee.business_id == business_id
            )
        
        # Count distinct employees with active mobile sessions
        active_mobile_users = mobile_users_query.distinct(EmployeeLoginSession.employee_id).count()
        
        # REAL SUBSCRIPTION DATA - Get current subscription for business
        subscription_validity = {
            "total_days": 0,
            "remaining_days": 0,
            "due_date": None,
            "percentage": 0
        }
        
        if business_id:
            current_subscription = db.query(Subscription).filter(
                Subscription.business_id == business_id,
                Subscription.is_active == True,
                Subscription.status == "Active"
            ).order_by(Subscription.end_date.desc()).first()
            
            if current_subscription:
                from datetime import date
                today = date.today()
                end_date = current_subscription.end_date.date()
                start_date = current_subscription.start_date.date()
                
                total_days = (end_date - start_date).days
                remaining_days = (end_date - today).days
                percentage = max(0, min(100, (remaining_days / total_days) * 100)) if total_days > 0 else 0
                
                subscription_validity = {
                    "total_days": total_days,
                    "remaining_days": max(0, remaining_days),
                    "due_date": end_date.strftime("%Y-%m-%d"),
                    "percentage": round(percentage, 1)
                }
        
        return OverviewStatsResponse(
            total_employees=total_employees,
            active_employees=active_employees,
            inactive_employees=inactive_employees,
            active_mobile_users=active_mobile_users,
            subscription_validity=subscription_validity
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch overview stats: {str(e)}"
        )


@router.get("/open-requests", response_model=OpenRequestsResponse)
async def get_open_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get open requests data from database
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Initialize all counts to 0
        missed_punches = 0
        time_relaxation = 0
        compoff_requests = 0
        leave_requests = 0
        shift_roster = 0
        weekoff_roster = 0
        strike_exemption = 0
        claims = 0
        helpdesk = 0
        workflow = 0
        
        # Try to get real counts from database, but handle any errors gracefully
        try:
            # Import the Request model for joining
            from app.models.requests import Request
            
            # Base query for business filtering
            base_query = db.query(Request).filter(Request.status == RequestStatus.PENDING)
            if business_id:
                base_query = base_query.filter(Request.business_id == business_id)
            
            # Count different types of pending requests by joining with specific request tables
            missed_punches = base_query.join(MissedPunchRequest, Request.id == MissedPunchRequest.request_id).count()
            
            time_relaxation = base_query.join(TimeRelaxationRequest, Request.id == TimeRelaxationRequest.request_id).count()
            
            compoff_requests = base_query.join(CompoffRequest, Request.id == CompoffRequest.request_id).count()
            
            leave_requests = base_query.join(LeaveRequest, Request.id == LeaveRequest.request_id).count()
            
            # Add the missing request types
            shift_roster = base_query.join(ShiftRosterRequest, Request.id == ShiftRosterRequest.request_id).count()
            
            # Now WeekoffRosterRequest is available
            weekoff_roster = base_query.join(WeekoffRosterRequest, Request.id == WeekoffRosterRequest.request_id).count()
            
            strike_exemption = base_query.join(StrikeExemptionRequest, Request.id == StrikeExemptionRequest.request_id).count()
            
            claims = base_query.join(ClaimRequest, Request.id == ClaimRequest.request_id).count()
            
            helpdesk = base_query.join(HelpdeskRequest, Request.id == HelpdeskRequest.request_id).count()
            
            workflow = base_query.join(WorkflowRequest, Request.id == WorkflowRequest.request_id).count()
            
        except Exception as db_error:
            # If database queries fail, use default values (0)
            pass
        
        # Build requests data with real counts from database
        requests_data = [
            {"type": "MissedPunches", "count": missed_punches, "icon": "bi-clock-history", "iconColor": "text-danger"},
            {"type": "TimeRelaxation", "count": time_relaxation, "icon": "fe-clock", "iconColor": "text-success"},
            {"type": "ComOff", "count": compoff_requests, "icon": "bi-calendar-range", "iconColor": "text-dark"},
            {"type": "Leaves", "count": leave_requests, "icon": "bi-calendar4-event", "iconColor": "text-primary"},
            {"type": "ShiftRoaster", "count": shift_roster, "icon": "bi-stopwatch", "iconColor": "text-success"},
            {"type": "WeekoffRoaster", "count": weekoff_roster, "icon": "bi-calendar-x", "iconColor": "text-secondary"},
            {"type": "StrikeExemption", "count": strike_exemption, "icon": "bi-lightning-fill", "iconColor": "text-danger"},
            {"type": "Claims", "count": claims, "icon": "bi-file-earmark-check-fill", "iconColor": "text-primary"},
            {"type": "HelpDesk", "count": helpdesk, "icon": "bi-question-diamond-fill", "iconColor": "text-danger"},
            {"type": "WorkFlow", "count": workflow, "icon": "bi-bar-chart-steps", "iconColor": "text-danger"}
        ]
        
        return OpenRequestsResponse(requests=requests_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch open requests: {str(e)}"
        )


@router.get("/birthdays", response_model=BirthdaysResponse)
async def get_birthdays(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get upcoming birthdays data
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Query employees with birthdays - eagerly load profile relationship
        employee_query = db.query(Employee).options(
            joinedload(Employee.profile),
            joinedload(Employee.designation)
        ).filter(Employee.employee_status == "active")
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        # Get employees with birthdays today
        today_birthdays = employee_query.filter(
            func.extract('month', Employee.date_of_birth) == today.month,
            func.extract('day', Employee.date_of_birth) == today.day
        ).all()
        
        # Get employees with birthdays tomorrow
        tomorrow_birthdays = employee_query.filter(
            func.extract('month', Employee.date_of_birth) == tomorrow.month,
            func.extract('day', Employee.date_of_birth) == tomorrow.day
        ).all()
        
        # Get upcoming birthdays (next 365 days, excluding today and tomorrow)
        # This ensures the "All Birthdays" page shows all birthdays for the entire year
        upcoming_birthdays = []
        for i in range(2, 366):  # Skip today and tomorrow, fetch entire year
            future_date = today + timedelta(days=i)
            future_birthday_employees = employee_query.filter(
                func.extract('month', Employee.date_of_birth) == future_date.month,
                func.extract('day', Employee.date_of_birth) == future_date.day
            ).all()
            
            for emp in future_birthday_employees:
                # Get profile image from EmployeeProfile relationship
                profile_image = emp.profile.profile_image_url if emp.profile and emp.profile.profile_image_url else None
                upcoming_birthdays.append({
                    "date": future_date.strftime("%d %b %Y"),
                    "avatar": profile_image if profile_image else "assets/img/users/default-avatar.jpg",
                    "name": emp.full_name,
                    "role": emp.designation.name if emp.designation else "Employee",
                    "id": emp.id
                })
        
        # Convert to expected format
        def format_birthday_data(employees, date_label=None):
            result = []
            for emp in employees:
                # Get profile image from EmployeeProfile relationship
                profile_image = emp.profile.profile_image_url if emp.profile and emp.profile.profile_image_url else None
                result.append({
                    "avatar": profile_image if profile_image else "assets/img/users/default-avatar.jpg",
                    "name": emp.full_name,
                    "role": emp.designation.name if emp.designation else "Employee",
                    "id": emp.id
                })
            return result
        
        # Return real data from database - NO HARDCODED DATA
        return BirthdaysResponse(
            today=format_birthday_data(today_birthdays),
            tomorrow=format_birthday_data(tomorrow_birthdays),
            upcoming=upcoming_birthdays
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch birthdays: {str(e)}"
        )


@router.post("/send-birthday-wish", response_model=SendBirthdayWishResponse)
async def send_birthday_wish(
    employee_name: str = Query(..., description="Employee name"),
    employee_id: Optional[int] = Query(None, description="Employee ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Send birthday wish to an employee via email
    
    **Parameters:**
    - employee_name: Name of the employee
    - employee_id: Optional employee ID for database lookup
    
    **Returns:**
    - Success status and message
    """
    try:
        from app.services.email_service import email_service
        from app.models.business import Business
        
        business_id = get_user_business_id(current_user, db)
        
        # Try to find the employee in database if ID provided
        employee = None
        if employee_id:
            employee_query = db.query(Employee).filter(Employee.id == employee_id)
            if business_id:
                employee_query = employee_query.filter(Employee.business_id == business_id)
            employee = employee_query.first()
        
        # If no employee found by ID, try to find by name
        if not employee and employee_name:
            employee_query = db.query(Employee).filter(
                or_(
                    Employee.first_name.ilike(f"%{employee_name}%"),
                    Employee.last_name.ilike(f"%{employee_name}%"),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{employee_name}%")
                )
            )
            if business_id:
                employee_query = employee_query.filter(Employee.business_id == business_id)
            employee = employee_query.first()
        
        if not employee:
            return SendBirthdayWishResponse(
                success=False,
                message=f"Employee not found: {employee_name}",
                employee_name=employee_name
            )
        
        # Check if employee has email
        if not employee.email:
            return SendBirthdayWishResponse(
                success=False,
                message=f"Employee {employee.full_name} does not have an email address",
                employee_name=employee.full_name
            )
        
        # Get business details
        business = db.query(Business).filter(Business.id == employee.business_id).first()
        company_name = business.business_name if business else "Levitica Technologies"
        
        # Get employee designation
        employee_designation = employee.designation.name if employee.designation else "Team Member"
        
        # Send birthday wishes email
        email_sent = await email_service.send_birthday_wishes_email(
            employee_name=employee.full_name,
            employee_email=employee.email,
            employee_designation=employee_designation,
            company_name=company_name,
            sender_name="HR Team"
        )
        
        if email_sent:
            return SendBirthdayWishResponse(
                success=True,
                message=f"🎉 Birthday wishes sent successfully to {employee.full_name} at {employee.email}!",
                employee_name=employee.full_name
            )
        else:
            return SendBirthdayWishResponse(
                success=False,
                message=f"Failed to send email to {employee.full_name}. Please check SMTP configuration.",
                employee_name=employee.full_name
            )
    
    except Exception as e:
        print(f"ERROR in send_birthday_wish: {str(e)}")
        import traceback
        traceback.print_exc()
        return SendBirthdayWishResponse(
            success=False,
            message=f"Failed to send birthday wish: {str(e)}",
            employee_name=employee_name
        )


@router.get("/attendance-trend", response_model=AttendanceTrendResponse)
async def get_attendance_trend(
    year: int = Query(None, description="Year for attendance trend"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get attendance trend data for the chart
    Returns monthly attendance data for presents, absents, and leaves
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Use current year if not specified
        if year is None:
            year = datetime.now().year
        
        # Month labels
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Initialize data arrays
        presents = []
        absents = []
        leaves = []
        
        # Get attendance data for each month
        for month in range(1, 13):
            # Query attendance records for this month
            attendance_query = db.query(AttendanceRecord).filter(
                func.extract('year', AttendanceRecord.attendance_date) == year,
                func.extract('month', AttendanceRecord.attendance_date) == month
            )
            
            if business_id:
                attendance_query = attendance_query.filter(AttendanceRecord.business_id == business_id)
            
            # Count by status using proper enum values
            month_presents = attendance_query.filter(AttendanceRecord.attendance_status == AttendanceStatus.PRESENT).count()
            month_absents = attendance_query.filter(AttendanceRecord.attendance_status == AttendanceStatus.ABSENT).count()
            month_leaves = attendance_query.filter(AttendanceRecord.attendance_status == AttendanceStatus.ON_LEAVE).count()
            
            presents.append(month_presents)
            absents.append(month_absents)
            leaves.append(month_leaves)
        
        return AttendanceTrendResponse(
            months=months,
            presents=presents,
            absents=absents,
            leaves=leaves
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance trend: {str(e)}"
        )


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get dashboard overview statistics
    
    **Returns:**
    - Employee counts and statistics
    - Today's attendance summary
    - Pending approvals count
    - Upcoming birthdays
    - Recent activities
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Employee statistics
        employee_query = db.query(Employee)
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        total_employees = employee_query.count()
        active_employees = employee_query.filter(Employee.employee_status == "active").count()
        
        # This month statistics
        current_month_start = date.today().replace(day=1)
        new_joinings_this_month = employee_query.filter(
            Employee.date_of_joining >= current_month_start
        ).count()
        
        terminations_this_month = employee_query.filter(
            and_(
                Employee.date_of_termination >= current_month_start,
                Employee.date_of_termination.isnot(None)
            )
        ).count()
        
        # Today's attendance
        today = date.today()
        attendance_query = db.query(AttendanceRecord).filter(
            AttendanceRecord.attendance_date == today
        )
        if business_id:
            attendance_query = attendance_query.filter(AttendanceRecord.business_id == business_id)
        
        total_attendance = attendance_query.count()
        present_today = attendance_query.filter(
            AttendanceRecord.attendance_status == AttendanceStatus.PRESENT
        ).count()
        absent_today = attendance_query.filter(
            AttendanceRecord.attendance_status == AttendanceStatus.ABSENT
        ).count()
        on_leave_today = attendance_query.filter(
            AttendanceRecord.attendance_status == AttendanceStatus.ON_LEAVE
        ).count()
        
        attendance_today = {
            "total": total_attendance,
            "present": present_today,
            "absent": absent_today,
            "on_leave": on_leave_today
        }
        
        # Upcoming birthdays (next 7 days)
        next_week = date.today() + timedelta(days=7)
        upcoming_birthdays = employee_query.filter(
            and_(
                Employee.date_of_birth.isnot(None),
                func.extract('month', Employee.date_of_birth) == next_week.month,
                func.extract('day', Employee.date_of_birth) <= next_week.day
            )
        ).count()
        
        # Mock data for pending approvals and recent activities
        pending_approvals = 5  # This would come from actual approval tables
        
        recent_activities = [
            {
                "type": "new_employee",
                "message": "New employee John Doe joined",
                "timestamp": datetime.now().isoformat(),
                "icon": "user-plus"
            },
            {
                "type": "leave_request",
                "message": "Leave request approved for Jane Smith",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "icon": "calendar"
            }
        ]
        
        return DashboardOverviewResponse(
            total_employees=total_employees,
            active_employees=active_employees,
            new_joinings_this_month=new_joinings_this_month,
            terminations_this_month=terminations_this_month,
            attendance_today=attendance_today,
            pending_approvals=pending_approvals,
            upcoming_birthdays=upcoming_birthdays,
            employees_on_leave=on_leave_today,
            recent_activities=recent_activities
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard overview: {str(e)}"
        )


@router.get("", response_model=DashboardMainResponse)
async def get_dashboard_main(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get main dashboard overview with key metrics
    
    Returns:
    - Employee statistics
    - Attendance summary
    - Recent activities
    - Key performance indicators
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Employee statistics
        total_employees = db.query(Employee).filter(Employee.business_id == business_id).count()
        active_employees = db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_status == "active"
        ).count()
        
        # Mock data for overview
        overview_data = {
            "employee_stats": {
                "total_employees": total_employees,
                "active_employees": active_employees,
                "new_hires_this_month": 5,
                "pending_onboarding": 3
            },
            "attendance_summary": {
                "present_today": active_employees - 2,
                "absent_today": 2,
                "late_arrivals": 1,
                "early_departures": 0
            },
            "recent_activities": [
                {
                    "type": "employee_joined",
                    "message": "New employee John Doe joined",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "leave_request",
                    "message": "Leave request submitted by Jane Smith",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "kpis": {
                "employee_satisfaction": 85,
                "attendance_rate": 94,
                "turnover_rate": 8,
                "productivity_score": 92
            }
        }
        
        return DashboardMainResponse(**overview_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard overview: {str(e)}"
        )


@router.get("/flight-risk", response_model=FlightRiskResponse)
async def get_flight_risk_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get flight risk analytics from real database data
    
    **Returns:**
    - Employee categorization by risk levels based on real data
    - Risk counts for dashboard cards
    - Employee details from database
    - Risk signals calculated from attendance and performance data
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Query real employees from database with profile relationship
        employee_query = db.query(Employee).options(
            joinedload(Employee.profile)
        ).filter(Employee.is_active == True)
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        employees = employee_query.all()
        
        # Get tracking status for all employees (using EmployeeProfile.bio field)
        # Check each employee's tracking status from the database
        
        # Calculate risk scores for each employee
        no_risk_employees = []
        moderate_risk_employees = []
        high_risk_employees = []
        untracked_employees = []
        
        for employee in employees:
            # Check if tracking is stopped for this employee
            tracking_status = None
            if employee.profile and employee.profile.bio:
                # Check if bio contains flight risk tracking info
                if 'FLIGHT_RISK_STOPPED' in employee.profile.bio:
                    tracking_status = 'stopped'
            
            if tracking_status == 'stopped':
                # Add to untracked category
                employee_data = {
                    "id": employee.employee_code or f"EMP{employee.id}",
                    "name": f"{employee.first_name} {employee.last_name}".strip(),
                    "deputation": employee.designation.name if employee.designation else "Not Assigned",
                    "dept": employee.department.name if employee.department else "Not Assigned",
                    "lastupdated": datetime.now().strftime("%b %d, %Y"),
                    "riskpercent": "N/A",
                    "riskstatus": "Tracking Stopped",
                    "Actions": "Resume Tracking",
                    "picture": f"https://placehold.co/100x100/lightgray/black.png?text={employee.first_name[0] if employee.first_name else 'E'}{employee.last_name[0] if employee.last_name else 'M'}",
                    "risk_signals": [{"text": "Flight risk tracking has been stopped", "color": "#6b7280"}],
                    "tracking_stopped": True,
                    "employee_id": employee.id
                }
                untracked_employees.append(employee_data)
                continue
            
            # Calculate risk score based on real data
            risk_data = _calculate_employee_risk_score(db, employee)
            
            employee_data = {
                "id": employee.employee_code or f"EMP{employee.id}",
                "name": f"{employee.first_name} {employee.last_name}".strip(),
                "deputation": employee.designation.name if employee.designation else "Not Assigned",
                "dept": employee.department.name if employee.department else "Not Assigned",
                "lastupdated": datetime.now().strftime("%b %d, %Y"),
                "riskpercent": f"{risk_data['risk_score']}%",
                "riskstatus": risk_data['risk_category'],
                "Actions": "Stop Tracking",
                "picture": f"https://placehold.co/100x100/lightblue/black.png?text={employee.first_name[0] if employee.first_name else 'E'}{employee.last_name[0] if employee.last_name else 'M'}",
                "risk_signals": risk_data['risk_signals'],
                "tracking_stopped": False,
                "employee_id": employee.id
            }
            
            # Categorize by risk level
            if risk_data['risk_score'] <= 20:
                no_risk_employees.append(employee_data)
            elif risk_data['risk_score'] <= 40:
                moderate_risk_employees.append(employee_data)
            else:
                high_risk_employees.append(employee_data)
        
        # Create response with real database data
        response_data = {
            "untracked": untracked_employees,
            "uncalculated": [],
            "noRisk": no_risk_employees,
            "moderate": moderate_risk_employees,
            "high": high_risk_employees,
            "counts": {
                "untracked": len(untracked_employees),
                "uncalculated": 0,
                "no_risk": len(no_risk_employees),
                "moderate": len(moderate_risk_employees),
                "high": len(high_risk_employees)
            },
            # Legacy fields for backward compatibility - all from real data
            "high_risk_employees": high_risk_employees,
            "medium_risk_employees": moderate_risk_employees,
            "risk_factors": {},  # Remove hardcoded risk factors
            "retention_rate": 0.0,  # Calculate from real data or set to 0
            "turnover_rate": 0.0,   # Calculate from real data or set to 0
            "risk_trends": []
        }
        
        return FlightRiskResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch flight risk analytics: {str(e)}"
        )


@router.post("/flight-risk/stop-tracking/{employee_id}")
async def stop_flight_risk_tracking(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Stop flight risk tracking for a specific employee
    
    **Parameters:**
    - employee_id: ID of the employee to stop tracking
    
    **Returns:**
    - Success message and updated status
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Verify employee exists and belongs to the business
        employee_query = db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.is_active == True
        )
        
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        employee = employee_query.first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Get or create employee profile
        if not employee.profile:
            from app.models.employee import EmployeeProfile
            profile = EmployeeProfile(employee_id=employee.id)
            db.add(profile)
            db.flush()  # Get the ID
            employee.profile = profile
        
        # Use bio field to store flight risk tracking status
        tracking_info = f"FLIGHT_RISK_STOPPED|{datetime.now().isoformat()}|{current_user.email}"
        
        if employee.profile.bio:
            # Remove any existing flight risk info and add new
            bio_lines = [line for line in employee.profile.bio.split('\n') if not line.startswith('FLIGHT_RISK_')]
            bio_lines.append(tracking_info)
            employee.profile.bio = '\n'.join(bio_lines)
        else:
            employee.profile.bio = tracking_info
        
        db.commit()
        db.refresh(employee)
        
        return {
            "success": True,
            "message": f"Flight risk tracking stopped for {employee.first_name} {employee.last_name}",
            "employee_id": employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "stopped_at": datetime.now().isoformat(),
            "stopped_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop flight risk tracking: {str(e)}"
        )


@router.post("/flight-risk/resume-tracking/{employee_id}")
async def resume_flight_risk_tracking(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Resume flight risk tracking for a specific employee
    
    **Parameters:**
    - employee_id: ID of the employee to resume tracking
    
    **Returns:**
    - Success message and updated status
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Verify employee exists and belongs to the business
        employee_query = db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.is_active == True
        )
        
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        employee = employee_query.first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Get or create employee profile
        if not employee.profile:
            from app.models.employee import EmployeeProfile
            profile = EmployeeProfile(employee_id=employee.id)
            db.add(profile)
            db.flush()
            employee.profile = profile
        
        # Remove flight risk tracking info from bio
        if employee.profile.bio:
            bio_lines = [line for line in employee.profile.bio.split('\n') if not line.startswith('FLIGHT_RISK_')]
            employee.profile.bio = '\n'.join(bio_lines) if bio_lines else None
        
        db.commit()
        db.refresh(employee)
        
        return {
            "success": True,
            "message": f"Flight risk tracking resumed for {employee.first_name} {employee.last_name}",
            "employee_id": employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "resumed_at": datetime.now().isoformat(),
            "resumed_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flight risk tracking: {str(e)}"
        )


def _calculate_employee_risk_score(db: Session, employee: Employee) -> Dict[str, Any]:
    """
    Calculate risk score for an employee based on real database data
    """
    risk_score = 0
    risk_signals = []
    
    # Calculate date ranges
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    
    # 1. Attendance Analysis (40% weight)
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.attendance_date >= ninety_days_ago
    ).all()
    
    if attendance_records:
        total_days = len(attendance_records)
        absent_days = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.ABSENT])
        late_days = len([r for r in attendance_records if r.is_late])
        early_out_days = len([r for r in attendance_records if r.is_early_out])
        
        # Absenteeism risk (0-15 points)
        absent_rate = (absent_days / total_days) * 100 if total_days > 0 else 0
        if absent_rate > 10:
            risk_score += 15
            risk_signals.append({"text": f"High absenteeism: {absent_rate:.1f}% in last 90 days", "color": "#ef4444"})
        elif absent_rate > 5:
            risk_score += 8
            risk_signals.append({"text": f"Moderate absenteeism: {absent_rate:.1f}% in last 90 days", "color": "#fbbf24"})
        else:
            risk_signals.append({"text": "Absents are under acceptable range", "color": "#10b981"})
        
        # Late coming risk (0-15 points)
        late_rate = (late_days / total_days) * 100 if total_days > 0 else 0
        if late_rate > 20:
            risk_score += 15
            risk_signals.append({"text": f"Frequent late arrivals: {late_days} days in last 90 days", "color": "#ef4444"})
        elif late_rate > 10:
            risk_score += 8
            risk_signals.append({"text": f"Moderate late arrivals: {late_days} days in last 90 days", "color": "#a78bfa"})
        else:
            risk_signals.append({"text": "Punctuality is good", "color": "#10b981"})
        
        # Early departure risk (0-10 points)
        early_out_rate = (early_out_days / total_days) * 100 if total_days > 0 else 0
        if early_out_rate > 15:
            risk_score += 10
            risk_signals.append({"text": f"Frequent early departures: {early_out_days} days", "color": "#ef4444"})
        elif early_out_rate > 5:
            risk_score += 5
            risk_signals.append({"text": f"Some early departures: {early_out_days} days", "color": "#fbbf24"})
        else:
            risk_signals.append({"text": "Early-Out events are under acceptable range", "color": "#10b981"})
    else:
        risk_signals.append({"text": "No attendance data available", "color": "#6b7280"})
    
    # 2. Leave Pattern Analysis (30% weight)
    leave_requests = db.query(LeaveRequest).join(Request).filter(
        Request.employee_id == employee.id,
        Request.from_date >= ninety_days_ago,
        Request.status == RequestStatus.APPROVED,
        Request.request_type == RequestType.LEAVE
    ).all()
    
    if leave_requests:
        total_leave_days = sum([req.total_days for req in leave_requests if req.total_days])
        unpaid_leaves = [req for req in leave_requests if req.leave_type and 'unpaid' in req.leave_type.lower()]
        
        # Excessive leave usage (0-20 points)
        if total_leave_days > 15:
            risk_score += 20
            risk_signals.append({"text": f"Excessive leave usage: {total_leave_days} days", "color": "#ef4444"})
        elif total_leave_days > 8:
            risk_score += 10
            risk_signals.append({"text": f"High leave usage: {total_leave_days} days", "color": "#fbbf24"})
        else:
            risk_signals.append({"text": "Leave usage is within acceptable range", "color": "#10b981"})
        
        # Unpaid leave pattern (0-10 points)
        if len(unpaid_leaves) > 2:
            risk_score += 10
            risk_signals.append({"text": f"Multiple unpaid leaves: {len(unpaid_leaves)} requests", "color": "#ef4444"})
        elif len(unpaid_leaves) > 0:
            risk_score += 5
            risk_signals.append({"text": f"Some unpaid leaves: {len(unpaid_leaves)} requests", "color": "#fbbf24"})
        else:
            risk_signals.append({"text": "No unpaid leave requests", "color": "#10b981"})
    else:
        risk_signals.append({"text": "Paid leaves are under acceptable range", "color": "#10b981"})
        risk_signals.append({"text": "Unpaid leaves are under acceptable range", "color": "#10b981"})
    
    # 3. Performance Indicators (30% weight)
    # Check for disciplinary actions, complaints, etc.
    recent_requests = db.query(Request).filter(
        Request.employee_id == employee.id,
        Request.created_at >= thirty_days_ago
    ).count()
    
    if recent_requests > 5:
        risk_score += 15
        risk_signals.append({"text": f"High request activity: {recent_requests} requests", "color": "#fbbf24"})
    elif recent_requests > 2:
        risk_score += 5
        risk_signals.append({"text": f"Moderate request activity: {recent_requests} requests", "color": "#a78bfa"})
    
    # Ensure minimum signals
    if len(risk_signals) < 3:
        risk_signals.append({"text": "Overall performance is satisfactory", "color": "#10b981"})
    
    # Determine risk category
    if risk_score <= 20:
        risk_category = "No Risk"
    elif risk_score <= 40:
        risk_category = "Moderate Risk"
    else:
        risk_category = "High"
    
    return {
        "risk_score": min(risk_score, 100),  # Cap at 100%
        "risk_category": risk_category,
        "risk_signals": risk_signals
    }

def _get_risk_factors(risk_score):
    """Get risk factors based on risk score"""
    if risk_score >= 35:
        return [
            "High absenteeism rate",
            "Frequent late arrivals", 
            "Below average performance",
            "Low engagement scores"
        ]
    elif risk_score >= 20:
        return [
            "Moderate late coming events",
            "Some unpaid leaves",
            "Average performance metrics"
        ]
    else:
        return [
            "Absents are under acceptable range",
            "Unpaid leaves are under acceptable range", 
            "Paid leaves are under acceptable range",
            "Good attendance record"
        ]


@router.get("/org-chart", response_model=OrgChartResponse)
async def get_organization_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get organization chart data from real database
    
    **Returns:**
    - Hierarchical organization tree from database
    - Employee reporting relationships
    - Real employee data
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Query real employees from database
        employee_query = db.query(Employee).options(
            joinedload(Employee.designation),
            joinedload(Employee.department)
        ).filter(
            Employee.is_active == True,
            Employee.employee_status.in_(["active", "ACTIVE"])
        )
        
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        employees = employee_query.all()
        
        if not employees:
            # Return empty org chart if no employees
            return OrgChartResponse(
                data=OrgChartNode(
                    id="no-employees",
                    name="No Employees Found",
                    level="N/A",
                    title="Please add employees to see organization chart",
                    children=[]
                ),
                total_employees=0,
                total_departments=0,
                organization_depth=1
            )
        
        # Build real org chart from database
        org_data = build_real_org_chart(employees)
        
        if not org_data:
            # If no clear hierarchy, create a flat structure with first employee as root
            root_employee = employees[0]
            other_employees = employees[1:] if len(employees) > 1 else []
            
            org_data = OrgChartNode(
                id=str(root_employee.id),
                name=root_employee.full_name,
                level=root_employee.employee_code or f"EMP{root_employee.id:03d}",
                title=root_employee.designation.name if root_employee.designation else "No Title",
                department=root_employee.department.name if root_employee.department else "No Department",
                email=root_employee.email,
                children=[
                    OrgChartNode(
                        id=str(emp.id),
                        name=emp.full_name,
                        level=emp.employee_code or f"EMP{emp.id:03d}",
                        title=emp.designation.name if emp.designation else "No Title",
                        department=emp.department.name if emp.department else "No Department",
                        email=emp.email,
                        children=[]
                    ) for emp in other_employees
                ]
            )
        
        # Get unique departments
        departments = set()
        for emp in employees:
            if emp.department:
                departments.add(emp.department.name)
        
        return OrgChartResponse(
            data=org_data,
            total_employees=len(employees),
            total_departments=len(departments),
            organization_depth=calculate_tree_depth(org_data)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch organization chart: {str(e)}"
        )


@router.get("/org-chart/download")
async def download_organization_chart(
    format: str = Query("json", description="Download format: json, csv, or pdf"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Download organization chart data in various formats
    
    **Formats:**
    - json: JSON format with complete hierarchy
    - csv: CSV format with flattened employee data
    - pdf: PDF format (future implementation)
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get organization chart data
        org_response = await get_organization_chart(db, current_user)
        org_data = org_response.data
        
        if format.lower() == "json":
            # Return JSON format
            from fastapi.responses import JSONResponse
            
            # Convert OrgChartNode to dict recursively
            def node_to_dict(node):
                return {
                    "id": node.id,
                    "name": node.name,
                    "level": node.level,
                    "title": node.title,
                    "department": node.department,
                    "email": node.email,
                    "children": [node_to_dict(child) for child in (node.children or [])]
                }
            
            response_data = {
                "organization_chart": node_to_dict(org_data),
                "metadata": {
                    "total_employees": org_response.total_employees,
                    "total_departments": org_response.total_departments,
                    "organization_depth": org_response.organization_depth,
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": current_user.email,
                    "business_id": business_id
                }
            }
            
            return JSONResponse(
                content=response_data,
                headers={
                    "Content-Disposition": f"attachment; filename=organization_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        
        elif format.lower() == "csv":
            # Return CSV format
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            # Flatten organization data for CSV
            csv_data = []
            
            def flatten_org_data(node, level=0, parent_name=""):
                csv_data.append({
                    "Employee_ID": node.id,
                    "Employee_Name": node.name,
                    "Employee_Code": node.level,
                    "Job_Title": node.title,
                    "Department": node.department or "",
                    "Email": node.email or "",
                    "Organization_Level": level,
                    "Parent_Manager": parent_name,
                    "Direct_Reports_Count": len(node.children) if node.children else 0
                })
                
                for child in (node.children or []):
                    flatten_org_data(child, level + 1, node.name)
            
            flatten_org_data(org_data)
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "Employee_ID", "Employee_Name", "Employee_Code", "Job_Title", 
                "Department", "Email", "Organization_Level", "Parent_Manager", "Direct_Reports_Count"
            ])
            writer.writeheader()
            writer.writerows(csv_data)
            
            csv_content = output.getvalue()
            output.close()
            
            return StreamingResponse(
                io.BytesIO(csv_content.encode('utf-8')),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=organization_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use 'json' or 'csv'"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download organization chart: {str(e)}"
        )


@router.get("/org-chart/search", response_model=OrgChartSearchResponse)
async def search_organization_chart(
    q: str = Query(..., description="Search term (name or employee ID)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Search organization chart for specific employee
    
    **Returns:**
    - Found employee node with their subtree
    - Search result status
    """
    try:
        # Get the full org chart first
        org_response = await get_organization_chart(db, current_user)
        org_data = org_response.data
        
        # Search for the employee
        found_node = search_org_tree(org_data, q.strip().lower())
        
        if found_node:
            return OrgChartSearchResponse(
                found=True,
                node=found_node,
                message=f"Found employee: {found_node.name}"
            )
        else:
            return OrgChartSearchResponse(
                found=False,
                node=None,
                message="No employee found. Try another name or ID."
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search organization chart: {str(e)}"
        )


def build_real_org_chart(employees: List[Employee]) -> Optional[OrgChartNode]:
    """Build real org chart from database employees"""
    try:
        if not employees:
            return None
        
        # Find the top-level manager (employee with no reporting manager OR manager not in active list)
        employee_ids = {emp.id for emp in employees}
        root_employees = [emp for emp in employees if not emp.reporting_manager_id or emp.reporting_manager_id not in employee_ids]
        
        if not root_employees:
            # If everyone has a manager (circular reference), take the first employee
            root_employee = employees[0]
        elif len(root_employees) == 1:
            # Perfect - one clear root
            root_employee = root_employees[0]
        else:
            # Multiple roots - take the one with most subordinates first
            def get_subordinate_count(emp):
                return len([e for e in employees if e.reporting_manager_id == emp.id])
            
            # Sort by subordinate count (descending), then prefer managers/leads
            root_employees_with_counts = [(emp, get_subordinate_count(emp)) for emp in root_employees]
            root_employees_with_counts.sort(key=lambda x: x[1], reverse=True)
            
            # If top employee has subordinates, use them
            if root_employees_with_counts[0][1] > 0:
                root_employee = root_employees_with_counts[0][0]
            else:
                # All have 0 subordinates - prefer by designation
                managers = [emp for emp in root_employees if emp.designation and 'manager' in emp.designation.name.lower()]
                if managers:
                    root_employee = managers[0]
                else:
                    team_leads = [emp for emp in root_employees if emp.designation and 'lead' in emp.designation.name.lower()]
                    if team_leads:
                        root_employee = team_leads[0]
                    else:
                        root_employee = root_employees[0]
        
        def build_node(employee: Employee) -> OrgChartNode:
            # Find direct subordinates
            subordinates = [emp for emp in employees if emp.reporting_manager_id == employee.id]
            
            return OrgChartNode(
                id=str(employee.id),
                name=employee.full_name,
                level=employee.employee_code or f"EMP{employee.id:03d}",
                title=employee.designation.name if employee.designation else "No Title",
                department=employee.department.name if employee.department else "No Department",
                email=employee.email,
                children=[build_node(sub) for sub in subordinates]
            )
        
        return build_node(root_employee)
    
    except Exception as e:
        # Log error but don't expose details to client
        return None


def search_org_tree(node: OrgChartNode, search_term: str) -> Optional[OrgChartNode]:
    """Search for employee in org tree"""
    # Normalize search term
    search_term = search_term.lower().strip()
    
    # Check current node - search in name, id, level, title, and department
    if (search_term in node.name.lower() or 
        search_term in node.id.lower() or 
        search_term in node.level.lower() or
        (node.title and search_term in node.title.lower()) or
        (node.department and search_term in node.department.lower()) or
        (node.email and search_term in node.email.lower())):
        return node
    
    # Search children
    if node.children:
        for child in node.children:
            found = search_org_tree(child, search_term)
            if found:
                return found
    
    return None


def count_total_employees(node: OrgChartNode) -> int:
    """Count total employees in org tree"""
    count = 1  # Current node
    if node.children:
        for child in node.children:
            count += count_total_employees(child)
    return count


def calculate_tree_depth(node: OrgChartNode, current_depth: int = 1) -> int:
    """Calculate organization tree depth"""
    if not node.children:
        return current_depth
    return max(calculate_tree_depth(child, current_depth + 1) for child in node.children)

# Update the OrgChartNode model to handle forward references
OrgChartNode.model_rebuild()

def create_attendance_employee_record(emp: Employee, attendance: AttendanceRecord, status: str) -> AttendanceEmployeeRecord:
    """Helper function to create attendance employee record"""
    # Get shift information from employee or attendance record
    shift_start = "09:00 AM"  # Default
    shift_end = "06:00 PM"    # Default
    
    if attendance and attendance.expected_in_time and attendance.expected_out_time:
        shift_start = attendance.expected_in_time.strftime("%I:%M %p")
        shift_end = attendance.expected_out_time.strftime("%I:%M %p")
    
    return AttendanceEmployeeRecord(
        id=emp.id,
        name=emp.full_name,
        employee_code=emp.employee_code or f"EMP{emp.id:04d}",
        department=emp.department.name if emp.department else "N/A",
        designation=emp.designation.name if emp.designation else "Employee",
        profile_image=None,
        shift_start=shift_start,
        shift_end=shift_end,
        time_in=attendance.punch_in_time.strftime("%I:%M %p") if attendance and attendance.punch_in_time else None,
        time_out=attendance.punch_out_time.strftime("%I:%M %p") if attendance and attendance.punch_out_time else None,
        status=status,
        hours_worked=float(attendance.total_hours) if attendance and attendance.total_hours else 0.0,
        late_minutes=0,
        early_departure_minutes=0
    )


@router.get("/attendance/employees/absent", response_model=AttendanceEmployeeListResponse)
async def get_absent_employees(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    location: Optional[str] = Query(None, description="Filter by location"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(10, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of absent employees for a specific date
    """
    try:
        target_date = date if date else datetime.now().date()
        business_id = get_user_business_id(current_user, db)
        
        # Query absent employees with proper attendance status filtering
        query = db.query(Employee).join(
            AttendanceRecord, 
            and_(
                Employee.id == AttendanceRecord.employee_id,
                AttendanceRecord.attendance_date == target_date
            )
        ).filter(
            AttendanceRecord.attendance_status == AttendanceStatus.ABSENT
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        if location:
            # Convert location name to location_id
            location_obj = db.query(Location).filter(
                Location.name == location,
                Location.business_id == business_id if business_id else True
            ).first()
            if location_obj:
                query = query.filter(Employee.location_id == location_obj.id)
        
        if department:
            # Convert department name to department_id
            department_obj = db.query(Department).filter(
                Department.name == department,
                Department.business_id == business_id if business_id else True
            ).first()
            if department_obj:
                query = query.filter(Employee.department_id == department_obj.id)
        
        employees = query.limit(limit).all()
        
        # Convert real employees to response format
        employee_records = []
        for emp in employees:
            # Get attendance record for this employee on the target date
            attendance = db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.attendance_date == target_date
            ).first()
            
            employee_records.append(create_attendance_employee_record(emp, attendance, "absent"))
        
        return AttendanceEmployeeListResponse(
            employees=employee_records,
            total=len(employee_records),
            date=str(target_date),
            filters={"location": location, "department": department, "limit": limit}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch absent employees: {str(e)}"
        )


@router.get("/attendance/employees/present", response_model=AttendanceEmployeeListResponse)
async def get_present_employees(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    location: Optional[str] = Query(None, description="Filter by location"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(10, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of present employees for a specific date
    """
    try:
        target_date = date if date else datetime.now().date()
        business_id = get_user_business_id(current_user, db)
        
        # Query present employees with proper attendance status filtering
        query = db.query(Employee).join(
            AttendanceRecord,
            and_(
                Employee.id == AttendanceRecord.employee_id,
                AttendanceRecord.attendance_date == target_date
            )
        ).filter(
            or_(
                AttendanceRecord.attendance_status == AttendanceStatus.PRESENT,
                AttendanceRecord.attendance_status == AttendanceStatus.HALF_DAY
            )
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        if location:
            # Convert location name to location_id
            location_obj = db.query(Location).filter(
                Location.name == location,
                Location.business_id == business_id if business_id else True
            ).first()
            if location_obj:
                query = query.filter(Employee.location_id == location_obj.id)
        
        if department:
            # Convert department name to department_id
            department_obj = db.query(Department).filter(
                Department.name == department,
                Department.business_id == business_id if business_id else True
            ).first()
            if department_obj:
                query = query.filter(Employee.department_id == department_obj.id)
        
        employees = query.limit(limit).all()
        
        # Convert real employees to response format
        employee_records = []
        for emp in employees:
            # Get attendance record for this employee
            attendance = db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.attendance_date == target_date
            ).first()
            
            employee_records.append(create_attendance_employee_record(emp, attendance, "present"))
        
        return AttendanceEmployeeListResponse(
            employees=employee_records,
            total=len(employee_records),
            date=str(target_date),
            filters={"location": location, "department": department, "limit": limit}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch present employees: {str(e)}"
        )


@router.get("/attendance/employees/late", response_model=AttendanceEmployeeListResponse)
async def get_late_employees(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    location: Optional[str] = Query(None, description="Filter by location"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(10, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of late employees for a specific date
    """
    try:
        target_date = date if date else datetime.now().date()
        business_id = get_user_business_id(current_user, db)
        
        # Query late employees with proper join and filtering
        query = db.query(Employee).join(
            AttendanceRecord,
            and_(
                Employee.id == AttendanceRecord.employee_id,
                AttendanceRecord.attendance_date == target_date
            )
        ).filter(
            AttendanceRecord.is_late == True
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        if location:
            # Convert location name to location_id
            location_obj = db.query(Location).filter(
                Location.name == location,
                Location.business_id == business_id if business_id else True
            ).first()
            if location_obj:
                query = query.filter(Employee.location_id == location_obj.id)
        
        if department:
            # Convert department name to department_id
            department_obj = db.query(Department).filter(
                Department.name == department,
                Department.business_id == business_id if business_id else True
            ).first()
            if department_obj:
                query = query.filter(Employee.department_id == department_obj.id)
        
        employees = query.limit(limit).all()
        
        # Convert real employees to response format
        employee_records = []
        for emp in employees:
            # Get attendance record for this employee
            attendance = db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.attendance_date == target_date
            ).first()
            
            employee_records.append(create_attendance_employee_record(emp, attendance, "late"))
        
        return AttendanceEmployeeListResponse(
            employees=employee_records,
            total=len(employee_records),
            date=str(target_date),
            filters={"location": location, "department": department, "limit": limit}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch late employees: {str(e)}"
        )


class AttendancePieChartResponse(BaseModel):
    """Attendance pie chart data response"""
    attendance_chart: Dict[str, Any]
    late_comers_chart: Dict[str, Any]
    early_goers_chart: Dict[str, Any]


class AttendanceFiltersResponse(BaseModel):
    """Attendance dashboard filters response"""
    locations: List[str]
    departments: List[str]
    date_options: List[str]
    top_options: List[str]


@router.get("/attendance/pie-charts", response_model=AttendancePieChartResponse)
async def get_attendance_pie_charts(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    location: Optional[str] = Query(None, description="Filter by location"),
    department: Optional[str] = Query(None, description="Filter by department"),
    top_n: int = Query(10, description="Top N employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get pie chart data for attendance dashboard
    
    **Returns:**
    - Attendance pie chart (Presents, Leaves, Absents, WeekOffs, Holidays)
    - Late Comers pie chart (On-Time, Late Comers)
    - Early Goers pie chart (On-Time, Early Goers)
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.now().date()
        business_id = get_user_business_id(current_user, db)
        
        # Build base query for attendance records with proper joins
        attendance_query = db.query(AttendanceRecord).join(Employee)
        
        # Apply business filter
        if business_id:
            attendance_query = attendance_query.filter(Employee.business_id == business_id)
        
        # Apply date filter
        attendance_query = attendance_query.filter(AttendanceRecord.attendance_date == target_date)
        
        # Apply location filter if provided
        if location:
            location_obj = db.query(Location).filter(
                Location.name == location,
                Location.business_id == business_id if business_id else True
            ).first()
            if location_obj:
                attendance_query = attendance_query.filter(Employee.location_id == location_obj.id)
        
        # Apply department filter if provided
        if department:
            department_obj = db.query(Department).filter(
                Department.name == department,
                Department.business_id == business_id if business_id else True
            ).first()
            if department_obj:
                attendance_query = attendance_query.filter(Employee.department_id == department_obj.id)
        
        attendance_records = attendance_query.all()
        
        # If no data available, return empty structure
        if not attendance_records:
            return AttendancePieChartResponse(
                attendance_chart={
                    "labels": [],
                    "data": [],
                    "colors": []
                },
                late_comers_chart={
                    "labels": [],
                    "data": [],
                    "colors": []
                },
                early_goers_chart={
                    "labels": [],
                    "data": [],
                    "colors": []
                }
            )
        
        # Count attendance statuses from real data using correct enum values
        presents = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.PRESENT])
        absents = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.ABSENT])
        leaves = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.ON_LEAVE])
        weekoffs = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.WEEKEND])
        holidays = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.HOLIDAY])
        half_days = len([r for r in attendance_records if r.attendance_status == AttendanceStatus.HALF_DAY])
        
        # Add half days to presents for chart display
        presents += half_days
        
        # Late comers data from real data
        late_comers = len([r for r in attendance_records if r.is_late])
        on_time_attendance = max(0, presents - late_comers)
        
        # Early goers data from real data
        early_goers = len([r for r in attendance_records if r.is_early_out])
        on_time_departure = max(0, presents - early_goers)
        
        # Format data for Chart.js
        attendance_chart = {
            "labels": ["Presents", "Leaves", "Absents", "WeekOffs", "Holidays"],
            "data": [presents, leaves, absents, weekoffs, holidays],
            "colors": ["#3b82f6", "#fde68a", "#ef4444", "#6b7280", "#22c55e"]
        }
        
        late_comers_chart = {
            "labels": ["On-Time", "Late Comers"],
            "data": [on_time_attendance, late_comers],
            "colors": ["#3b82f6", "#fbbf24"]
        }
        
        early_goers_chart = {
            "labels": ["On-Time", "Early Goers"],
            "data": [on_time_departure, early_goers],
            "colors": ["#3b82f6", "#fbbf24"]
        }
        
        return AttendancePieChartResponse(
            attendance_chart=attendance_chart,
            late_comers_chart=late_comers_chart,
            early_goers_chart=early_goers_chart
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance pie charts: {str(e)}"
        )


@router.get("/attendance/filters", response_model=AttendanceFiltersResponse)
async def get_attendance_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get filter options for attendance dashboard
    
    **Returns:**
    - Available locations, departments, date options, top-N options
    - Used for dropdown filters in frontend
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get locations from database only
        locations = []
        location_query = db.query(Location).filter(Location.is_active == True)
        if business_id:
            location_query = location_query.filter(Location.business_id == business_id)
        locations.extend([l.name for l in location_query.all()])
        
        # Get departments from database only
        departments = []
        dept_query = db.query(Department).filter(Department.is_active == True)
        if business_id:
            dept_query = dept_query.filter(Department.business_id == business_id)
        departments.extend([d.name for d in dept_query.all()])
        
        # Date options - dynamic based on available data
        date_options = []
        today = datetime.now().date()
        date_options.extend([
            today.strftime("%Y-%m-%d"),
            (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            (today - timedelta(days=30)).strftime("%Y-%m-%d")
        ])
        
        # Top-N options
        top_options = ["Top-10", "Top 20", "Top 50", "All"]
        
        return AttendanceFiltersResponse(
            locations=locations,
            departments=departments,
            date_options=date_options,
            top_options=top_options
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance filters: {str(e)}"
        )

@router.get("/attendance/employees/early-departure", response_model=AttendanceEmployeeListResponse)
async def get_early_departure_employees(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    location: Optional[str] = Query(None, description="Filter by location"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(10, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of employees who left early for a specific date
    """
    try:
        target_date = date if date else datetime.now().date()
        business_id = get_user_business_id(current_user, db)
        
        # Query early departure employees with proper join and filtering
        query = db.query(Employee).join(
            AttendanceRecord,
            and_(
                Employee.id == AttendanceRecord.employee_id,
                AttendanceRecord.attendance_date == target_date
            )
        ).filter(
            AttendanceRecord.is_early_out == True
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        if location:
            # Convert location name to location_id
            location_obj = db.query(Location).filter(
                Location.name == location,
                Location.business_id == business_id if business_id else True
            ).first()
            if location_obj:
                query = query.filter(Employee.location_id == location_obj.id)
        
        if department:
            # Convert department name to department_id
            department_obj = db.query(Department).filter(
                Department.name == department,
                Department.business_id == business_id if business_id else True
            ).first()
            if department_obj:
                query = query.filter(Employee.department_id == department_obj.id)
        
        employees = query.limit(limit).all()
        
        # Convert real employees to response format
        employee_records = []
        for emp in employees:
            # Get attendance record for this employee
            attendance = db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.attendance_date == target_date
            ).first()
            
            employee_records.append(create_attendance_employee_record(emp, attendance, "early_departure"))
        
        return AttendanceEmployeeListResponse(
            employees=employee_records,
            total=len(employee_records),
            date=str(target_date),
            filters={"location": location, "department": department, "limit": limit}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch early departure employees: {str(e)}"
        )