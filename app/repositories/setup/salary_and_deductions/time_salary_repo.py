from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.time_salary import TimeSalaryRule
from app.schemas.setup.salary_and_deductions.time_salary import TimeRuleCreate, TimeRuleUpdate


class TimeSalaryRuleRepository:

    def list(self, db: Session, business_id: int):
        """List all rules for a given business."""
        return db.query(TimeSalaryRule).filter(
            TimeSalaryRule.business_id == business_id
        ).all()

    def list_by_component(self, db: Session, business_id: int, component_id: int):
        """List rules filtered by business + component."""
        return db.query(TimeSalaryRule).filter(
            TimeSalaryRule.business_id == business_id,
            TimeSalaryRule.component_id == component_id
        ).all()

    def create(self, db: Session, data: TimeRuleCreate):
        obj = TimeSalaryRule(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, rule_id: int, business_id: int):
        """Get rule only if it belongs to the business."""
        return db.query(TimeSalaryRule).filter(
            TimeSalaryRule.id == rule_id,
            TimeSalaryRule.business_id == business_id
        ).first()

    def update(self, db: Session, obj: TimeSalaryRule, data: TimeRuleUpdate):
        update_data = data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: TimeSalaryRule):
        db.delete(obj)
        db.commit()
        return True
