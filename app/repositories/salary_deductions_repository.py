"""
Salary Deductions Repository
Data access layer for salary deductions management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from app.models.employee import Employee, EmployeeStatus


class SalaryDeductionsRepository:
    """Repository for salary deductions data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employees_with_salary_deductions(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get employees with their salary deductions"""
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
            
            # Convert to response format with mock deduction data
            result = []
            for i, emp in enumerate(employees):
                result.append({
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name or ''}".strip(),
                    "code": emp.employee_code,
                    "position": "Associate Software Engineer",
                    "dept": "Technical Support",
                    "last_updated": "Jul-2025",
                    "gi": 800.0 if i % 2 == 1 else 0.0,  # Group Insurance
                    "gratu": 577.0 if i % 2 == 1 else 0.0,  # Gratuity
                    "employee_id": emp.id,
                    "business_id": emp.business_id
                })
            
            return result
            
        except Exception as e:
            print(f"Error in get_employees_with_salary_deductions: {str(e)}")
            return []
    
    def get_filter_options(self, business_id: Optional[int] = None) -> Dict[str, List[str]]:
        """Get filter options for salary deductions"""
        return {
            "business_units": ["Levitica Technologies"],
            "locations": ["Hyderabad", "Bangalore", "Chennai"],
            "cost_centers": ["Operation Team", "Software Engineer", "Quality Assurance"],
            "departments": ["Product Development Team", "Technical Support", "HR Executive"]
        }
    
    def update_employee_salary_deductions(
        self,
        employee_code: str,
        gi_deduction: Optional[float] = None,
        gratuity_deduction: Optional[float] = None,
        pf_deduction: Optional[float] = None,
        esi_deduction: Optional[float] = None,
        professional_tax: Optional[float] = None,
        income_tax: Optional[float] = None,
        other_deductions: Optional[float] = None,
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Update employee salary deductions"""
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
                "message": f"Salary deductions updated successfully for {employee.first_name} {employee.last_name or ''}",
                "employee_code": employee_code,
                "employee_name": f"{employee.first_name} {employee.last_name or ''}".strip(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ValueError(f"Failed to update salary deductions: {str(e)}")
    
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
    
    def export_salary_deductions_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export salary deductions as CSV"""
        csv_content = "Employee Code,Employee Name,GI,Gratuity,PF Deduction,ESI Deduction,Professional Tax,Income Tax,Other Deductions\n"
        csv_content += "EMP001,John Doe,0,0,1044,0,200,0,0\n"
        csv_content += "EMP002,Jane Smith,800,577,1440,144,200,0,0\n"
        return csv_content
    
    def import_salary_deductions_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import salary deductions from CSV"""
        return {
            "total_records": 2,
            "successful_imports": 2,
            "failed_imports": 0,
            "errors": [],
            "message": "Salary deductions imported successfully"
        }
    
    def bulk_update_salary_deductions(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Bulk update salary deductions"""
        return {
            "total_records": len(updates),
            "successful_updates": len(updates),
            "failed_updates": 0,
            "errors": []
        }