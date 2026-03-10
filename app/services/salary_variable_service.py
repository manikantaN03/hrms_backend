"""
Salary Variable Service
Business logic layer for salary variable operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import io
import csv

from app.repositories.salary_variable_repository import SalaryVariableRepository
from app.schemas.datacapture import (
    SalaryVariableCreate, SalaryVariableUpdate, SalaryVariableResponse,
    SalaryVariableEmployeeResponse, SalaryVariableUpdateRequest,
    AddNonCashSalaryRequest, SalaryVariableTypeEnum
)
from app.models.employee import Employee


class SalaryVariableService:
    """Service for salary variable business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = SalaryVariableRepository(db)
    
    def get_salary_variables(
        self,
        business_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get salary variables with business logic validation"""
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10
        
        # Get variables from repository
        variables = self.repository.get_salary_variables(
            business_id=business_id,
            employee_id=employee_id,
            page=page,
            size=size
        )
        
        return variables
    
    def create_salary_variable(
        self,
        variable_data: SalaryVariableCreate,
        business_id: int,
        created_by: int
    ) -> Dict[str, Any]:
        """Create new salary variable with validation"""
        
        # Validate employee exists and belongs to business
        employee = self.db.query(Employee).filter(
            Employee.id == variable_data.employee_id,
            Employee.business_id == business_id,
            Employee.employee_status == "active"
        ).first()
        
        if not employee:
            raise ValueError("Employee not found or inactive")
        
        # Validate amount
        if variable_data.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        # Validate dates
        if variable_data.end_date and variable_data.end_date <= variable_data.effective_date:
            raise ValueError("End date must be after effective date")
        
        # Create variable through repository
        return self.repository.create_salary_variable(
            variable_data=variable_data,
            business_id=business_id,
            created_by=created_by
        )
    
    def update_salary_variable(
        self,
        variable_id: int,
        variable_data: SalaryVariableUpdate,
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update salary variable with validation"""
        
        # Validate amount if provided
        if variable_data.amount is not None and variable_data.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        # Validate dates if provided
        if (variable_data.end_date is not None and 
            variable_data.effective_date is not None and 
            variable_data.end_date <= variable_data.effective_date):
            raise ValueError("End date must be after effective date")
        
        # Update through repository
        result = self.repository.update_salary_variable(
            variable_id=variable_id,
            variable_data=variable_data,
            business_id=business_id,
            updated_by=updated_by
        )
        
        if not result:
            raise ValueError("Salary variable not found")
        
        return result
    
    def delete_salary_variable(
        self,
        variable_id: int,
        business_id: Optional[int] = None
    ) -> Dict[str, str]:
        """Delete salary variable with business logic"""
        
        success = self.repository.delete_salary_variable(
            variable_id=variable_id,
            business_id=business_id
        )
        
        if not success:
            raise ValueError("Salary variable not found")
        
        return {
            "message": f"Salary variable {variable_id} deleted successfully",
            "variable_id": str(variable_id),
            "deleted_at": datetime.now().isoformat()
        }
    
    def get_salary_variable_employees(
        self,
        business_id: Optional[int] = None,
        month: str = "January 2026",
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        leave_option: Optional[str] = None,
        arrear: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> Dict[str, Any]:
        """Get employees with salary variable data for frontend table"""
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10
        
        # Get employees from repository
        result = self.repository.get_salary_variable_employees(
            business_id=business_id,
            month=month,
            business_unit=business_unit,
            location=location,
            department=department,
            leave_option=leave_option,
            arrear=arrear,
            search=search,
            page=page,
            size=size,
            current_user=current_user
        )
        
        return result
    
    def update_salary_variable_employee(
        self,
        update_data: SalaryVariableUpdateRequest,
        business_id: int,
        updated_by: int
    ) -> Dict[str, str]:
        """Update salary variable for an employee with validation"""
        
        # Validate amount
        if update_data.amount < 0:
            raise ValueError("Amount cannot be negative")
        
        # Update through repository
        return self.repository.update_salary_variable_employee(
            update_data=update_data,
            business_id=business_id,
            updated_by=updated_by
        )
    
    def export_salary_variables_csv(
        self,
        business_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        month: str = "January 2026",
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        business_unit: Optional[str] = None
    ) -> str:
        """Export salary variables as CSV content with filtering options"""
        
        # Get employees data with filters
        employees_result = self.repository.get_salary_variable_employees(
            business_id=business_id,
            month=month,
            location=location,
            department=department,
            business_unit=business_unit,
            page=1,
            size=10000  # Large size for export
        )
        
        employees = employees_result.get("employees", [])
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Employee ID', 'Employee Name', 'Employee Code', 'Location', 'Department',
            'Amount', 'Comments', 'Total', 'Month'
        ])
        
        # Write data rows
        for emp in employees:
            writer.writerow([
                emp.get("employee_id", ""),
                emp.get("employee_name", ""),
                emp.get("employee_code", ""),
                emp.get("location", ""),
                emp.get("department", ""),
                emp.get("amount", 0),
                emp.get("comments", ""),
                emp.get("total", 0),
                month
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def import_salary_variables_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False,
        consider_arrear: bool = False
    ) -> Dict[str, Any]:
        """Import salary variables from CSV content with arrear support"""
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Get employee by code or ID
                employee_code = row.get('Employee Code', '').strip()
                employee_id = row.get('Employee ID', '').strip()
                
                if not employee_code and not employee_id:
                    errors.append(f"Row {row_num}: Missing employee identifier")
                    continue
                
                # Find employee
                employee_query = self.db.query(Employee).filter(Employee.business_id == business_id)
                if employee_code:
                    employee = employee_query.filter(Employee.employee_code == employee_code).first()
                else:
                    employee = employee_query.filter(Employee.id == int(employee_id)).first()
                
                if not employee:
                    errors.append(f"Row {row_num}: Employee not found")
                    continue
                
                # Parse variable data
                variable_name = row.get('Variable Name', '').strip()
                amount = row.get('Amount', '0').strip()
                effective_date_str = row.get('Effective Date', '').strip()
                
                if not variable_name:
                    errors.append(f"Row {row_num}: Missing variable name")
                    continue
                
                try:
                    amount_decimal = Decimal(amount)
                except:
                    errors.append(f"Row {row_num}: Invalid amount format")
                    continue
                
                # Parse effective date
                try:
                    if effective_date_str:
                        effective_date = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
                    else:
                        effective_date = date.today()
                except:
                    effective_date = date.today()
                
                # Create salary variable
                description = row.get('Comments', '').strip()
                if consider_arrear:
                    description = f"[ARREAR] {description}" if description else "[ARREAR] Arrear payment"
                
                variable_data = SalaryVariableCreate(
                    employee_id=employee.id,
                    variable_name=variable_name,
                    variable_type=SalaryVariableTypeEnum.ALLOWANCE,  # Use proper enum
                    amount=amount_decimal,
                    effective_date=effective_date,
                    description=description
                )
                
                self.create_salary_variable(
                    variable_data=variable_data,
                    business_id=business_id,
                    created_by=created_by
                )
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        return {
            "message": f"CSV import completed. {imported_count} records imported" + (" as arrear payments" if consider_arrear else ""),
            "imported_records": imported_count,
            "errors": errors[:10],  # Limit errors to first 10
            "total_errors": len(errors),
            "overwrite_existing": overwrite_existing,
            "consider_arrear": consider_arrear
        }
    
    def add_non_cash_salary(
        self,
        request_data: AddNonCashSalaryRequest,
        business_id: int,
        created_by: int
    ) -> Dict[str, Any]:
        """Add non-cash salary components"""
        
        # Validate employee IDs
        if not request_data.employee_ids:
            raise ValueError("At least one employee must be selected")
        
        # Validate employees exist
        if business_id is None:
            # Superadmin case - no business filtering
            employees = self.db.query(Employee).filter(
                Employee.id.in_(request_data.employee_ids),
                Employee.employee_status == "active"
            ).all()
        else:
            # Regular user case - filter by business
            employees = self.db.query(Employee).filter(
                Employee.id.in_(request_data.employee_ids),
                Employee.business_id == business_id,
                Employee.employee_status == "active"
            ).all()
        
        found_employee_ids = [emp.id for emp in employees]
        missing_employee_ids = [emp_id for emp_id in request_data.employee_ids if emp_id not in found_employee_ids]
        
        if missing_employee_ids:
            # Check if employees exist but are inactive or belong to different business
            all_employees = self.db.query(Employee).filter(
                Employee.id.in_(missing_employee_ids)
            ).all()
            
            error_details = []
            for emp_id in missing_employee_ids:
                emp = next((e for e in all_employees if e.id == emp_id), None)
                if emp:
                    if emp.employee_status != "active":
                        error_details.append(f"Employee ID {emp_id} ({emp.full_name}) is {emp.employee_status}")
                    elif business_id is not None and emp.business_id != business_id:
                        error_details.append(f"Employee ID {emp_id} ({emp.full_name}) belongs to different business")
                    else:
                        error_details.append(f"Employee ID {emp_id} ({emp.full_name}) validation failed")
                else:
                    error_details.append(f"Employee ID {emp_id} not found in database")
            
            raise ValueError(f"Employee validation failed: {'; '.join(error_details)}")
        
        # Create salary variables for each employee
        created_count = 0
        errors = []
        
        for employee in employees:
            try:
                # Create variable for target component
                variable_data = SalaryVariableCreate(
                    employee_id=employee.id,
                    variable_name=request_data.target_component,
                    variable_type=SalaryVariableTypeEnum.ALLOWANCE,
                    amount=Decimal("0.00"),  # Amount to be set later
                    effective_date=request_data.start_date,
                    end_date=request_data.end_date,
                    description=f"Non-cash salary: {request_data.source_component} to {request_data.target_component}"
                )
                
                self.create_salary_variable(
                    variable_data=variable_data,
                    business_id=business_id or employee.business_id,  # Use employee's business_id if business_id is None
                    created_by=created_by
                )
                
                created_count += 1
                
            except Exception as e:
                errors.append(f"Employee {employee.full_name}: {str(e)}")
        
        return {
            "message": f"Non-cash salary components added for {created_count} employees",
            "created_count": created_count,
            "errors": errors,
            "source_component": request_data.source_component,
            "target_component": request_data.target_component,
            "date_range": f"{request_data.start_date} to {request_data.end_date}"
        }
    
    def get_salary_variable_filters(
        self,
        business_id: Optional[int] = None,
        current_user = None
    ) -> Dict[str, List[str]]:
        """Get filter options for salary variable requests"""
        
        return self.repository.get_salary_variable_filters(
            business_id=business_id,
            current_user=current_user
        )