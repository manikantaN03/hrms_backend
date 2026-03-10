"""
Request Management API Endpoints
Complete request management and workflow API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.utils.business_unit_utils import get_user_business_context
from app.models.user import User
from app.models.employee import Employee
from app.models.location import Location
from app.models.requests import (
    Request, LeaveRequest, MissedPunchRequest, ClaimRequest, CompoffRequest,
    TimeRelaxationRequest, VisitPunchRequest, WorkflowRequest, HelpdeskRequest,
    StrikeExemptionRequest, ShiftRosterRequest, RequestStatus, RequestType
)
from app.models.attendance import ShiftRoster
from app.schemas.requests import (
    RequestCreate, RequestUpdate, RequestResponse, RequestWithDetails,
    LeaveRequestCreate, LeaveRequestResponse, MissedPunchRequestCreate,
    ClaimRequestCreate, CompoffRequestCreate, TimeRelaxationRequestCreate,
    VisitPunchRequestCreate, HelpdeskRequestCreate, ShiftRosterCreate,
    ShiftRosterUpdate, ShiftRosterResponse, ShiftRosterRequestCreate,
    RequestStatistics, RequestApproval,
    StrikeExemptionRequestCreate, WeekRosterRequestCreate, WorkflowRequestCreate,
    ApprovalActionRequest, RejectionActionRequest,
    APIResponse, APIListResponse, APIErrorResponse
)
from app.schemas.requests_additional import (
    MissedPunchRequestUpdate,
    RequestApprovalRequest,
    RequestRejectionRequest,
    StrikeExemptionRequestCreate as StrikeExemptionCreate,
    WeekRosterRequestCreate as WeekRosterCreate,
    WorkflowRequestCreate as WorkflowCreate,
    VisitPunchRequestUpdate,
    HelpdeskRequestCreate as HelpdeskCreate,
    ClaimRequestCreate as ClaimCreate,
    LeaveRequestCreate as LeaveCreate,
    CompOffRequestCreate,
    TimeRelaxationRequestCreate as TimeRelaxationCreate,
    MissedPunchRequestCreate as MissedPunchCreate
)

router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_requests_dashboard(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    request_type: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get requests dashboard with filtering and pagination
    
    **Returns:**
    - List of requests with pagination
    - Request statistics
    - Filter options
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Base query
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.approver)
        )
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status:
            query = query.filter(Request.status == request_status)
        
        if request_type:
            query = query.filter(Request.request_type == request_type)
        
        if employee_id:
            query = query.filter(Request.employee_id == employee_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response
        request_list = []
        for req in requests:
            request_data = {
                "id": req.id,
                "request_type": req.request_type.value,
                "title": req.title,
                "description": req.description,
                "status": req.status.value,
                "priority": req.priority,
                "request_date": req.request_date.isoformat(),
                "from_date": req.from_date.isoformat() if req.from_date else None,
                "to_date": req.to_date.isoformat() if req.to_date else None,
                "employee_name": f"{req.employee.first_name} {req.employee.last_name}" if req.employee else None,
                "employee_code": req.employee.employee_code if req.employee else None,
                "approver_name": f"{req.approver.first_name} {req.approver.last_name}" if req.approver else None,
                "created_at": req.created_at.isoformat(),
                "amount": float(req.amount) if req.amount else None
            }
            request_list.append(request_data)
        
        # Get statistics
        stats_query = db.query(Request)
        if business_id:
            stats_query = stats_query.filter(Request.business_id == business_id)
        
        total_requests = stats_query.count()
        pending_requests = stats_query.filter(Request.status == RequestStatus.PENDING).count()
        approved_requests = stats_query.filter(Request.status == RequestStatus.APPROVED).count()
        rejected_requests = stats_query.filter(Request.status == RequestStatus.REJECTED).count()
        
        dashboard_data = {
            "requests": request_list,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "statistics": {
                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "approved_requests": approved_requests,
                "rejected_requests": rejected_requests
            },
            "filters": {
                "available_statuses": [status.value for status in RequestStatus],
                "available_types": [req_type.value for req_type in RequestType]
            }
        }
        
        return APIResponse(
            success=True,
            message="Requests dashboard data retrieved successfully",
            data=dashboard_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch requests: {str(e)}"
        )


@router.get("/locations", response_model=APIResponse)
async def get_request_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available locations for request filtering
    
    **Returns:**
    - List of locations available for filtering requests
    - Includes "All Locations" option for no filtering
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Query unique location names using DISTINCT to avoid duplicates at database level
        query = db.query(Location.name).filter(
            Location.is_active == True,
            Location.name.isnot(None),
            Location.name != ''
        ).distinct()
        
        if business_id:
            query = query.filter(Location.business_id == business_id)
        
        location_results = query.order_by(Location.name).all()
        
        # Extract location names and build final list
        unique_location_names = [result[0] for result in location_results if result[0] and result[0].strip()]
        
        # Build final location list with "All Locations" as first option
        sorted_locations = ["All Locations"] + unique_location_names
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(unique_location_names)} unique locations successfully",
            data={
                "locations": sorted_locations,
                "total_locations": len(unique_location_names)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch locations: {str(e)}"
        )


@router.get("/detail/{request_id}", response_model=Dict[str, Any])
async def get_request_by_id(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single request by ID with all details
    
    **Returns:**
    - Complete request information
    - Request-specific details (helpdesk, leave, etc.)
    - Employee information
    - Approval information
    """
    try:
        # Use hybrid business context
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        # Query request with relationships
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.approver),
            joinedload(Request.approved_by_employee)
        ).filter(Request.id == request_id)
        
        # Apply business filter for non-superadmin users
        if not is_superadmin and business_id:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found or not accessible"
            )
        
        # Build base response
        response_data = {
            "id": request_obj.id,
            "business_id": request_obj.business_id,
            "employee_id": request_obj.employee_id,
            "request_type": request_obj.request_type.value,
            "title": request_obj.title,
            "description": request_obj.description,
            "status": request_obj.status.value,
            "priority": request_obj.priority,
            "request_date": request_obj.request_date.isoformat() if request_obj.request_date else None,
            "from_date": request_obj.from_date.isoformat() if request_obj.from_date else None,
            "to_date": request_obj.to_date.isoformat() if request_obj.to_date else None,
            "approved_date": request_obj.approved_date.isoformat() if request_obj.approved_date else None,
            "approval_comments": request_obj.approval_comments,
            "amount": float(request_obj.amount) if request_obj.amount else None,
            "attachment_url": request_obj.attachment_url,
            "created_at": request_obj.created_at.isoformat() if request_obj.created_at else None,
            "updated_at": request_obj.updated_at.isoformat() if request_obj.updated_at else None,
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "employee_code": request_obj.employee.employee_code if request_obj.employee else None,
            "approver_name": f"{request_obj.approver.first_name} {request_obj.approver.last_name}" if request_obj.approver else None,
            "approved_by_name": f"{request_obj.approved_by_employee.first_name} {request_obj.approved_by_employee.last_name}" if request_obj.approved_by_employee else None
        }
        
        # Add request-specific details based on type
        if request_obj.request_type == RequestType.HELPDESK:
            helpdesk_details = db.query(HelpdeskRequest).filter(
                HelpdeskRequest.request_id == request_id
            ).first()
            
            if helpdesk_details:
                response_data.update({
                    "category": helpdesk_details.category,
                    "subcategory": helpdesk_details.subcategory,
                    "issue_type": helpdesk_details.issue_type,
                    "urgency": helpdesk_details.urgency,
                    "asset_tag": helpdesk_details.asset_tag,
                    "location": helpdesk_details.location
                })
        
        elif request_obj.request_type == RequestType.LEAVE:
            leave_details = db.query(LeaveRequest).filter(
                LeaveRequest.request_id == request_id
            ).first()
            
            if leave_details:
                response_data.update({
                    "leave_type": leave_details.leave_type,
                    "total_days": leave_details.total_days,
                    "half_day": leave_details.half_day,
                    "reason": leave_details.reason,
                    "emergency_contact": leave_details.emergency_contact,
                    "emergency_phone": leave_details.emergency_phone
                })
        
        elif request_obj.request_type == RequestType.MISSED_PUNCH:
            missed_punch_details = db.query(MissedPunchRequest).filter(
                MissedPunchRequest.request_id == request_id
            ).first()
            
            if missed_punch_details:
                response_data.update({
                    "missed_date": missed_punch_details.missed_date.isoformat() if missed_punch_details.missed_date else None,
                    "punch_type": missed_punch_details.punch_type,
                    "expected_time": missed_punch_details.expected_time,
                    "reason": missed_punch_details.reason
                })
        
        elif request_obj.request_type == RequestType.CLAIM:
            claim_details = db.query(ClaimRequest).filter(
                ClaimRequest.request_id == request_id
            ).first()
            
            if claim_details:
                response_data.update({
                    "claim_type": claim_details.claim_type,
                    "claim_amount": float(claim_details.claim_amount) if claim_details.claim_amount else None,
                    "expense_date": claim_details.expense_date.isoformat() if claim_details.expense_date else None,
                    "vendor_name": claim_details.vendor_name,
                    "bill_number": claim_details.bill_number,
                    "project_code": claim_details.project_code,
                    "client_name": claim_details.client_name
                })
        
        elif request_obj.request_type == RequestType.COMPOFF:
            compoff_details = db.query(CompoffRequest).filter(
                CompoffRequest.request_id == request_id
            ).first()
            
            if compoff_details:
                response_data.update({
                    "worked_date": compoff_details.worked_date.isoformat() if compoff_details.worked_date else None,
                    "worked_hours": float(compoff_details.worked_hours) if compoff_details.worked_hours else None,
                    "compoff_date": compoff_details.compoff_date.isoformat() if compoff_details.compoff_date else None,
                    "reason_for_work": compoff_details.reason_for_work
                })
        
        elif request_obj.request_type == RequestType.TIME_RELAXATION:
            time_relaxation_details = db.query(TimeRelaxationRequest).filter(
                TimeRelaxationRequest.request_id == request_id
            ).first()
            
            if time_relaxation_details:
                response_data.update({
                    "relaxation_date": time_relaxation_details.relaxation_date.isoformat() if time_relaxation_details.relaxation_date else None,
                    "requested_in_time": time_relaxation_details.requested_in_time,
                    "requested_out_time": time_relaxation_details.requested_out_time,
                    "reason": time_relaxation_details.reason
                })
        
        elif request_obj.request_type == RequestType.VISIT_PUNCH:
            visit_punch_details = db.query(VisitPunchRequest).filter(
                VisitPunchRequest.request_id == request_id
            ).first()
            
            if visit_punch_details:
                response_data.update({
                    "visit_date": visit_punch_details.visit_date.isoformat() if visit_punch_details.visit_date else None,
                    "client_name": visit_punch_details.client_name,
                    "client_address": visit_punch_details.client_address,
                    "purpose": visit_punch_details.purpose,
                    "expected_duration": visit_punch_details.expected_duration
                })
        
        return response_data
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch request: {str(e)}"
        )



