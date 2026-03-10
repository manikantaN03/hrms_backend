from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.overtime import (
    OvertimePolicy,
    OvertimeRule,
)


# ============================================================
#                      POLICY REPOSITORY
# ============================================================

class OvertimePolicyRepository:

    def list(self, db: Session, business_id: int):
        """List all overtime policies for a business."""
        return (
            db.query(OvertimePolicy)
            .filter(OvertimePolicy.business_id == business_id)
            .all()
        )

    def create(self, db: Session, data):
        obj = OvertimePolicy(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, policy_id: int, business_id: int):
        """Get one policy + ensure it belongs to business."""
        return (
            db.query(OvertimePolicy)
            .filter(
                OvertimePolicy.id == policy_id,
                OvertimePolicy.business_id == business_id,
            )
            .first()
        )

    def update(self, db: Session, obj: OvertimePolicy, data):
        for key, value in data.dict(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: OvertimePolicy):
        db.delete(obj)
        db.commit()
        return True


# ============================================================
#                       RULE REPOSITORY
# ============================================================

class OvertimeRuleRepository:

    def list_by_policy(self, db: Session, policy_id: int, business_id: int):
        """List rules only for that business & policy."""
        return (
            db.query(OvertimeRule)
            .filter(
                OvertimeRule.policy_id == policy_id,
                OvertimeRule.business_id == business_id,
            )
            .all()
        )

    def create(self, db: Session, data):
        obj = OvertimeRule(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, rule_id: int, business_id: int):
        """Get specific rule only inside the business."""
        return (
            db.query(OvertimeRule)
            .filter(
                OvertimeRule.id == rule_id,
                OvertimeRule.business_id == business_id,
            )
            .first()
        )

    def update(self, db: Session, obj: OvertimeRule, data):
        for key, value in data.dict(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: OvertimeRule):
        db.delete(obj)
        db.commit()
        return True
