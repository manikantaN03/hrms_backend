from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.setup.salary_and_deductions.salary_structure_rule_repo import (
    SalaryStructureRuleRepository,
)
from app.schemas.setup.salary_and_deductions.salary_structure_rule import (
    SalaryStructureRuleCreate,
    SalaryStructureRuleUpdate,
)
from app.models.setup.salary_and_deductions.salary_structure_rule import SalaryStructureRule
from app.models.setup.salary_and_deductions.salary_structure import SalaryStructure
from app.models.setup.salary_and_deductions.salary_component import SalaryComponent


class SalaryStructureRuleService:
    def __init__(self):
        self.repo = SalaryStructureRuleRepository()

    # -------------------------------
    # LIST (BUSINESS SCOPED)
    # -------------------------------
    def list(self, db: Session, structure_id: int, business_id: int):
        """List all rules for a salary structure"""
        try:
            return (
                db.query(SalaryStructureRule)
                .filter(
                    SalaryStructureRule.structure_id == structure_id,
                    SalaryStructureRule.business_id == business_id,
                )
                .order_by(SalaryStructureRule.sequence)
                .all()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve rules: {str(e)}"
            )

    # -------------------------------
    # CREATE (BUSINESS SCOPED)
    # -------------------------------
    def create(self, db: Session, data: SalaryStructureRuleCreate, business_id: int):
        """Create a new salary structure rule"""
        # Validate that the structure exists and belongs to the business
        structure = db.query(SalaryStructure).filter(
            SalaryStructure.id == data.structure_id,
            SalaryStructure.business_id == business_id
        ).first()
        
        if not structure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary structure not found for this business"
            )
        
        # Validate that the component exists and belongs to the business
        component = db.query(SalaryComponent).filter(
            SalaryComponent.id == data.component_id,
            SalaryComponent.business_id == business_id
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary component not found for this business"
            )
        
        try:
            # Create rule with business_id
            rule_data = data.dict()
            rule_data["business_id"] = business_id
            
            obj = SalaryStructureRule(**rule_data)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
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
                detail=f"Failed to create rule: {str(e)}"
            )

    # -------------------------------
    # UPDATE (BUSINESS SCOPED)
    # -------------------------------
    def update(self, db: Session, rule_id: int, business_id: int, data: SalaryStructureRuleUpdate):
        """Update an existing salary structure rule"""
        obj = self.repo.get(db, rule_id)

        if not obj or obj.business_id != business_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found for this business"
            )
        
        # Validate component if being updated
        if data.component_id:
            component = db.query(SalaryComponent).filter(
                SalaryComponent.id == data.component_id,
                SalaryComponent.business_id == business_id
            ).first()
            
            if not component:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Salary component not found for this business"
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
                detail=f"Failed to update rule: {str(e)}"
            )

    # -------------------------------
    # DELETE (BUSINESS SCOPED)
    # -------------------------------
    def delete(self, db: Session, rule_id: int, business_id: int):
        """Delete a salary structure rule"""
        obj = self.repo.get(db, rule_id)

        if not obj or obj.business_id != business_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found for this business"
            )

        try:
            return self.repo.delete(db, obj)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete rule: {str(e)}"
            )

