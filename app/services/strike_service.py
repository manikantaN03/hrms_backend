from sqlalchemy.orm import Session

from app.repositories.strike_repository import check_overlap
from app.models.strike_adjustment import StrikeAdjustment


def create_strike(db: Session, data):
    # Accept either a Pydantic model or a dict payload
    if isinstance(data, dict):
        payload = data
        business_id = payload.get("business_id")
    else:
        payload = data.model_dump()
        business_id = getattr(data, "business_id", None) or payload.get("business_id")

    if not business_id:
        raise ValueError("business_id is required")

    # Validate overlap
    overlap = check_overlap(
        db, payload.get("strike_type"), payload.get("strike_range_from"), payload.get("strike_range_to"), business_id
    )
    if overlap:
        raise ValueError("Overlapping strike range")

    obj = StrikeAdjustment(**payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_strike(db: Session, obj, data):
    # data is a Pydantic model; use model_dump to get values
    payload = data.model_dump()
    business_id = getattr(obj, "business_id", None)
    overlap = check_overlap(
        db,
        payload.get("strike_type"),
        payload.get("strike_range_from"),
        payload.get("strike_range_to"),
        business_id,
        exclude_id=obj.id,
    )

    if overlap:
        raise ValueError("Overlapping strike range")

    for k, v in payload.items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj
