"""
Week Off Policy Repository
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.weekoff_policy import WeekOffPolicy
from app.schemas.weekoff_policy import WeekOffPolicyCreate, WeekOffPolicyUpdate


class WeekOffPolicyRepository:
    
    @staticmethod
    def get_all(db: Session, business_id: int) -> List[WeekOffPolicy]:
        """Get all week off policies for a business."""
        return db.query(WeekOffPolicy).filter(
            WeekOffPolicy.business_id == business_id
        ).order_by(WeekOffPolicy.id.desc()).all()
    
    @staticmethod
    def get_by_id(db: Session, policy_id: int, business_id: int) -> Optional[WeekOffPolicy]:
        """Get week off policy by ID for a business."""
        return db.query(WeekOffPolicy).filter(
            WeekOffPolicy.id == policy_id,
            WeekOffPolicy.business_id == business_id
        ).first()
    
    @staticmethod
    def create(db: Session, policy_data: WeekOffPolicyCreate) -> WeekOffPolicy:
        """Create new week off policy."""
        db_policy = WeekOffPolicy(
            business_id=policy_data.business_id,
            title=policy_data.title,
            description=policy_data.description,
            is_default=policy_data.is_default,
            general_week_offs=policy_data.general_week_offs,
            alternating_week_offs=policy_data.alternating_week_offs,
            weekoffs_payable=policy_data.weekoffs_payable
        )
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        return db_policy
    
    @staticmethod
    def update(db: Session, policy_id: int, business_id: int, policy_data: WeekOffPolicyUpdate) -> Optional[WeekOffPolicy]:
        """Update existing week off policy."""
        db_policy = WeekOffPolicyRepository.get_by_id(db, policy_id, business_id)
        if not db_policy:
            return None
        
        update_data = policy_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_policy, field, value)
        
        db.commit()
        db.refresh(db_policy)
        return db_policy
    
    @staticmethod
    def delete(db: Session, policy_id: int, business_id: int) -> bool:
        """Delete week off policy."""
        db_policy = WeekOffPolicyRepository.get_by_id(db, policy_id, business_id)
        if not db_policy:
            return False
        
        db.delete(db_policy)
        db.commit()
        return True
    
    @staticmethod
    def get_default_policy(db: Session, business_id: int) -> Optional[WeekOffPolicy]:
        """Get the default week off policy for a business."""
        return db.query(WeekOffPolicy).filter(
            WeekOffPolicy.business_id == business_id,
            WeekOffPolicy.is_default == True
        ).first()
    
    @staticmethod
    def set_as_default(db: Session, policy_id: int, business_id: int) -> Optional[WeekOffPolicy]:
        """Set a policy as default and unset others."""
        # Unset all defaults for this business
        db.query(WeekOffPolicy).filter(
            WeekOffPolicy.business_id == business_id
        ).update({WeekOffPolicy.is_default: False})
        
        # Set the specified policy as default
        db_policy = WeekOffPolicyRepository.get_by_id(db, policy_id, business_id)
        if db_policy:
            db_policy.is_default = True
            db.commit()
            db.refresh(db_policy)
        
        return db_policy