"""
Hold Salary Service
Service for handling hold salary business logic
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.repositories.hold_salary_repository import HoldSalaryRepository
from app.models.payroll import HoldSalary
from app.models.employee import Employee
from app.schemas.payroll import HoldSalaryCreate, HoldSalaryUpdate
from sqlalchemy import or_, func


class HoldSalaryService:
    """Service for hold salary operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = HoldSalaryRepository(db)
    
    def get_hold_salaries(
        self,
        business_id: int,
        page: int = 1,
        size: int = 20,
        employee_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        employee_search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get hold salaries with pagination and filters"""
        result = self.repository.get_by_business_id(
            business_id=business_id,
            page=page,
            size=size,
            employee_id=employee_id,
            is_active=is_active,
            employee_search=employee_search
        )
        
        # Build response
        hold_list = []
        for hold in result["items"]:
            # Safely get employee details
            employee_name = None
            employee_code = None
            department_name = None
            designation_name = None
            location_name = None
            
            if hold.employee:
                employee_name = f"{hold.employee.first_name} {hold.employee.last_name}"
                employee_code = hold.employee.employee_code
                
                # Safely get related object names
                if hasattr(hold.employee, 'department') and hold.employee.department:
                    department_name = hold.employee.department.name
                if hasattr(hold.employee, 'designation') and hold.employee.designation:
                    designation_name = hold.employee.designation.name
                if hasattr(hold.employee, 'location') and hold.employee.location:
                    location_name = hold.employee.location.name
            
            hold_data = {
                "id": hold.id,
                "employee": employee_name.upper() if employee_name else None,
                "employee_name": employee_name,
                "code": employee_code,
                "employee_code": employee_code,
                "holdStart": hold.hold_start_date.strftime("%b %d, %Y"),
                "hold_start_date": hold.hold_start_date.isoformat(),  # ISO format for frontend parsing
                "holdEnd": hold.hold_end_date.strftime("%b %d, %Y") if hold.hold_end_date else None,
                "hold_end_date": hold.hold_end_date.isoformat() if hold.hold_end_date else None,
                "notes": hold.reason,  # Frontend uses 'notes' for reason
                "reason": hold.reason,
                "is_active": hold.is_active,
                "employee_id": hold.employee_id,
                "department": department_name,
                "designation": designation_name,
                "location": location_name,
                "created_at": hold.created_at.isoformat(),
                "updated_at": hold.updated_at.isoformat() if hold.updated_at else None
            }
            hold_list.append(hold_data)
        
        # Get statistics
        statistics = self.repository.get_statistics(business_id)
        
        return {
            "success": True,
            "hold_salaries": hold_list,
            "data": hold_list,  # Frontend expects 'data' key
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
                "pages": result["pages"]
            },
            "statistics": statistics
        }
    
    def create_hold_salary(
        self,
        business_id: int,
        created_by: int,
        employee_search: str,
        hold_start_date: str,
        notes: str
    ) -> Dict[str, Any]:
        """Create hold salary record from frontend data"""
        
        # Parse hold start date
        try:
            if hold_start_date:
                hold_date = datetime.strptime(hold_start_date, "%Y-%m-%d").date()
            else:
                hold_date = date.today()
        except ValueError:
            raise ValueError("Invalid hold start date format. Use YYYY-MM-DD")
        
        # Find employee by name or code
        employee = self._find_employee_by_search(business_id, employee_search)
        
        if not employee:
            raise ValueError(f"Employee '{employee_search}' not found")
        
        # Check if employee already has active hold
        existing_hold = self.repository.get_active_hold_for_employee(business_id, employee.id)
        
        if existing_hold:
            raise ValueError(f"Employee {employee.first_name} {employee.last_name} already has an active salary hold")
        
        # Create hold salary record
        hold_salary = self.repository.create_hold_salary(
            business_id=business_id,
            employee_id=employee.id,
            created_by=created_by,
            hold_start_date=hold_date,
            reason=notes or "Salary hold",
            notes=notes
        )
        
        return {
            "success": True,
            "message": f"Salary hold created for {employee.first_name} {employee.last_name}",
            "hold_id": hold_salary.id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "hold_start_date": hold_salary.hold_start_date.isoformat()
        }
    
    def create_hold_salary_direct(
        self,
        business_id: int,
        created_by: int,
        employee_id: int,
        hold_start_date: date,
        reason: str,
        hold_end_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create hold salary record with direct parameters (Pydantic validated)"""
        
        # Validate employee exists
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.business_id == business_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Check if employee already has active hold
        existing_hold = self.repository.get_active_hold_for_employee(business_id, employee_id)
        
        if existing_hold:
            raise ValueError(f"Employee {employee.first_name} {employee.last_name} already has an active salary hold")
        
        # Create hold salary record
        hold_salary = self.repository.create_hold_salary(
            business_id=business_id,
            employee_id=employee_id,
            created_by=created_by,
            hold_start_date=hold_start_date,
            hold_end_date=hold_end_date,
            reason=reason,
            notes=notes
        )
        
        return {
            "success": True,
            "message": f"Salary hold created for {employee.first_name} {employee.last_name}",
            "hold_id": hold_salary.id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "hold_start_date": hold_salary.hold_start_date.isoformat()
        }
    
    def update_hold_salary(
        self,
        business_id: int,
        hold_id: int,
        employee_search: Optional[str] = None,
        hold_start_date: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update hold salary record"""
        
        # Parse hold start date if provided
        hold_date = None
        if hold_start_date:
            try:
                hold_date = datetime.strptime(hold_start_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Invalid hold start date format. Use YYYY-MM-DD")
        
        # Update hold salary record
        hold_salary = self.repository.update_hold_salary(
            hold_id=hold_id,
            business_id=business_id,
            hold_start_date=hold_date,
            reason=notes,
            notes=notes,
            is_active=is_active
        )
        
        if not hold_salary:
            raise ValueError("Hold salary record not found")
        
        return {
            "success": True,
            "message": "Hold salary updated successfully",
            "hold_id": hold_salary.id,
            "employee_name": f"{hold_salary.employee.first_name} {hold_salary.employee.last_name}",
            "hold_start_date": hold_salary.hold_start_date.isoformat()
        }
    
    def update_hold_salary_direct(
        self,
        business_id: int,
        hold_id: int,
        hold_start_date: Optional[date] = None,
        hold_end_date: Optional[date] = None,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update hold salary record with direct parameters (Pydantic validated)"""
        
        # Update hold salary record
        hold_salary = self.repository.update_hold_salary(
            hold_id=hold_id,
            business_id=business_id,
            hold_start_date=hold_start_date,
            hold_end_date=hold_end_date,
            reason=reason,
            notes=notes,
            is_active=is_active
        )
        
        if not hold_salary:
            raise ValueError("Hold salary record not found")
        
        return {
            "success": True,
            "message": "Hold salary updated successfully",
            "hold_id": hold_salary.id,
            "employee_name": f"{hold_salary.employee.first_name} {hold_salary.employee.last_name}",
            "hold_start_date": hold_salary.hold_start_date.isoformat()
        }
    
    def delete_hold_salary(self, business_id: int, hold_id: int) -> Dict[str, Any]:
        """Delete hold salary record"""
        
        # Get hold salary record first for response
        hold_salary = self.db.query(HoldSalary).filter(
            HoldSalary.id == hold_id,
            HoldSalary.business_id == business_id
        ).first()
        
        if not hold_salary:
            raise ValueError("Hold salary record not found")
        
        employee_name = f"{hold_salary.employee.first_name} {hold_salary.employee.last_name}"
        
        # Delete the record
        success = self.repository.delete_hold_salary(hold_id, business_id)
        
        if not success:
            raise ValueError("Failed to delete hold salary record")
        
        return {
            "success": True,
            "message": f"Hold salary removed for {employee_name}",
            "hold_id": hold_id
        }
    
    def search_employees(
        self,
        business_id: int,
        search_term: Optional[str] = None,
        exclude_on_hold: bool = True
    ) -> List[Dict[str, Any]]:
        """Search employees for hold salary"""
        try:
            employees = self.repository.get_employees_for_hold_salary(
                business_id=business_id,
                search_term=search_term,
                exclude_on_hold=exclude_on_hold
            )
            
            employee_list = []
            for employee in employees:
                # Safely get related object names
                department_name = None
                designation_name = None
                location_name = None
                
                try:
                    if hasattr(employee, 'department') and employee.department:
                        department_name = employee.department.name
                except:
                    pass
                    
                try:
                    if hasattr(employee, 'designation') and employee.designation:
                        designation_name = employee.designation.name
                except:
                    pass
                    
                try:
                    if hasattr(employee, 'location') and employee.location:
                        location_name = employee.location.name
                except:
                    pass
                
                employee_list.append({
                    "id": employee.id,
                    "employee_code": employee.employee_code,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "full_name": f"{employee.first_name} {employee.last_name}".upper(),
                    "department": department_name,
                    "designation": designation_name,
                    "location": location_name
                })
            
            return employee_list
            
        except Exception as e:
            print(f"Error in search_employees: {e}")
            return []
    
    def get_hold_salary_summary(self, business_id: int) -> Dict[str, Any]:
        """Get hold salary summary"""
        summary = self.repository.get_hold_salary_summary(business_id)
        statistics = self.repository.get_statistics(business_id)
        
        return {
            "summary": summary,
            "statistics": statistics,
            "total_active_holds": len(summary)
        }
    
    def _find_employee_by_search(self, business_id: int, search_term: str) -> Optional[Employee]:
        """Find employee by name or code"""
        if not search_term:
            return None
        
        # Try to find by exact employee code first
        employee = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.employee_code.ilike(search_term.strip())
        ).first()
        
        if employee:
            return employee
        
        # Try to find by name (case insensitive)
        search_pattern = f"%{search_term.strip()}%"
        employee = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_pattern)
            )
        ).first()
        
        return employee
    
    def convert_frontend_to_backend_format(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert frontend data format to backend format"""
        # Handle both old format (employee name) and new format (employee_id)
        employee_search = ""
        
        if "employee_id" in frontend_data and frontend_data["employee_id"]:
            # New format: convert employee_id to employee_code for search
            try:
                employee_id = int(frontend_data["employee_id"])
                employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
                if employee:
                    employee_search = employee.employee_code
            except (ValueError, TypeError):
                pass
        elif "employee" in frontend_data:
            # Old format: use employee name/code directly
            employee_search = frontend_data.get("employee", "")
        
        return {
            "employee_search": employee_search,
            "hold_start_date": frontend_data.get("hold_start_date", frontend_data.get("holdStart", "")),
            "notes": frontend_data.get("notes", "")
        }