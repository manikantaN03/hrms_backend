from fastapi import APIRouter, Depends, status, HTTPException, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, validate_business_access
from app.models.user import User

from app.schemas.setup.salary_and_deductions.time_salary import (
    TimeRuleCreate,
    TimeRuleUpdate,
    TimeRuleResponse
)
from app.services.setup.salary_and_deductions.time_salary_service import (
    TimeSalaryRuleService,
)

# Remove the duplicate prefix - it's already set in router.py
router = APIRouter()
service = TimeSalaryRuleService()


@router.get(
    "/{component_id}",
    response_model=list[TimeRuleResponse],
    summary="Get time salary rules for a component",
    description="Retrieve all time salary rules for a specific business and salary component"
)
def list_rules(
    component_id: int = Path(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get all time salary rules for a specific component
    
    - **business_id**: Business ID (must be positive integer)
    - **component_id**: Salary Component ID (must be positive integer)
    
    Returns list of time salary rules with all configuration details
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if component_id <= 0:
        raise HTTPException(status_code=400, detail="Component ID must be positive")
    validate_business_access(business_id, current_user, db)
    return service.list(db, business_id, component_id)


@router.post(
    "/{component_id}",
    response_model=TimeRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new time salary rule",
    description="Create a new time salary rule with attendance, shift, and timing configurations"
)
def create_rule(
    component_id: int = Path(...),
    data: TimeRuleCreate = Body(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new time salary rule
    
    Required fields:
    - business_id: Business ID
    - component_id: Salary Component ID
    - attendance: Attendance type (e.g., Present, Half Day)
    - shift: Shift name (e.g., Regular Shift, Night Shift)
    - early_coming_minutes: Early coming allowance (0-120 minutes)
    - in_office_time: Office in time (HH:MM:SS format)
    - out_office_time: Office out time (HH:MM:SS format)
    - lunch_always_minutes: Lunch break duration (0-180 minutes)
    - lunch_working_minutes: Working lunch duration (0-180 minutes)
    - late_going_minutes: Late going allowance (0-120 minutes)
    - limit_shift_hours: Maximum shift hours (1-24 hours)
    
    Returns the created time salary rule with ID and timestamps
    """
    try:
        if business_id <= 0:
            raise HTTPException(status_code=400, detail="Business ID must be positive")
        if component_id <= 0:
            raise HTTPException(status_code=400, detail="Component ID must be positive")
        validate_business_access(business_id, current_user, db)
        return service.create(db, business_id, component_id, data)
    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid business_id or component_id. Please ensure they exist in the database."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create time salary rule: {str(e)}")


@router.put(
    "/{rule_id}",
    response_model=TimeRuleResponse,
    summary="Update an existing time salary rule",
    description="Update specific fields of an existing time salary rule"
)
def update_rule(
    rule_id: int = Path(...),
    data: TimeRuleUpdate = Body(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an existing time salary rule
    
    - **business_id**: Business ID (must match the rule's business)
    - **rule_id**: Time Salary Rule ID to update
    - **data**: Fields to update (all fields are optional)
    
    Only provided fields will be updated. Returns the updated rule.
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if rule_id <= 0:
        raise HTTPException(status_code=400, detail="Rule ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        return service.update(db, rule_id, business_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update time salary rule: {str(e)}")


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a time salary rule",
    description="Delete an existing time salary rule by ID"
)
def delete_rule(
    rule_id: int = Path(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a time salary rule
    
    - **business_id**: Business ID (must match the rule's business)
    - **rule_id**: Time Salary Rule ID to delete
    
    Returns 204 No Content on successful deletion
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if rule_id <= 0:
        raise HTTPException(status_code=400, detail="Rule ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        service.delete(db, rule_id, business_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete time salary rule: {str(e)}")

