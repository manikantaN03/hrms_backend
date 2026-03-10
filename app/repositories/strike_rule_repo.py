from sqlalchemy.orm import Session

from app.models.strike_rule import StrikeRule
from app.schemas.strike_rule import StrikeRuleCreate, StrikeRuleUpdate


def get_strike_rule(db: Session, rule_id: int):
    return db.query(StrikeRule).filter(StrikeRule.id == rule_id).first()


def get_strike_rules(db: Session, rule_type: str = None, business_id: int = None):
    query = db.query(StrikeRule)
    if rule_type:
        query = query.filter(StrikeRule.rule_type == rule_type)
    if business_id is not None:
        query = query.filter(StrikeRule.business_id == business_id)
    return query.order_by(StrikeRule.rule_type, StrikeRule.minutes).all()


def create_strike_rule(db: Session, rule: StrikeRuleCreate):
    data = rule.dict()
    # ensure business_id provided
    if not data.get("business_id"):
        raise ValueError("business_id is required")
    db_rule = StrikeRule(**data)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def update_strike_rule(db: Session, db_rule: StrikeRule, rule_update: StrikeRuleUpdate):
    update_data = rule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def delete_strike_rule(db: Session, db_rule: StrikeRule):
    db.delete(db_rule)
    db.commit()


def delete_rules_by_type(db: Session, rule_type: str):
    deleted_count = db.query(StrikeRule).filter(StrikeRule.rule_type == rule_type).delete()
    db.commit()
    return deleted_count


def reset_all_strike_rules(db: Session):
    deleted_count = db.query(StrikeRule).delete()
    db.commit()
    return deleted_count
