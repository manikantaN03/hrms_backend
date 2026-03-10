# ============================================================
# services/weekoff_policy_service.py
# ============================================================
from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from app.repositories.weekoff_policy_repository import WeekOffPolicyRepository
from app.schemas.weekoff_policy import WeekOffPolicyCreate, WeekOffPolicyUpdate, WeekOffPolicyResponse
from app.models.weekoff_policy import WeekOffPolicy


class WeekOffPolicyService:
    
    @staticmethod
    def create_policy(db: Session, payload: WeekOffPolicyCreate) -> WeekOffPolicyResponse:
        """Create new week off policy."""
        if payload.is_default:
            # Unset other defaults for this business (use model directly to avoid empty-list indexing)
            db.query(WeekOffPolicy)\
                .filter(WeekOffPolicy.business_id == payload.business_id)\
                .update({"is_default": False})
            db.commit()
        
        policy = WeekOffPolicyRepository.create(db, payload)
        return WeekOffPolicyResponse.model_validate(policy)
    
    @staticmethod
    def get_all_policies(db: Session, business_id: int) -> List[WeekOffPolicyResponse]:
        """Get all week off policies for a business."""
        policies = WeekOffPolicyRepository.get_all(db, business_id)
        return [WeekOffPolicyResponse.model_validate(p) for p in policies]
    
    @staticmethod
    def get_policy_by_id(db: Session, policy_id: int, business_id: int) -> WeekOffPolicyResponse:
        """Get week off policy by ID."""
        policy = WeekOffPolicyRepository.get_by_id(db, policy_id, business_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Week off policy with ID {policy_id} not found"
            )
        return WeekOffPolicyResponse.model_validate(policy)
    
    @staticmethod
    def update_policy(db: Session, policy_id: int, business_id: int, payload: WeekOffPolicyUpdate) -> WeekOffPolicyResponse:
        """Update existing week off policy."""
        if payload.is_default:
            WeekOffPolicyRepository.set_as_default(db, policy_id, business_id)
        
        policy = WeekOffPolicyRepository.update(db, policy_id, business_id, payload)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Week off policy with ID {policy_id} not found"
            )
        return WeekOffPolicyResponse.model_validate(policy)
    
    @staticmethod
    def delete_policy(db: Session, policy_id: int, business_id: int) -> dict:
        """Delete week off policy."""
        success = WeekOffPolicyRepository.delete(db, policy_id, business_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Week off policy with ID {policy_id} not found"
            )
        return {"message": "Week off policy deleted successfully"}
    
    @staticmethod
    def get_default_policy(db: Session, business_id: int) -> WeekOffPolicyResponse:
        """Get the default week off policy."""
        policy = WeekOffPolicyRepository.get_default_policy(db, business_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No default week off policy found"
            )
        return WeekOffPolicyResponse.model_validate(policy)