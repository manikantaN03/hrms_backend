from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.salary_and_deductions.salary_deduction import (
    SalaryDeductionCreate,
    SalaryDeductionUpdate,
    SalaryDeductionResponse
)
from app.services.setup.salary_and_deductions.salary_deduction_service import (
    SalaryDeductionService
)

# Remove the duplicate prefix - it's already set in router.py
router = APIRouter()
service = SalaryDeductionService()


# 🚀 LIST (Business Scoped)
@router.get(
    "/{business_id}",
    response_model=list[SalaryDeductionResponse],
    summary="List all salary deductions for a business",
    description="Retrieve all salary deduction types configured for a specific business"
)
def list_deductions(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all salary deductions for a business.
    
    - **business_id**: ID of the business
    """
    if business_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID"
        )
    return service.list(db, business_id)


# 🚀 CREATE (Business Scoped)
@router.post(
    "/",
    response_model=SalaryDeductionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create salary deduction",
    description="Create a new salary deduction type for a business"
)
def create_deduction(
    data: SalaryDeductionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new salary deduction.
    
    Required fields:
    - **business_id**: ID of the business
    - **name**: Full name of the deduction
    - **code**: Short code/alias for the deduction
    - **type**: Type of deduction (Fixed/Variable)
    """
    return service.create(db, data)


# 🚀 GET (Business Scoped)
@router.get(
    "/{business_id}/{deduction_id}",
    response_model=SalaryDeductionResponse,
    summary="Get salary deduction by ID",
    description="Retrieve a specific salary deduction by its ID"
)
def get_deduction(
    business_id: int,
    deduction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get a single salary deduction.
    
    - **business_id**: ID of the business
    - **deduction_id**: ID of the salary deduction
    """
    if business_id <= 0 or deduction_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or deduction ID"
        )
    return service.get(db, deduction_id, business_id)


# 🚀 UPDATE (Business Scoped)
@router.put(
    "/{business_id}/{deduction_id}",
    response_model=SalaryDeductionResponse,
    summary="Update salary deduction",
    description="Update an existing salary deduction"
)
def update_deduction(
    business_id: int,
    deduction_id: int,
    data: SalaryDeductionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a salary deduction.
    
    - **business_id**: ID of the business
    - **deduction_id**: ID of the salary deduction
    
    All fields are optional. Only provided fields will be updated.
    """
    if business_id <= 0 or deduction_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or deduction ID"
        )
    return service.update(db, deduction_id, business_id, data)


# 🚀 DELETE (Business Scoped)
@router.delete(
    "/{business_id}/{deduction_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete salary deduction",
    description="Delete a salary deduction (if not in use)"
)
def delete_deduction(
    business_id: int,
    deduction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a salary deduction.
    
    - **business_id**: ID of the business
    - **deduction_id**: ID of the salary deduction
    
    Note: Cannot delete if deduction is being used in employee records.
    """
    if business_id <= 0 or deduction_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or deduction ID"
        )
    service.delete(db, deduction_id, business_id)
    return {"message": "Salary deduction deleted successfully"}
