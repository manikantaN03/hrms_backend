"""
Business Information Repository
"""

from sqlalchemy.orm import Session
from typing import Optional
from app.models.business_info import BusinessInformation
from app.schemas.business_info import BusinessInformationCreate, BusinessInformationUpdate


class BusinessInformationRepository:
    
    @staticmethod
    def get(db: Session, business_id: int) -> Optional[BusinessInformation]:
        """Get business information for a specific business."""
        return db.query(BusinessInformation).filter(
            BusinessInformation.business_id == business_id
        ).first()
    
    @staticmethod
    def create(db: Session, business_data: BusinessInformationCreate) -> BusinessInformation:
        """Create business information."""
        db_business = BusinessInformation(
            business_id=business_data.business_id,
            bank_name=business_data.bank_name,
            bank_branch=business_data.bank_branch,
            bank_ifsc=business_data.bank_ifsc,
            bank_account=business_data.bank_account,
            pan=business_data.pan,
            tan=business_data.tan,
            gstin=business_data.gstin,
            esi=business_data.esi,
            pf=business_data.pf,
            shop_act=business_data.shop_act,
            labour_act=business_data.labour_act,
            employee_info=business_data.employee_info
        )
        db.add(db_business)
        db.commit()
        db.refresh(db_business)
        return db_business
    
    @staticmethod
    def update(db: Session, business_id: int, business_data: BusinessInformationUpdate) -> BusinessInformation:
        """Update business information."""
        db_business = BusinessInformationRepository.get(db, business_id)
        
        if not db_business:
            # Create if doesn't exist - wrap in Create schema
            create_data = BusinessInformationCreate(
                business_id=business_id,
                **business_data.model_dump(exclude_unset=True)
            )
            return BusinessInformationRepository.create(db, create_data)
        
        # Update existing record
        update_data = business_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_business, field, value)
        
        db.commit()
        db.refresh(db_business)
        return db_business
    
    @staticmethod
    def delete(db: Session, business_id: int) -> bool:
        """Delete business information."""
        db_business = BusinessInformationRepository.get(db, business_id)
        if not db_business:
            return False
        
        db.delete(db_business)
        db.commit()
        return True