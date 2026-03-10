"""
Employee Service
Business logic for employee management
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import uuid

from app.repositories.employee_repository import (
    EmployeeRepository, EmployeeProfileRepository, 
    EmployeeDocumentRepository, EmployeeSalaryRepository
)
from app.models.employee import Employee, EmployeeProfile, EmployeeDocument, EmployeeSalary
from app.models.business import Business
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeSearchRequest,
    EmployeeBulkCreateRequest, EmployeeBulkUpdateRequest,
    EmployeeProfileCreate, EmployeeProfileUpdate,
    EmployeeDocumentCreate, EmployeeSalaryCreate, EmployeeSalaryUpdate
)
from app.core.exceptions import ValidationError, NotFoundError
from app.services.email_service import EmailService


class EmployeeService:
    """Service class for employee operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
        self.profile_repo = EmployeeProfileRepository(db)
        self.document_repo = EmployeeDocumentRepository(db)
        self.salary_repo = EmployeeSalaryRepository(db)
        self.email_service = EmailService()
    
    def generate_employee_code(self, business_id: int) -> str:
        """Generate unique employee code"""
        # Get business prefix
        business = self.db.query(Business).filter(Business.id == business_id).first()
        prefix = getattr(business, 'code', 'EMP') if business else "EMP"
        
        # Get next sequence number
        last_employee = self.employee_repo.get_last_employee_by_business(business_id)
        
        if last_employee and last_employee.employee_code:
            try:
                last_number = int(last_employee.employee_code.replace(prefix, ""))
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}{next_number:04d}"
    
    def create_employee(self, employee_data: EmployeeCreate, created_by: int) -> Employee:
        """Create new employee"""
        # Validate business exists
        business = self.db.query(Business).filter(Business.id == employee_data.business_id).first()
        if not business:
            raise NotFoundError("Business not found")
        
        # Check if email already exists
        existing_employee = self.employee_repo.get_by_email(employee_data.email)
        if existing_employee:
            raise ValidationError("Employee with this email already exists")
        
        # Generate employee code if not provided
        if not employee_data.employee_code:
            employee_data.employee_code = self.generate_employee_code(employee_data.business_id)
        else:
            # Check if employee code is unique
            existing_code = self.employee_repo.get_by_code(employee_data.employee_code, employee_data.business_id)
            if existing_code:
                raise ValidationError("Employee code already exists")
        
        # Create employee using repository
        employee_dict = employee_data.dict()
        employee_dict['created_by'] = created_by
        employee = self.employee_repo.create(employee_dict)
        
        # Send welcome email
        try:
            self.email_service.send_welcome_email(employee)
        except Exception as e:
            # Log error but don't fail the creation
            print(f"Failed to send welcome email: {e}")
        
        return employee
    
    def get_employee(self, employee_id: int, business_id: Optional[int] = None) -> Optional[Employee]:
        """Get employee by ID with relations"""
        return self.employee_repo.get_with_relations(employee_id, business_id)
    
    def get_employee_by_code(self, employee_code: str, business_id: int) -> Optional[Employee]:
        """Get employee by employee code"""
        return self.employee_repo.get_by_code(employee_code, business_id)
    
    def update_employee(self, employee_id: int, employee_data: EmployeeUpdate, updated_by: int, business_id: Optional[int] = None) -> Employee:
        """Update employee"""
        employee = self.get_employee(employee_id, business_id)
        if not employee:
            raise NotFoundError("Employee not found")
        
        # Check email uniqueness if email is being updated
        if employee_data.email and employee_data.email != employee.email:
            existing_employee = self.employee_repo.get_by_email(employee_data.email)
            if existing_employee and existing_employee.id != employee_id:
                raise ValidationError("Employee with this email already exists")
        
        # Update employee fields using repository
        update_data = employee_data.dict(exclude_unset=True)
        update_data['updated_by'] = updated_by
        
        return self.employee_repo.update(employee, update_data)
    
    def delete_employee(self, employee_id: int, business_id: Optional[int] = None) -> bool:
        """Soft delete employee"""
        employee = self.get_employee(employee_id, business_id)
        if not employee:
            raise NotFoundError("Employee not found")
        
        return self.employee_repo.soft_delete(employee_id)
    
    def search_employees(self, search_params: EmployeeSearchRequest, business_id: Optional[int] = None) -> Dict[str, Any]:
        """Search employees with filters and pagination"""
        skip = (search_params.page - 1) * search_params.size
        
        result = self.employee_repo.search_employees(
            query=search_params.query,
            business_id=business_id,
            department_id=search_params.department_id,
            designation_id=search_params.designation_id,
            location_id=search_params.location_id,
            employee_status=search_params.employee_status,
            date_of_joining_from=search_params.date_of_joining_from,
            date_of_joining_to=search_params.date_of_joining_to,
            skip=skip,
            limit=search_params.size
        )
        
        # Calculate pages
        pages = (result["total"] + search_params.size - 1) // search_params.size
        
        return {
            "items": result["items"],
            "total": result["total"],
            "page": search_params.page,
            "size": search_params.size,
            "pages": pages
        }
    
    def get_employee_stats(self, business_id: Optional[int] = None) -> Dict[str, Any]:
        """Get employee statistics"""
        return self.employee_repo.get_employee_stats(business_id)
    
    def get_dropdown_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get dropdown data for employee forms"""
        return self.employee_repo.get_dropdown_data()
    
    def search_managers(self, query: Optional[str] = None) -> List[Employee]:
        """Search for managers"""
        return self.employee_repo.get_managers(query)
    
    def bulk_create_employees(self, bulk_data: EmployeeBulkCreateRequest, created_by: int) -> List[Employee]:
        """Bulk create employees"""
        created_employees = []
        errors = []
        
        for idx, employee_data in enumerate(bulk_data.employees):
            try:
                employee = self.create_employee(employee_data, created_by)
                created_employees.append(employee)
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        if errors:
            raise ValidationError(f"Bulk creation failed with errors: {'; '.join(errors)}")
        
        return created_employees
    
    def bulk_update_employees(self, bulk_data: EmployeeBulkUpdateRequest, updated_by: int, business_id: Optional[int] = None) -> List[Employee]:
        """Bulk update employees"""
        updated_employees = []
        
        for employee_id in bulk_data.employee_ids:
            try:
                employee = self.update_employee(employee_id, bulk_data.updates, updated_by, business_id)
                updated_employees.append(employee)
            except Exception as e:
                # Log error but continue with other employees
                print(f"Failed to update employee {employee_id}: {e}")
        
        return updated_employees
    
    # Employee Profile Methods
    def create_employee_profile(self, profile_data: EmployeeProfileCreate) -> EmployeeProfile:
        """Create employee profile"""
        # Check if employee exists
        employee = self.employee_repo.get(profile_data.employee_id)
        if not employee:
            raise NotFoundError("Employee not found")
        
        # Check if profile already exists
        existing_profile = self.profile_repo.get_by_employee_id(profile_data.employee_id)
        if existing_profile:
            raise ValidationError("Employee profile already exists")
        
        return self.profile_repo.create(profile_data.dict())
    
    def get_employee_profile(self, employee_id: int) -> Optional[EmployeeProfile]:
        """Get employee profile"""
        return self.profile_repo.get_by_employee_id(employee_id)
    
    def update_employee_profile(self, employee_id: int, profile_data: EmployeeProfileUpdate) -> EmployeeProfile:
        """Update employee profile"""
        profile = self.profile_repo.get_by_employee_id(employee_id)
        if not profile:
            raise NotFoundError("Employee profile not found")
        
        update_data = profile_data.dict(exclude_unset=True)
        return self.profile_repo.update(profile, update_data)
    
    # Employee Document Methods
    def add_employee_document(self, document_data: EmployeeDocumentCreate, uploaded_by: int) -> EmployeeDocument:
        """Add employee document"""
        document_dict = document_data.dict()
        document_dict['uploaded_by'] = uploaded_by
        return self.document_repo.create(document_dict)
    
    def get_employee_documents(self, employee_id: int) -> List[EmployeeDocument]:
        """Get employee documents"""
        return self.document_repo.get_by_employee_id(employee_id)
    
    def delete_employee_document(self, document_id: int, employee_id: int) -> bool:
        """Delete employee document"""
        return self.document_repo.delete_by_id_and_employee(document_id, employee_id)
    
    # Employee Salary Methods
    def create_employee_salary(self, salary_data: EmployeeSalaryCreate) -> EmployeeSalary:
        """Create employee salary record"""
        # Deactivate previous salary records
        self.salary_repo.deactivate_previous_salaries(salary_data.employee_id, salary_data.effective_from)
        
        return self.salary_repo.create(salary_data.dict())
    
    def get_employee_current_salary(self, employee_id: int) -> Optional[EmployeeSalary]:
        """Get employee current salary"""
        return self.salary_repo.get_current_salary(employee_id)