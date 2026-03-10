from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.salary_structure import SalaryStructure
from app.models.setup.salary_and_deductions.salary_structure_rule import SalaryStructureRule
from app.schemas.setup.salary_and_deductions.salary_structure import (
    SalaryStructureCreate,
    SalaryStructureUpdate,
)


class SalaryStructureRepository:

    def list(self, db: Session):
        return db.query(SalaryStructure).all()

    def list_by_business(self, db: Session, business_id: int):
        return (
            db.query(SalaryStructure)
            .filter(SalaryStructure.business_id == business_id)
            .all()
        )

    def get(self, db: Session, structure_id: int):
        return (
            db.query(SalaryStructure)
            .filter(SalaryStructure.id == structure_id)
            .first()
        )

    def get_by_business(self, db: Session, structure_id: int, business_id: int):
        return (
            db.query(SalaryStructure)
            .filter(SalaryStructure.id == structure_id)
            .filter(SalaryStructure.business_id == business_id)
            .first()
        )

    def exists(self, db: Session, name: str, business_id: int = None):
        """Check if a structure name exists, optionally scoped to business"""
        query = db.query(SalaryStructure).filter(SalaryStructure.name == name)
        if business_id is not None:
            query = query.filter(SalaryStructure.business_id == business_id)
        return query.first()

    def create(self, db: Session, data: SalaryStructureCreate):
        # Create the structure and persist rules in the same transaction
        obj = SalaryStructure(
            name=data.name,
            business_id=data.business_id,
        )
        db.add(obj)

        # flush so obj.id is assigned and can be used for rule FK
        db.flush()

        # create rules if provided, linking to the new structure
        rules = getattr(data, "rules", None) or []
        for r in rules:
            rule_obj = SalaryStructureRule(
                business_id=data.business_id,
                structure_id=obj.id,
                component_id=r.component_id,
                calculation_type=r.calculation_type,
                value=r.value,
                sequence=getattr(r, "sequence", 1),
            )
            db.add(rule_obj)

        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, db_obj: SalaryStructure, data: SalaryStructureUpdate):
        update_data = data.dict(exclude_unset=True)

        # 🔥 Allow updating business_id also
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: SalaryStructure):
        db.delete(db_obj)
        db.commit()
        return True
