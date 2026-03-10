from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.setup.salary_and_deductions.salary_component_repo import SalaryComponentRepository
from app.schemas.setup.salary_and_deductions.salary_component import SalaryComponentCreate, SalaryComponentUpdate
from app.models.business import Business


class SalaryComponentService:

    def __init__(self):
        self.repo = SalaryComponentRepository()

    # 🔹 List salary components for a specific business
    def list(self, db: Session, business_id: int):
        """List all salary components for a business"""
        try:
            comps = self.repo.list(db, business_id)
            # Coerce missing/empty unit_type values to a valid enum string to satisfy response validation
            for c in comps:
                ut = getattr(c, "unit_type", None)
                if ut is None or (isinstance(ut, str) and ut.strip() == ""):
                    setattr(c, "unit_type", "Paid Days")
            return comps
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve salary components: {str(e)}"
            )

    # 🔹 Get a component but ensure ownership
    def get(self, db: Session, component_id: int, business_id: int):
        """Get a single salary component by ID with business validation"""
        component = self.repo.get(db, component_id)

        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary Component not found"
            )

        # Business access restriction
        if component.business_id != business_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this component"
            )

        return component

    # 🔹 Create new component (business_id inside payload)
    def create(self, db: Session, data: SalaryComponentCreate):
        """Create a new salary component"""
        # Ensure the referenced business exists
        business = db.query(Business).filter(Business.id == data.business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business does not exist"
            )
        
        # Business-scoped alias uniqueness check
        existing = self.repo.check_exists(
            db,
            alias=data.alias,
            business_id=data.business_id
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Alias '{data.alias}' already exists for this business"
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
                detail=f"Failed to create salary component: {str(e)}"
            )

    # 🔹 Update component (business-scoped)
    def update(self, db: Session, component_id: int, business_id: int, data: SalaryComponentUpdate):
        """Update an existing salary component"""
        component = self.get(db, component_id, business_id)
        
        # Check alias uniqueness if alias is being updated
        if data.alias and data.alias != component.alias:
            existing = self.repo.check_exists(
                db,
                alias=data.alias,
                business_id=business_id,
                exclude_id=component_id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Alias '{data.alias}' already exists for this business"
                )
        
        try:
            return self.repo.update(db, component, data)
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
                detail=f"Failed to update salary component: {str(e)}"
            )

    # 🔹 Delete component (business-scoped)
    def delete(self, db: Session, component_id: int, business_id: int):
        """Delete a salary component"""
        component = self.get(db, component_id, business_id)
        
        try:
            return self.repo.delete(db, component)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete salary component: it is being used in salary structures or other records"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete salary component: {str(e)}"
            )
