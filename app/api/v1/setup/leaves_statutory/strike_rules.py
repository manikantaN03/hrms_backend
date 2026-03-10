from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.strike_rule import StrikeRuleCreate, StrikeRuleResponse, StrikeRuleUpdate
from app.repositories.strike_rule_repo import (
    get_strike_rule,
    get_strike_rules,
    create_strike_rule,
    update_strike_rule,
    delete_strike_rule,
    delete_rules_by_type,
)
from app.core.database import  get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business

router = APIRouter()

valid_rule_types = ["Early Coming", "Late Coming", "Early Going", "Late Going", "Late Lunch"]
valid_strikes = ["None", "Green", "Orange", "Red", "Yellow"]
valid_adjustments = ["No Adjustment", "Ignore Late/Early", "Round"]
valid_directions = ["next", "previous"]


@router.post("/", response_model=StrikeRuleResponse, status_code=201)
def create_rule(rule: StrikeRuleCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    if rule.rule_type not in valid_rule_types:
        raise HTTPException(400, f"Invalid rule type. Must be one of: {valid_rule_types}")
    if rule.strike not in valid_strikes:
        raise HTTPException(400, f"Invalid strike. Must be one of: {valid_strikes}")
    if rule.time_adjustment not in valid_adjustments:
        raise HTTPException(400, f"Invalid time adjustment. Must be one of: {valid_adjustments}")
    if rule.round_direction not in valid_directions:
        raise HTTPException(400, "Round direction must be 'next' or 'previous'")
    if rule.minutes < 0 or rule.round_minutes < 0:
        raise HTTPException(400, "Minutes and round_minutes cannot be negative")
    # validate business exists and admin owns it
    biz_id = getattr(rule, "business_id", None) or getattr(rule, "dict", lambda: {})().get("business_id")
    if not biz_id:
        raise HTTPException(status_code=400, detail="business_id is required")
    biz = db.query(Business).filter(Business.id == biz_id).first()
    if not biz:
        raise HTTPException(status_code=400, detail="Business not found")
    if biz.owner_id != current_admin.id:
        raise HTTPException(status_code=403, detail="You don't have access to this business")

    return create_strike_rule(db, rule)


@router.get("/", response_model=List[StrikeRuleResponse])
def read_rules(
    rule_type: Optional[str] = None,
    business_id: int = Query(..., description="Business id for validation"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if rule_type and rule_type not in valid_rule_types:
        raise HTTPException(400, f"Invalid rule type. Must be one of: {valid_rule_types}")
    # if business_id provided, validate ownership
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
    else:
        # scope to admin's businesses
        biz_ids = [b.id for b in getattr(current_admin, "businesses", [])]
        if biz_ids:
            # pass business filter to repo
            return get_strike_rules(db, rule_type, None) if business_id is None else get_strike_rules(db, rule_type, business_id)
    return get_strike_rules(db, rule_type, business_id)


@router.get("/{rule_id}", response_model=StrikeRuleResponse)
def read_rule(rule_id: int, business_id: int = Query(..., description="Business id for validation"), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    db_rule = get_strike_rule(db, rule_id)
    if not db_rule:
        raise HTTPException(404, "Strike rule not found")
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        if db_rule.business_id != business_id:
            raise HTTPException(status_code=404, detail="Strike rule not found for this business")
    else:
        biz_ids = [b.id for b in getattr(current_admin, "businesses", [])]
        if db_rule.business_id not in biz_ids:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")
    return db_rule


@router.get("/type/{rule_type}", response_model=List[StrikeRuleResponse])
def read_rules_by_type(
    rule_type: str,
    business_id: int = Query(..., description="Business id for validation"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if rule_type not in valid_rule_types:
        raise HTTPException(400, f"Invalid rule type. Must be one of: {valid_rule_types}")
    # validate business and admin access
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=400, detail="Business not found")
    if biz.owner_id != current_admin.id:
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return get_strike_rules(db, rule_type, business_id)


@router.put("/{rule_id}", response_model=StrikeRuleResponse)
def update_rule(rule_id: int, rule_update: StrikeRuleUpdate, business_id: int = Query(..., description="Business id for validation"), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    db_rule = get_strike_rule(db, rule_id)
    if not db_rule:
        raise HTTPException(404, "Strike rule not found")
    if rule_update.strike and rule_update.strike not in valid_strikes:
        raise HTTPException(400, f"Invalid strike. Must be one of: {valid_strikes}")
    if rule_update.time_adjustment and rule_update.time_adjustment not in valid_adjustments:
        raise HTTPException(400, f"Invalid time adjustment. Must be one of: {valid_adjustments}")
    if rule_update.minutes is not None and rule_update.minutes < 0:
        raise HTTPException(400, "Minutes cannot be negative")
    if rule_update.round_minutes is not None and rule_update.round_minutes < 0:
        raise HTTPException(400, "Round minutes cannot be negative")
    # business validation
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        if db_rule.business_id != business_id:
            raise HTTPException(status_code=404, detail="Strike rule not found for this business")
    else:
        biz = db.query(Business).filter(Business.id == db_rule.business_id).first()
        if not biz or biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")

    return update_strike_rule(db, db_rule, rule_update)


@router.delete("/{rule_id}", status_code=200)
def delete_rule(rule_id: int, business_id: int = Query(..., description="Business id for validation"), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    db_rule = get_strike_rule(db, rule_id)
    if not db_rule:
        raise HTTPException(404, "Strike rule not found")
    if business_id is not None:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            raise HTTPException(status_code=400, detail="Business not found")
        if biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this business")
        if db_rule.business_id != business_id:
            raise HTTPException(status_code=404, detail="Strike rule not found for this business")
    else:
        biz = db.query(Business).filter(Business.id == db_rule.business_id).first()
        if not biz or biz.owner_id != current_admin.id:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")
    delete_strike_rule(db, db_rule)
    return {"message": "Strike rule deleted successfully", "id": rule_id}

@router.get("/summary/all")
def get_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="Business id for validation"),
):
    # validate business and admin access
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=400, detail="Business not found")
    if biz.owner_id != current_admin.id:
        raise HTTPException(status_code=403, detail="You don't have access to this business")

    summary = {}
    for rule_type in valid_rule_types:
        rules = get_strike_rules(db, rule_type, business_id)
        summary[rule_type] = {
            "count": len(rules),
            "rules": [
                {
                    "id": r.id,
                    "minutes": r.minutes,
                    "strike": r.strike,
                    "time_adjustment": r.time_adjustment,
                    "full_day_only": r.full_day_only,
                }
                for r in rules
            ],
        }
    return summary


@router.post("/reset", status_code=200)
def reset_rules(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    # Reset endpoint removed - keep for backward compatibility placeholder
    raise HTTPException(status_code=404, detail="Endpoint removed")
