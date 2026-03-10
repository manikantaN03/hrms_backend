from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.setup.salary_and_deductions.overtime_payable_component_repo import OvertimePayableComponentRepository


payable_component_repo = OvertimePayableComponentRepository()


class OvertimePayableComponentService:
    
    def list_by_policy(self, db: Session, policy_id: int, business_id: int):
        """Get all payable components for a policy"""
        return payable_component_repo.list_by_policy(db, policy_id, business_id)

    def toggle_payable(self, db: Session, policy_id: int, component_id: int, business_id: int, is_payable: bool):
        """Toggle payable status for a component in a policy"""
        return payable_component_repo.toggle_payable(db, policy_id, component_id, business_id, is_payable)


payable_component_service = OvertimePayableComponentService()
