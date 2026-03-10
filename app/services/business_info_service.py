# ============================================================
# services/business_info_service.py
# ============================================================
from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from app.repositories.business_info_repository import BusinessInformationRepository
from app.schemas.business_info import BusinessInformationCreate, BusinessInformationUpdate, BusinessInformationResponse


class BusinessInformationService:
    
    @staticmethod
    def create_business_information(db: Session, payload: BusinessInformationCreate) -> BusinessInformationResponse:
        """Create business information."""
        business_info = BusinessInformationRepository.create(db, payload)
        return BusinessInformationResponse.model_validate(business_info)
    
    @staticmethod
    def get_business_information(db: Session, business_id: int) -> BusinessInformationResponse:
        """Get business information."""
        business_info = BusinessInformationRepository.get(db, business_id)
        if not business_info:
            # Return default empty response instead of 404
            # This allows frontend to show "Create Business Info" form
            from datetime import datetime
            return BusinessInformationResponse(
                id=0,  # 0 indicates no record exists
                business_id=business_id,
                bank_name=None,
                bank_branch=None,
                bank_ifsc=None,
                bank_account=None,
                pan=None,
                tan=None,
                gstin=None,
                esi=None,
                pf=None,
                shop_act=None,
                labour_act=None,
                employee_info=[f"Other Info {i+1}" for i in range(10)],
                created_at=datetime.now(),
                updated_at=None
            )
        return BusinessInformationResponse.model_validate(business_info)
    
    @staticmethod
    def update_business_information(
        db: Session, 
        business_id: int,
        payload: BusinessInformationUpdate
    ) -> BusinessInformationResponse:
        """Update business information."""
        business_info = BusinessInformationRepository.update(db, business_id, payload)
        return BusinessInformationResponse.model_validate(business_info)
    
    @staticmethod
    def delete_business_information(db: Session, business_id: int) -> dict:
        """Delete business information."""
        success = BusinessInformationRepository.delete(db, business_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business information not found"
            )
        return {"message": "Business information deleted successfully"}
