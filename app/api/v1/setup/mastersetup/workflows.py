"""
Workflow Endpoints
API routes for Workflow management
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
)
from app.services.workflow_service import (
    create_workflow_service,
    get_workflows_service,
    get_workflow_service,
    update_workflow_service,
    delete_workflow_service,
)
from app.api.v1.endpoints.master_setup import get_user_business_id

router = APIRouter()


# ============================================================================
# Helpers
# ============================================================================

def validate_business_exists(db: Session, business_id: int) -> Business:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found",
        )
    return business


# ============================================================================
# List Workflows → 200 OK
# ============================================================================

@router.get(
    "",
    response_model=List[WorkflowResponse],
    status_code=status.HTTP_200_OK,
    summary="List workflows for authenticated user's business",
)
def get_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all workflows for the authenticated user's business.

    **Access:** ADMIN or SUPERADMIN
    """
    business_id = get_user_business_id(current_user, db)
    validate_business_exists(db, business_id)

    try:
        workflows = get_workflows_service(db, business_id)
        return workflows

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Create Workflow → 201 CREATED
# ============================================================================

@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
)
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new workflow for the authenticated user's business.

    **Access:** ADMIN or SUPERADMIN
    """
    # Get business_id from authenticated user
    business_id = get_user_business_id(current_user, db)
    validate_business_exists(db, business_id)

    try:
        workflow = create_workflow_service(db, payload, business_id)
        return workflow

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Get Single Workflow → 200 OK
# ============================================================================

@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workflow",
)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get a workflow by ID for the authenticated user's business.

    **Access:** ADMIN or SUPERADMIN
    """
    business_id = get_user_business_id(current_user, db)
    validate_business_exists(db, business_id)

    try:
        workflow = get_workflow_service(db, workflow_id, business_id)
        return workflow

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Update Workflow → 200 OK
# ============================================================================

@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workflow",
)
def update_workflow(
    workflow_id: int,
    payload: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a workflow for the authenticated user's business.

    **Access:** ADMIN or SUPERADMIN
    """
    # Get business_id from authenticated user
    business_id = get_user_business_id(current_user, db)
    validate_business_exists(db, business_id)

    try:
        workflow = update_workflow_service(
            db,
            workflow_id,
            business_id,
            payload,
        )
        return workflow

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Delete Workflow → 200 OK
# ============================================================================

@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete workflow",
)
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a workflow for the authenticated user's business.

    **Access:** ADMIN or SUPERADMIN
    """
    business_id = get_user_business_id(current_user, db)
    validate_business_exists(db, business_id)

    try:
        delete_workflow_service(db, workflow_id, business_id)
        return {"detail": "Workflow deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

