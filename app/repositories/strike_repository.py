from sqlalchemy.orm import Session

from app.models.strike_adjustment import StrikeAdjustment


def check_overlap(db: Session, strike_type, from_val, to_val, business_id, exclude_id=None):
    query = db.query(StrikeAdjustment).filter(
        StrikeAdjustment.strike_type == strike_type,
        StrikeAdjustment.business_id == business_id,
        StrikeAdjustment.strike_range_from <= to_val,
        StrikeAdjustment.strike_range_to >= from_val,
    )

    if exclude_id:
        query = query.filter(StrikeAdjustment.id != exclude_id)

    return query.first()