@router.get("/leave", response_model=APIListResponse)
async def get_leave_requests(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    request_status: Optional[str] = Query(None, alias="status"),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all leave requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    - employee_id: Filter by specific employee
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 10, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Query actual leave requests from database
        query = db.query(Request).options(
            joinedload(Request.employee).joinedload(Employee.location),
            joinedload(Request.leave_details)
        ).filter(Request.request_type == RequestType.LEAVE)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
            else:
                # Map other status values to proper enum
                status_mapping = {
                    "approved": RequestStatus.APPROVED,
                    "rejected": RequestStatus.REJECTED,
                    "pending": RequestStatus.PENDING,
                    "in_review": RequestStatus.IN_REVIEW
                }
                mapped_status = status_mapping.get(request_status.lower())
                if mapped_status:
                    query = query.filter(Request.status == mapped_status)
        
        if location and location != "All Locations":
            # Join with Employee and Location to filter by actual location
            query = query.join(Employee, Request.employee_id == Employee.id)\
                         .join(Location, Employee.location_id == Location.id)\
                         .filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.from_date >= date_from)
        if date_to:
            query = query.filter(Request.to_date <= date_to)
        
        if search:
            query = query.join(Employee, Request.employee_id == Employee.id).filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
        
        if employee_id:
            query = query.filter(Request.employee_id == employee_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        leave_requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        result = []
        for req in leave_requests:
            # Get leave details
            leave_detail = req.leave_details[0] if req.leave_details else None
            
            # Format date range
            date_range = ""
            if req.from_date:
                if req.to_date and req.from_date != req.to_date:
                    date_range = f"{req.from_date.strftime('%b %d, %Y')} - {req.to_date.strftime('%b %d, %Y')}"
                else:
                    date_range = req.from_date.strftime('%b %d, %Y')
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            leave_data = {
                "id": req.id,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "daterange": date_range,
                "leavetype": leave_detail.leave_type if leave_detail else "General Leave",
                "comment": leave_detail.reason if leave_detail else req.description or "No comment provided",
                "requestedOn": req.request_date.strftime('%b %d, %Y'),
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": req.employee.location.name if req.employee and req.employee.location else "Unknown Location",
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "employee_name": f"{req.employee.first_name} {req.employee.last_name}" if req.employee else None,
                "employee_code": req.employee.employee_code if req.employee else None,
                "from_date": req.from_date.isoformat() if req.from_date else None,
                "to_date": req.to_date.isoformat() if req.to_date else None,
                "total_days": leave_detail.total_days if leave_detail else 1,
                "half_day": leave_detail.half_day if leave_detail else False,
                "emergency_contact": leave_detail.emergency_contact if leave_detail else None,
                "emergency_phone": leave_detail.emergency_phone if leave_detail else None,
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            
            result.append(leave_data)
        
        return APIListResponse(
            success=True,
            message=f"Retrieved {len(result)} leave requests successfully",
            data=result,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leave requests: {str(e)}"
        )


@router.get("/claims", response_model=APIListResponse)
async def get_claim_requests(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all claim requests with filtering and pagination
    
    **Filters:**
    - status: Filter by request status (pending, approved, rejected)
    - employee_id: Filter by specific employee
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 10, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        # Query actual claim requests from database
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.claim_details)
        ).filter(Request.request_type == RequestType.CLAIM)
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status:
            query = query.filter(Request.status == request_status)
        if employee_id:
            query = query.filter(Request.employee_id == employee_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        claim_requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response
        result = []
        for req in claim_requests:
            claim_data = {
                "id": req.id,
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "employee_name": f"{req.employee.first_name} {req.employee.last_name}" if req.employee else None,
                "employee_code": req.employee.employee_code if req.employee else None,
                "request_type": req.request_type.value,
                "title": req.title,
                "description": req.description,
                "status": req.status.value,
                "request_date": req.request_date.isoformat(),
                "from_date": req.from_date.isoformat() if req.from_date else None,
                "amount": float(req.amount) if req.amount else None,
                "priority": req.priority,
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            
            # Add claim-specific details if available
            if hasattr(req, 'claim_details') and req.claim_details:
                for detail in req.claim_details:
                    claim_data.update({
                        "claim_type": detail.claim_type,
                        "claim_amount": float(detail.claim_amount),
                        "expense_date": detail.expense_date.isoformat(),
                        "vendor_name": detail.vendor_name,
                        "bill_number": detail.bill_number,
                        "project_code": detail.project_code,
                        "client_name": detail.client_name,
                        "currency": "INR"
                    })
                    break  # Take first detail record
            
            result.append(claim_data)
        
        return APIListResponse(
            success=True,
            message=f"Retrieved {len(result)} claim requests successfully",
            data=result,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch claim requests: {str(e)}"
        )


@router.get("/claim-requests", response_model=List[Dict[str, Any]])
async def get_claim_requests_frontend(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None, alias="status"),
    location: Optional[str] = Query(None),
    component: Optional[str] = Query(None),  # Claim type filter
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get claim requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by employee location
    - component: Filter by claim type (Travel, Medical, Food, etc.)
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.claim_details)
        ).filter(Request.request_type == RequestType.CLAIM)
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            else:
                query = query.filter(Request.status == request_status.lower())
        
        if location and location != "All Locations":
            # Filter by employee location using proper join
            query = query.join(Employee, Request.employee_id == Employee.id).join(
                Location, Employee.location_id == Location.id
            ).filter(Location.name == location)
        
        if component and component != "All Component":
            # Filter by claim type using join with claim_details
            from app.models.requests import ClaimRequest
            query = query.join(ClaimRequest, Request.id == ClaimRequest.request_id).filter(
                ClaimRequest.claim_type == component
            )
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.filter(
                Request.employee.has(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            )
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            claim_details = req.claim_details[0] if req.claim_details else None
            
            # Format date as expected by frontend
            date_formatted = req.request_date.strftime('%b %d, %Y %H:%M:%S') if req.request_date else "N/A"
            if claim_details and claim_details.expense_date:
                date_formatted = claim_details.expense_date.strftime('%b %d, %Y') + " 18:00:00"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            # Create claim note from claim details
            claim_note = req.description or "Claim request"
            if claim_details:
                claim_note = f"{claim_details.claim_type} claim for ₹{claim_details.claim_amount}"
                if claim_details.vendor_name:
                    claim_note += f" from {claim_details.vendor_name}"
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": claim_note,
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": location or "Hyderabad",  # Default location
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "claim_type": claim_details.claim_type if claim_details else "General",
                "claim_amount": float(claim_details.claim_amount) if claim_details else 0.0,
                "expense_date": claim_details.expense_date.isoformat() if claim_details and claim_details.expense_date else None,
                "vendor_name": claim_details.vendor_name if claim_details else None,
                "bill_number": claim_details.bill_number if claim_details else None,
                "project_code": claim_details.project_code if claim_details else None,
                "client_name": claim_details.client_name if claim_details else None,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch claim requests: {str(e)}"
        )


@router.put("/claim-requests/{request_id}/approve", response_model=APIResponse)
async def approve_claim_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a claim request
    
    **Updates:**
    - Claim request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find claim request
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.CLAIM
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Claim request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Claim request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments,
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "request_title": request_obj.title,
            "claim_amount": float(request_obj.amount) if request_obj.amount else None
        }
        
        return APIResponse(
            success=True,
            message="Claim request approved successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve claim request: {str(e)}"
        )


@router.put("/claim-requests/{request_id}/reject", response_model=APIResponse)
async def reject_claim_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a claim request
    
    **Updates:**
    - Claim request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find claim request
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.CLAIM
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Claim request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Claim request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": employee_id,
            "rejected_date": request_obj.approved_date.isoformat(),
            "rejection_comments": request_obj.approval_comments,
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "request_title": request_obj.title,
            "claim_amount": float(request_obj.amount) if request_obj.amount else None
        }
        
        return APIResponse(
            success=True,
            message="Claim request rejected successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject claim request: {str(e)}"
        )


@router.delete("/claim-requests/{request_id}", response_model=APIResponse)
async def delete_claim_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a claim request
    
    **Deletes:**
    - Claim request and associated details
    - Claim details if any
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        # Find claim request
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.CLAIM
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Claim request not found"
            )
        
        # Store request details for response
        employee_name = f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else "Unknown Employee"
        request_title = request_obj.title
        claim_amount = float(request_obj.amount) if request_obj.amount else None
        
        # Delete associated claim details first
        if request_obj.claim_details:
            for detail in request_obj.claim_details:
                db.delete(detail)
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "employee_name": employee_name,
            "request_title": request_title,
            "claim_amount": claim_amount,
            "deleted_at": datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Claim request deleted successfully",
            data=response_data
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete claim request: {str(e)}"
        )


@router.post("/leave", response_model=APIResponse)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new leave request
    
    **Creates:**
    - Leave request with specified details
    - Automatic approval workflow
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id (e.g., superadmin), use the first active employee for testing
        if not employee_id:
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id,
                Employee.employee_status == "active"
            ).first()
            
            if first_employee:
                employee_id = first_employee.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active employee found to create request for"
                )
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.LEAVE,
            title=f"Leave Request - {leave_data.leave_type}",
            description=leave_data.reason,
            from_date=leave_data.from_date,
            to_date=leave_data.to_date,
            status=RequestStatus.PENDING,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create leave details
        leave_details = LeaveRequest(
            request_id=new_request.id,
            leave_type=leave_data.leave_type,
            total_days=leave_data.total_days,
            half_day=leave_data.half_day,
            reason=leave_data.reason,
            emergency_contact=leave_data.emergency_contact,
            emergency_phone=leave_data.emergency_phone
        )
        
        db.add(leave_details)
        db.commit()
        
        # Prepare response data
        response_data = {
            "request_id": new_request.id,
            "request_type": new_request.request_type.value,
            "title": new_request.title,
            "status": new_request.status.value,
            "from_date": new_request.from_date.isoformat(),
            "to_date": new_request.to_date.isoformat(),
            "leave_type": leave_data.leave_type,
            "total_days": leave_data.total_days,
            "half_day": leave_data.half_day,
            "reason": leave_data.reason,
            "created_at": new_request.created_at.isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Leave request created successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create leave request: {str(e)}"
        )


@router.post("/missed-punch", response_model=APIResponse)
async def create_missed_punch_request(
    punch_data: MissedPunchRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a missed punch request
    
    **Creates:**
    - Missed punch correction request
    - Attendance correction workflow
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id (e.g., superadmin), use the first active employee for testing
        if not employee_id:
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id,
                Employee.employee_status == "active"
            ).first()
            
            if first_employee:
                employee_id = first_employee.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active employee found to create request for"
                )
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.MISSED_PUNCH,
            title=f"Missed Punch - {punch_data.punch_type.title()} on {punch_data.missed_date}",
            description=punch_data.reason,
            from_date=punch_data.missed_date,
            status=RequestStatus.PENDING,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create missed punch details
        punch_details = MissedPunchRequest(
            request_id=new_request.id,
            missed_date=punch_data.missed_date,
            punch_type=punch_data.punch_type,
            expected_time=punch_data.expected_time,
            reason=punch_data.reason
        )
        
        db.add(punch_details)
        db.commit()
        
        # Prepare response data
        response_data = {
            "request_id": new_request.id,
            "request_type": new_request.request_type.value,
            "title": new_request.title,
            "status": new_request.status.value,
            "missed_date": punch_data.missed_date.isoformat(),
            "punch_type": punch_data.punch_type,
            "expected_time": punch_data.expected_time,
            "reason": punch_data.reason,
            "created_at": new_request.created_at.isoformat(),
            "employee_id": employee_id
        }
        
        return APIResponse(
            success=True,
            message="Missed punch request created successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create missed punch request: {str(e)}"
        )


@router.post("/claim", response_model=APIResponse)
async def create_claim_request(
    claim_data: ClaimRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a claim/expense request
    
    **Creates:**
    - Expense claim request
    - Reimbursement workflow
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Get employee_id - priority: request data > current user > fallback
        employee_id = getattr(current_user, 'employee_id', None)  # is_superadmin already set
        
        # If admin user provided employee_id in request, use that
        if hasattr(claim_data, 'employee_id') and claim_data.employee_id:
            # For superadmin users, allow employees from any business
            if is_superadmin:
                target_employee = db.query(Employee).filter(
                    Employee.id == claim_data.employee_id,
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
                
                if not target_employee:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Selected employee not found or not active"
                    )
            else:
                # For regular admin users, validate business context
                target_employee = db.query(Employee).filter(
                    Employee.id == claim_data.employee_id,
                    Employee.business_id == business_id,
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
                
                if not target_employee:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Selected employee not found or not active in this business"
                    )
            
            employee_id = claim_data.employee_id
            # Update business_id to match the selected employee's business for superadmin
            if is_superadmin:
                business_id = target_employee.business_id
        
        elif not employee_id:
            # For superadmin users without employee_id, get the first active employee as fallback
            if is_superadmin:
                first_employee = db.query(Employee).filter(
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
            else:
                first_employee = db.query(Employee).filter(
                    Employee.business_id == business_id,
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
            
            if not first_employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active employees found"
                )
            
            employee_id = first_employee.id
            # Update business_id to match the selected employee's business for superadmin
            if is_superadmin:
                business_id = first_employee.business_id
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.CLAIM,
            title=f"Claim Request - {claim_data.claim_type}",
            description=f"Amount: {claim_data.claim_amount}",
            from_date=claim_data.expense_date,
            amount=claim_data.claim_amount,
            status=RequestStatus.PENDING,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create claim details
        claim_details = ClaimRequest(
            request_id=new_request.id,
            claim_type=claim_data.claim_type,
            claim_amount=claim_data.claim_amount,
            expense_date=claim_data.expense_date,
            vendor_name=claim_data.vendor_name,
            bill_number=claim_data.bill_number,
            project_code=claim_data.project_code,
            client_name=claim_data.client_name
        )
        
        db.add(claim_details)
        db.commit()
        
        # Prepare response data
        response_data = {
            "request_id": new_request.id,
            "request_type": new_request.request_type.value,
            "title": new_request.title,
            "status": new_request.status.value,
            "claim_type": claim_data.claim_type,
            "claim_amount": float(claim_data.claim_amount),
            "expense_date": claim_data.expense_date.isoformat(),
            "vendor_name": claim_data.vendor_name,
            "bill_number": claim_data.bill_number,
            "project_code": claim_data.project_code,
            "client_name": claim_data.client_name,
            "created_at": new_request.created_at.isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Claim request created successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create claim request: {str(e)}"
        )


@router.post("/compoff", response_model=RequestResponse)
async def create_compoff_request(
    compoff_data: CompoffRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a compensatory off request
    
    **Creates:**
    - Comp-off request for overtime work
    - Leave credit workflow
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id (e.g., superadmin), use the first active employee for testing
        if not employee_id:
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id,
                Employee.employee_status == "active"
            ).first()
            
            if first_employee:
                employee_id = first_employee.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active employee found to create request for"
                )
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.COMPOFF,
            title=f"Comp-off Request for {compoff_data.worked_date}",
            description=compoff_data.reason_for_work,
            from_date=compoff_data.compoff_date,
            status=RequestStatus.PENDING
        )
        
        db.add(new_request)
        db.flush()
        
        # Create compoff details
        compoff_details = CompoffRequest(
            request_id=new_request.id,
            worked_date=compoff_data.worked_date,
            worked_hours=compoff_data.worked_hours,
            compoff_date=compoff_data.compoff_date,
            reason_for_work=compoff_data.reason_for_work
        )
        
        db.add(compoff_details)
        db.commit()
        
        return RequestResponse.from_orm(new_request)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comp-off request: {str(e)}"
        )


