from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.compoff_rule import CompOffRule


# -------------------------------------------------------------------
# Create comp-off rule
# -------------------------------------------------------------------
def create_rule(db: Session, rule_data: dict) -> CompOffRule:
    """Create a new comp-off rule with validation."""
    # business_id is required to scope rules
    biz_id = rule_data.get("business_id")
    if not biz_id:
        raise HTTPException(status_code=400, detail="business_id is required")

    # Check if name already exists for this business
    existing = db.query(CompOffRule).filter(
        CompOffRule.name == rule_data.get("name"),
        CompOffRule.business_id == biz_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule with this name already exists for this business")

    # Validate
    validate_rule_data(rule_data)

    # Create rule
    new_rule = CompOffRule(**rule_data)
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


# -------------------------------------------------------------------
# Validate rule data
# -------------------------------------------------------------------
def validate_rule_data(data: dict):
    """Validate comp-off rule data."""
    if data.get("half_day_hours", 0) < 0 or data.get("half_day_mins", 0) < 0:
        raise HTTPException(status_code=400, detail="Half day hours/mins cannot be negative")

    if data.get("full_day_hours", 0) < 0 or data.get("full_day_mins", 0) < 0:
        raise HTTPException(status_code=400, detail="Full day hours/mins cannot be negative")

    if data.get("half_day_mins", 0) > 59 or data.get("full_day_mins", 0) > 59:
        raise HTTPException(status_code=400, detail="Minutes cannot exceed 59")

    if data.get("half_day_hours", 0) > 23 or data.get("full_day_hours", 0) > 23:
        raise HTTPException(status_code=400, detail="Hours cannot exceed 23")

    grant_type = data.get("grant_type", "grant_comp_off")
    if grant_type not in ["grant_comp_off", "add_to_extra_days"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid grant type. Must be 'grant_comp_off' or 'add_to_extra_days'"
        )

    if data.get("max_days", 0) < 0:
        raise HTTPException(status_code=400, detail="Max days cannot be negative")

    if data.get("expiry_days", 0) < 0:
        raise HTTPException(status_code=400, detail="Expiry days cannot be negative")



def get_or_create_rule(db: Session, rule_type: str, business_id: int) -> CompOffRule:
    """Get existing rule for a business or create a new default one.

    `business_id` is required to scope rules per business.
    """
    if not business_id:
        raise HTTPException(status_code=400, detail="business_id is required")

    rule = db.query(CompOffRule).filter(
        CompOffRule.rule_type == rule_type,
        CompOffRule.business_id == business_id,
    ).first()
    if not rule:
        # Generate a friendly name based on rule_type
        rule_names = {
            "weekly_offs": "Weekly Comp Off",
            "holidays": "Holiday Comp Off",
        }
        name = rule_names.get(rule_type, rule_type.replace("_", " ").title())
        
        rule = CompOffRule(
            name=name,
            rule_type=rule_type,
            business_id=business_id,
            auto_grant_enabled=False,
            half_day_hours=0,
            half_day_mins=0,
            full_day_hours=0,
            full_day_mins=0,
            grant_type="grant_comp_off"
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return rule


# -------------------------------------------------------------------
# Update comp-off rule
# -------------------------------------------------------------------
def update_rule(db: Session, rule_type: str, update_data: dict, business_id: int):
    """Update a comp-off rule with validation for a specific business."""
    rule = get_or_create_rule(db, rule_type, business_id)

    # Apply updates
    for field, value in update_data.items():
        if value is not None:
            setattr(rule, field, value)

    # Validation
    if rule.half_day_hours < 0 or rule.half_day_mins < 0:
        raise HTTPException(status_code=400, detail="Half day hours/mins cannot be negative")

    if rule.full_day_hours < 0 or rule.full_day_mins < 0:
        raise HTTPException(status_code=400, detail="Full day hours/mins cannot be negative")

    if rule.half_day_mins > 59 or rule.full_day_mins > 59:
        raise HTTPException(status_code=400, detail="Minutes cannot exceed 59")

    if rule.half_day_hours > 23 or rule.full_day_hours > 23:
        raise HTTPException(status_code=400, detail="Hours cannot exceed 23")

    if rule.grant_type not in ["grant_comp_off", "add_to_extra_days"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid grant type. Must be 'grant_comp_off' or 'add_to_extra_days'"
        )

    db.commit()
    db.refresh(rule)
    return rule


# -------------------------------------------------------------------
# Reset rules
# -------------------------------------------------------------------
def reset_rules(db: Session, business_id: int):
    """Reset comp-off rules for a specific business to default values."""
    weekly = get_or_create_rule(db, "weekly_offs", business_id)
    holiday = get_or_create_rule(db, "holidays", business_id)

    for rule in [weekly, holiday]:
        rule.auto_grant_enabled = False
        rule.half_day_hours = 0
        rule.half_day_mins = 0
        rule.full_day_hours = 0
        rule.full_day_mins = 0
        rule.grant_type = "grant_comp_off"

    db.commit()
    return {"message": "All comp off rules reset to default values"}


# -------------------------------------------------------------------
# Get rule
# -------------------------------------------------------------------
def get_rule(db: Session, rule_type: str, business_id: int) -> CompOffRule:
    """Get or create a comp-off rule for a business."""
    return get_or_create_rule(db, rule_type, business_id)


# -------------------------------------------------------------------
# Get all rules
# -------------------------------------------------------------------
def get_all_rules(db: Session, business_id: int):
    """Get all comp-off rules for a business."""
    return db.query(CompOffRule).filter(CompOffRule.business_id == business_id).all()
