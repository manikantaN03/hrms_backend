from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.models.employee import Employee
from app.models.location import Location
from app.models.cost_center import CostCenter
from app.models.department import Department
from app.models.user import User


class UserManagementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_filter_options(self, business_id: int) -> Dict[str, List[str]]:
        """Get available filter options for employee selection"""
        
        # Get locations
        locations = self.db.query(distinct(Location.name)).filter(
            Location.business_id == business_id,
            Location.is_active == True
        ).all()
        location_names = [loc[0] for loc in locations if loc[0]]
        
        # Get cost centers
        cost_centers = self.db.query(distinct(CostCenter.name)).filter(
            CostCenter.business_id == business_id,
            CostCenter.is_active == True
        ).all()
        cost_center_names = [cc[0] for cc in cost_centers if cc[0]]
        
        # Get departments
        departments = self.db.query(distinct(Department.name)).filter(
            Department.business_id == business_id,
            Department.is_active == True
        ).all()
        department_names = [dept[0] for dept in departments if dept[0]]
        
        return {
            "locations": location_names,
            "cost_centers": cost_center_names,
            "departments": department_names
        }

    def get_filtered_employees(
        self,
        business_id: int,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        include_logged_in: bool = False
    ) -> List[Employee]:
        """Get employees matching filter criteria"""
        
        query = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.is_active == True
        )
        
        # Apply location filter - use outerjoin to avoid issues
        if location:
            query = query.join(Location, Employee.location_id == Location.id, isouter=False).filter(
                Location.name == location
            )
        
        # Apply cost center filter - use outerjoin to avoid issues
        if cost_center:
            query = query.join(CostCenter, Employee.cost_center_id == CostCenter.id, isouter=False).filter(
                CostCenter.name == cost_center
            )
        
        # Apply department filter - use outerjoin to avoid issues
        if department:
            query = query.join(Department, Employee.department_id == Department.id, isouter=False).filter(
                Department.name == department
            )
        
        # Apply logged-in filter for mobile login
        if not include_logged_in:
            # For now, we'll include all employees since there's no direct user-employee relationship
            # In a real implementation, you would filter based on existing user accounts
            pass
        
        return query.all()

    def get_filtered_employee_count(
        self,
        business_id: int,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> int:
        """Get count of employees matching filter criteria"""
        
        query = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.is_active == True
        )
        
        # Apply location filter
        if location:
            query = query.join(Location, Employee.location_id == Location.id).filter(
                Location.name == location
            )
        
        # Apply cost center filter
        if cost_center:
            query = query.join(CostCenter, Employee.cost_center_id == CostCenter.id).filter(
                CostCenter.name == cost_center
            )
        
        # Apply department filter
        if department:
            query = query.join(Department, Employee.department_id == Department.id).filter(
                Department.name == department
            )
        
        return query.count()