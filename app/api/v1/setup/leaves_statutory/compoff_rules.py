from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas.compoff_rule_schema import (
    CompOffRuleCreate,
    CompOffRuleUpdate,
    CompOffRuleResponse,
)
from app.services.compoff_rule_service import (
    create_rule,
    get_or_create_rule,
    update_rule,
    reset_rules,
)
from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

router = APIRouter()


# -------------------------------------------------------------------
# Create Rule
# -------------------------------------------------------------------
@router.post("", response_model=CompOffRuleResponse, status_code=201)
def create_comp_off_rule(
    data: CompOffRuleCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Create a new Comp Off rule for a business. Admin must own the business."""
    biz_id = getattr(data, "business_id", None)
    if not biz_id:
        if not current_admin.businesses:
            raise HTTPException(status_code=400, detail="No businesses found for this admin")
        biz_id = current_admin.businesses[0].id

    # verify ownership
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")

    payload = data.dict()
    payload["business_id"] = biz_id
    return create_rule(db, payload)


# -------------------------------------------------------------------
# Get Rules
# -------------------------------------------------------------------
@router.get("/weekly-offs", response_model=CompOffRuleResponse)
def get_weekly_offs_rule(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    """Get Comp Off rules for weekly offs."""
    # prefer provided business_id, otherwise fall back to admin's first business
    biz_id = business_id or (current_admin.businesses[0].id if current_admin.businesses else None)
    if not biz_id:
        raise HTTPException(status_code=400, detail="No businesses found for this admin")
    # verify ownership
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return get_or_create_rule(db, "weekly_offs", biz_id)


@router.get("/holidays", response_model=CompOffRuleResponse)
def get_holidays_rule(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    """Get Comp Off rules for holidays."""
    biz_id = business_id or (current_admin.businesses[0].id if current_admin.businesses else None)
    if not biz_id:
        raise HTTPException(status_code=400, detail="No businesses found for this admin")
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return get_or_create_rule(db, "holidays", biz_id)


# -------------------------------------------------------------------
# Update Rules
# -------------------------------------------------------------------
@router.put("/weekly-offs", response_model=CompOffRuleResponse)
def update_weekly_rule(
    data: CompOffRuleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    """Update Comp Off rules for weekly offs."""
    biz_id = business_id or (current_admin.businesses[0].id if current_admin.businesses else None)
    if not biz_id:
        raise HTTPException(status_code=400, detail="No businesses found for this admin")
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return update_rule(db, "weekly_offs", data.dict(exclude_unset=True), biz_id)


@router.put("/holidays", response_model=CompOffRuleResponse)
def update_holiday_rule(
    data: CompOffRuleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    """Update Comp Off rules for holidays."""
    biz_id = business_id or (current_admin.businesses[0].id if current_admin.businesses else None)
    if not biz_id:
        raise HTTPException(status_code=400, detail="No businesses found for this admin")
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return update_rule(db, "holidays", data.dict(exclude_unset=True), biz_id)


# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
@router.get("/summary")
def rules_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    """Get summary of all Comp Off rules."""
    biz_id = business_id or (current_admin.businesses[0].id if current_admin.businesses else None)
    if not biz_id:
        raise HTTPException(status_code=400, detail="No businesses found for this admin")
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")

    weekly = get_or_create_rule(db, "weekly_offs", biz_id)
    holiday = get_or_create_rule(db, "holidays", biz_id)

    return {
        "weekly_offs": {
            "auto_grant_enabled": weekly.auto_grant_enabled,
            "half_day_threshold_minutes": weekly.half_day_hours * 60 + weekly.half_day_mins,
            "full_day_threshold_minutes": weekly.full_day_hours * 60 + weekly.full_day_mins,
            "grant_type": weekly.grant_type,
        },
        "holidays": {
            "auto_grant_enabled": holiday.auto_grant_enabled,
            "half_day_threshold_minutes": holiday.half_day_hours * 60 + holiday.half_day_mins,
            "full_day_threshold_minutes": holiday.full_day_hours * 60 + holiday.full_day_mins,
            "grant_type": holiday.grant_type,
        },
    }


# -------------------------------------------------------------------
# Reset
# -------------------------------------------------------------------
@router.post("/reset")
def reset_all_rules(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    """Reset all Comp Off rules to default values."""
    biz_id = business_id or (current_admin.businesses[0].id if current_admin.businesses else None)
    if not biz_id:
        raise HTTPException(status_code=400, detail="No businesses found for this admin")
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return reset_rules(db, biz_id)
