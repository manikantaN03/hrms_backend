"""
ESS User Management Endpoints
API routes for managing employee access to mobile app and web portal
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business
from app.schemas.user_management_schema import (
    FilterOptionsResponse,
    SendLoginRequest,
    SendLoginResponse,
    EmployeeFilterRequest
)
from app.services.user_management_service import get_user_management_service

router = APIRouter(prefix="/user-management")


# ============================================================================
# Helpers
# ============================================================================

def validate_business_exists(db: Session, business_id: int) -> Business:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    return business


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get(
    "/filter-options/{business_id}",
    status_code=status.HTTP_200_OK,
    summary="Get filter options for employee selection",
)
def get_filter_options(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get available locations, cost centers, and departments for filtering employees
    **Access:** ADMIN or SUPERADMIN
    """
    validate_business_exists(db, business_id)
    service = get_user_management_service(db)
    
    options = service.get_filter_options(business_id)
    
    return {
        "locations": options["locations"],
        "costCenters": options["cost_centers"],
        "departments": options["departments"]
    }


@router.post(
    "/send-mobile-login",
    status_code=status.HTTP_200_OK,
    summary="Send mobile login details via email",
)
async def send_mobile_login(
    request: SendLoginRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Send mobile app login details to selected employees via email
    **Access:** ADMIN or SUPERADMIN
    """
    validate_business_exists(db, request.business_id)
    service = get_user_management_service(db)
    
    result = await service.send_mobile_login_details(
        business_id=request.business_id,
        location=request.location,
        cost_center=request.cost_center,
        department=request.department,
        include_logged_in=request.include_logged_in
    )
    
    return {
        "success": True,
        "message": f"Mobile login details sent successfully to {result['emails_sent']} employees",
        "employeesNotified": result["employees_notified"],
        "emailsSent": result["emails_sent"],
        "failedCount": result["failed_count"],
        "details": f"Sent emails to {result['emails_sent']} out of {result['employees_notified']} employees"
    }


@router.post(
    "/send-web-login",
    status_code=status.HTTP_200_OK,
    summary="Send web portal login invitations via email",
)
async def send_web_login(
    request: SendLoginRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create web portal accounts and send invitation emails to selected employees
    **Access:** ADMIN or SUPERADMIN
    """
    validate_business_exists(db, request.business_id)
    service = get_user_management_service(db)
    
    result = await service.send_web_login_invitations(
        business_id=request.business_id,
        location=request.location,
        cost_center=request.cost_center,
        department=request.department
    )
    
    return {
        "success": True,
        "message": f"Web portal invitations sent successfully to {result['emails_sent']} employees",
        "employeesNotified": result["employees_notified"],
        "accountsCreated": result["accounts_created"],
        "emailsSent": result["emails_sent"],
        "failedCount": result["failed_count"],
        "details": f"Sent invitation emails to {result['emails_sent']} out of {result['employees_notified']} employees"
    }


@router.get(
    "/employee-count",
    status_code=status.HTTP_200_OK,
    summary="Get count of employees matching filter criteria",
)
def get_employee_count(
    business_id: int,
    location: Optional[str] = None,
    cost_center: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get count of employees that match the filter criteria
    **Access:** ADMIN or SUPERADMIN
    """
    validate_business_exists(db, business_id)
    service = get_user_management_service(db)
    
    count = service.get_filtered_employee_count(
        business_id=business_id,
        location=location,
        cost_center=cost_center,
        department=department
    )
    
    return {
        "totalEmployees": count,
        "filters": {
            "location": location or "All Locations",
            "costCenter": cost_center or "All Cost Centers", 
            "department": department or "All Departments"
        }
    }