@router.post("/time-relaxation", response_model=RequestResponse)
async def create_time_relaxation_request(
    time_data: TimeRelaxationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a time relaxation request
    
    **Creates:**
    - Flexible timing request
    - Schedule adjustment workflow
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.TIME_RELAXATION,
            title=f"Time Relaxation for {time_data.relaxation_date}",
            description=time_data.reason,
            from_date=time_data.relaxation_date,
            status=RequestStatus.PENDING
        )
        
        db.add(new_request)
        db.flush()
        
        # Create time relaxation details
        time_details = TimeRelaxationRequest(
            request_id=new_request.id,
            relaxation_date=time_data.relaxation_date,
            requested_in_time=time_data.requested_in_time,
            requested_out_time=time_data.requested_out_time,
            reason=time_data.reason
        )
        
        db.add(time_details)
        db.commit()
        
        return RequestResponse.from_orm(new_request)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create time relaxation request: {str(e)}"
        )


@router.post("/helpdesk", response_model=RequestResponse)
async def create_helpdesk_request(
    helpdesk_data: HelpdeskRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a helpdesk ticket
    
    **Creates:**
    - IT/HR support ticket
    - Issue resolution workflow
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        print(f"🔍 Debug - Current user: {current_user.id}")
        print(f"🔍 Debug - Business context: {business_context}")
        print(f"🔍 Debug - Employee ID from user: {employee_id}")
        print(f"🔍 Debug - Helpdesk data: {helpdesk_data}")
        
        # If admin user provides employee_id, use that instead of current user's employee_id
        target_employee_id = helpdesk_data.employee_id if helpdesk_data.employee_id else employee_id
        
        # For superadmin without employee_id, get the first business and first employee
        if not business_id and is_superadmin:
            from app.models.business import Business
            from app.models.employee import Employee
            
            # Get first business
            first_business = db.query(Business).first()
            if not first_business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No business found in the system"
                )
            business_id = first_business.id
            
            # If no employee_id provided, get the first active employee from this business
            if not target_employee_id:
                first_employee = db.query(Employee).filter(
                    Employee.business_id == business_id,
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
                
                if not first_employee:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No active employee found in the business"
                    )
                target_employee_id = first_employee.id
        
        # Ensure we have required values
        if not business_id:
            # For non-superadmin users, get business_id from the target employee
            if target_employee_id:
                from app.models.employee import Employee
                target_employee = db.query(Employee).filter(Employee.id == target_employee_id).first()
                if target_employee:
                    business_id = target_employee.business_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Employee not found"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Business ID is required. Please contact administrator."
                )
        
        if not target_employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID is required. Please contact administrator."
            )
        
        # Validate that the target employee exists and belongs to the same business (if not superadmin)
        from app.models.employee import Employee
        employee_query = db.query(Employee).filter(Employee.id == target_employee_id)
        if not is_superadmin:  # Non-superadmin users
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        target_employee = employee_query.first()
        if not target_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found or not accessible"
            )
        
        # Use the employee's business_id to ensure consistency
        business_id = target_employee.business_id
        
        # Validate required fields
        if not helpdesk_data.category or not helpdesk_data.category.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category is required"
            )
        
        if not helpdesk_data.issue_type or not helpdesk_data.issue_type.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Issue type is required"
            )
        
        if not helpdesk_data.urgency or helpdesk_data.urgency not in ['low', 'medium', 'high', 'critical']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid urgency level is required (low, medium, high, critical)"
            )
        
        # Create main request with all required fields
        new_request = Request(
            business_id=business_id,
            employee_id=target_employee_id,
            request_type=RequestType.HELPDESK,
            title=f"Helpdesk - {helpdesk_data.category.strip()}: {helpdesk_data.issue_type.strip()}",
            description=f"Category: {helpdesk_data.category.strip()}, Issue: {helpdesk_data.issue_type.strip()}",
            priority=helpdesk_data.urgency,
            status=RequestStatus.PENDING,
            request_date=date.today()  # Ensure request_date is set
        )
        
        db.add(new_request)
        db.flush()
        
        print(f"✅ Request created with ID: {new_request.id}")
        
        # Create helpdesk details
        helpdesk_details = HelpdeskRequest(
            request_id=new_request.id,
            category=helpdesk_data.category.strip(),
            subcategory=helpdesk_data.subcategory.strip() if helpdesk_data.subcategory else None,
            issue_type=helpdesk_data.issue_type.strip(),
            urgency=helpdesk_data.urgency,
            asset_tag=helpdesk_data.asset_tag.strip() if helpdesk_data.asset_tag else None,
            location=helpdesk_data.location.strip() if helpdesk_data.location else None
        )
        
        db.add(helpdesk_details)
        print(f"✅ Helpdesk details created for request ID: {new_request.id}")
        
        db.commit()
        print(f"✅ Transaction committed successfully")
        
        return RequestResponse.from_orm(new_request)
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        print(f"❌ Helpdesk creation error: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        print(f"❌ Helpdesk data: {helpdesk_data}")
        print(f"❌ Business context: {business_context}")
        print(f"❌ Target employee ID: {target_employee_id}")
        print(f"❌ Business ID: {business_id}")
        
        # More specific error messages
        error_msg = str(e).lower()
        if "null value" in error_msg and "violates not-null constraint" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field. Please ensure all required fields are filled."
            )
        elif "foreign key constraint" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reference. Please check employee and business information."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create helpdesk request: {str(e)}"
            )


@router.put("/{request_id}/approve", response_model=RequestResponse)
async def approve_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve or reject a request
    
    **Updates:**
    - Request status
    - Approval details
    - Workflow progression
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        # Update request
        request_obj.status = RequestStatus(approval_data.status)
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return RequestResponse.from_orm(request_obj)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve request: {str(e)}"
        )


@router.put("/leave/{request_id}/approve", response_model=APIResponse)
async def approve_leave_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a leave request
    
    **Updates:**
    - Leave request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find leave request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.LEAVE,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Leave request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments,
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "request_title": request_obj.title
        }
        
        return APIResponse(
            success=True,
            message="Leave request approved successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve leave request: {str(e)}"
        )


@router.put("/leave/{request_id}/reject", response_model=APIResponse)
async def reject_leave_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a leave request
    
    **Updates:**
    - Leave request status to rejected
    - Rejection reason and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find leave request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.LEAVE,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Leave request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": employee_id,
            "rejected_date": request_obj.approved_date.isoformat(),
            "rejection_comments": request_obj.approval_comments,
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "request_title": request_obj.title
        }
        
        return APIResponse(
            success=True,
            message="Leave request rejected successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject leave request: {str(e)}"
        )


@router.delete("/leave/{request_id}", response_model=APIResponse)
async def delete_leave_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a leave request
    
    **Deletes:**
    - Leave request details from leave_requests table
    - Main request from requests table
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find leave request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.LEAVE,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        # Store request details for response
        employee_name = f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else "Unknown Employee"
        request_title = request_obj.title
        
        # Delete leave details first (foreign key constraint)
        db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).delete()
        
        # Delete main request
        db.delete(request_obj)
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "employee_name": employee_name,
            "request_title": request_title,
            "deleted_at": datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            message=f"Leave request #{request_id} deleted successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete leave request: {str(e)}"
        )


@router.get("/statistics", response_model=APIResponse)
async def get_request_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get request statistics and analytics
    
    **Returns:**
    - Request counts by type and status
    - Approval metrics
    - Trend analysis
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Base query
        query = db.query(Request)
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(Request.request_date >= start_date)
        
        if end_date:
            query = query.filter(Request.request_date <= end_date)
        
        # Get basic counts
        total_requests = query.count()
        pending_requests = query.filter(Request.status == RequestStatus.PENDING).count()
        approved_requests = query.filter(Request.status == RequestStatus.APPROVED).count()
        rejected_requests = query.filter(Request.status == RequestStatus.REJECTED).count()
        
        # Get requests by type
        requests_by_type = {}
        for req_type in RequestType:
            count = query.filter(Request.request_type == req_type).count()
            requests_by_type[req_type.value] = count
        
        # Get requests by status
        requests_by_status = {}
        for req_status in RequestStatus:
            count = query.filter(Request.status == req_status).count()
            requests_by_status[req_status.value] = count
        
        statistics_data = {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "requests_by_type": requests_by_type,
            "requests_by_status": requests_by_status,
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
        
        return APIResponse(
            success=True,
            message="Request statistics retrieved successfully",
            data=statistics_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch request statistics: {str(e)}"
        )


# STRIKE EXEMPTION REQUESTS
@router.get("/strikerequests", response_model=List[Dict[str, Any]])
async def get_strike_exemption_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get strike exemption requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Approved, Rejected)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Base query
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.strike_exemption_details)
        ).filter(Request.request_type == RequestType.STRIKE_EXEMPTION)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Approved":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
        
        if location and location != "All Locations":
            # Filter by employee location using proper join
            query = query.join(Employee, Request.employee_id == Employee.id).join(
                Location, Employee.location_id == Location.id
            ).filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.filter(Request.employee.has(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            ))
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            strike_details = req.strike_exemption_details[0] if req.strike_exemption_details else None
            
            # Format date as expected by frontend
            date_formatted = req.request_date.strftime('%b %d, %Y %H:%M:%S') if req.request_date else "N/A"
            if strike_details and strike_details.strike_date:
                date_formatted = strike_details.strike_date.strftime('%b %d, %Y') + " 18:00:00"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Approved",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            # Determine strike type based on exemption reason
            strike_type = "Strike Exemption"
            if strike_details and strike_details.exemption_reason:
                reason = strike_details.exemption_reason.lower()
                if "late" in reason and "coming" in reason:
                    strike_type = "Late Coming"
                elif "early" in reason and "going" in reason:
                    strike_type = "Early Going"
                elif "late" in reason and "going" in reason:
                    strike_type = "Late Going"
                else:
                    strike_type = strike_details.exemption_reason
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": strike_details.work_justification if strike_details else req.description or "Strike exemption request",
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": location or "Hyderabad",  # Default location
                "shift": "Regular",  # Default shift
                "stricke": strike_type,  # Note: frontend uses "stricke" (typo in frontend)
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "strike_date": strike_details.strike_date.isoformat() if strike_details and strike_details.strike_date else None,
                "exemption_reason": strike_details.exemption_reason if strike_details else None,
                "work_justification": strike_details.work_justification if strike_details else req.description,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch strike exemption requests: {str(e)}"
        )


