from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from typing import List
import re

from app.core.database import get_db
from app.models.tds24q_models import TDS24Q
from app.models.business import Business
from app.schemas.tds24q_schemas import TDS24QCreate, TDS24QUpdate, TDS24QResponse
from app.repositories.tds24q_repository import tds24q_repository as repo
from app.api.v1.deps import get_current_admin
router = APIRouter()

def _camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

@router.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "TDS 24Q API is running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "create": "POST /api/v1/setup/tds24q",
            "get_all": "GET /api/v1/setup/tds24q",
            "get_one": "GET /api/v1/setup/tds24q/{id}",
            "update": "PUT /api/v1/setup/tds24q/{id}",
            "delete": "DELETE /api/v1/setup/tds24q/{id}"
        }
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_tds_record(
    tds_data: TDS24QCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Create a new TDS 24Q record with business_id resolved from payload (preferred) or current user."""
    raw = tds_data.model_dump() if hasattr(tds_data, "model_dump") else tds_data.dict()
    business_id = raw.get("business_id") or getattr(current_user, "business_id", None)
    if business_id is None:
        try:
            businesses = getattr(current_user, "businesses", None)
            if businesses:
                business_id = businesses[0].id
        except Exception:
            business_id = None
    if not business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business context missing")

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Business with id {business_id} does not exist. Create the business before adding TDS 24Q."
        )

    # Use the validated Pydantic model, convert to dict, attach business_id and pass to repo.
    raw["business_id"] = business_id

    try:
        result = repo.create_tds24q(db, raw)  # pass dict (repo updated to accept dict)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error creating record: {str(e)}")


@router.get("", response_model=List[dict])
def get_all_tds_records(skip: int = 0, limit: int = 100, business_id: int = Query(..., description="business_id is required"), db: Session = Depends(get_db)):
    """Get all TDS 24Q records for a business with pagination"""
    result = repo.get_all_tds24q(db, skip, limit)
    # filter by business_id to ensure only requested business records returned
    return [r for r in result if r.get("business_id") == business_id]


@router.get("/{record_id}", response_model=dict)
def get_tds_record(record_id: int, business_id: int = Query(..., description="business_id is required"), db: Session = Depends(get_db)):
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
    business_id: int = Query(..., description="business_id is required"),
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
def delete_tds_record(record_id: int, business_id: int = Query(..., description="business_id is required"), db: Session = Depends(get_db)):
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
