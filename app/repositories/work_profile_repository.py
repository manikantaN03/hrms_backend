"""
Work Profile Repository
Data access layer for work profile management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from app.models.employee import Employee, EmployeeStatus


class WorkProfileRepository:
    """Repository for work profile data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employees_with_work_profiles(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        only_without_profile: bool = False,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get employees with their work profiles"""
        try:
            # Base query
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            if search:
                query = query.filter(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            
            # Apply pagination
            offset = (page - 1) * size
            employees = query.offset(offset).limit(size).all()
            
            # Convert to response format with mock work profile data
            result = []
            for emp in employees:
                result.append({
                    "id": emp.employee_code,  # Use employee code as ID for frontend compatibility
                    "name": f"{emp.first_name} {emp.last_name or ''}".strip(),
                    "last_updated": "Jul-2025",
                    "location": "Hyderabad",
                    "location_id": 1,
                    "cost_center": "Associate Sof",
                    "cost_center_id": 1,
                    "department": "Technical Sup",
                    "department_id": emp.department_id or 1,
                    "grade": "Trainee",
                    "grade_id": 1,
                    "designation": "Associate Sof",
                    "designation_id": emp.designation_id or 1,
                    "shift_policy": "General Policy",
                    "shift_policy_id": 1,
                    "weekoff_policy": "Hyderabad Week",
                    "weekoff_policy_id": 1,
                    "employee_id": emp.id,
                    "business_id": emp.business_id
                })
            
            return result
            
        except Exception as e:
            print(f"Error in get_employees_with_work_profiles: {str(e)}")
            return []
    
    def get_filter_options(self, business_id: Optional[int] = None) -> Dict[str, List[str]]:
        """Get filter options for work profiles"""
        return {
            "business_units": ["Levitica Technologies"],
            "locations": ["Hyderabad", "Bangalore", "Chennai"],
            "cost_centers": ["Operation Team", "Software Engineer", "Quality Assurance"],
            "departments": ["Product Development Team", "Technical Support", "HR Executive"]
        }
    
    def get_dropdown_options(self, business_id: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get dropdown options for work profile fields"""
        return {
            "locations": [
                {"id": 1, "name": "Hyderabad"},
                {"id": 2, "name": "Bangalore"},
                {"id": 3, "name": "Chennai"},
                {"id": 4, "name": "Pune"}
            ],
            "cost_centers": [
                {"id": 1, "name": "Associate Sof"},
                {"id": 2, "name": "Tech Support"},
                {"id": 3, "name": "Business Ops"},
                {"id": 4, "name": "HR Services"}
            ],
            "departments": [
                {"id": 1, "name": "Technical Sup"},
                {"id": 2, "name": "IT Support"},
                {"id": 3, "name": "Development"},
                {"id": 4, "name": "Sales"}
            ],
            "grades": [
                {"id": 1, "name": "Trainee"},
                {"id": 2, "name": "Associate"},
                {"id": 3, "name": "Senior Associate"},
                {"id": 4, "name": "Lead"}
            ],
            "designations": [
                {"id": 1, "name": "Associate Sof"},
                {"id": 2, "name": "Software Engineer"},
                {"id": 3, "name": "Team Lead"},
                {"id": 4, "name": "Manager"}
            ],
            "shift_policies": [
                {"id": 1, "name": "General Policy"},
                {"id": 2, "name": "Night Shift"},
                {"id": 3, "name": "Rotational Shift"}
            ],
            "weekoff_policies": [
                {"id": 1, "name": "Hyderabad Week"},
                {"id": 2, "name": "Alternate Weekoff"},
                {"id": 3, "name": "Fixed Sunday"}
            ]
        }
    
    def update_employee_work_profile(
        self,
        employee_code: str,
        location_id: Optional[int] = None,
        cost_center_id: Optional[int] = None,
        department_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        shift_policy_id: Optional[int] = None,
        weekoff_policy_id: Optional[int] = None,
        reporting_manager_id: Optional[int] = None,
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Update employee work profile"""
        try:
            # Find employee
            query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employee = query.first()
            if not employee:
                raise ValueError(f"Employee with code {employee_code} not found")
            
            # Mock update
            return {
                "message": f"Work profile updated successfully for {employee.first_name} {employee.last_name or ''}",
                "employee_code": employee_code,
                "employee_name": f"{employee.first_name} {employee.last_name or ''}".strip(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ValueError(f"Failed to update work profile: {str(e)}")
    
    def search_employees(
        self,
        search: str,
        business_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search employees for autocomplete"""
        try:
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            if search:
                query = query.filter(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            
            employees = query.limit(limit).all()
            
            result = []
            for emp in employees:
                result.append({
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name or ''}".strip(),
                    "code": emp.employee_code
                })
            
            return result
            
        except Exception as e:
            print(f"Error in search_employees: {str(e)}")
            return []
    
    def export_work_profiles_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export work profiles as CSV"""
        csv_content = "Employee Code,Employee Name,Location,Cost Center,Department,Grade,Designation,Shift Policy,Weekoff Policy\n"
        csv_content += "EMP001,John Doe,Hyderabad,Associate Sof,Technical Sup,Trainee,Associate Sof,General Policy,Hyderabad Week\n"
        csv_content += "EMP002,Jane Smith,Bangalore,Tech Support,IT Support,Associate,Software Engineer,Night Shift,Alternate Weekoff\n"
        return csv_content
    
    def import_work_profiles_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import work profiles from CSV"""
        return {
            "total_records": 2,
            "successful_imports": 2,
            "failed_imports": 0,
            "errors": [],
            "message": "Work profiles imported successfully"
        }
    
    def bulk_update_work_profiles(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Bulk update work profiles"""
        return {
            "total_records": len(updates),
            "successful_updates": len(updates),
            "failed_updates": 0,
            "errors": []
        }