@router.post("/strikerequests", response_model=RequestResponse)
async def create_strike_exemption_request(
    strike_data: StrikeExemptionRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a strike exemption request
    
    **Creates:**
    - Strike exemption request
    - Work justification workflow
    
    **Request Body:**
    - strike_date: Required, date of the strike
    - exemption_reason: Required, reason for exemption (min 10 chars)
    - work_justification: Required, justification for working during strike (min 10 chars)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Use employee_id from request data if provided, otherwise use current user's employee_id
        if hasattr(strike_data, 'employee_id') and strike_data.employee_id:
            employee_id = strike_data.employee_id
            # Validate that the employee exists and belongs to the same business
            employee = db.query(Employee).filter(
                Employee.id == employee_id,
                Employee.is_active == True,
                Employee.business_id == business_id if business_id else True
            ).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid employee ID or employee not found"
                )
        else:
            # Use current user's employee_id
            employee_id = getattr(current_user, 'employee_id', None)
            
            # If no employee_id (e.g., superadmin), use the first active employee for testing
            if not employee_id:
                first_employee = db.query(Employee).filter(
                    Employee.is_active == True,
                    Employee.business_id == business_id if business_id else True
                ).first()
                if first_employee:
                    employee_id = first_employee.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No active employees found for request creation"
                    )
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.STRIKE_EXEMPTION,
            title=f"Strike Exemption Request - {strike_data.strike_date}",
            description=strike_data.exemption_reason,
            from_date=strike_data.strike_date,
            status=RequestStatus.PENDING,
            created_by=employee_id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create strike exemption details
        from app.models.requests import StrikeExemptionRequest
        strike_details = StrikeExemptionRequest(
            request_id=new_request.id,
            strike_date=strike_data.strike_date,
            exemption_reason=strike_data.exemption_reason,
            work_justification=strike_data.work_justification,
            department_approval=False
        )
        
        db.add(strike_details)
        db.commit()
        
        return RequestResponse.from_orm(new_request)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strike exemption request: {str(e)}"
        )


# WEEK ROSTER REQUESTS
@router.get("/weekroaster", response_model=List[Dict[str, Any]])
async def get_week_roster_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get week off roster change requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Approved, Rejected)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Base query - using WEEKOFF_ROSTER requests (not SHIFT_ROSTER)
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.weekoff_roster_details)
        ).filter(Request.request_type == RequestType.WEEKOFF_ROSTER)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Approved":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
        
        if location and location != "All Locations":
            # Filter by employee location using proper join
            query = query.join(Employee, Request.employee_id == Employee.id).join(
                Location, Employee.location_id == Location.id
            ).filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.filter(Request.employee.has(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            ))
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            weekoff_details = req.weekoff_roster_details[0] if req.weekoff_roster_details else None
            
            # Format date as expected by frontend
            date_formatted = req.request_date.strftime('%b %d, %Y %H:%M:%S') if req.request_date else "N/A"
            if weekoff_details and weekoff_details.requested_date:
                date_formatted = weekoff_details.requested_date.strftime('%b %d, %Y') + " 18:00:00"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Approved",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            # Format shift info to show weekoff change
            shift_info = "Regular"
            if weekoff_details:
                if weekoff_details.current_weekoff_day and weekoff_details.requested_weekoff_day:
                    shift_info = f"{weekoff_details.current_weekoff_day} → {weekoff_details.requested_weekoff_day}"
                else:
                    shift_info = weekoff_details.requested_weekoff_day
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": weekoff_details.reason if weekoff_details else req.description or "Week off roster change request",
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": req.employee.location.name if req.employee and req.employee.location else "N/A",
                "shift": shift_info,
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "requested_date": weekoff_details.requested_date.isoformat() if weekoff_details and weekoff_details.requested_date else None,
                "current_weekoff_day": weekoff_details.current_weekoff_day if weekoff_details else None,
                "requested_weekoff_day": weekoff_details.requested_weekoff_day if weekoff_details else None,
                "is_permanent": weekoff_details.is_permanent if weekoff_details else False,
                "effective_from": weekoff_details.effective_from.isoformat() if weekoff_details and weekoff_details.effective_from else None,
                "effective_to": weekoff_details.effective_to.isoformat() if weekoff_details and weekoff_details.effective_to else None,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch week roster requests: {str(e)}"
        )


@router.get("/weekroaster/filters", response_model=Dict[str, Any])
async def get_week_roster_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for week roster requests
    
    **Returns:**
    - Available locations from database
    - Available status options
    - Available roster types
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Default filters that will always work
        filters = {
            "locations": ["All Locations"],
            "statuses": ["All", "Open", "Approved", "Rejected"],
            "roster_types": ["Regular Week", "Night Week", "Morning Week", "Evening Week"]
        }
        
        # Try to get locations from database
        try:
            location_query = db.query(Location.name).distinct().filter(Location.is_active == True)
            if business_id:
                location_query = location_query.filter(Location.business_id == business_id)
            
            location_results = location_query.all()
            if location_results:
                dynamic_locations = ["All Locations"] + [loc.name for loc in location_results if loc.name]
                filters["locations"] = dynamic_locations
        except Exception as loc_error:
            print(f"Location query error: {loc_error}")
            # Use default locations if database query fails
            filters["locations"] = ["All Locations", "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi"]
        
        # Try to get roster types from existing requests
        try:
            roster_types_query = db.query(ShiftRosterRequest.requested_shift_type).distinct()
            roster_type_results = roster_types_query.all()
            if roster_type_results:
                dynamic_roster_types = list(set([rt.requested_shift_type for rt in roster_type_results if rt.requested_shift_type]))
                if dynamic_roster_types:
                    filters["roster_types"] = dynamic_roster_types
        except Exception as roster_error:
            print(f"Roster types query error: {roster_error}")
            # Keep default roster types
        
        return filters
        
    except Exception as e:
        # Always return default filters if anything fails
        return {
            "locations": ["All Locations", "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi"],
            "statuses": ["All", "Open", "Approved", "Rejected"],
            "roster_types": ["Regular Week", "Night Week", "Morning Week", "Evening Week"]
        }


@router.post("/weekroaster", response_model=RequestResponse)
async def create_week_roster_request(
    roster_data: WeekRosterRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a week off roster change request
    
    **Creates:**
    - Week off roster change request
    - Week off modification workflow
    
    **Request Body:**
    - employee_id: Required, employee ID
    - week_start_date: Required, start date of the week
    - week_end_date: Required, end date of the week
    - roster_type: Required, requested weekoff day (e.g., "Saturday", "Sunday")
    - notes: Required, reason for change
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Validate employee exists and belongs to business
        employee = db.query(Employee).filter(
            Employee.id == roster_data.employee_id,
            Employee.employee_status == "active"
        ).first()
        
        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee not found or inactive"
            )
        
        # Use employee's business_id if current user doesn't have one (superadmin case)
        if not business_id:
            business_id = employee.business_id
        
        # Verify employee belongs to the same business
        if business_id and employee.business_id != business_id:
            raise HTTPException(
                status_code=403,
                detail="Employee does not belong to your business"
            )
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=roster_data.employee_id,
            request_type=RequestType.WEEKOFF_ROSTER,
            title=f"Week Off Change Request - {roster_data.roster_type}",
            description=roster_data.notes or 'Week off roster change request',
            from_date=roster_data.week_start_date,
            to_date=roster_data.week_end_date,
            status=RequestStatus.PENDING,
            request_date=roster_data.week_start_date,
            priority="medium",
            created_by=getattr(current_user, 'employee_id', None) or roster_data.employee_id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create weekoff roster details
        from app.models.requests import WeekoffRosterRequest
        weekoff_details = WeekoffRosterRequest(
            request_id=new_request.id,
            requested_date=roster_data.week_start_date,
            current_weekoff_day='Sunday',  # Default, should be fetched from employee settings
            requested_weekoff_day=roster_data.roster_type,
            reason=roster_data.notes or '',
            is_permanent=False,
            effective_from=roster_data.week_start_date,
            effective_to=roster_data.week_end_date,
            department_approval=False,
            hr_approval=False
        )
        
        db.add(weekoff_details)
        db.commit()
        
        return RequestResponse.from_orm(new_request)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create week roster request: {str(e)}"
        )


# WORKFLOW REQUESTS (Frontend Compatible)
@router.get("/workflowrequest", response_model=List[Dict[str, Any]])
async def get_workflow_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    workflow: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workflow requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by workflow location
    - workflow: Filter by workflow type
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        # Base query with proper joins
        query = db.query(Request).options(
            joinedload(Request.employee).joinedload(Employee.location),
            joinedload(Request.workflow_details)
        ).filter(Request.request_type == RequestType.WORKFLOW)
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All" and request_status != "open":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
        
        if workflow and workflow != "All Workflows":
            # Join with WorkflowRequest to filter by workflow name
            query = query.join(WorkflowRequest, Request.id == WorkflowRequest.request_id).filter(
                WorkflowRequest.workflow_name.ilike(f"%{workflow}%")
            )
        
        if location and location != "All Locations":
            # Filter by employee location using proper join
            query = query.join(Employee, Request.employee_id == Employee.id).join(
                Location, Employee.location_id == Location.id
            ).filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.filter(
                Request.employee.has(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            )
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            workflow_details = req.workflow_details[0] if req.workflow_details else None
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending", 
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            # Get actual location from employee
            workflow_location = "Head Office"  # Default
            if req.employee and req.employee.location:
                workflow_location = req.employee.location.name
            
            # Format date for frontend
            date_formatted = req.request_date.strftime('%Y-%m-%d') if req.request_date else "N/A"
            
            request_data = {
                "id": req.id,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "workflow": workflow_details.workflow_name if workflow_details else "General Workflow",
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "date": date_formatted,
                "current_step": f"{workflow_details.current_step}/{workflow_details.total_steps}" if workflow_details else "1/1",
                "actions": "View Details",  # For frontend actions column
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "location": workflow_location,
                "description": req.description or "Workflow request",
                "workflow_data": workflow_details.workflow_data if workflow_details else None,
                "request_date": req.request_date.isoformat() if req.request_date else None,
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch workflow requests: {str(e)}"
        )


@router.post("/workflowrequest", response_model=RequestResponse)
async def create_workflow_request(
    workflow_data: WorkflowRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a workflow request
    
    **Creates:**
    - Custom workflow request
    - Multi-step approval process
    
    **Request Body:**
    - workflow_type: Required, type of workflow
    - title: Required, workflow title
    - description: Required, workflow description
    - priority: Optional, priority level (low/medium/high/urgent)
    - due_date: Optional, due date for completion
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.WORKFLOW,
            title=workflow_data.title,
            description=workflow_data.description,
            status=RequestStatus.PENDING,
            priority=workflow_data.priority,
            created_by=employee_id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create workflow details
        from app.models.requests import WorkflowRequest
        workflow_details = WorkflowRequest(
            request_id=new_request.id,
            workflow_name=workflow_data.workflow_type,
            current_step=1,
            total_steps=3,
            workflow_data='{}'
        )
        
        db.add(workflow_details)
        db.commit()
        
        return RequestResponse.from_orm(new_request)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow request: {str(e)}"
        )


@router.put("/workflowrequest/{request_id}/approve", response_model=APIResponse)
async def approve_workflow_request(
    request_id: int,
    approval_data: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a workflow request
    
    **Updates:**
    - Workflow request status to approved
    - Approval details and comments
    - Approval timestamp
    
    **Request Body:**
    - comments: Optional, approval comments
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find workflow request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.WORKFLOW,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Workflow request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or 'Workflow request approved'
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Workflow request approved successfully",
            data={
                "request_id": request_id,
                "status": "approved",
                "approved_by": employee_id,
                "approved_date": request_obj.approved_date.isoformat(),
                "approval_comments": request_obj.approval_comments
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve workflow request: {str(e)}"
        )


@router.put("/workflowrequest/{request_id}/reject", response_model=APIResponse)
async def reject_workflow_request(
    request_id: int,
    rejection_data: RejectionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a workflow request
    
    **Updates:**
    - Workflow request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    
    **Request Body:**
    - rejection_comments: Required, rejection reason
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find workflow request with proper business filtering
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.WORKFLOW
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Workflow request not found or not accessible"
            )
        
        # Get rejection comments from the correct field
        rejection_comments = getattr(rejection_data, 'approval_comments', None) or 'Workflow request rejected'
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = rejection_comments
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Workflow request rejected successfully",
            data={
                "request_id": request_id,
                "status": "rejected",
                "rejected_by": employee_id,
                "rejected_date": request_obj.approved_date.isoformat(),
                "rejection_comments": request_obj.approval_comments
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject workflow request: {str(e)}"
        )


@router.delete("/workflowrequest/{request_id}", response_model=APIResponse)
async def delete_workflow_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a workflow request
    
    **Deletes:**
    - Workflow request and all related data
    - Workflow details
    - Request history
    
    **Returns:**
    - Success confirmation
    - Deleted request information
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        # Find workflow request with proper business filtering
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.WORKFLOW
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Workflow request not found or not accessible"
            )
        
        # Store request info for response
        request_info = {
            "request_id": request_id,
            "workflow_name": None,
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "status": request_obj.status.value,
            "created_date": request_obj.created_at.isoformat()
        }
        
        # Get workflow details before deletion
        workflow_details = db.query(WorkflowRequest).filter(
            WorkflowRequest.request_id == request_id
        ).first()
        
        if workflow_details:
            request_info["workflow_name"] = workflow_details.workflow_name
            # Delete workflow details first (foreign key constraint)
            db.delete(workflow_details)
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Workflow request deleted successfully",
            data={
                **request_info,
                "deleted": True,
                "deleted_by": current_user.id,
                "deleted_at": datetime.now().isoformat()
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workflow request: {str(e)}"
        )


@router.get("/workflowrequest/filter-options", response_model=APIResponse)
async def get_workflow_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for workflow requests
    
    **Returns:**
    - Available locations from database
    - Available workflow types from database
    - Status options
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        
        # Get unique locations - simplified query
        locations = []
        try:
            location_query = db.query(Location.name).filter(
                Location.is_active == True,
                Location.name.isnot(None),
                Location.name != ''
            ).distinct()
            
            if business_id and not is_superadmin:
                location_query = location_query.filter(Location.business_id == business_id)
            
            location_results = location_query.limit(50).all()  # Limit to prevent timeout
            locations = [result[0] for result in location_results if result[0] and result[0].strip()]
        except Exception as e:
            print(f"Location query error: {e}")
            locations = ["Hyderabad", "Bangalore", "Chennai"]  # Fallback
        
        # Get unique workflow types - simplified query
        workflows = []
        try:
            workflow_query = db.query(WorkflowRequest.workflow_name).filter(
                WorkflowRequest.workflow_name.isnot(None),
                WorkflowRequest.workflow_name != ''
            ).distinct()
            
            workflow_results = workflow_query.limit(50).all()  # Limit to prevent timeout
            workflows = [result[0] for result in workflow_results if result[0] and result[0].strip()]
        except Exception as e:
            print(f"Workflow query error: {e}")
            workflows = ["Document Review", "Expense Approval", "Policy Review", "Project Approval"]  # Fallback
        
        # Build filter options
        filter_options = {
            "locations": ["All Locations"] + sorted(locations),
            "workflows": ["All Workflows"] + sorted(workflows),
            "statuses": ["All", "Open", "Pending", "Processing", "Completed", "Rejected"]
        }
        
        return APIResponse(
            success=True,
            message="Filter options retrieved successfully",
            data=filter_options
        )
    
    except Exception as e:
        print(f"Filter options error: {e}")
        # Return fallback data to prevent complete failure
        fallback_options = {
            "locations": ["All Locations", "Hyderabad", "Bangalore", "Chennai"],
            "workflows": ["All Workflows", "Document Review", "Expense Approval", "Policy Review", "Project Approval"],
            "statuses": ["All", "Open", "Pending", "Processing", "Completed", "Rejected"]
        }
        
        return APIResponse(
            success=True,
            message="Filter options retrieved with fallback data",
            data=fallback_options
        )


# REQUEST APPROVAL ENDPOINTS
@router.put("/strikerequests/{request_id}/approve", response_model=Dict[str, Any])
async def approve_strike_exemption_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a strike exemption request
    
    **Updates:**
    - Strike exemption request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find strike exemption request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.STRIKE_EXEMPTION,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Strike exemption request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Strike exemption request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Strike exemption request approved successfully",
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve strike exemption request: {str(e)}"
        )


