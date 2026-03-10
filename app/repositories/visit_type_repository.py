"""
Visit Type Repository
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.visit_type import VisitType
from app.schemas.visit_type import VisitTypeCreate, VisitTypeUpdate


class VisitTypeRepository:
    
    @staticmethod
    def get_all(db: Session, business_id: int) -> List[VisitType]:
        """Get all visit types for a business."""
        return db.query(VisitType).filter(
            VisitType.business_id == business_id
        ).order_by(VisitType.id.desc()).all()
    
    @staticmethod
    def get_by_id(db: Session, visit_type_id: int, business_id: int) -> Optional[VisitType]:
        """Get visit type by ID for a business."""
        return db.query(VisitType).filter(
            VisitType.id == visit_type_id,
            VisitType.business_id == business_id
        ).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str, business_id: int) -> Optional[VisitType]:
        """Get visit type by name for a business."""
        return db.query(VisitType).filter(
            VisitType.name == name,
            VisitType.business_id == business_id
        ).first()
    
    @staticmethod
    def create(db: Session, visit_type_data: VisitTypeCreate) -> VisitType:
        """Create new visit type."""
        # Check if name already exists for this business
        existing = VisitTypeRepository.get_by_name(
            db, visit_type_data.name, visit_type_data.business_id
        )
        if existing:
            raise ValueError(f"Visit type '{visit_type_data.name}' already exists")
        
        db_visit_type = VisitType(
            business_id=visit_type_data.business_id,
            name=visit_type_data.name
        )
        db.add(db_visit_type)
        db.commit()
        db.refresh(db_visit_type)
        return db_visit_type
    
    @staticmethod
    def update(db: Session, visit_type_id: int, business_id: int, visit_type_data: VisitTypeUpdate) -> Optional[VisitType]:
        """Update existing visit type."""
        db_visit_type = VisitTypeRepository.get_by_id(db, visit_type_id, business_id)
        if not db_visit_type:
            return None
        
        # Check if new name already exists for this business
        existing = VisitTypeRepository.get_by_name(db, visit_type_data.name, business_id)
        if existing and existing.id != visit_type_id:
            raise ValueError(f"Visit type '{visit_type_data.name}' already exists")
        
        db_visit_type.name = visit_type_data.name
        db.commit()
        db.refresh(db_visit_type)
        return db_visit_type
    
    @staticmethod
    def delete(db: Session, visit_type_id: int, business_id: int) -> bool:
        """Delete visit type."""
        db_visit_type = VisitTypeRepository.get_by_id(db, visit_type_id, business_id)
        if not db_visit_type:
            return False
        
        db.delete(db_visit_type)
        db.commit()
        return True