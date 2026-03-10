from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.exit_reason_repository import (
    create_exit_reason,
    get_all_exit_reasons,
    get_exit_reason_by_id,
    update_exit_reason,
    delete_exit_reason,
)
from app.schemas.exit_reason import ExitReasonCreate, ExitReasonUpdate

def create_exit_reason_service(db: Session, payload: ExitReasonCreate):
    return create_exit_reason(db, payload)


def get_exit_reasons_service(db: Session, business_id: int):
    return get_all_exit_reasons(db, business_id)


def update_exit_reason_service(db: Session, reason_id: int, business_id: int, payload: ExitReasonUpdate):
    updated = update_exit_reason(db, reason_id, business_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Exit reason not found")
    return updated


def delete_exit_reason_service(db: Session, reason_id: int, business_id: int):
    deleted = delete_exit_reason(db, reason_id, business_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Exit reason not found")
    return {"message": "Exit reason deleted successfully"}