@router.put("/strikerequests/{request_id}/reject", response_model=Dict[str, Any])
async def reject_strike_exemption_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a strike exemption request
    
    **Updates:**
    - Strike exemption request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find strike exemption request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.STRIKE_EXEMPTION,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Strike exemption request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Strike exemption request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Strike exemption request rejected successfully",
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": employee_id,
            "rejected_date": request_obj.approved_date.isoformat(),
            "rejection_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject strike exemption request: {str(e)}"
        )


@router.delete("/strikerequests/{request_id}", response_model=Dict[str, Any])
async def delete_strike_exemption_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a strike exemption request
    
    **Deletes:**
    - Strike exemption request and associated details
    - Strike exemption details if any
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find strike exemption request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.STRIKE_EXEMPTION,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Strike exemption request not found"
            )
        
        # Delete associated strike exemption details first
        if request_obj.strike_exemption_details:
            for detail in request_obj.strike_exemption_details:
                db.delete(detail)
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": "Strike exemption request deleted successfully",
            "request_id": request_id,
            "deleted": True
        }
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete strike exemption request: {str(e)}"
        )


@router.put("/weekroaster/{request_id}/approve", response_model=Dict[str, Any])
async def approve_week_roster_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a week off roster request
    
    **Updates:**
    - Week off roster request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find week off roster request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.WEEKOFF_ROSTER,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Week off roster request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Week off roster request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Week off roster request approved successfully",
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve week off roster request: {str(e)}"
        )


@router.put("/weekroaster/{request_id}/reject", response_model=Dict[str, Any])
async def reject_week_roster_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a week off roster request
    
    **Updates:**
    - Week off roster request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find week off roster request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.WEEKOFF_ROSTER,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Week off roster request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Week off roster request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Week off roster request rejected successfully",
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": employee_id,
            "rejected_date": request_obj.approved_date.isoformat(),
            "rejection_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject week off roster request: {str(e)}"
        )


@router.delete("/weekroaster/{request_id}", response_model=Dict[str, Any])
async def delete_week_roster_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a week off roster request
    
    **Deletes:**
    - Week off roster request and associated details
    - Weekoff roster details if any
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find week off roster request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.WEEKOFF_ROSTER,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Week off roster request not found"
            )
        
        # Delete associated weekoff roster details first
        if request_obj.weekoff_roster_details:
            for detail in request_obj.weekoff_roster_details:
                db.delete(detail)
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": "Week off roster request deleted successfully",
            "request_id": request_id,
            "deleted": True
        }
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete week off roster request: {str(e)}"
        )


