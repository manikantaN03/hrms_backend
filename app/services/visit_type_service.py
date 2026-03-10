# ============================================================
# services/visit_type_service.py
# ============================================================
from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from app.repositories.visit_type_repository import VisitTypeRepository
from app.schemas.visit_type import VisitTypeCreate, VisitTypeUpdate, VisitTypeResponse


class VisitTypeService:
    
    @staticmethod
    def create_visit_type(db: Session, payload: VisitTypeCreate) -> VisitTypeResponse:
        """Create new visit type."""
        try:
            visit_type = VisitTypeRepository.create(db, payload)
            return VisitTypeResponse.model_validate(visit_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @staticmethod
    def get_all_visit_types(db: Session, business_id: int) -> List[VisitTypeResponse]:
        """Get all visit types for a business."""
        visit_types = VisitTypeRepository.get_all(db, business_id)
        return [VisitTypeResponse.model_validate(vt) for vt in visit_types]
    
    @staticmethod
    def get_visit_type_by_id(db: Session, visit_type_id: int, business_id: int) -> VisitTypeResponse:
        """Get visit type by ID."""
        visit_type = VisitTypeRepository.get_by_id(db, visit_type_id, business_id)
        if not visit_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Visit type with ID {visit_type_id} not found"
            )
        return VisitTypeResponse.model_validate(visit_type)
    
    @staticmethod
    def update_visit_type(db: Session, visit_type_id: int, business_id: int, payload: VisitTypeUpdate) -> VisitTypeResponse:
        """Update existing visit type."""
        try:
            visit_type = VisitTypeRepository.update(db, visit_type_id, business_id, payload)
            if not visit_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Visit type with ID {visit_type_id} not found"
                )
            return VisitTypeResponse.model_validate(visit_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @staticmethod
    def delete_visit_type(db: Session, visit_type_id: int, business_id: int) -> dict:
        """Delete visit type."""
        success = VisitTypeRepository.delete(db, visit_type_id, business_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Visit type with ID {visit_type_id} not found"
            )
        return {"message": "Visit type deleted successfully"}