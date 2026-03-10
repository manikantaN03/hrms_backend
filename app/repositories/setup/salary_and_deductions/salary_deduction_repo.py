from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.salary_deduction import SalaryDeduction
from app.schemas.setup.salary_and_deductions.salary_deduction import (
    SalaryDeductionCreate,
    SalaryDeductionUpdate
)


class SalaryDeductionRepository:

    # 🔥 List only deductions for a business
    def list(self, db: Session, business_id: int):
        return (
            db.query(SalaryDeduction)
            .filter(SalaryDeduction.business_id == business_id)
            .all()
        )

    def get(self, db: Session, id: int, business_id: int):
        return (
            db.query(SalaryDeduction)
            .filter(
                SalaryDeduction.id == id,
                SalaryDeduction.business_id == business_id
            )
            .first()
        )

    def create(self, db: Session, data: SalaryDeductionCreate):
        obj = SalaryDeduction(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: SalaryDeduction, data: SalaryDeductionUpdate):
        update_data = data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: SalaryDeduction):
        db.delete(obj)
        db.commit()
        return True

    # 🔥 Check if code already exists inside the same business
    def exists(self, db: Session, business_id: int, code: str):
        """Check if a deduction code exists for the business"""
        return (
            db.query(SalaryDeduction)
            .filter(
                SalaryDeduction.business_id == business_id,
                SalaryDeduction.code == code
            )
            .first()
        )
    
    def exists_exclude(self, db: Session, business_id: int, code: str, exclude_id: int):
        """Check if a deduction code exists for the business, excluding a specific ID"""
        return (
            db.query(SalaryDeduction)
            .filter(
                SalaryDeduction.business_id == business_id,
                SalaryDeduction.code == code,
                SalaryDeduction.id != exclude_id
            )
            .first()
        )