# SHIFT ROSTER REQUESTS (Frontend Compatible)
@router.post("/shiftroster", response_model=Dict[str, Any])
async def create_shift_roster_request(
    request_data: ShiftRosterRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new shift roster request
    
    **Required Fields:**
    - employee_id: Employee requesting shift change
    - date_range: Date for shift change (format: "Oct 27, 2025 18:00:00")
    - shift_type: Requested shift type (General, Regular, Night, Morning, Evening)
    - note: Reason for shift change (minimum 10 characters)
    - location: Employee location (optional, defaults to Hyderabad)
    """
    try:
        # Get business ID from current user
        from app.api.v1.endpoints.master_setup import get_user_business_id
        from app.models.employee import EmployeeStatus
        business_id = get_user_business_id(current_user, db)
        
        # Validate employee exists and belongs to user's business
        employee = db.query(Employee).filter(
            Employee.id == request_data.employee_id,
            Employee.business_id == business_id,
            Employee.employee_status == EmployeeStatus.ACTIVE
        ).first()
        
        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee not found, inactive, or access denied"
            )
        
        # Parse date from frontend format
        try:
            # Convert "Oct 27, 2025 18:00:00" to date
            from datetime import datetime
            parsed_date = datetime.strptime(request_data.date_range, "%b %d, %Y %H:%M:%S").date()
        except ValueError:
            try:
                # Try alternative format
                parsed_date = datetime.strptime(request_data.date_range, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use 'Oct 27, 2025 18:00:00' or 'YYYY-MM-DD'"
                )
        
        # Validate shift type
        valid_shift_types = ["General", "Regular", "Night", "Morning", "Evening"]
        if request_data.shift_type not in valid_shift_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid shift type. Must be one of: {', '.join(valid_shift_types)}"
            )
        
        # Validate note length
        if len(request_data.note.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Note must be at least 10 characters long"
            )
        
        # Create main request record
        new_request = Request(
            business_id=business_id,
            employee_id=request_data.employee_id,
            request_type=RequestType.SHIFT_ROSTER,
            title=f"Shift Change Request - {request_data.shift_type}",
            status=RequestStatus.PENDING,
            request_date=parsed_date,
            description=request_data.note,
            created_by=current_user.id,
            created_at=datetime.now()
        )
        
        db.add(new_request)
        db.flush()  # Get the ID
        
        # Create shift roster request details
        shift_roster_details = ShiftRosterRequest(
            request_id=new_request.id,
            requested_date=parsed_date,
            current_shift_type="Regular",  # Default current shift
            requested_shift_type=request_data.shift_type,
            reason=request_data.note,
            location=request_data.location or "Hyderabad",
            is_permanent=False,  # Default to temporary
            effective_from=parsed_date,
            manager_approval=False,
            hr_approval=False
        )
        
        db.add(shift_roster_details)
        db.commit()
        
        return {
            "message": "Shift roster request created successfully",
            "request_id": new_request.id,
            "employee_id": request_data.employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "employee_code": employee.employee_code,
            "requested_date": parsed_date.isoformat(),
            "shift_type": request_data.shift_type,
            "location": request_data.location or "Hyderabad",
            "status": "pending",
            "created_at": new_request.created_at.isoformat()
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create shift roster request: {str(e)}"
        )


@router.get("/shiftroster", response_model=List[Dict[str, Any]])
async def get_shift_roster_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get shift roster requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed, Approved)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    
    def map_frontend_status_to_enum(frontend_status):
        """Map frontend status values to backend RequestStatus enum"""
        status_mapping = {
            "Open": RequestStatus.PENDING,
            "Pending": RequestStatus.IN_REVIEW,
            "Processing": RequestStatus.IN_REVIEW,
            "Completed": RequestStatus.APPROVED,
            "Approved": RequestStatus.APPROVED,  # Handle both Completed and Approved
            "Rejected": RequestStatus.REJECTED
        }
        return status_mapping.get(frontend_status)
    try:
        # Get business ID from current user (query Business table by owner_id)
        from app.api.v1.endpoints.master_setup import get_user_business_id
        business_id = get_user_business_id(current_user, db)
        
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.shift_roster_details)
        ).filter(Request.request_type == RequestType.SHIFT_ROSTER)
        
        # Always filter by business_id for security
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Approved":  # Handle "Approved" status from frontend
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
            else:
                query = query.filter(Request.status == status.lower())
        
        if location and location != "All Locations":
            # Join with Employee and Location to filter by actual location
            query = query.join(Employee, Request.employee_id == Employee.id)\
                         .join(Location, Employee.location_id == Location.id)\
                         .filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            # Use explicit join to avoid ambiguous join since we already have joinedload
            query = query.filter(Request.employee.has(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            ))
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            shift_details = req.shift_roster_details[0] if req.shift_roster_details else None
            
            # Format date as expected by frontend
            date_formatted = req.request_date.strftime('%b %d, %Y %H:%M:%S') if req.request_date else "N/A"
            if shift_details and shift_details.requested_date:
                date_formatted = shift_details.requested_date.strftime('%b %d, %Y') + " 18:00:00"
            
            # Map status to frontend format for shift roster
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Approved",  # Changed from "Completed" to "Approved"
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": shift_details.reason if shift_details else req.description or "Shift roster change request",
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": req.employee.location.name if req.employee and req.employee.location else (shift_details.location if shift_details else "Unknown Location"),
                "shift": shift_details.requested_shift_type if shift_details else "Regular",
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "requested_date": shift_details.requested_date.isoformat() if shift_details and shift_details.requested_date else None,
                "current_shift_type": shift_details.current_shift_type if shift_details else None,
                "requested_shift_type": shift_details.requested_shift_type if shift_details else "Regular",
                "is_permanent": shift_details.is_permanent if shift_details else False,
                "effective_from": shift_details.effective_from.isoformat() if shift_details and shift_details.effective_from else None,
                "effective_to": shift_details.effective_to.isoformat() if shift_details and shift_details.effective_to else None,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch shift roster requests: {str(e)}"
        )


@router.put("/shiftroster/{request_id}/approve", response_model=Dict[str, Any])
async def approve_shift_roster_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a shift roster request
    
    **Updates:**
    - Shift roster request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Get business ID from current user
        from app.api.v1.endpoints.master_setup import get_user_business_id
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find shift roster request with business_id validation
        request_obj = db.query(Request).filter(
            Request.id == request_id,
            Request.request_type == RequestType.SHIFT_ROSTER,
            Request.business_id == business_id
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Shift roster request not found or access denied"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Shift roster request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Shift roster request approved successfully",
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve shift roster request: {str(e)}"
        )


@router.put("/shiftroster/{request_id}/reject", response_model=Dict[str, Any])
async def reject_shift_roster_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a shift roster request
    
    **Updates:**
    - Shift roster request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    """
    try:
        # Get business ID from current user
        from app.api.v1.endpoints.master_setup import get_user_business_id
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find shift roster request with business_id validation
        request_obj = db.query(Request).filter(
            Request.id == request_id,
            Request.request_type == RequestType.SHIFT_ROSTER,
            Request.business_id == business_id
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Shift roster request not found or access denied"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Shift roster request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Shift roster request rejected successfully",
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": employee_id,
            "rejected_date": request_obj.approved_date.isoformat(),
            "rejection_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject shift roster request: {str(e)}"
        )


@router.delete("/shiftroster/{request_id}", response_model=Dict[str, Any])
async def delete_shift_roster_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a shift roster request
    
    **Deletes:**
    - Shift roster request and associated details
    - Only allows deletion of pending/rejected requests
    """
    try:
        # Get business ID from current user
        from app.api.v1.endpoints.master_setup import get_user_business_id
        business_id = get_user_business_id(current_user, db)
        
        # Find shift roster request with business_id validation
        request_obj = db.query(Request).filter(
            Request.id == request_id,
            Request.request_type == RequestType.SHIFT_ROSTER,
            Request.business_id == business_id
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Shift roster request not found or access denied"
            )
        
        # Check if request can be deleted (only pending or rejected requests)
        if request_obj.status == RequestStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete approved shift roster request"
            )
        
        # Delete associated shift roster details first
        if request_obj.shift_roster_details:
            for detail in request_obj.shift_roster_details:
                db.delete(detail)
        
        # Delete the request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": "Shift roster request deleted successfully",
            "request_id": request_id,
            "status": "deleted"
        }
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete shift roster request: {str(e)}"
        )


@router.get("/shiftroster/health")
async def shift_roster_health_check():
    """
    Simple health check for shift roster endpoints
    """
    return {
        "status": "healthy",
        "module": "shift_roster",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "GET /api/v1/requests/shiftroster",
            "POST /api/v1/requests/shiftroster", 
            "GET /api/v1/requests/shiftroster/filters",
            "PUT /api/v1/requests/shiftroster/{id}/approve",
            "PUT /api/v1/requests/shiftroster/{id}/reject",
            "DELETE /api/v1/requests/shiftroster/{id}"
        ]
    }


@router.get("/shiftroster/filters", response_model=Dict[str, Any])
async def get_shift_roster_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filter options for shift roster requests
    
    **Returns:**
    - Available locations from database
    - Available status options
    - Available shift types
    """
    try:
        # Get business ID from current user (query Business table by owner_id)
        from app.api.v1.endpoints.master_setup import get_user_business_id
        business_id = get_user_business_id(current_user, db)
        
        # Default filters that will always work
        filters = {
            "locations": ["All Locations", "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi"],
            "statuses": ["All", "Open", "Approved", "Rejected", "Pending", "Processing"],
            "shift_types": ["All Shifts", "General", "Regular", "Night", "Morning", "Evening"]
        }
        
        # Try to get locations from database
        try:
            location_query = db.query(Location.name).distinct()
            if business_id:
                location_query = location_query.filter(Location.business_id == business_id)
            
            location_results = location_query.all()
            if location_results:
                filters["locations"] = ["All Locations"] + [loc.name for loc in location_results if loc.name]
        except:
            pass  # Use default locations
        
        # Try to get shift types from existing requests
        try:
            shift_types_query = db.query(ShiftRosterRequest.requested_shift_type).distinct()
            shift_type_results = shift_types_query.all()
            if shift_type_results:
                shift_types = ["All Shifts"] + [st.requested_shift_type for st in shift_type_results if st.requested_shift_type]
                if len(shift_types) > 1:  # More than just "All Shifts"
                    filters["shift_types"] = shift_types
        except:
            pass  # Use default shift types
        
        return filters
        
    except Exception:
        # Always return default filters if anything fails
        return {
            "locations": ["All Locations", "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi"],
            "statuses": ["All", "Open", "Approved", "Rejected", "Pending", "Processing"],
            "shift_types": ["All Shifts", "General", "Regular", "Night", "Morning", "Evening"]
        }


# ADDITIONAL GET ENDPOINTS FOR SPECIFIC REQUEST TYPES
@router.get("/missed-punches", response_model=APIResponse)
async def get_missed_punch_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get missed punch requests with filtering and pagination"""
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        query = db.query(Request).options(
            joinedload(Request.employee).joinedload(Employee.location),
            joinedload(Request.missed_punch_details)
        ).filter(Request.request_type == RequestType.MISSED_PUNCH)
        
        # Apply business_id filtering for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Approved":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
        
        if location and location != "All Locations":
            # Join with Employee and Location to filter by actual location
            query = query.join(Employee, Request.employee_id == Employee.id)\
                         .join(Location, Employee.location_id == Location.id)\
                         .filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.join(Employee).filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        request_list = []
        for req in requests:
            punch_details = req.missed_punch_details[0] if req.missed_punch_details else None
            
            # Format date as expected by frontend
            missed_datetime = None
            if punch_details and punch_details.missed_date:
                if punch_details.expected_time:
                    missed_datetime = f"{punch_details.missed_date.strftime('%b %d, %Y')} {punch_details.expected_time}"
                else:
                    missed_datetime = f"{punch_details.missed_date.strftime('%b %d, %Y')} 09:00:00"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Processing", 
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            request_data = {
                "id": req.id,
                "date": missed_datetime or req.request_date.strftime('%b %d, %Y %H:%M:%S'),
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown",
                "note": punch_details.reason if punch_details else req.description,
                "lastUpdated": req.updated_at.strftime('%b %d, %Y %H:%M:%S') if req.updated_at else req.created_at.strftime('%b %d, %Y %H:%M:%S'),
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": req.employee.location.name if req.employee and req.employee.location else "Unknown Location",
                "punch_type": punch_details.punch_type if punch_details else "in",
                "expected_time": punch_details.expected_time if punch_details else "09:00",
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat()
            }
            request_list.append(request_data)
        
        response_data = {
            "requests": request_list,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "statistics": {
                "total_requests": total,
                "open_requests": query.filter(Request.status == RequestStatus.PENDING).count(),
                "processing_requests": query.filter(Request.status == RequestStatus.IN_REVIEW).count(),
                "completed_requests": query.filter(Request.status == RequestStatus.APPROVED).count()
            }
        }
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(request_list)} missed punch requests successfully",
            data=response_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch missed punch requests: {str(e)}"
        )


@router.get("/compoff", response_model=APIListResponse)
async def get_compoff_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None, alias="status"),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comp-off requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        query = db.query(Request).options(
            joinedload(Request.employee).joinedload(Employee.location),
            joinedload(Request.compoff_details)
        ).filter(Request.request_type == RequestType.COMPOFF)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            else:
                query = query.filter(Request.status == request_status.lower())
        
        if location and location != "All Locations":
            # Join with Employee and Location to filter by actual location
            query = query.join(Employee, Request.employee_id == Employee.id)\
                         .join(Location, Employee.location_id == Location.id)\
                         .filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            # Use explicit join to avoid ambiguous join since we already have joinedload
            query = query.filter(Request.employee.has(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            ))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            compoff_details = req.compoff_details[0] if req.compoff_details else None
            
            # Format date
            date_formatted = req.request_date.strftime('%b %d, %Y') if req.request_date else "N/A"
            
            # Format time range (using worked hours for comp-off)
            time_range = "N/A"
            if compoff_details and compoff_details.worked_hours:
                hours = float(compoff_details.worked_hours)
                time_range = f"{hours} hours worked"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "time": time_range,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": compoff_details.reason_for_work if compoff_details else req.description or "No note provided",
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": req.employee.location.name if req.employee and req.employee.location else "Unknown Location",
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "worked_date": compoff_details.worked_date.isoformat() if compoff_details and compoff_details.worked_date else None,
                "worked_hours": float(compoff_details.worked_hours) if compoff_details else 0,
                "compoff_date": compoff_details.compoff_date.isoformat() if compoff_details and compoff_details.compoff_date else None,
                "reason_for_work": compoff_details.reason_for_work if compoff_details else req.description,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return APIListResponse(
            success=True,
            message=f"Retrieved {len(request_list)} comp-off requests successfully",
            data=request_list,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch comp-off requests: {str(e)}"
        )


@router.put("/compoff/{request_id}/approve", response_model=Dict[str, Any])
async def approve_compoff_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a comp-off request
    
    **Updates:**
    - Comp-off request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find comp-off request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.COMPOFF,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Comp-off request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Comp-off request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Comp-off request approved successfully",
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve comp-off request: {str(e)}"
        )


@router.put("/compoff/{request_id}/reject", response_model=Dict[str, Any])
async def reject_compoff_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a comp-off request
    
    **Updates:**
    - Comp-off request status to rejected
    - Rejection reason and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find comp-off request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.COMPOFF,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Comp-off request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Comp-off request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Comp-off request rejected successfully",
            "request_id": request_id,
            "status": "rejected",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject comp-off request: {str(e)}"
        )


@router.delete("/compoff/{request_id}", response_model=Dict[str, Any])
async def delete_compoff_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a comp-off request
    
    **Deletes:**
    - Comp-off request and associated details
    - Only allows deletion of pending/rejected requests
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find comp-off request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.COMPOFF,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Comp-off request not found"
            )
        
        # Check if request can be deleted (only pending or rejected requests)
        if request_obj.status == RequestStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete approved comp-off request"
            )
        
        # Delete associated comp-off details first
        if request_obj.compoff_details:
            for detail in request_obj.compoff_details:
                db.delete(detail)
        
        # Delete the request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": "Comp-off request deleted successfully",
            "request_id": request_id,
            "status": "deleted"
        }
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete comp-off request: {str(e)}"
        )


@router.get("/time-relaxation", response_model=List[Dict[str, Any]])
async def get_time_relaxation_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None, alias="status"),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get time relaxation requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        query = db.query(Request).options(
            joinedload(Request.employee).joinedload(Employee.location),
            joinedload(Request.time_relaxation_details)
        ).filter(Request.request_type == RequestType.TIME_RELAXATION)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            else:
                query = query.filter(Request.status == request_status.lower())
        
        if location and location != "All Locations":
            # Join with Employee and Location to filter by actual location
            query = query.join(Employee, Request.employee_id == Employee.id)\
                         .join(Location, Employee.location_id == Location.id)\
                         .filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.join(Employee, Request.employee_id == Employee.id).filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            time_details = req.time_relaxation_details[0] if req.time_relaxation_details else None
            
            # Format date
            date_formatted = req.request_date.strftime('%b %d, %Y') if req.request_date else "N/A"
            
            # Format time range
            time_range = "N/A"
            if time_details:
                in_time = time_details.requested_in_time or "N/A"
                out_time = time_details.requested_out_time or "N/A"
                time_range = f"{in_time} to {out_time}"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "time": time_range,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": time_details.reason if time_details else req.description or "No note provided",
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": req.employee.location.name if req.employee and req.employee.location else "Unknown Location",
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "relaxation_date": time_details.relaxation_date.isoformat() if time_details and time_details.relaxation_date else None,
                "requested_in_time": time_details.requested_in_time if time_details else None,
                "requested_out_time": time_details.requested_out_time if time_details else None,
                "reason": time_details.reason if time_details else req.description,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch time relaxation requests: {str(e)}"
        )


@router.put("/time-relaxation/{request_id}/approve", response_model=Dict[str, Any])
async def approve_time_relaxation_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a time relaxation request
    
    **Updates:**
    - Time relaxation request status to approved
    - Approval details and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find time relaxation request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.TIME_RELAXATION,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Time relaxation request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Time relaxation request approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Time relaxation request approved successfully",
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve time relaxation request: {str(e)}"
        )


@router.put("/time-relaxation/{request_id}/reject", response_model=Dict[str, Any])
async def reject_time_relaxation_request(
    request_id: int,
    approval_data: RequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a time relaxation request
    
    **Updates:**
    - Time relaxation request status to rejected
    - Rejection reason and comments
    - Approval timestamp
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find time relaxation request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.TIME_RELAXATION,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Time relaxation request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or "Time relaxation request rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Time relaxation request rejected successfully",
            "request_id": request_id,
            "status": "rejected",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "approval_comments": request_obj.approval_comments
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject time relaxation request: {str(e)}"
        )


@router.delete("/time-relaxation/{request_id}", response_model=Dict[str, Any])
async def delete_time_relaxation_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a time relaxation request
    
    **Deletes:**
    - Time relaxation request details from time_relaxation_requests table
    - Main request from requests table
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find time relaxation request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.TIME_RELAXATION,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail=f"Time relaxation request #{request_id} not found or you don't have permission to delete it"
            )
        
        # Check if request can be deleted (optional business logic)
        if request_obj.status == RequestStatus.APPROVED:
            # You might want to prevent deletion of approved requests
            # Uncomment the next two lines if needed:
            # raise HTTPException(status_code=400, 
            #                   detail="Cannot delete approved requests")
            pass
        
        # Delete time relaxation details first (foreign key constraint)
        deleted_details = db.query(TimeRelaxationRequest).filter(
            TimeRelaxationRequest.request_id == request_id
        ).delete()
        
        # Delete main request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": f"Time relaxation request #{request_id} deleted successfully",
            "request_id": request_id,
            "status": "deleted",
            "deleted_details": deleted_details
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        # Log the actual error for debugging
        import logging
        logging.error(f"Error deleting time relaxation request {request_id}: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete time relaxation request #{request_id}. Please try again or contact support."
        )


# MISSED PUNCH SPECIFIC ENDPOINTS
@router.put("/missed-punches/{request_id}/approve", response_model=APIResponse)
async def approve_missed_punch_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Approve a missed punch request"""
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.MISSED_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missed punch request not found"
            )
        
        # Update request
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = "Approved"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "status": "approved",
            "approved_by": employee_id,
            "approved_date": request_obj.approved_date.isoformat(),
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "request_title": request_obj.title
        }
        
        return APIResponse(
            success=True,
            message=f"Missed punch request #{request_id} approved successfully",
            data=response_data
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve missed punch request: {str(e)}"
        )


