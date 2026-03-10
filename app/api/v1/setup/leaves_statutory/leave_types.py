from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.schemas.leave_type import LeaveTypeCreate, LeaveTypeUpdate, LeaveTypeResponse
from app.services.leave_type_service import leave_type_service

# Prefix is provided by include_router(...) in app/api/v1/router.py
router = APIRouter()

@router.post("/", response_model=LeaveTypeResponse, status_code=201)
def create_leave_type(
    payload: LeaveTypeCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Create a leave type for a business. Admin must own the business."""
    biz_id = getattr(payload, "business_id", None)
    if not biz_id:
        if not current_admin.businesses:
            raise HTTPException(status_code=400, detail="No businesses found for this admin")
        biz_id = current_admin.businesses[0].id

    # Verify admin owns this business
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")

    return leave_type_service.create_leave_type(db, payload, biz_id)

@router.get("/", response_model=List[LeaveTypeResponse])
def get_leave_types(
    business_id: int = Query(..., description="Business ID (required)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get all leave types for a business (business_id required)."""
    if not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return leave_type_service.get_all(db, business_id)

@router.get("/{leave_type_id}", response_model=LeaveTypeResponse)
def get_leave_type(
    leave_type_id: int,
    business_id: int = Query(..., description="Business ID (required)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get a specific leave type for a business (business_id required)."""
    if not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return leave_type_service.get_one(db, leave_type_id, business_id)

@router.put("/{leave_type_id}", response_model=LeaveTypeResponse)
def update_leave_type(
    leave_type_id: int,
    payload: LeaveTypeUpdate,
    business_id: int = Query(..., description="Business ID (required)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update a leave type for a business (business_id required)."""
    if not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return leave_type_service.update(db, leave_type_id, payload, business_id)

@router.delete("/{leave_type_id}")
def delete_leave_type(
    leave_type_id: int,
    business_id: int = Query(..., description="Business ID (required)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a leave type for a business (business_id required)."""
    if not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    leave_type_service.delete(db, leave_type_id, business_id)
    return {"message": "Leave type deleted successfully", "id": leave_type_id}
