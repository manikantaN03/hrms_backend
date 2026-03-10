"""
Biometric Code Service
Business logic layer for biometric code management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.repositories.biometric_code_repository import BiometricCodeRepository
from app.utils.business_unit_utils import (
    get_business_unit_options,
    apply_business_unit_filter
)


class BiometricCodeService:
    """Service for biometric code business logic"""
    
    def __init__(self, db: Session):
        self.repository = BiometricCodeRepository(db)
    
    def get_employees_with_biometric_codes(
        self,
        current_user,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get employees with biometric codes using hybrid business unit logic"""
        # For now, delegate to repository but with hybrid logic awareness
        # The repository will be updated to handle the business unit filter properly
        return self.repository.get_employees_with_biometric_codes(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            cost_center=cost_center,
            department=department,
            search=search,
            page=page,
            size=size,
            current_user=current_user  # Pass current user to repository
        )
    
    def get_filter_options(
        self, 
        current_user,
        business_id: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """Get filter options with hybrid business unit logic"""
        try:
            from sqlalchemy.orm import Session
            
            # Get business units using hybrid approach
            business_units = get_business_unit_options(self.repository.db, current_user, business_id)
            
            # Get other filter options from repository
            other_options = self.repository.get_filter_options(business_id=business_id)
            
            # Combine with hybrid business units
            return {
                "business_units": business_units,
                "locations": other_options["locations"],
                "cost_centers": other_options["cost_centers"],
                "departments": other_options["departments"]
            }
            
        except Exception as e:
            # Fallback to repository method if hybrid logic fails
            return self.repository.get_filter_options(business_id=business_id)
    
    def update_employee_biometric_code(
        self,
        employee_code: str,
        biometric_code: str,
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Update employee biometric code"""
        return self.repository.update_employee_biometric_code(
            employee_code=employee_code,
            biometric_code=biometric_code,
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
    
    def export_biometric_codes_csv(
        self,
        current_user,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export biometric codes as CSV with hybrid business unit logic"""
        return self.repository.export_biometric_codes_csv(
            current_user=current_user,
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            department=department
        )
    
    def import_biometric_codes_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import biometric codes from CSV"""
        return self.repository.import_biometric_codes_csv(
            csv_content=csv_content,
            business_id=business_id,
            created_by=created_by,
            overwrite_existing=overwrite_existing
        )