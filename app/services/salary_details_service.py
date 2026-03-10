"""
Salary Details Service
Business logic layer for salary details management
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.repositories.salary_details_repository import SalaryDetailsRepository


class SalaryDetailsService:
    """Service for salary details business logic"""
    
    def __init__(self, db: Session):
        self.repository = SalaryDetailsRepository(db)
    
    def get_employees_with_salary_details(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get employees with salary details and total count"""
        return self.repository.get_employees_with_salary_details(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            cost_center=cost_center,
            department=department,
            search=search,
            page=page,
            size=size,
            current_user=current_user
        )
    
    def get_filter_options(self, business_id: Optional[int] = None, current_user = None) -> Dict[str, List[str]]:
        """Get filter options"""
        return self.repository.get_filter_options(business_id=business_id, current_user=current_user)
    
    def update_employee_salary_details(
        self,
        employee_code: str,
        basic_salary: float,
        hra: Optional[float] = None,
        transport_allowance: Optional[float] = None,
        medical_allowance: Optional[float] = None,
        special_allowance: Optional[float] = None,
        conveyance_allowance: Optional[float] = None,
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Update employee salary details"""
        return self.repository.update_employee_salary_details(
            employee_code=employee_code,
            basic_salary=basic_salary,
            hra=hra,
            transport_allowance=transport_allowance,
            medical_allowance=medical_allowance,
            special_allowance=special_allowance,
            conveyance_allowance=conveyance_allowance,
            business_id=business_id,
            updated_by=updated_by
        )
    
    def search_employees(
        self,
        search: str,
        business_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search employees"""
        return self.repository.search_employees(
            search=search,
            business_id=business_id,
            limit=limit
        )
    
    def export_salary_details_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export salary details as CSV"""
        return self.repository.export_salary_details_csv(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            cost_center=cost_center,
            department=department
        )
    
    def import_salary_details_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import salary details from CSV"""
        return self.repository.import_salary_details_csv(
            csv_content=csv_content,
            business_id=business_id,
            created_by=created_by,
            overwrite_existing=overwrite_existing
        )
    
    def bulk_update_salary_details(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Bulk update salary details"""
        return self.repository.bulk_update_salary_details(
            updates=updates,
            business_id=business_id,
            updated_by=updated_by
        )