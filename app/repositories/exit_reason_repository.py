from sqlalchemy.orm import Session
from app.models.exit_reason import ExitReason
from app.schemas.exit_reason import ExitReasonCreate, ExitReasonUpdate


def create_exit_reason(db: Session, payload: ExitReasonCreate):
    reason = ExitReason(
        business_id=payload.business_id,      
        name=payload.name,
        esi_mapping=payload.esi_mapping,      
    )
    db.add(reason)
    db.commit()
    db.refresh(reason)
    return reason


def get_all_exit_reasons(db: Session, business_id: int):
    return (
        db.query(ExitReason)
        .filter(ExitReason.business_id == business_id)   
        .order_by(ExitReason.id.desc())
        .all()
    )


def get_exit_reason_by_id(db: Session, reason_id: int, business_id: int):
    return (
        db.query(ExitReason)
        .filter(
            ExitReason.id == reason_id,
            ExitReason.business_id == business_id   
        )
        .first()
    )


def update_exit_reason(db: Session, reason_id: int, business_id: int, payload: ExitReasonUpdate):
    reason = get_exit_reason_by_id(db, reason_id, business_id)
    if not reason:
        return None

    reason.name = payload.name
    reason.esi_mapping = payload.esi_mapping   

    db.commit()
    db.refresh(reason)
    return reason


def delete_exit_reason(db: Session, reason_id: int, business_id: int):
    reason = get_exit_reason_by_id(db, reason_id, business_id)
    if not reason:
        return False

    db.delete(reason)
    db.commit()
    return True