@router.put("/missed-punches/{request_id}/reject", response_model=APIResponse)
async def reject_missed_punch_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Reject a missed punch request"""
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.MISSED_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missed punch request not found"
            )
        
        # Update request
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = "Rejected"
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": employee_id,
            "rejected_date": request_obj.approved_date.isoformat(),
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None,
            "request_title": request_obj.title
        }
        
        return APIResponse(
            success=True,
            message=f"Missed punch request #{request_id} rejected successfully",
            data=response_data
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject missed punch request: {str(e)}"
        )


@router.put("/missed-punches/{request_id}", response_model=APIResponse)
async def update_missed_punch_request(
    request_id: int,
    update_data: MissedPunchRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a missed punch request
    
    **Request body:**
    - punch_time: Updated punch time in HH:MM:SS format (optional)
    - punch_type: Punch type - in, out (optional)
    - reason: Updated reason (optional)
    - location: Punch location (optional)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.MISSED_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missed punch request not found"
            )
        
        # Only allow updates for pending requests
        if request_obj.status not in [RequestStatus.PENDING, RequestStatus.IN_REVIEW]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update approved or rejected requests"
            )
        
        # Update base request fields
        if update_data.reason:
            request_obj.description = update_data.reason
        
        # Update missed punch details
        punch_details = db.query(MissedPunchRequest).filter(
            MissedPunchRequest.request_id == request_id
        ).first()
        
        if punch_details:
            if update_data.punch_type:
                punch_details.punch_type = update_data.punch_type
            if update_data.punch_time:
                punch_details.expected_time = update_data.punch_time
            if update_data.reason:
                punch_details.reason = update_data.reason
                request_obj.description = update_data.reason
            if update_data.location:
                punch_details.location = update_data.location
        
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "title": request_obj.title,
            "description": request_obj.description,
            "status": request_obj.status.value,
            "updated_at": request_obj.updated_at.isoformat(),
            "employee_name": f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None
        }
        
        return APIResponse(
            success=True,
            message=f"Missed punch request #{request_id} updated successfully",
            data=response_data
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update missed punch request: {str(e)}"
        )


@router.delete("/missed-punches/{request_id}", response_model=APIResponse)
async def delete_missed_punch_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a missed punch request"""
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.MISSED_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missed punch request not found"
            )
        
        # Only allow deletion for pending requests
        if request_obj.status not in [RequestStatus.PENDING, RequestStatus.IN_REVIEW]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete approved or rejected requests"
            )
        
        # Store request info before deletion
        employee_name = f"{request_obj.employee.first_name} {request_obj.employee.last_name}" if request_obj.employee else None
        request_title = request_obj.title
        
        # Delete missed punch details first (foreign key constraint)
        db.query(MissedPunchRequest).filter(
            MissedPunchRequest.request_id == request_id
        ).delete()
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        response_data = {
            "request_id": request_id,
            "employee_name": employee_name,
            "request_title": request_title,
            "deleted_at": datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            message=f"Missed punch request #{request_id} deleted successfully",
            data=response_data
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete missed punch request: {str(e)}"
        )


# VISIT PUNCH REQUESTS - CREATE
@router.post("/visitpunch-request", response_model=APIResponse)
async def create_visit_punch_request(
    visit_punch_data: VisitPunchRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a visit punch request
    
    **Creates:**
    - Visit punch request for client/site visits
    - Visit details with client information
    
    **Request Body:**
    - visit_date: Date of the visit (required)
    - client_name: Name of client/company (required, 1-200 chars)
    - client_address: Address of visit location (required)
    - purpose: Purpose of the visit (required)
    - expected_duration: Expected duration (optional, e.g., "2 hours")
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Determine employee_id - use provided employee_id or current user's employee_id
        if hasattr(visit_punch_data, 'employee_id') and visit_punch_data.employee_id:
            # Admin creating request for another employee
            employee_id = visit_punch_data.employee_id
            
            # Verify the employee exists and belongs to the same business context
            employee = db.query(Employee).filter(
                Employee.id == employee_id,
                Employee.business_id == business_id if business_id else True,
                Employee.employee_status.in_(["active", "ACTIVE"])
            ).first()
            
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected employee not found or inactive"
                )
        else:
            # Regular user creating request for themselves
            employee_id = getattr(current_user, 'employee_id', None)
            
            # If no employee_id (e.g., superadmin), use the first active employee for testing
            if not employee_id:
                first_employee = db.query(Employee).filter(
                    Employee.business_id == business_id,
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
                
                if first_employee:
                    employee_id = first_employee.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No active employees found"
                    )
        
        # Create main request
        new_request = Request(
            business_id=business_id,
            employee_id=employee_id,
            request_type=RequestType.VISIT_PUNCH,
            title=f"Visit Punch Request - {visit_punch_data.client_name}",
            description=f"Client visit to {visit_punch_data.client_name} for {visit_punch_data.purpose}",
            from_date=visit_punch_data.visit_date,
            status=RequestStatus.PENDING,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(new_request)
        db.flush()
        
        # Create visit punch details
        visit_details = VisitPunchRequest(
            request_id=new_request.id,
            visit_date=visit_punch_data.visit_date,
            client_name=visit_punch_data.client_name,
            client_address=visit_punch_data.client_address,
            purpose=visit_punch_data.purpose,
            expected_duration=visit_punch_data.expected_duration
        )
        
        db.add(visit_details)
        db.commit()
        
        # Prepare response data
        response_data = {
            "request_id": new_request.id,
            "request_type": new_request.request_type.value,
            "title": new_request.title,
            "status": new_request.status.value,
            "visit_date": visit_punch_data.visit_date.isoformat(),
            "client_name": visit_punch_data.client_name,
            "client_address": visit_punch_data.client_address,
            "purpose": visit_punch_data.purpose,
            "expected_duration": visit_punch_data.expected_duration,
            "created_at": new_request.created_at.isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Visit punch request created successfully",
            data=response_data
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visit punch request: {str(e)}"
        )


# VISIT PUNCH REQUESTS (Frontend Compatible)
@router.get("/visitpunch-request", response_model=List[Dict[str, Any]])
async def get_visit_punch_requests_frontend(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get visit punch requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.visit_punch_details)
        ).filter(Request.request_type == RequestType.VISIT_PUNCH)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            if request_status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif request_status == "Pending":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Processing":
                query = query.filter(Request.status == RequestStatus.IN_REVIEW)
            elif request_status == "Completed":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Approved":  # Handle "Approved" status from frontend
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif request_status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
            else:
                query = query.filter(Request.status == status.lower())
        
        if location and location != "All Locations":
            # Filter by employee location using proper join
            query = query.join(Employee, Request.employee_id == Employee.id).join(
                Location, Employee.location_id == Location.id
            ).filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.filter(
                Request.employee.has(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            )
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            visit_details = req.visit_punch_details[0] if req.visit_punch_details else None
            
            # Format date as expected by frontend
            date_formatted = req.request_date.strftime('%b %d, %Y %H:%M:%S') if req.request_date else "N/A"
            if visit_details and visit_details.visit_date:
                date_formatted = visit_details.visit_date.strftime('%b %d, %Y') + " 18:00:00"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            # Create visit note from visit details
            visit_note = req.description or "Visit punch request"
            if visit_details:
                visit_note = f"Client visit to {visit_details.client_name}"
                if visit_details.purpose:
                    visit_note += f" - {visit_details.purpose}"
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": visit_note,
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": location or "Hyderabad",  # Default location
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "visit_date": visit_details.visit_date.isoformat() if visit_details and visit_details.visit_date else None,
                "client_name": visit_details.client_name if visit_details else None,
                "client_address": visit_details.client_address if visit_details else None,
                "purpose": visit_details.purpose if visit_details else req.description,
                "expected_duration": visit_details.expected_duration if visit_details else None,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch visit punch requests: {str(e)}"
        )


@router.put("/visitpunch-request/{request_id}", response_model=APIResponse)
async def update_visit_punch_request(
    request_id: int,
    visit_punch_data: VisitPunchRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a visit punch request
    
    **Request body:**
    - visit_type_id: Visit type ID (optional)
    - visit_location: Visit location (optional)
    - visit_purpose: Visit purpose (optional)
    - punch_in_time: Punch in time in HH:MM:SS format (optional)
    - punch_out_time: Punch out time in HH:MM:SS format (optional)
    - latitude: GPS latitude (optional)
    - longitude: GPS longitude (optional)
    - notes: Additional notes (optional)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find visit punch request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.VISIT_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Visit punch request not found"
            )
        
        # Update main request
        request_obj.title = f"Visit Punch Request - {visit_punch_data.client_name}"
        request_obj.description = f"Client visit to {visit_punch_data.client_name} for {visit_punch_data.purpose}"
        request_obj.from_date = visit_punch_data.visit_date
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        # Update visit punch details
        visit_details = db.query(VisitPunchRequest).filter(
            VisitPunchRequest.request_id == request_id
        ).first()
        
        if visit_details:
            visit_details.visit_date = visit_punch_data.visit_date
            visit_details.client_name = visit_punch_data.client_name
            visit_details.client_address = visit_punch_data.client_address
            visit_details.purpose = visit_punch_data.purpose
            visit_details.expected_duration = visit_punch_data.expected_duration
        else:
            # Create new visit details if not exists
            visit_details = VisitPunchRequest(
                request_id=request_id,
                visit_date=visit_punch_data.visit_date,
                client_name=visit_punch_data.client_name,
                client_address=visit_punch_data.client_address,
                purpose=visit_punch_data.purpose,
                expected_duration=visit_punch_data.expected_duration
            )
            db.add(visit_details)
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Visit punch request updated successfully",
            data={
                "request_id": request_id,
                "status": request_obj.status.value,
                "visit_date": visit_punch_data.visit_date.isoformat(),
                "client_name": visit_punch_data.client_name,
                "client_address": visit_punch_data.client_address,
                "purpose": visit_punch_data.purpose,
                "expected_duration": visit_punch_data.expected_duration,
                "updated_at": request_obj.updated_at.isoformat()
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update visit punch request: {str(e)}"
        )


