"""
Bank Details Service
Business logic layer for bank details management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.repositories.bank_details_repository import BankDetailsRepository


class BankDetailsService:
    """Service for bank details business logic"""
    
    def __init__(self, db: Session):
        self.repository = BankDetailsRepository(db)
    
    def get_employees_with_bank_details(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """Get employees with bank details and pagination metadata"""
        return self.repository.get_employees_with_bank_details(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            department=department,
            search=search,
            page=page,
            size=size
        )
    
    def get_filter_options(self, business_id: Optional[int] = None) -> Dict[str, List[str]]:
        """Get filter options"""
        return self.repository.get_filter_options(business_id=business_id)
    
    def update_employee_bank_details(
        self,
        employee_code: str,
        bank_name: str,
        ifsc_code: str,
        account_number: str,
        bank_branch: Optional[str] = None,
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Update employee bank details"""
        return self.repository.update_employee_bank_details(
            employee_code=employee_code,
            bank_name=bank_name,
            ifsc_code=ifsc_code,
            account_number=account_number,
            bank_branch=bank_branch,
            business_id=business_id,
            updated_by=updated_by
        )
    
    def verify_bank_details(
        self,
        employee_code: str,
        business_id: Optional[int] = None,
        verified_by: int = None
    ) -> Dict[str, Any]:
        """Verify bank details"""
        return self.repository.verify_bank_details(
            employee_code=employee_code,
            business_id=business_id,
            verified_by=verified_by
        )
    
    def validate_ifsc_code(self, ifsc_code: str) -> Dict[str, Any]:
        """Validate IFSC code"""
        return self.repository.validate_ifsc_code(ifsc_code)
    
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
    
    def export_bank_details_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export bank details as CSV"""
        return self.repository.export_bank_details_csv(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            department=department
        )
    
    def import_bank_details_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import bank details from CSV"""
        return self.repository.import_bank_details_csv(
            csv_content=csv_content,
            business_id=business_id,
            created_by=created_by,
            overwrite_existing=overwrite_existing
        )
    
    def bulk_update_bank_details(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Bulk update bank details"""
        return self.repository.bulk_update_bank_details(
            updates=updates,
            business_id=business_id,
            updated_by=updated_by
        )
        return self.repository.bulk_update_bank_details(
            updates=updates,
            business_id=business_id,
            updated_by=updated_by
        )