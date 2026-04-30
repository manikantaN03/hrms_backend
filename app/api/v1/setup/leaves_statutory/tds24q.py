from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List
import re

from app.core.database import get_db
from app.models.tds24q_models import TDS24Q
from app.models.business import Business
from app.schemas.tds24q_schemas import TDS24QCreate, TDS24QUpdate, TDS24QResponse
from app.repositories.tds24q_repository import tds24q_repository as repo
from app.api.v1.deps import get_current_admin, validate_business_access
router = APIRouter()

def _camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

@router.get("/")
def read_root(business_id: int = Path(...), db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    """Root endpoint with API information (business-scoped)"""
    # Validate admin access to the business path param
    validate_business_access(business_id, current_user, db)

    return {
        "message": "TDS 24Q API is running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "create": "POST /api/v1/{business_id}/setup/tds24q",
            "get_all": "GET /api/v1/{business_id}/setup/tds24q",
            "get_one": "GET /api/v1/{business_id}/setup/tds24q/{id}",
            "update": "PUT /api/v1/{business_id}/setup/tds24q/{id}",
            "delete": "DELETE /api/v1/{business_id}/setup/tds24q/{id}"
        }
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_tds_record(
    business_id: int = Path(...),
    tds_data: TDS24QCreate = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Create a new TDS 24Q record for the given business_id."""
    # Validate admin access to provided business_id
    validate_business_access(business_id, current_user, db)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Business with id {business_id} does not exist. Create the business before adding TDS 24Q."
        )

    raw = tds_data.model_dump() if hasattr(tds_data, "model_dump") else tds_data.dict()
    raw["business_id"] = business_id

    try:
        result = repo.create_tds24q(db, raw)  # pass dict (repo updated to accept dict)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error creating record: {str(e)}")


@router.get("", response_model=List[dict])
def get_all_tds_records(skip: int = 0, limit: int = 100, business_id: int = Path(...), db: Session = Depends(get_db)):
    """Get all TDS 24Q records for a business with pagination"""
    result = repo.get_all_tds24q(db, skip, limit)
    # filter by business_id to ensure only requested business records returned
    return [r for r in result if r.get("business_id") == business_id]


@router.get("/{record_id}", response_model=dict)
def get_tds_record(record_id: int, business_id: int = Path(...), db: Session = Depends(get_db)):
    """Get a specific TDS 24Q record by ID (must belong to business_id)"""
    result = repo.get_tds24q(db, record_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if result.get("business_id") != business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Record does not belong to the given business_id")
    return result


@router.put("/{record_id}", response_model=dict)
def update_tds_record(
    record_id: int,
    tds_data: TDS24QUpdate,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Update a TDS 24Q record (must belong to business_id)"""
    existing = repo.get_tds24q(db, record_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if existing.get("business_id") != business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this record for the given business_id")
    try:
        result = repo.update_tds24q(db, record_id, tds_data)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error updating record: {str(e)}")


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tds_record(record_id: int, business_id: int = Path(...), db: Session = Depends(get_db)):
    """Delete a TDS 24Q record by id (must belong to business_id)."""
    existing = repo.get_tds24q(db, record_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if existing.get("business_id") != business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this record for the given business_id")
    deleted = repo.delete_tds24q(db, record_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return {"message": "Record deleted successfully", "id": record_id}
