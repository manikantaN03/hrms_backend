from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.setup.salary_and_deductions.salary_deduction_repo import (
    SalaryDeductionRepository
)
from app.schemas.setup.salary_and_deductions.salary_deduction import (
    SalaryDeductionCreate,
    SalaryDeductionUpdate
)
from app.models.business import Business


class SalaryDeductionService:

    def __init__(self):
        self.repo = SalaryDeductionRepository()

    # 🔥 List all deductions for a business
    def list(self, db: Session, business_id: int):
        """List all salary deductions for a business"""
        try:
            return self.repo.list(db, business_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve salary deductions: {str(e)}"
            )

    # 🔥 Get single deduction (business-scoped)
    def get(self, db: Session, id: int, business_id: int):
        """Get a single salary deduction by ID with business validation"""
        obj = self.repo.get(db, id, business_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary Deduction not found"
            )
        return obj

    # 🔥 Create deduction for a business
    def create(self, db: Session, data: SalaryDeductionCreate):
        """Create a new salary deduction"""
        # Ensure the referenced business exists
        business = db.query(Business).filter(Business.id == data.business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business does not exist"
            )
        
        # Validate duplicate code only inside the same business
        exists = self.repo.exists(db, data.business_id, data.code)
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code '{data.code}' already exists for this business"
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
                detail=f"Failed to create salary deduction: {str(e)}"
            )

    # 🔥 Update deduction (business-scoped)
    def update(self, db: Session, id: int, business_id: int, data: SalaryDeductionUpdate):
        """Update an existing salary deduction"""
        obj = self.get(db, id, business_id)
        
        # Check code uniqueness if code is being updated
        if data.code and data.code != obj.code:
            exists = self.repo.exists_exclude(db, business_id, data.code, id)
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Code '{data.code}' already exists for this business"
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
                detail=f"Failed to update salary deduction: {str(e)}"
            )

    # 🔥 Delete deduction (business-scoped)
    def delete(self, db: Session, id: int, business_id: int):
        """Delete a salary deduction"""
        obj = self.get(db, id, business_id)
        
        try:
            return self.repo.delete(db, obj)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete salary deduction: it is being used in employee records or other tables"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete salary deduction: {str(e)}"
            )