@router.put("/visitpunch-request/{request_id}/approve", response_model=APIResponse)
async def approve_visit_punch_request(
    request_id: int,
    approval_data: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a visit punch request
    
    **Updates:**
    - Visit punch request status to approved
    - Approval details and comments
    - Approval timestamp
    
    **Request Body:**
    - comments: Optional, approval comments
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find visit punch request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.VISIT_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Visit punch request not found"
            )
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_data.approval_comments or 'Visit punch request approved'
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Visit punch request approved successfully",
            data={
                "request_id": request_id,
                "status": "approved",
                "approved_by": employee_id,
                "approved_date": request_obj.approved_date.isoformat(),
                "approval_comments": request_obj.approval_comments
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve visit punch request: {str(e)}"
        )


@router.put("/visitpunch-request/{request_id}/reject", response_model=APIResponse)
async def reject_visit_punch_request(
    request_id: int,
    rejection_data: RejectionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a visit punch request
    
    **Updates:**
    - Visit punch request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    
    **Request Body:**
    - comments: Required, rejection reason
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Find visit punch request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.VISIT_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Visit punch request not found"
            )
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = rejection_data.approval_comments
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Visit punch request rejected successfully",
            data={
                "request_id": request_id,
                "status": "rejected",
                "rejected_by": employee_id,
                "rejected_date": request_obj.approved_date.isoformat(),
                "rejection_comments": request_obj.approval_comments
            }
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject visit punch request: {str(e)}"
        )


@router.delete("/visitpunch-request/{request_id}", response_model=Dict[str, Any])
async def delete_visit_punch_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a visit punch request
    
    **Deletes:**
    - Visit punch request and associated details
    - Visit punch details if any
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find visit punch request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.VISIT_PUNCH,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Visit punch request not found"
            )
        
        # Delete associated visit punch details first
        if request_obj.visit_punch_details:
            for detail in request_obj.visit_punch_details:
                db.delete(detail)
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": "Visit punch request deleted successfully",
            "request_id": request_id,
            "deleted": True
        }
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete visit punch request: {str(e)}"
        )


# HELPDESK REQUESTS (Frontend Compatible)
@router.get("/helpdesk", response_model=List[Dict[str, Any]])
async def get_helpdesk_requests_frontend(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    request_status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get helpdesk requests with filtering and pagination - Frontend Compatible Format
    
    **Filters:**
    - status: Filter by request status (Open, Pending, Processing, Completed)
    - location: Filter by employee location
    - date_from/date_to: Filter by date range
    - search: Search by employee name or code
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        query = db.query(Request).options(
            joinedload(Request.employee),
            joinedload(Request.helpdesk_details)
        ).filter(Request.request_type == RequestType.HELPDESK)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if request_status and request_status != "All":
            # Handle comma-separated status values
            if "," in status:
                # Split comma-separated values and convert to enum
                status_list = [s.strip().upper() for s in status.split(",")]
                # Map common status names to enum values
                status_enum_list = []
                for s in status_list:
                    if s == "PENDING":
                        status_enum_list.append(RequestStatus.PENDING)
                    elif s == "IN_REVIEW":
                        status_enum_list.append(RequestStatus.IN_REVIEW)
                    elif s == "APPROVED":
                        status_enum_list.append(RequestStatus.APPROVED)
                    elif s == "REJECTED":
                        status_enum_list.append(RequestStatus.REJECTED)
                    elif s == "CANCELLED":
                        status_enum_list.append(RequestStatus.CANCELLED)
                
                if status_enum_list:
                    query = query.filter(Request.status.in_(status_enum_list))
            else:
                # Single status value
                if request_status == "Open":
                    query = query.filter(Request.status == RequestStatus.PENDING)
                elif request_status == "Pending":
                    query = query.filter(Request.status == RequestStatus.IN_REVIEW)
                elif request_status == "Processing":
                    query = query.filter(Request.status == RequestStatus.IN_REVIEW)
                elif request_status == "Completed":
                    query = query.filter(Request.status == RequestStatus.APPROVED)
                else:
                    # Try to match as enum value
                    try:
                        status_enum = RequestStatus[status.upper()]
                        query = query.filter(Request.status == status_enum)
                    except KeyError:
                        # If not a valid enum, try lowercase match
                        query = query.filter(Request.status == status.lower())
        
        if location and location != "All Locations":
            # Filter by employee location using proper join
            query = query.join(Employee, Request.employee_id == Employee.id).join(
                Location, Employee.location_id == Location.id
            ).filter(Location.name == location)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.filter(
                Request.employee.has(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            )
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        request_list = []
        for req in requests:
            helpdesk_details = req.helpdesk_details[0] if req.helpdesk_details else None
            
            # Format date as expected by frontend
            date_formatted = req.request_date.strftime('%b %d, %Y %H:%M:%S') if req.request_date else "N/A"
            
            # Map status to frontend format
            status_mapping = {
                "pending": "Open",
                "in_review": "Pending",
                "approved": "Completed",
                "rejected": "Rejected"
            }
            
            # Format last updated
            last_updated = req.updated_at or req.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y %H:%M:%S') if last_updated else "N/A"
            
            # Create helpdesk note from helpdesk details
            helpdesk_note = req.description or "Helpdesk request"
            if helpdesk_details:
                helpdesk_note = f"{helpdesk_details.category} - {helpdesk_details.issue_type}"
                if helpdesk_details.urgency:
                    helpdesk_note += f" (Priority: {helpdesk_details.urgency.title()})"
            
            request_data = {
                "id": req.id,
                "date": date_formatted,
                "employee": f"{req.employee.first_name} {req.employee.last_name} ({req.employee.employee_code})" if req.employee else "Unknown Employee",
                "note": helpdesk_note,
                "lastUpdated": last_updated_formatted,
                "status": status_mapping.get(req.status.value, req.status.value.title()),
                "location": helpdesk_details.location if helpdesk_details else location or "Hyderabad",  # Default location
                
                # Additional fields for backend compatibility
                "business_id": req.business_id,
                "employee_id": req.employee_id,
                "category": helpdesk_details.category if helpdesk_details else "General",
                "subcategory": helpdesk_details.subcategory if helpdesk_details else None,
                "issue_type": helpdesk_details.issue_type if helpdesk_details else "General Issue",
                "urgency": helpdesk_details.urgency if helpdesk_details else "medium",
                "asset_tag": helpdesk_details.asset_tag if helpdesk_details else None,
                "request_date": req.request_date.isoformat(),
                "created_at": req.created_at.isoformat(),
                "approved_date": req.approved_date.isoformat() if req.approved_date else None,
                "approval_comments": req.approval_comments
            }
            request_list.append(request_data)
        
        return request_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch helpdesk requests: {str(e)}"
        )


@router.put("/helpdesk/{request_id}/approve", response_model=APIResponse)
async def approve_helpdesk_request(
    request_id: int,
    approval_data: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a helpdesk request
    
    **Updates:**
    - Helpdesk request status to approved
    - Approval details and comments
    - Approval timestamp
    
    **Request Body:**
    - approval_comments: Optional, approval comments
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        print(f"🔍 Debug - Approving helpdesk request {request_id}")
        print(f"🔍 Debug - Business ID: {business_id}")
        print(f"🔍 Debug - Employee ID: {employee_id}")
        print(f"🔍 Debug - Approval data: {approval_data}")
        
        # Find helpdesk request with proper business filtering
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.HELPDESK
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Helpdesk request not found or not accessible"
            )
        
        print(f"✅ Found helpdesk request: {request_obj.id}")
        
        # Get approval comments from the correct field
        approval_comments = getattr(approval_data, 'approval_comments', None) or getattr(approval_data, 'comments', None) or 'Helpdesk request approved'
        
        # Update request status to approved
        request_obj.status = RequestStatus.APPROVED
        request_obj.approved_by = employee_id  # This can be None for superadmin users
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = approval_comments
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        print(f"✅ Updated request status to approved")
        
        db.commit()
        
        print(f"✅ Transaction committed successfully")
        
        return APIResponse(
            success=True,
            message="Helpdesk request approved successfully",
            data={
                "request_id": request_id,
                "status": "approved",
                "approved_by": employee_id,
                "approved_date": request_obj.approved_date.isoformat(),
                "approval_comments": request_obj.approval_comments
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        print(f"❌ Error approving helpdesk request: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        
        # More specific error messages
        error_msg = str(e).lower()
        if "foreign key constraint" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid reference in approval data. Please check employee information."
            )
        elif "null value" in error_msg and "violates not-null constraint" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Missing required field in approval process."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to approve helpdesk request: {str(e)}"
            )


@router.put("/helpdesk/{request_id}/reject", response_model=APIResponse)
async def reject_helpdesk_request(
    request_id: int,
    rejection_data: RejectionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a helpdesk request
    
    **Updates:**
    - Helpdesk request status to rejected
    - Rejection details and comments
    - Rejection timestamp
    
    **Request Body:**
    - rejection_comments: Required, rejection reason
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set  # is_superadmin already set
        employee_id = getattr(current_user, 'employee_id', None)
        
        print(f"🔍 Debug - Rejecting helpdesk request {request_id}")
        print(f"🔍 Debug - Business context: {business_context}")
        
        # Find helpdesk request with proper business filtering
        query = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.HELPDESK
            )
        )
        
        # Apply business filtering only for non-superadmin users
        if business_id and not is_superadmin:
            query = query.filter(Request.business_id == business_id)
        
        request_obj = query.first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Helpdesk request not found or not accessible"
            )
        
        # Get rejection comments from the correct field
        rejection_comments = getattr(rejection_data, 'rejection_comments', None) or getattr(rejection_data, 'comments', None) or 'Helpdesk request rejected'
        
        # Update request status to rejected
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id  # This can be None for superadmin users
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = rejection_comments
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Helpdesk request rejected successfully",
            data={
                "request_id": request_id,
                "status": "rejected",
                "rejected_by": employee_id,
                "rejected_date": request_obj.approved_date.isoformat(),
                "rejection_comments": request_obj.approval_comments
            }
        )
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        print(f"❌ Error rejecting helpdesk request: {str(e)}")
        
        # More specific error messages
        error_msg = str(e).lower()
        if "foreign key constraint" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid reference in rejection data. Please check employee information."
            )
        elif "null value" in error_msg and "violates not-null constraint" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Missing required field in rejection process."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reject helpdesk request: {str(e)}"
            )
        request_obj.status = RequestStatus.REJECTED
        request_obj.approved_by = employee_id
        request_obj.approved_date = datetime.now()
        request_obj.approval_comments = rejection_data.comments
        request_obj.updated_by = current_user.id
        request_obj.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Helpdesk request rejected successfully",
            data={
                "request_id": request_id,
                "status": "rejected",
                "rejected_by": employee_id,
                "rejected_date": request_obj.approved_date.isoformat(),
                "rejection_comments": request_obj.approval_comments
            }
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject helpdesk request: {str(e)}"
        )


@router.delete("/helpdesk/{request_id}", response_model=Dict[str, Any])
async def delete_helpdesk_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a helpdesk request
    
    **Deletes:**
    - Helpdesk request and associated details
    - Hard delete - removes record completely from database
    """
    try:
        # Use hybrid business context instead of manual extraction
        is_superadmin, business_id = get_user_business_context(current_user, db)  # business_id already set
        
        # Find helpdesk request
        request_obj = db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.request_type == RequestType.HELPDESK,
                Request.business_id == business_id if business_id else True
            )
        ).first()
        
        if not request_obj:
            raise HTTPException(
                status_code=404,
                detail="Helpdesk request not found"
            )
        
        # Delete associated helpdesk details first
        if request_obj.helpdesk_details:
            for detail in request_obj.helpdesk_details:
                db.delete(detail)
        
        # Delete the main request
        db.delete(request_obj)
        db.commit()
        
        return {
            "message": "Helpdesk request deleted successfully",
            "request_id": request_id,
            "deleted": True
        }
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete helpdesk request: {str(e)}"
        )