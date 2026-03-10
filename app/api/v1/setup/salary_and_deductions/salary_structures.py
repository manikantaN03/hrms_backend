from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.salary_and_deductions.salary_structure import (
    SalaryStructureCreate,
    SalaryStructureUpdate,
    SalaryStructureResponse
)
from app.services.setup.salary_and_deductions.salary_structure_service import (
    SalaryStructureService,
)

# Remove the duplicate prefix - it's already set in router.py
router = APIRouter()
service = SalaryStructureService()


# ✅ List all structures for a business
@router.get(
    "/{business_id}",
    response_model=list[SalaryStructureResponse],
    summary="List all salary structures for a business",
    description="Retrieve all salary structures configured for a specific business"
)
def list_structures(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all salary structures for a business.
    
    - **business_id**: ID of the business
    """
    if business_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID"
        )
    return service.list_by_business(db, business_id)


# ✅ Create structure (business_id comes from payload)
@router.post(
    "/",
    response_model=SalaryStructureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create salary structure",
    description="Create a new salary structure with allocation rules"
)
def create_structure(
    data: SalaryStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new salary structure.
    
    Required fields:
    - **business_id**: ID of the business
    - **name**: Name of the salary structure
    - **rules**: List of allocation rules (optional)
    """
    return service.create(db, data)


# ✅ Get a single structure (business scoped)
@router.get(
    "/{business_id}/{structure_id}",
    response_model=SalaryStructureResponse,
    summary="Get salary structure by ID",
    description="Retrieve a specific salary structure with its allocation rules"
)
def get_structure(
    business_id: int,
    structure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get a single salary structure.
    
    - **business_id**: ID of the business
    - **structure_id**: ID of the salary structure
    """
    if business_id <= 0 or structure_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or structure ID"
        )
    return service.get_by_business(db, structure_id, business_id)


# ✅ Update a structure (business scoped)
@router.put(
    "/{business_id}/{structure_id}",
    response_model=SalaryStructureResponse,
    summary="Update salary structure",
    description="Update an existing salary structure"
)
def update_structure(
    business_id: int,
    structure_id: int,
    data: SalaryStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a salary structure.
    
    - **business_id**: ID of the business
    - **structure_id**: ID of the salary structure
    
    All fields are optional. Only provided fields will be updated.
    """
    if business_id <= 0 or structure_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or structure ID"
        )
    return service.update(db, structure_id, business_id, data)


# ✅ Delete a structure (business scoped)
@router.delete(
    "/{business_id}/{structure_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete salary structure",
    description="Delete a salary structure (if not in use)"
)
def delete_structure(
    business_id: int,
    structure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a salary structure.
    
    - **business_id**: ID of the business
    - **structure_id**: ID of the salary structure
    
    Note: Cannot delete if structure is being used in employee records.
    """
    if business_id <= 0 or structure_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID or structure ID"
        )
    service.delete(db, structure_id, business_id)
    return {"message": "Salary structure deleted successfully"}
