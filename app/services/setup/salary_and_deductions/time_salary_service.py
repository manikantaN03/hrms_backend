from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.setup.salary_and_deductions.time_salary_repo import TimeSalaryRuleRepository
from app.schemas.setup.salary_and_deductions.time_salary import TimeRuleCreate, TimeRuleUpdate


class TimeSalaryRuleService:

    def __init__(self):
        self.repo = TimeSalaryRuleRepository()

    def list(self, db: Session, business_id: int, component_id: int = None):
        """List rules for business, optionally filtered by component."""
        if component_id:
            return self.repo.list_by_component(db, business_id, component_id)
        else:
            return self.repo.list(db, business_id)

    def create(self, db: Session, data: TimeRuleCreate):
        """Create rule — data already contains business_id + component_id."""
        return self.repo.create(db, data)

    def update(self, db: Session, rule_id: int, business_id: int, data: TimeRuleUpdate):
        """Update only if rule belongs to the same business."""
        obj = self.repo.get(db, rule_id, business_id)
        if not obj:
            raise HTTPException(404, "Time rule not found for this business")
        return self.repo.update(db, obj, data)

    def delete(self, db: Session, rule_id: int, business_id: int):
        """Delete only if rule belongs to the business."""
        obj = self.repo.get(db, rule_id, business_id)
        if not obj:
            raise HTTPException(404, "Time rule not found for this business")
        return self.repo.delete(db, obj)
