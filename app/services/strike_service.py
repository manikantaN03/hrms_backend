from sqlalchemy.orm import Session

from app.repositories.strike_repository import check_overlap
from app.models.strike_adjustment import StrikeAdjustment


def create_strike(db: Session, data):
    business_id = getattr(data, "business_id", None) or data.model_dump().get("business_id")
    if not business_id:
        raise ValueError("business_id is required")

    overlap = check_overlap(
        db, data.strike_type, data.strike_range_from, data.strike_range_to, business_id
    )
    if overlap:
        raise ValueError("Overlapping strike range")

    obj = StrikeAdjustment(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_strike(db: Session, obj, data):
    business_id = getattr(obj, "business_id", None)
    overlap = check_overlap(
        db,
        data.strike_type,
        data.strike_range_from,
        data.strike_range_to,
        business_id,
        exclude_id=obj.id,
    )

    if overlap:
        raise ValueError("Overlapping strike range")

    for k, v in data.model_dump().items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj
