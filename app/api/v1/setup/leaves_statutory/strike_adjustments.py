from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.strike_adjustment import (
    StrikeAdjustmentCreate,
    StrikeAdjustmentUpdate,
    StrikeAdjustmentResponse,
)
from app.models.strike_adjustment import StrikeAdjustment
from app.models.business import Business
from app.services.strike_service import create_strike, update_strike
from app.core.database import get_db
from app.api.v1.deps import get_current_admin, validate_business_access
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=StrikeAdjustmentResponse, status_code=201)
def create(
    adjustment: StrikeAdjustmentCreate,
    business_id: int = Path(..., description="Business id for validation"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    # Validate access to provided business_id
    validate_business_access(business_id, current_admin, db)

    # inject business_id into payload dict and create
    payload = adjustment.model_dump()
    payload["business_id"] = business_id
    try:
        return create_strike(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_all(
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get all strike adjustments. Optionally filter by `business_id` (admin must own it)."""
    if business_id:
        # verify business exists and admin owns it
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        return db.query(StrikeAdjustment).filter(StrikeAdjustment.business_id == business_id).all()

    # Default: scope to businesses owned by admin
    biz_ids = [b.id for b in getattr(current_admin, "businesses", [])]
    if not biz_ids:
        return []
    return db.query(StrikeAdjustment).filter(StrikeAdjustment.business_id.in_(biz_ids)).all()


@router.get("/{id}")
def get_by_id(
    id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    obj = db.query(StrikeAdjustment).filter(StrikeAdjustment.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not Found")

    # If business_id provided, validate it and admin ownership
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        if obj.business_id != business_id:
            raise HTTPException(status_code=404, detail="Not Found")

    else:
        # Verify ownership using admin's businesses
        biz_ids = [b.id for b in getattr(current_admin, "businesses", [])]
        if obj.business_id not in biz_ids:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")

    return obj


@router.put("/{id}", response_model=StrikeAdjustmentResponse)
def update(
    id: int,
    adjustment: StrikeAdjustmentUpdate = Body(...),
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    obj = db.query(StrikeAdjustment).filter(StrikeAdjustment.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not Found")

    # If business_id provided, validate and check ownership
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        if obj.business_id != business_id:
            raise HTTPException(status_code=404, detail="Not Found")
    else:
        # Verify ownership via admin's businesses
        biz = db.query(Business).filter(Business.id == obj.business_id).first()
        if not biz or biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")

    try:
        return update_strike(db, obj, adjustment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id}", status_code=200)
def delete(
    id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    obj = db.query(StrikeAdjustment).filter(StrikeAdjustment.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not Found")

    # If business_id provided, validate and check ownership
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        if obj.business_id != business_id:
            raise HTTPException(status_code=404, detail="Not Found")
    else:
        # Verify ownership via admin's businesses
        biz = db.query(Business).filter(Business.id == obj.business_id).first()
        if not biz or biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")

    db.delete(obj)
    db.commit()
    return {"message": "Deleted Successfully"}
