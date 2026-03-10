from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.overtime_payable_component import OvertimePolicyPayableComponent


class OvertimePayableComponentRepository:

    def list_by_policy(self, db: Session, policy_id: int, business_id: int):
        """List all payable components for a policy"""
        return (
            db.query(OvertimePolicyPayableComponent)
            .filter(
                OvertimePolicyPayableComponent.policy_id == policy_id,
                OvertimePolicyPayableComponent.business_id == business_id,
            )
            .all()
        )

    def get_by_policy_and_component(self, db: Session, policy_id: int, component_id: int, business_id: int):
        """Get specific policy-component relationship"""
        return (
            db.query(OvertimePolicyPayableComponent)
            .filter(
                OvertimePolicyPayableComponent.policy_id == policy_id,
                OvertimePolicyPayableComponent.component_id == component_id,
                OvertimePolicyPayableComponent.business_id == business_id,
            )
            .first()
        )

    def create(self, db: Session, data):
        obj = OvertimePolicyPayableComponent(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: OvertimePolicyPayableComponent, data):
        for key, value in data.dict(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: OvertimePolicyPayableComponent):
        db.delete(obj)
        db.commit()
        return True

    def toggle_payable(self, db: Session, policy_id: int, component_id: int, business_id: int, is_payable: bool):
        """Toggle or create payable component status"""
        existing = self.get_by_policy_and_component(db, policy_id, component_id, business_id)
        
        if existing:
            existing.is_payable = is_payable
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new entry
            from app.schemas.setup.salary_and_deductions.overtime_payable_component import OvertimePayableComponentCreate
            data = OvertimePayableComponentCreate(
                business_id=business_id,
                policy_id=policy_id,
                component_id=component_id,
                is_payable=is_payable
            )
            return self.create(db, data)
