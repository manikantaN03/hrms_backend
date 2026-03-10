from __future__ import annotations

import os
from typing import List, Optional, Any, Annotated
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business
from app.models.form16_models import PersonResponsible, EmployerInfo, CitInfo
from app.schemas.form16_schemas import (
    EmployerCreate,
    EmployerResponse,
    PersonResponsibleResponse,
    EmployerInfoResponse,
    EmployerInfoCreate,
    CITInfoResponse,
    CITInfoCreate,
)
from app.services.form16_service import get_form16_service
from app.repositories.form16_repository import Form16Repository

router = APIRouter()

# Use the project's uploads folder and create a `signatures` subfolder
UPLOAD_ROOT = Path(settings.UPLOAD_DIR)
UPLOAD_DIR = UPLOAD_ROOT / "signatures"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_URL_PATH = f"/{UPLOAD_ROOT.name}/signatures"

MODELS_AVAILABLE = True


async def save_upload_file(file: UploadFile, allow_empty: bool = False) -> str | None:
    """Validate and save an uploaded image file.

    If `allow_empty` is True and the uploaded file is empty, return None (no file saved).
    Otherwise returns a URL path string for the saved file.
    """
    contents = await file.read()

    # If empty upload and caller allows empty, treat as no-op
    if allow_empty and (not contents or len(contents) == 0):
        return None

    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds limit")

    if not file.content_type or file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"signature_{int(datetime.utcnow().timestamp())}.{ext}"
    dest_path = UPLOAD_DIR / unique_filename
    with open(dest_path, "wb") as buffer:
        buffer.write(contents)

    # Return a URL path that can be served by the static files mount
    return f"{UPLOAD_URL_PATH}/{unique_filename}"


# Note: text-signature fallback removed. API now expects a binary `file` upload for signatures.


def delete_file(path: str):
    try:
        if not path:
            return

        # If path is a URL path like '/uploads/signatures/name.ext', convert to file system path
        if path.startswith(UPLOAD_URL_PATH):
            filename = path.split("/")[-1]
            fs_path = UPLOAD_DIR / filename
        else:
            fs_path = Path(path)

        if fs_path.exists():
            fs_path.unlink()
    except Exception:
        pass


def _resolve_business_id(current_user: Any, db: Session, business_id: Optional[int] = None) -> Optional[int]:
    """Resolve business_id from provided value, user context, or user's businesses list."""
    bid = business_id or getattr(current_user, "business_id", None)
    if bid is None:
        try:
            businesses = getattr(current_user, "businesses", None)
            if businesses:
                bid = businesses[0].id
        except Exception:
            bid = None
    return bid


def person_responsible_to_dict(record: Any) -> dict:
    return {
        "id": getattr(record, "id", None),
        "fullName": getattr(record, "full_name", None),
        "designation": getattr(record, "designation", None),
        "fatherName": getattr(record, "father_name", None),
        "signaturePath": getattr(record, "signature_path", None),
        "business_id": getattr(record, "business_id", None),
        "created_at": getattr(record, "created_at", None),
        "updated_at": getattr(record, "updated_at", None),
    }


def employer_info_to_dict(record: Any) -> dict:
    return {
        "id": getattr(record, "id", None),
        "name": getattr(record, "name", None),
        "address1": getattr(record, "address1", None),
        "address2": getattr(record, "address2", None),
        "address3": getattr(record, "address3", None),
        "placeOfIssue": getattr(record, "place_of_issue", None),
        "business_id": getattr(record, "business_id", None),
        "created_at": getattr(record, "created_at", None),
        "updated_at": getattr(record, "updated_at", None),
    }


@router.get("/")
def read_root():
    return {
        "message": "Form 16 Info API is running",
        "version": "1.0.0",
        "endpoints": {
            "person": "/api/v1/form16/person",
            "employer": "/api/v1/form16/employer",
            "cit": "/api/v1/form16/cit",
        },
    }


# ==================== PERSON RESPONSIBLE ROUTES ====================

