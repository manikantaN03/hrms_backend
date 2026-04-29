from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, validate_business_access
from app.models.user import User

from app.schemas.setup.salary_and_deductions.overtime import (
    OvertimePolicyCreate,
    OvertimePolicyUpdate,
    OvertimePolicyOut,
    OvertimeRuleCreate,
    OvertimeRuleUpdate,
    OvertimeRuleOut,
)
from app.schemas.setup.salary_and_deductions.overtime_payable_component import (
    OvertimePayableComponentOut,
)
from app.services.setup.salary_and_deductions.overtime_service import (
    policy_service,
    rule_service,
)
from app.services.setup.salary_and_deductions.overtime_payable_component_service import (
    payable_component_service,
)

# Remove the duplicate prefix - it's already set in router.py
router = APIRouter()


# ============================================================
#                       OVERTIME POLICIES
# ============================================================

@router.get(
    "/policies", 
    response_model=list[OvertimePolicyOut],
    summary="Get all overtime policies",
    description="Retrieve all overtime policies for a specific business"
)
def list_policies(
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get all overtime policies for a business
    
    - **business_id**: Business ID (must be positive integer)
    
    Returns list of overtime policies with their details
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    validate_business_access(business_id, current_user, db)
    return policy_service.list(db, business_id)


@router.post(
    "/policies", 
    response_model=OvertimePolicyOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new overtime policy",
    description="Create a new overtime policy with a unique name"
)
def create_policy(
    data: OvertimePolicyCreate,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new overtime policy
    
    Required fields:
    - business_id: Business ID
    - policy_name: Unique policy name (1-255 characters)
    
    Returns the created overtime policy with ID and timestamps
    """
    try:
        if business_id <= 0:
            raise HTTPException(status_code=400, detail="Business ID must be positive")
        validate_business_access(business_id, current_user, db)
        return policy_service.create_with_business(db, business_id, data)
    except IntegrityError as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Policy name already exists. Please use a different name."
            )
        raise HTTPException(
            status_code=400,
            detail="Invalid business_id. Please ensure it exists in the database."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create overtime policy: {str(e)}")


@router.put(
    "/policies/{policy_id}", 
    response_model=OvertimePolicyOut,
    summary="Update an existing overtime policy",
    description="Update specific fields of an existing overtime policy"
)
def update_policy(
    policy_id: int = Path(...),
    business_id: int = Path(...),
    data: OvertimePolicyUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an existing overtime policy
    
    - **business_id**: Business ID (must match the policy's business)
    - **policy_id**: Overtime Policy ID to update
    - **data**: Fields to update (all fields are optional)
    
    Only provided fields will be updated. Returns the updated policy.
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if policy_id <= 0:
        raise HTTPException(status_code=400, detail="Policy ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        return policy_service.update(db, policy_id, business_id, data)
    except HTTPException:
        raise
    except IntegrityError as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Policy name already exists. Please use a different name."
            )
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update overtime policy: {str(e)}")


@router.delete(
    "/policies/{policy_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an overtime policy",
    description="Delete an existing overtime policy by ID (cascades to rules)"
)
def delete_policy(
    policy_id: int = Path(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete an overtime policy
    
    - **business_id**: Business ID (must match the policy's business)
    - **policy_id**: Overtime Policy ID to delete
    
    Note: This will also delete all associated overtime rules (CASCADE DELETE)
    
    Returns 204 No Content on successful deletion
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if policy_id <= 0:
        raise HTTPException(status_code=400, detail="Policy ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        policy_service.delete(db, policy_id, business_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete overtime policy: {str(e)}")


# ============================================================
#                       OVERTIME RULES
# ============================================================

@router.get(
    "/rules/{policy_id}", 
    response_model=list[OvertimeRuleOut],
    summary="Get overtime rules for a policy",
    description="Retrieve all overtime rules for a specific policy"
)
def list_rules(
    policy_id: int = Path(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get all overtime rules for a specific policy
    
    - **business_id**: Business ID (must be positive integer)
    - **policy_id**: Policy ID (must be positive integer)
    
    Returns list of overtime rules with all configuration details
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if policy_id <= 0:
        raise HTTPException(status_code=400, detail="Policy ID must be positive")
    validate_business_access(business_id, current_user, db)
    return rule_service.list(db, policy_id, business_id)


@router.post(
    "/rules/{policy_id}", 
    response_model=OvertimeRuleOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new overtime rule",
    description="Create a new overtime rule with attendance, time, and calculation configurations"
)
def create_rule(
    policy_id: int = Path(...),
    business_id: int = Path(...),
    data: OvertimeRuleCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new overtime rule
    
    Required fields:
    - business_id: Business ID
    - policy_id: Overtime Policy ID
    - attendance_type: Attendance type (e.g., Present, Absent, Half Day)
    - time_basis: Time basis (e.g., Early Coming, Late Going, Daily, Weekly)
    - from_hrs: From hours (0-23)
    - from_mins: From minutes (0-59)
    - to_hrs: To hours (0-23)
    - to_mins: To minutes (0-59)
    - calculation_method: Calculation method (e.g., Exclusive, Progressive, Multiplier)
    - multiplier: Multiplier (1-10)
    - overtime_mins_type: Overtime minutes type (e.g., Actual, Above, Fixed)
    - fixed_mins: Fixed minutes (0-1440, required if overtime_mins_type is Fixed)
    
    Returns the created overtime rule with ID and timestamps
    """
    try:
        if business_id <= 0:
            raise HTTPException(status_code=400, detail="Business ID must be positive")
        if policy_id <= 0:
            raise HTTPException(status_code=400, detail="Policy ID must be positive")
        validate_business_access(business_id, current_user, db)
        return rule_service.create(db, business_id, policy_id, data)
    except HTTPException:
        raise
    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid business_id or policy_id. Please ensure they exist in the database."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create overtime rule: {str(e)}")


@router.put(
    "/rules/{rule_id}", 
    response_model=OvertimeRuleOut,
    summary="Update an existing overtime rule",
    description="Update specific fields of an existing overtime rule"
)
def update_rule(
    rule_id: int = Path(...),
    business_id: int = Path(...),
    data: OvertimeRuleUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an existing overtime rule
    
    - **business_id**: Business ID (must match the rule's business)
    - **rule_id**: Overtime Rule ID to update
    - **data**: Fields to update (all fields are optional)
    
    Only provided fields will be updated. Returns the updated rule.
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if rule_id <= 0:
        raise HTTPException(status_code=400, detail="Rule ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        return rule_service.update(db, rule_id, business_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update overtime rule: {str(e)}")


@router.delete(
    "/rules/{rule_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an overtime rule",
    description="Delete an existing overtime rule by ID"
)
def delete_rule(
    rule_id: int = Path(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete an overtime rule
    
    - **business_id**: Business ID (must match the rule's business)
    - **rule_id**: Overtime Rule ID to delete
    
    Returns 204 No Content on successful deletion
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if rule_id <= 0:
        raise HTTPException(status_code=400, detail="Rule ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        rule_service.delete(db, rule_id, business_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete overtime rule: {str(e)}")


# ============================================================
#                  PAYABLE COMPONENTS
# ============================================================

@router.get(
    "/payable-components/{policy_id}", 
    response_model=list[OvertimePayableComponentOut],
    summary="Get payable components for a policy",
    description="Retrieve all payable components configuration for a specific overtime policy"
)
def list_payable_components(
    policy_id: int = Path(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get all payable components for a policy
    
    - **business_id**: Business ID (must be positive integer)
    - **policy_id**: Policy ID (must be positive integer)
    
    Returns list of salary components with their payable status for overtime
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if policy_id <= 0:
        raise HTTPException(status_code=400, detail="Policy ID must be positive")
    validate_business_access(business_id, current_user, db)
    return payable_component_service.list_by_policy(db, policy_id, business_id)


@router.post(
    "/payable-components/{policy_id}/{component_id}/toggle", 
    response_model=OvertimePayableComponentOut,
    summary="Toggle payable status for a component",
    description="Enable or disable a salary component for overtime calculation in a specific policy"
)
def toggle_payable_component(
    policy_id: int = Path(...),
    component_id: int = Path(...),
    business_id: int = Path(...),
    is_payable: bool = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Toggle payable status for a component
    
    - **business_id**: Business ID (must be positive integer)
    - **policy_id**: Policy ID (must be positive integer)
    - **component_id**: Salary Component ID (must be positive integer)
    - **is_payable**: Boolean flag to enable/disable component for overtime
    
    Returns the updated payable component configuration
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    if policy_id <= 0:
        raise HTTPException(status_code=400, detail="Policy ID must be positive")
    if component_id <= 0:
        raise HTTPException(status_code=400, detail="Component ID must be positive")
    validate_business_access(business_id, current_user, db)
    try:
        return payable_component_service.toggle_payable(db, policy_id, component_id, business_id, is_payable)
    except HTTPException:
        raise
    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid policy_id or component_id. Please ensure they exist in the database."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle payable component: {str(e)}")
