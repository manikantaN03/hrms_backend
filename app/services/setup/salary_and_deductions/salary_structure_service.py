from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas.setup.salary_and_deductions.salary_structure import (
    SalaryStructureCreate,
    SalaryStructureUpdate,
)
from app.repositories.setup.salary_and_deductions.salary_structure_repo import (
    SalaryStructureRepository,
)
from app.models.business import Business


class SalaryStructureService:

    def __init__(self):
        self.repo = SalaryStructureRepository()

    def list(self, db: Session):
        """List all salary structures"""
        try:
            return self.repo.list(db)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve salary structures: {str(e)}"
            )

    def list_by_business(self, db: Session, business_id: int):
        """List all salary structures for a business"""
        try:
            return self.repo.list_by_business(db, business_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve salary structures: {str(e)}"
            )

    def get(self, db: Session, id: int):
        """Get a salary structure by ID"""
        obj = self.repo.get(db, id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary Structure not found"
            )
        return obj

    def get_by_business(self, db: Session, id: int, business_id: int):
        """Get a salary structure by ID with business validation"""
        obj = self.repo.get_by_business(db, id, business_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary Structure not found for this business"
            )
        return obj

    def create(self, db: Session, data: SalaryStructureCreate):
        """Create a new salary structure"""
        # Ensure the referenced business exists
        business = db.query(Business).filter(Business.id == data.business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business does not exist"
            )
        
        # Check if structure name already exists for this business
        exists = self.repo.exists(db, data.name, data.business_id)
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Structure name '{data.name}' already exists for this business"
            )

        try:
            return self.repo.create(db, data)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create salary structure: {str(e)}"
            )

    def update(self, db: Session, id: int, business_id: int, data: SalaryStructureUpdate):
        """Update an existing salary structure"""
        obj = self.get_by_business(db, id, business_id)

        # Prevent switching structure to another business
        if data.business_id is not None and data.business_id != obj.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change business_id of this structure"
            )
        
        # Check name uniqueness if name is being updated (scoped to business)
        if data.name and data.name != obj.name:
            exists = self.repo.exists(db, data.name, business_id)
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Structure name '{data.name}' already exists for this business"
                )

        try:
            return self.repo.update(db, obj, data)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update salary structure: {str(e)}"
            )

    def delete(self, db: Session, id: int, business_id: int):
        """Delete a salary structure"""
        obj = self.get_by_business(db, id, business_id)
        
        try:
            return self.repo.delete(db, obj)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete salary structure: it is being used in employee records or other tables"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete salary structure: {str(e)}"
            )
