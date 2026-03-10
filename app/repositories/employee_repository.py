"""
Employee Repository
Data access layer for employee management
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import date

from app.repositories.base_repository import BaseRepository
from app.models.employee import Employee, EmployeeStatus, EmployeeProfile, EmployeeDocument, EmployeeSalary
from app.models.business import Business
from app.models.department import Department
from app.models.designations import Designation
from app.models.location import Location
from app.models.cost_center import CostCenter
from app.models.shift_policy import ShiftPolicy
from app.models.weekoff_policy import WeekOffPolicy


class EmployeeRepository(BaseRepository[Employee]):
    """Repository for employee data operations"""
    
    def __init__(self, db: Session):
        super().__init__(Employee, db)
    
    def get_with_relations(self, employee_id: int, business_id: Optional[int] = None) -> Optional[Employee]:
        """Get employee with all related data"""
        query = self.db.query(Employee).options(
            joinedload(Employee.profile),
            joinedload(Employee.documents),
            joinedload(Employee.salary_records),
            joinedload(Employee.department),
            joinedload(Employee.designation),
            joinedload(Employee.location),
            joinedload(Employee.cost_center),
            joinedload(Employee.grade),
            joinedload(Employee.shift_policy),
            joinedload(Employee.weekoff_policy),
            joinedload(Employee.reporting_manager)
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        return query.filter(Employee.id == employee_id).first()
    
    def get_by_code(self, employee_code: str, business_id: int) -> Optional[Employee]:
        """Get employee by employee code"""
        return (
            self.db.query(Employee)
            .filter(Employee.employee_code == employee_code)
            .filter(Employee.business_id == business_id)
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email"""
        return self.db.query(Employee).filter(Employee.email == email).first()
    
    def search_employees(
        self,
        query: Optional[str] = None,
        business_id: Optional[int] = None,
        current_user = None,
        department_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        location_id: Optional[int] = None,
        cost_center_id: Optional[int] = None,
        employee_status: Optional[str] = None,
        date_of_joining_from: Optional[date] = None,
        date_of_joining_to: Optional[date] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search employees with filters and pagination"""
        
        # Import here to avoid circular imports
        from app.utils.business_unit_utils import get_user_business_context
        
        # Determine business context
        if current_user:
            is_superadmin, user_business_id = get_user_business_context(current_user, self.db)
            if not is_superadmin and user_business_id:
                business_id = user_business_id
        
        base_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation),
            joinedload(Employee.location),
            joinedload(Employee.cost_center),
            joinedload(Employee.reporting_manager)
        )
        
        # Apply business filter
        if business_id:
            base_query = base_query.filter(Employee.business_id == business_id)
        
        # Apply text search
        if query:
            search_term = f"%{query}%"
            base_query = base_query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    Employee.email.ilike(search_term),
                    Employee.mobile.ilike(search_term)
                )
            )
        
        # Apply filters
        if department_id:
            base_query = base_query.filter(Employee.department_id == department_id)
        
        if designation_id:
            base_query = base_query.filter(Employee.designation_id == designation_id)
        
        if location_id:
            base_query = base_query.filter(Employee.location_id == location_id)
        
        if cost_center_id:
            base_query = base_query.filter(Employee.cost_center_id == cost_center_id)
        
        if employee_status:
            base_query = base_query.filter(Employee.employee_status == employee_status)
        
        if is_active is not None:
            base_query = base_query.filter(Employee.is_active == is_active)
        
        if date_of_joining_from:
            base_query = base_query.filter(Employee.date_of_joining >= date_of_joining_from)
        
        if date_of_joining_to:
            base_query = base_query.filter(Employee.date_of_joining <= date_of_joining_to)
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and get results
        employees = base_query.offset(skip).limit(limit).all()
        
        return {
            "items": employees,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    def get_last_employee_by_business(self, business_id: int) -> Optional[Employee]:
        """Get last employee by business for code generation"""
        return (
            self.db.query(Employee)
            .filter(Employee.business_id == business_id)
            .order_by(desc(Employee.id))
            .first()
        )
    
    def get_employee_stats(self, business_id: Optional[int] = None) -> Dict[str, Any]:
        """Get employee statistics"""
        query = self.db.query(Employee)
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Basic counts
        total_employees = query.count()
        active_employees = query.filter(Employee.employee_status == EmployeeStatus.ACTIVE).count()
        inactive_employees = query.filter(Employee.employee_status != EmployeeStatus.ACTIVE).count()
        
        # This month statistics
        current_month_start = date.today().replace(day=1)
        new_joinings_this_month = query.filter(Employee.date_of_joining >= current_month_start).count()
        terminations_this_month = query.filter(
            and_(
                Employee.date_of_termination >= current_month_start,
                Employee.date_of_termination.isnot(None)
            )
        ).count()
        
        employees_on_probation = query.filter(Employee.employee_status == "probation").count()
        
        # Department-wise distribution
        dept_stats = (
            self.db.query(Department.name, func.count(Employee.id))
            .join(Employee, Employee.department_id == Department.id)
            .group_by(Department.name)
        )
        if business_id:
            dept_stats = dept_stats.filter(Employee.business_id == business_id)
        
        employees_by_department = dict(dept_stats.all())
        
        # Location-wise distribution
        location_stats = (
            self.db.query(Location.name, func.count(Employee.id))
            .join(Employee, Employee.location_id == Location.id)
            .group_by(Location.name)
        )
        if business_id:
            location_stats = location_stats.filter(Employee.business_id == business_id)
        
        employees_by_location = dict(location_stats.all())
        
        # Status-wise distribution
        status_stats = (
            query.with_entities(Employee.employee_status, func.count(Employee.id))
            .group_by(Employee.employee_status)
            .all()
        )
        employees_by_status = dict(status_stats)
        
        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "inactive_employees": inactive_employees,
            "new_joinings_this_month": new_joinings_this_month,
            "terminations_this_month": terminations_this_month,
            "employees_on_probation": employees_on_probation,
            "employees_by_department": employees_by_department,
            "employees_by_location": employees_by_location,
            "employees_by_status": employees_by_status
        }
    
    def get_managers(self, search_query: Optional[str] = None, limit: int = 20) -> List[Employee]:
        """Get employees who can be managers"""
        query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation)
        ).filter(
            Employee.is_active == True,
            Employee.employee_status == EmployeeStatus.ACTIVE
        )
        
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term)
                )
            )
        
        return query.limit(limit).all()
    
    def soft_delete(self, employee_id: int) -> bool:
        """Soft delete employee"""
        employee = self.get(employee_id)
        if employee:
            employee.is_active = False
            employee.employee_status = "terminated"
            employee.date_of_termination = date.today()
            self.db.commit()
            return True
        return False
    
    def get_dropdown_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get dropdown data for employee forms"""
        # Get departments
        departments = self.db.query(Department).filter(Department.is_active == True).all()
        department_list = [{"id": d.id, "name": d.name} for d in departments]
        
        # Get designations
        designations = self.db.query(Designation).all()
        designation_list = [{"id": d.id, "name": d.name} for d in designations]
        
        # Get locations
        locations = self.db.query(Location).filter(Location.is_active == True).all()
        location_list = [{"id": l.id, "name": l.name} for l in locations]
        
        # Get cost centers
        cost_centers = self.db.query(CostCenter).filter(CostCenter.is_active == True).all()
        cost_center_list = [{"id": c.id, "name": c.name} for c in cost_centers]
        
        # Get shift policies
        shift_policies = self.db.query(ShiftPolicy).all()
        shift_policy_list = [{"id": s.id, "name": s.title} for s in shift_policies]
        
        # Get week off policies
        week_off_policies = self.db.query(WeekOffPolicy).all()
        week_off_policy_list = [{"id": w.id, "name": w.title} for w in week_off_policies]
        
        # Hardcoded grades (since Grade model might not exist)
        grade_list = [
            {"id": 1, "name": "Associate"},
            {"id": 2, "name": "Engineer"},
            {"id": 3, "name": "Senior Engineer"},
            {"id": 4, "name": "Manager"},
            {"id": 5, "name": "Executive"},
            {"id": 6, "name": "Supervisor"},
            {"id": 7, "name": "Trainee"}
        ]
        
        return {
            "departments": department_list,
            "designations": designation_list,
            "locations": location_list,
            "grades": grade_list,
            "costCenters": cost_center_list,
            "shiftPolicies": shift_policy_list,
            "weekOffPolicies": week_off_policy_list
        }


class EmployeeProfileRepository(BaseRepository[EmployeeProfile]):
    """Repository for employee profile operations"""
    
    def __init__(self, db: Session):
        super().__init__(EmployeeProfile, db)
    
    def get_by_employee_id(self, employee_id: int) -> Optional[EmployeeProfile]:
        """Get profile by employee ID"""
        return self.db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == employee_id).first()


