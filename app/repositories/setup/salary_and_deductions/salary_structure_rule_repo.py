from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.salary_structure_rule import SalaryStructureRule
from app.schemas.setup.salary_and_deductions.salary_structure_rule import (
    SalaryStructureRuleCreate, 
    SalaryStructureRuleUpdate
)


class SalaryStructureRuleRepository:

    def list_by_structure(self, db: Session, structure_id: int):
        return (
            db.query(SalaryStructureRule)
            .filter(SalaryStructureRule.structure_id == structure_id)
            .order_by(SalaryStructureRule.sequence)
            .all()
        )

    def create(self, db: Session, data: SalaryStructureRuleCreate):
        obj = SalaryStructureRule(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, rule_id: int):
        return (
            db.query(SalaryStructureRule)
            .filter(SalaryStructureRule.id == rule_id)
            .first()
        )

    def update(self, db: Session, obj: SalaryStructureRule, data: SalaryStructureRuleUpdate):
        update_data = data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: SalaryStructureRule):
        db.delete(obj)
        db.commit()
        return True