@router.post("/person", response_model=PersonResponsibleResponse)
async def create_person_responsible(
    fullName: str = Form(...),
    designation: str = Form(...),
    fatherName: str = Form(...),
    file: UploadFile = File(...),
    business_id: int = Form(...),  # REQUIRED in payload
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    # save file
    signature_path = await save_upload_file(file)

    payload = {
        "fullName": fullName,
        "designation": designation,
        "fatherName": fatherName,
        "business_id": business_id,
    }

    repo = Form16Repository(db)
    person = repo.create_person(payload, signature_path=signature_path)

    return {
        "id": person.id,
        "fullName": person.full_name,
        "designation": person.designation,
        "fatherName": person.father_name,
        "signaturePath": person.signature_path,
        "business_id": person.business_id,
        "created_at": person.created_at,
        "updated_at": person.updated_at,
    }


@router.get("/person", response_model=List[PersonResponsibleResponse])
def get_all_person_responsible(skip: int = 0, limit: int = 100, business_id: int = Query(..., description="business_id is required"), db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    q = db.query(PersonResponsible)
    if business_id is not None:
        q = q.filter(PersonResponsible.business_id == business_id)
    records = q.offset(skip).limit(limit).all()
    return [person_responsible_to_dict(r) for r in records]


@router.get("/person/{record_id}", response_model=PersonResponsibleResponse)
def get_person_responsible(record_id: int, business_id: int = Query(..., description="business_id is required"), db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(PersonResponsible).filter(PersonResponsible.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if business_id is not None and getattr(record, "business_id", None) != business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Record does not belong to the given business_id")
    return person_responsible_to_dict(record)


@router.put("/person/{record_id}", response_model=PersonResponsibleResponse)
async def update_person_responsible(
    record_id: int,
    fullName: str = Form(...),
    designation: str = Form(...),
    fatherName: str = Form(...),
    file: UploadFile = File(None),  # Make file optional for updates
    business_id: int = Form(...),  # REQUIRED
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(PersonResponsible).filter(PersonResponsible.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # resolve business context: payload preferred, else user context
    bid = business_id or getattr(current_user, "business_id", None)
    if bid is None:
        try:
            businesses = getattr(current_user, "businesses", None)
            if businesses:
                bid = businesses[0].id
        except Exception:
            bid = None

    if bid is not None and getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this record for the given business_id")
    
    try:
        record.full_name = fullName
        record.designation = designation
        record.father_name = fatherName

        # Handle signature update: only update if new file is provided
        if file and file.filename:
            new_path = await save_upload_file(file, allow_empty=False)
            if new_path:
                if record.signature_path:
                    delete_file(record.signature_path)
                record.signature_path = new_path

        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)

        return person_responsible_to_dict(record)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating record: {str(e)}")


@router.delete("/person/{record_id}")
def delete_person_responsible(
    record_id: int,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(PersonResponsible).filter(PersonResponsible.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.signature_path:
        delete_file(record.signature_path)

    # resolve business context for delete
    bid = business_id or getattr(current_user, "business_id", None)
    if bid is None:
        try:
            businesses = getattr(current_user, "businesses", None)
            if businesses:
                bid = businesses[0].id
        except Exception:
            bid = None

    if bid is not None and getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this record for the given business_id")
    
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully", "id": record_id}


# ==================== EMPLOYER INFO ROUTES ====================

@router.post("/employer", response_model=EmployerInfoResponse, status_code=status.HTTP_201_CREATED)
def create_employer_info(
    employer_data: EmployerInfoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")
 
    # business_id provided as required query param; resolve/validate
    bid = _resolve_business_id(current_user, db, business_id)
    if not bid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business context missing")
 
    # validate business exists
    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Business with id {bid} does not exist.")
 
    try:
        db_employer = EmployerInfo(
            name=employer_data.name,
            address1=employer_data.address1,
            address2=employer_data.address2,
            address3=employer_data.address3,
            place_of_issue=employer_data.placeOfIssue,
            business_id=bid,
        )
 
        db.add(db_employer)
        db.commit()
        db.refresh(db_employer)
 
        return employer_info_to_dict(db_employer)
 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating record: {str(e)}")


@router.get("/employer", response_model=List[EmployerInfoResponse])
def get_all_employer_info(
    skip: int = 0,
    limit: int = 100,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    q = db.query(EmployerInfo)
    if business_id is not None:
        q = q.filter(EmployerInfo.business_id == business_id)
    records = q.offset(skip).limit(limit).all()
    return [employer_info_to_dict(r) for r in records]


@router.get("/employer/{record_id}", response_model=EmployerInfoResponse)
def get_employer_info(record_id: int, business_id: int = Query(..., description="business_id is required"), db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(EmployerInfo).filter(EmployerInfo.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if business_id is not None and getattr(record, "business_id", None) != business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Record does not belong to the given business_id")
    
    return employer_info_to_dict(record)


@router.put("/employer/{record_id}", response_model=EmployerInfoResponse)
def update_employer_info(
    record_id: int,
    employer_data: EmployerInfoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(EmployerInfo).filter(EmployerInfo.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # business_id provided as required query param; validate access/ownership
    bid = _resolve_business_id(current_user, db, business_id)
    if bid is None or getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this record for the given business_id")
    
    try:
        record.name = employer_data.name
        record.address1 = employer_data.address1
        record.address2 = employer_data.address2
        record.address3 = employer_data.address3
        record.place_of_issue = employer_data.placeOfIssue
        record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(record)

        return employer_info_to_dict(record)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating record: {str(e)}")


@router.delete("/employer/{record_id}")
def delete_employer_info(
    record_id: int,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(EmployerInfo).filter(EmployerInfo.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # If business_id provided, ensure record belongs to it; otherwise try user context
    bid = business_id or getattr(current_user, "business_id", None)
    if bid is None:
        try:
            businesses = getattr(current_user, "businesses", None)
            if businesses:
                bid = businesses[0].id
        except Exception:
            bid = None

    if bid is not None and getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this record for the given business_id")
    
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully", "id": record_id}


# ==================== CIT INFO ROUTES ====================

@router.post("/cit", response_model=CITInfoResponse, status_code=status.HTTP_201_CREATED)
def create_cit_info(
    cit_data: CITInfoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    # resolve business_id from user context (no query param)
    bid = _resolve_business_id(current_user, db, None)
    if not bid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business context missing")
    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Business with id {bid} does not exist.")
 
    try:
        repo = Form16Repository(db)
        payload = cit_data.model_dump()
        payload["business_id"] = bid
        db_cit = repo.create_cit(payload)  # ensures commit + refresh
 
        return {
            "id": db_cit.id,
            "name": db_cit.name,
            "address1": db_cit.address1,
            "address2": db_cit.address2,
            "address3": db_cit.address3,
            "business_id": db_cit.business_id,
            "created_at": db_cit.created_at,
            "updated_at": db_cit.updated_at,
        }
 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating record: {str(e)}")


@router.get("/cit", response_model=List[CITInfoResponse])
def get_all_cit_info(
    skip: int = 0,
    limit: int = 100,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    # business_id provided as required query param; resolve/validate
    bid = _resolve_business_id(current_user, db, business_id)
    if not bid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business context missing")
 
    q = db.query(CitInfo).filter(CitInfo.business_id == bid)
    records = q.offset(skip).limit(limit).all()
    return [ 
        {
            "id": r.id,
            "name": r.name,
            "address1": r.address1,
            "address2": r.address2,
            "address3": r.address3,
            "business_id": r.business_id,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        } for r in records
    ]


@router.get("/cit/{record_id}", response_model=CITInfoResponse)
def get_cit_info(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(CitInfo).filter(CitInfo.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    bid = _resolve_business_id(current_user, db, business_id)
    if not bid or getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Record does not belong to the given business_id")

    return {
        "id": record.id,
        "name": record.name,
        "address1": record.address1,
        "address2": record.address2,
        "address3": record.address3,
        "business_id": record.business_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.put("/cit/{record_id}", response_model=CITInfoResponse)
def update_cit_info(
    record_id: int,
    cit_data: CITInfoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(CitInfo).filter(CitInfo.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    bid = _resolve_business_id(current_user, db, business_id)
    if not bid or getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this record for the given business_id")
    
    try:
        record.name = cit_data.name
        record.address1 = cit_data.address1
        record.address2 = cit_data.address2
        record.address3 = cit_data.address3
        record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(record)

        return {
            "id": record.id,
            "name": record.name,
            "address1": record.address1,
            "address2": record.address2,
            "address3": record.address3,
            "business_id": record.business_id,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating record: {str(e)}")


@router.delete("/cit/{record_id}")
def delete_cit_info(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Form16 models/schemas not available")

    record = db.query(CitInfo).filter(CitInfo.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    bid = _resolve_business_id(current_user, db, business_id)
    if bid is None or getattr(record, "business_id", None) != bid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this record for the given business_id")
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully", "id": record_id}


@router.post("/form16/employer", response_model=EmployerResponse, status_code=status.HTTP_201_CREATED)
def create_employer(employer: EmployerCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    service = get_form16_service(db)
    payload = employer.model_dump()
    # resolve business_id: prefer provided, then admin.business_id, then admin.businesses[0]
    bid = payload.get("business_id") or getattr(current_admin, "business_id", None)
    if not bid:
        businesses = getattr(current_admin, "businesses", None)
        if businesses:
            bid = businesses[0].id
    if not bid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="business_id missing")
    if not db.query(Business).filter(Business.id == bid).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Business {bid} not found")
    payload["business_id"] = bid
    created = service.create_employer(payload, business_id=bid)
    # Return a mapped dict so camelCase `placeOfIssue` is populated from the ORM field
    return employer_info_to_dict(created)