class EmployeeDocumentRepository(BaseRepository[EmployeeDocument]):
    """Repository for employee document operations"""
    
    def __init__(self, db: Session):
        super().__init__(EmployeeDocument, db)
    
    def get_by_employee_id(self, employee_id: int) -> List[EmployeeDocument]:
        """Get documents by employee ID"""
        return self.db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee_id).all()
    
    def delete_by_id_and_employee(self, document_id: int, employee_id: int) -> bool:
        """Delete document by ID and employee ID"""
        document = (
            self.db.query(EmployeeDocument)
            .filter(EmployeeDocument.id == document_id)
            .filter(EmployeeDocument.employee_id == employee_id)
            .first()
        )
        
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False


class EmployeeSalaryRepository(BaseRepository[EmployeeSalary]):
    """Repository for employee salary operations"""
    
    def __init__(self, db: Session):
        super().__init__(EmployeeSalary, db)
    
    def get_current_salary(self, employee_id: int) -> Optional[EmployeeSalary]:
        """Get current active salary for employee"""
        return (
            self.db.query(EmployeeSalary)
            .filter(EmployeeSalary.employee_id == employee_id)
            .filter(EmployeeSalary.is_active == True)
            .first()
        )
    
    def deactivate_previous_salaries(self, employee_id: int, effective_from: date) -> None:
        """Deactivate previous salary records"""
        self.db.query(EmployeeSalary).filter(
            EmployeeSalary.employee_id == employee_id,
            EmployeeSalary.is_active == True
        ).update({"is_active": False, "effective_to": effective_from})
        self.db.commit()