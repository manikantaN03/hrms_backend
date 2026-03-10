from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models.shift_policy import ShiftPolicy
from app.schemas.shift_policy import ShiftPolicyCreate, ShiftPolicyUpdate

class ShiftPolicyRepository:

    @staticmethod
    def get_all(db: Session, business_id: int) -> List[ShiftPolicy]:
        return db.query(ShiftPolicy).options(joinedload(ShiftPolicy.default_shift))\
                 .filter(ShiftPolicy.business_id == business_id).order_by(ShiftPolicy.id.desc()).all()

    @staticmethod
    def get_by_id(db: Session, policy_id: int, business_id: int) -> Optional[ShiftPolicy]:
        return db.query(ShiftPolicy).options(joinedload(ShiftPolicy.default_shift))\
                 .filter(ShiftPolicy.id == policy_id, ShiftPolicy.business_id == business_id).first()

    @staticmethod
    def create(db: Session, payload: ShiftPolicyCreate) -> ShiftPolicy:
        db_policy = ShiftPolicy(**payload.model_dump())
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        return db_policy

    @staticmethod
    def update(db: Session, policy_id: int, business_id: int, payload: ShiftPolicyUpdate) -> Optional[ShiftPolicy]:
        db_policy = ShiftPolicyRepository.get_by_id(db, policy_id, business_id)
        if not db_policy:
            return None
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_policy, field, value)
        db.commit()
        db.refresh(db_policy)
        return db_policy

    @staticmethod
    def delete(db: Session, policy_id: int, business_id: int) -> bool:
        db_policy = ShiftPolicyRepository.get_by_id(db, policy_id, business_id)
        if not db_policy:
            return False
        db.delete(db_policy)
        db.commit()
        return True

    @staticmethod
    def get_default_policy(db: Session, business_id: int) -> Optional[ShiftPolicy]:
        return db.query(ShiftPolicy).options(joinedload(ShiftPolicy.default_shift))\
                 .filter(ShiftPolicy.business_id == business_id, ShiftPolicy.is_default == True).first()

    @staticmethod
    def set_as_default(db: Session, policy_id: int, business_id: int) -> Optional[ShiftPolicy]:
        db.query(ShiftPolicy).filter(ShiftPolicy.business_id == business_id).update({"is_default": False})
        db_policy = ShiftPolicyRepository.get_by_id(db, policy_id, business_id)
        if db_policy:
            db_policy.is_default = True
            db.commit()
            db.refresh(db_policy)
        return db_policy
