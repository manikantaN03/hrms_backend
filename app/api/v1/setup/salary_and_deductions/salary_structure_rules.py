from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.salary_and_deductions.salary_structure_rule import (
    SalaryStructureRuleCreate,
    SalaryStructureRuleUpdate,
    SalaryStructureRuleResponse
)
from app.services.setup.salary_and_deductions.salary_structure_rule_service import (
    SalaryStructureRuleService,
)

router = APIRouter()
service = SalaryStructureRuleService()


@router.get(
    "/salary-structure-rules/{business_id}/{structure_id}",
    response_model=list[SalaryStructureRuleResponse],
    summary="List all rules for a salary structure",
    description="Retrieve all allocation rules for a specific salary structure"
)
def list_rules(
    business_id: int,
    structure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all allocation rules for a salary structure.
    
    - **business_id**: ID of the business
    - **structure_id**: ID of the salary structure
    """
    if business_id <= 0 or structure_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or structure ID"
        )
    return service.list(db, structure_id, business_id)


@router.post(
    "/salary-structure-rules/{business_id}",
    response_model=SalaryStructureRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create salary structure rule",
    description="Create a new allocation rule for a salary structure"
)
def create_rule(
    business_id: int,
    data: SalaryStructureRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new salary structure rule.
    
    Required fields:
    - **structure_id**: ID of the salary structure
    - **component_id**: ID of the salary component
    - **calculation_type**: Type of calculation (Fixed/Percentage)
    - **value**: Amount or percentage value
    - **sequence**: Display order (default: 1)
    """
    if business_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID"
        )
    return service.create(db, data, business_id)


@router.put(
    "/salary-structure-rules/{business_id}/{rule_id}",
    response_model=SalaryStructureRuleResponse,
    summary="Update salary structure rule",
    description="Update an existing allocation rule"
)
def update_rule(
    business_id: int,
    rule_id: int,
    data: SalaryStructureRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a salary structure rule.
    
    - **business_id**: ID of the business
    - **rule_id**: ID of the rule
    
    All fields are optional. Only provided fields will be updated.
    """
    if business_id <= 0 or rule_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or rule ID"
        )
    return service.update(db, rule_id, business_id, data)


@router.delete(
    "/salary-structure-rules/{business_id}/{rule_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete salary structure rule",
    description="Delete an allocation rule from a salary structure"
)
def delete_rule(
    business_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a salary structure rule.
    
    - **business_id**: ID of the business
    - **rule_id**: ID of the rule
    """
    if business_id <= 0 or rule_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or rule ID"
        )
    service.delete(db, rule_id, business_id)
    return {"message": "Salary structure rule deleted successfully"}

