"""
Salary Details Repository
Data access layer for salary details management
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime, date
from decimal import Decimal

from app.models.employee import Employee, EmployeeSalary, EmployeeStatus
from app.models.business_unit import BusinessUnit
from app.models.location import Location
from app.models.cost_center import CostCenter
from app.models.department import Department
from app.models.designations import Designation


class SalaryDetailsRepository:
    """Repository for salary details data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
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
        """Get employees with their salary details and total count"""
        try:
            # Base query - FIXED: Use EmployeeStatus.ACTIVE enum instead of lowercase string
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            # Apply business unit filter - HYBRID APPROACH (same as Daily Punches)
            if business_unit and business_unit != "All Business Units":
                if current_user:
                    user_role = getattr(current_user, 'role', 'admin')
                    
                    if user_role == "superadmin" or str(user_role) == "UserRole.SUPERADMIN":
                        # For superadmin: filter by business (company) - use Employee.business_id
                        from app.models.business import Business
                        business_obj = self.db.query(Business).filter(Business.business_name == business_unit).first()
                        if business_obj:
                            query = query.filter(Employee.business_id == business_obj.id)
                    else:
                        # For company admin: filter by business unit (division)
                        bu_obj = self.db.query(BusinessUnit).filter(BusinessUnit.name == business_unit).first()
                        if bu_obj:
                            query = query.filter(Employee.business_unit_id == bu_obj.id)
                else:
                    # Fallback: try business unit filter
                    bu_obj = self.db.query(BusinessUnit).filter(BusinessUnit.name == business_unit).first()
                    if bu_obj:
                        query = query.filter(Employee.business_unit_id == bu_obj.id)
            
            # Apply location filter
            if location and location != "All Locations":
                location_obj = self.db.query(Location).filter(Location.name == location).first()
                if location_obj:
                    query = query.filter(Employee.location_id == location_obj.id)
            
            # Apply cost center filter
            if cost_center and cost_center != "All Cost Centers":
                cost_center_obj = self.db.query(CostCenter).filter(CostCenter.name == cost_center).first()
                if cost_center_obj:
                    query = query.filter(Employee.cost_center_id == cost_center_obj.id)
            
            # Apply department filter
            if department and department != "All Departments":
                dept_obj = self.db.query(Department).filter(Department.name == department).first()
                if dept_obj:
                    query = query.filter(Employee.department_id == dept_obj.id)
            
            # Apply search filter
            if search:
                query = query.filter(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * size
            employees = query.offset(offset).limit(size).all()
            
            # Convert to response format with real salary data
            result = []
            for emp in employees:
                # Get department name
                dept_name = "Not Assigned"
                if emp.department_id:
                    dept = self.db.query(Department).filter(Department.id == emp.department_id).first()
                    if dept:
                        dept_name = dept.name
                
                # Get designation name
                designation_name = "Not Assigned"
                if emp.designation_id:
                    designation = self.db.query(Designation).filter(Designation.id == emp.designation_id).first()
                    if designation:
                        designation_name = designation.name
                
                # Get employee salary details from EmployeeSalary table
                salary_record = self.db.query(EmployeeSalary).filter(
                    and_(
                        EmployeeSalary.employee_id == emp.id,
                        EmployeeSalary.is_active == True
                    )
                ).order_by(EmployeeSalary.effective_from.desc()).first()
                
                # Default salary values if no record found
                basic_salary = 0.0
                hra = 0.0
                special_allowance = 0.0
                medical_allowance = 0.0
                conveyance_allowance = 0.0
                transport_allowance = 0.0
                last_updated = "Not Set"
                
                if salary_record:
                    basic_salary = float(salary_record.basic_salary) if salary_record.basic_salary else 0.0
                    last_updated = salary_record.effective_from.strftime("%b-%Y") if salary_record.effective_from else "Not Set"
                    
                    # Extract allowances from salary_options JSON if available
                    if salary_record.salary_options:
                        options = salary_record.salary_options
                        hra = float(options.get('hra', 0.0))
                        special_allowance = float(options.get('special_allowance', 0.0))
                        medical_allowance = float(options.get('medical_allowance', 0.0))
                        conveyance_allowance = float(options.get('conveyance_allowance', 0.0))
                        transport_allowance = float(options.get('transport_allowance', 0.0))
                    else:
                        # Use individual allowance columns if available
                        hra = float(salary_record.house_rent_allowance) if salary_record.house_rent_allowance else 0.0
                        special_allowance = float(salary_record.special_allowance) if salary_record.special_allowance else 0.0
                        medical_allowance = float(salary_record.medical_allowance) if salary_record.medical_allowance else 0.0
                        conveyance_allowance = float(salary_record.conveyance_allowance) if salary_record.conveyance_allowance else 0.0
                        transport_allowance = float(salary_record.telephone_allowance) if salary_record.telephone_allowance else 0.0
                
                result.append({
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name or ''}".strip(),
                    "code": emp.employee_code,
                    "designation": designation_name,
                    "department": dept_name,
                    "last_updated": last_updated,
                    "basic": basic_salary,
                    "hra": hra,
                    "sa": special_allowance,  # SA = Special Allowance
                    "mda": medical_allowance,  # MDA = Medical Allowance
                    "ca": conveyance_allowance,  # CA = Conveyance Allowance
                    "ta": transport_allowance,  # TA = Transport Allowance
                    "employee_id": emp.id,
                    "business_id": emp.business_id
                })
            
            return result, total_count
            
        except Exception as e:
            print(f"Error in get_employees_with_salary_details: {str(e)}")
            return [], 0
    
    def get_filter_options(self, business_id: Optional[int] = None, current_user = None) -> Dict[str, List[str]]:
        """Get filter options for salary details from database"""
        try:
            # Get business units - use utility function for consistency
            if current_user:
                from app.utils.business_unit_utils import get_business_unit_options
                business_units = get_business_unit_options(self.db, current_user, business_id)
            else:
                # Fallback if no user provided
                bu_query = self.db.query(BusinessUnit.name).filter(BusinessUnit.is_active == True)
                if business_id:
                    bu_query = bu_query.filter(BusinessUnit.business_id == business_id)
                business_units = ["All Business Units"] + [bu[0] for bu in bu_query.distinct().all()]
            
            # Get locations
            location_query = self.db.query(Location.name).filter(Location.is_active == True)
            if business_id:
                location_query = location_query.filter(Location.business_id == business_id)
            locations = ["All Locations"] + [loc[0] for loc in location_query.distinct().all()]
            
            # Get cost centers
            cc_query = self.db.query(CostCenter.name).filter(CostCenter.is_active == True)
            if business_id:
                cc_query = cc_query.filter(CostCenter.business_id == business_id)
            cost_centers = ["All Cost Centers"] + [cc[0] for cc in cc_query.distinct().all()]
            
            # Get departments
            dept_query = self.db.query(Department.name).filter(Department.is_active == True)
            if business_id:
                dept_query = dept_query.filter(Department.business_id == business_id)
            departments = ["All Departments"] + [dept[0] for dept in dept_query.distinct().all()]
            
            return {
                "business_units": business_units,
                "locations": locations,
                "cost_centers": cost_centers,
                "departments": departments
            }
            
        except Exception as e:
            print(f"Error in get_filter_options: {str(e)}")
            return {
                "business_units": ["All Business Units"],
                "locations": ["All Locations"],
                "cost_centers": ["All Cost Centers"],
                "departments": ["All Departments"]
            }
    
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
        """Update employee salary details in database"""
        try:
            # Find employee
            query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employee = query.first()
            if not employee:
                raise ValueError(f"Employee with code {employee_code} not found")
            
            # Get or create employee salary record
            salary_record = self.db.query(EmployeeSalary).filter(
                and_(
                    EmployeeSalary.employee_id == employee.id,
                    EmployeeSalary.is_active == True
                )
            ).first()
            
            if not salary_record:
                # Create new salary record
                salary_record = EmployeeSalary(
                    employee_id=employee.id,
                    basic_salary=Decimal(str(basic_salary)),
                    gross_salary=Decimal(str(basic_salary * 2)),  # Simple calculation
                    ctc=Decimal(str(basic_salary * 2.5)),  # Simple calculation
                    effective_from=date.today(),
                    is_active=True,
                    salary_options={}
                )
                self.db.add(salary_record)
            
            # Update salary details
            salary_record.basic_salary = Decimal(str(basic_salary))
            
            # Update salary options JSON
            salary_options = salary_record.salary_options or {}
            if hra is not None:
                salary_options['hra'] = float(hra)
            if special_allowance is not None:
                salary_options['special_allowance'] = float(special_allowance)
            if medical_allowance is not None:
                salary_options['medical_allowance'] = float(medical_allowance)
            if conveyance_allowance is not None:
                salary_options['conveyance_allowance'] = float(conveyance_allowance)
            if transport_allowance is not None:
                salary_options['transport_allowance'] = float(transport_allowance)
            
            salary_record.salary_options = salary_options
            
            # Update employee timestamp
            if updated_by:
                employee.updated_by = updated_by
            employee.updated_at = datetime.now()
            
            self.db.commit()
            
            return {
                "message": f"Salary details updated successfully for {employee.first_name} {employee.last_name or ''}",
                "employee_code": employee_code,
                "employee_name": f"{employee.first_name} {employee.last_name or ''}".strip(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update salary details: {str(e)}")
    
    def search_employees(
        self,
        search: str,
        business_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search employees for autocomplete from database"""
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
    
    def export_salary_details_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export salary details as CSV from database"""
        try:
            # Get employees with filters
            employees, _ = self.get_employees_with_salary_details(
                business_id=business_id,
                business_unit=business_unit,
                location=location,
                cost_center=cost_center,
                department=department,
                page=1,
                size=10000  # Large number to get all records
            )
            
            # Create CSV content
            csv_content = "Employee Code,Employee Name,Designation,Department,Basic,HRA,SA,MDA,CA,TA,Last Updated\n"
            
            for emp in employees:
                csv_content += f"{emp['code']},{emp['name']},{emp['designation']},{emp['department']},{emp['basic']},{emp['hra']},{emp['sa']},{emp['mda']},{emp['ca']},{emp['ta']},{emp['last_updated']}\n"
            
            return csv_content
            
        except Exception as e:
            print(f"Error in export_salary_details_csv: {str(e)}")
            return "Employee Code,Employee Name,Designation,Department,Basic,HRA,SA,MDA,CA,TA,Last Updated\n"
    
    def import_salary_details_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import salary details from CSV with real database operations"""
        try:
            import csv
            import io
            
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            successful_imports = 0
            failed_imports = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
                try:
                    # Validate required fields
                    employee_code = row.get('Employee Code', '').strip()
                    if not employee_code:
                        errors.append(f"Row {row_num}: Employee Code is required")
                        failed_imports += 1
                        continue
                    
                    # Find employee
                    employee = self.db.query(Employee).filter(
                        and_(
                            Employee.employee_code == employee_code,
                            Employee.business_id == business_id
                        )
                    ).first()
                    
                    if not employee:
                        errors.append(f"Row {row_num}: Employee with code '{employee_code}' not found")
                        failed_imports += 1
                        continue
                    
                    # Parse salary components
                    try:
                        basic_salary = float(row.get('Basic', 0))
                        hra = float(row.get('HRA', 0))
                        special_allowance = float(row.get('SA', 0))
                        medical_allowance = float(row.get('MDA', 0))
                        conveyance_allowance = float(row.get('CA', 0))
                        transport_allowance = float(row.get('TA', 0))
                    except ValueError as ve:
                        errors.append(f"Row {row_num}: Invalid numeric value - {str(ve)}")
                        failed_imports += 1
                        continue
                    
                    # Update salary details
                    self.update_employee_salary_details(
                        employee_code=employee_code,
                        basic_salary=basic_salary,
                        hra=hra,
                        special_allowance=special_allowance,
                        medical_allowance=medical_allowance,
                        conveyance_allowance=conveyance_allowance,
                        transport_allowance=transport_allowance,
                        business_id=business_id,
                        updated_by=created_by
                    )
                    
                    successful_imports += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    failed_imports += 1
                    continue
            
            return {
                "total_records": successful_imports + failed_imports,
                "successful_imports": successful_imports,
                "failed_imports": failed_imports,
                "errors": errors,
                "message": f"Import completed: {successful_imports} successful, {failed_imports} failed"
            }
            
        except Exception as e:
            return {
                "total_records": 0,
                "successful_imports": 0,
                "failed_imports": 0,
                "errors": [f"CSV parsing error: {str(e)}"],
                "message": "Import failed due to CSV parsing error"
            }
    
    def bulk_update_salary_details(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Bulk update salary details with real database operations"""
        try:
            successful_updates = 0
            failed_updates = 0
            errors = []
            
            for update in updates:
                try:
                    employee_code = update.get('employee_code')
                    if not employee_code:
                        errors.append("Employee code is required")
                        failed_updates += 1
                        continue
                    
                    # Update salary details
                    self.update_employee_salary_details(
                        employee_code=employee_code,
                        basic_salary=update.get('basic_salary', 0),
                        hra=update.get('hra'),
                        special_allowance=update.get('special_allowance'),
                        medical_allowance=update.get('medical_allowance'),
                        conveyance_allowance=update.get('conveyance_allowance'),
                        transport_allowance=update.get('transport_allowance'),
                        business_id=business_id,
                        updated_by=updated_by
                    )
                    
                    successful_updates += 1
                    
                except Exception as e:
                    errors.append(f"Employee {employee_code}: {str(e)}")
                    failed_updates += 1
                    continue
            
            return {
                "total_records": len(updates),
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "total_records": len(updates) if updates else 0,
                "successful_updates": 0,
                "failed_updates": len(updates) if updates else 0,
                "errors": [f"Bulk update error: {str(e)}"]
            }