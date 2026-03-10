"""
Extra Hours Repository
Data access layer for extra hours operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from datetime import date, datetime
from decimal import Decimal

from app.repositories.base_repository import BaseRepository
from app.models.datacapture import ExtraHour
from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.location import Location
from app.models.designations import Designation
from app.utils.business_unit_utils import (
    get_business_unit_options, 
    apply_business_unit_filter,
    get_user_business_context
)


class ExtraHoursRepository(BaseRepository[ExtraHour]):
    """Repository for extra hours operations"""
    
    def __init__(self, db: Session):
        super().__init__(ExtraHour, db)
    
    def get_by_employee_and_date(self, employee_id: int, work_date: date, business_id: Optional[int] = None) -> Optional[ExtraHour]:
        """Get extra hours record by employee and work date"""
        query = self.db.query(ExtraHour).filter(
            ExtraHour.employee_id == employee_id,
            ExtraHour.work_date == work_date
        )
        
        if business_id:
            query = query.filter(ExtraHour.business_id == business_id)
        
        return query.first()
    
    def get_by_employee_and_month(self, employee_id: int, year: int, month: int, business_id: Optional[int] = None) -> List[ExtraHour]:
        """Get extra hours records for employee in specific month"""
        query = self.db.query(ExtraHour).filter(
            ExtraHour.employee_id == employee_id,
            func.extract('year', ExtraHour.work_date) == year,
            func.extract('month', ExtraHour.work_date) == month
        )
        
        if business_id:
            query = query.filter(ExtraHour.business_id == business_id)
        
        return query.all()
    
    def get_employees_with_extra_hours(
        self,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search_term: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> Dict[str, Any]:
        """Get employees with their extra hours data for a specific month"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        
        # Base query for employees
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.location),
            joinedload(Employee.designation)
        ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
        
        # Apply business context filter
        if not is_superadmin and user_business_id:
            employee_query = employee_query.filter(Employee.business_id == user_business_id)
        
        # Apply business unit filter using hybrid logic
        employee_query = apply_business_unit_filter(
            employee_query, self.db, current_user, business_unit, Employee
        )
        
        # Apply location filter
        if location and location != "All Locations":
            from app.models.location import Location
            location_obj = self.db.query(Location).filter(
                Location.name == location,
                Location.is_active == True
            ).first()
            if location_obj:
                employee_query = employee_query.filter(Employee.location_id == location_obj.id)
        
        # Apply department filter
        if department and department != "All Departments":
            from app.models.department import Department
            dept_obj = self.db.query(Department).filter(
                Department.name == department,
                Department.is_active == True
            ).first()
            if dept_obj:
                employee_query = employee_query.filter(Employee.department_id == dept_obj.id)
        
        # Apply search filter
        if search_term:
            search_pattern = f"%{search_term}%"
            employee_query = employee_query.filter(
                or_(
                    Employee.first_name.ilike(search_pattern),
                    Employee.last_name.ilike(search_pattern),
                    Employee.employee_code.ilike(search_pattern)
                )
            )
        
        # Get total count
        total = employee_query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        employees = employee_query.offset(offset).limit(size).all()
        
        # Get extra hours data for these employees
        employee_ids = [emp.id for emp in employees]
        extra_hours_query = self.db.query(ExtraHour).filter(
            ExtraHour.employee_id.in_(employee_ids)
        )
        
        # Apply business context filter for extra hours
        if not is_superadmin and user_business_id:
            extra_hours_query = extra_hours_query.filter(ExtraHour.business_id == user_business_id)
        
        if year and month:
            extra_hours_query = extra_hours_query.filter(
                func.extract('year', ExtraHour.work_date) == year,
                func.extract('month', ExtraHour.work_date) == month
            )
        
        extra_hours_records = extra_hours_query.all()
        
        # Group extra hours by employee
        extra_hours_by_employee = {}
        for record in extra_hours_records:
            if record.employee_id not in extra_hours_by_employee:
                extra_hours_by_employee[record.employee_id] = []
            extra_hours_by_employee[record.employee_id].append(record)
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return {
            "employees": employees,
            "extra_hours_by_employee": extra_hours_by_employee,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def create_extra_hours_record(
        self,
        employee_id: int,
        work_date: date,
        extra_hours: Decimal,
        overtime_rate: Decimal,
        work_description: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        current_user = None,
        created_by: Optional[int] = None
    ) -> ExtraHour:
        """Create extra hours record"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        business_id = user_business_id if not is_superadmin else None
        
        # Check if record exists
        existing_record = self.get_by_employee_and_date(employee_id, work_date, business_id)
        
        if existing_record:
            # Update existing record
            existing_record.extra_hours = extra_hours
            existing_record.overtime_rate = overtime_rate
            existing_record.total_amount = extra_hours * overtime_rate
            existing_record.work_description = work_description
            existing_record.start_time = start_time
            existing_record.end_time = end_time
            existing_record.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(existing_record)
            return existing_record
        else:
            # Create new record
            total_amount = extra_hours * overtime_rate
            
            new_record = ExtraHour(
                business_id=business_id,
                employee_id=employee_id,
                work_date=work_date,
                regular_hours=Decimal("8.0"),  # Default regular hours
                extra_hours=extra_hours,
                overtime_rate=overtime_rate,
                total_amount=total_amount,
                start_time=start_time,
                end_time=end_time,
                work_description=work_description,
                created_by=created_by
            )
            
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)
            return new_record
    
    def get_filter_options(self, current_user = None) -> Dict[str, List[str]]:
        """Get filter options for dropdowns"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        
        # Get departments from database
        dept_query = self.db.query(Department).filter(Department.is_active == True)
        if not is_superadmin and user_business_id:
            dept_query = dept_query.filter(Department.business_id == user_business_id)
        departments = [dept.name for dept in dept_query.all()]
        
        # Get locations from database
        location_query = self.db.query(Location).filter(Location.is_active == True)
        if not is_superadmin and user_business_id:
            location_query = location_query.filter(Location.business_id == user_business_id)
        locations = [loc.name for loc in location_query.all()]
        
        # Get business units using hybrid logic - pass business_id to filter properly
        business_units = get_business_unit_options(self.db, current_user, business_id=user_business_id)
        
        return {
            "businessUnits": business_units,
            "locations": ["All Locations"] + locations,
            "departments": ["All Departments"] + departments
        }
    
    def search_employees_by_name(
        self,
        search_term: str,
        current_user = None,
        limit: int = 5
    ) -> List[Employee]:
        """Search employees by name for autocomplete"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        
        query = self.db.query(Employee).filter(
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(f"%{search_term}%"),
                Employee.last_name.ilike(f"%{search_term}%")
            )
        )
        
        # Apply business context filter
        if not is_superadmin and user_business_id:
            query = query.filter(Employee.business_id == user_business_id)
        
        return query.limit(limit).all()
    
    def find_employee_by_code(self, employee_code: str, current_user = None) -> Optional[Employee]:
        """Find employee by code with business context"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        
        query = self.db.query(Employee).filter(
            Employee.employee_code == employee_code,
            Employee.employee_status == EmployeeStatus.ACTIVE
        )
        
        # Apply business context filter
        if not is_superadmin and user_business_id:
            query = query.filter(Employee.business_id == user_business_id)
        
        return query.first()
    
    def get_extra_hours_for_export(
        self,
        location: Optional[str] = None,
        department: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        current_user = None
    ) -> List[Dict[str, Any]]:
        """Get extra hours data for CSV export"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        
        # Get employees with their extra hours
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.location),
            joinedload(Employee.designation)
        ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
        
        # Apply business context filter
        if not is_superadmin and user_business_id:
            employee_query = employee_query.filter(Employee.business_id == user_business_id)
        
        # Apply location filter
        if location and location != "All Locations":
            from app.models.location import Location
            location_obj = self.db.query(Location).filter(
                Location.name == location,
                Location.is_active == True
            ).first()
            if location_obj:
                employee_query = employee_query.filter(Employee.location_id == location_obj.id)
        
        # Apply department filter
        if department and department != "All Departments":
            from app.models.department import Department
            dept_obj = self.db.query(Department).filter(
                Department.name == department,
                Department.is_active == True
            ).first()
            if dept_obj:
                employee_query = employee_query.filter(Employee.department_id == dept_obj.id)
        
        employees = employee_query.all()
        
        # Get extra hours for these employees
        employee_ids = [emp.id for emp in employees]
        extra_hours_query = self.db.query(ExtraHour).filter(
            ExtraHour.employee_id.in_(employee_ids)
        )
        
        # Apply business context filter
        if not is_superadmin and user_business_id:
            extra_hours_query = extra_hours_query.filter(ExtraHour.business_id == user_business_id)
        
        if year and month:
            extra_hours_query = extra_hours_query.filter(
                func.extract('year', ExtraHour.work_date) == year,
                func.extract('month', ExtraHour.work_date) == month
            )
        
        extra_hours_records = extra_hours_query.all()
        
        # Group by employee
        extra_hours_by_employee = {}
        for record in extra_hours_records:
            if record.employee_id not in extra_hours_by_employee:
                extra_hours_by_employee[record.employee_id] = []
            extra_hours_by_employee[record.employee_id].append(record)
        
        # Build export data
        export_data = []
        for i, employee in enumerate(employees, start=1):
            extra_hours_list = extra_hours_by_employee.get(employee.id, [])
            
            # Calculate totals
            total_extra_hours = sum(float(eh.extra_hours) for eh in extra_hours_list)
            total_amount = sum(float(eh.total_amount) for eh in extra_hours_list)
            avg_hourly_rate = (total_amount / total_extra_hours) if total_extra_hours > 0 else 0.0
            
            export_data.append({
                "sn": i,
                "employee_name": employee.full_name,
                "employee_code": employee.employee_code,
                "designation": employee.designation.name if employee.designation else "Associate Software Engineer",
                "extra_hours": total_extra_hours,
                "hourly_rate": avg_hourly_rate,
                "total_amount": total_amount
            })
        
        return export_data
    
    def bulk_import_extra_hours(
        self,
        import_data: List[Dict[str, Any]],
        year: int,
        month: int,
        created_by: int,
        overwrite_existing: bool = False,
        current_user = None
    ) -> Dict[str, Any]:
        """Bulk import extra hours from CSV data"""
        
        # Get user business context
        is_superadmin, user_business_id = get_user_business_context(current_user, self.db) if current_user else (False, None)
        business_id = user_business_id or 1
        
        imported_count = 0
        errors = []
        
        # Calculate effective date (first day of month)
        effective_date = date(year, month, 1)
        
        for row_num, row_data in enumerate(import_data, start=2):
            try:
                # Get employee by code
                employee_code = row_data.get('employee_code', '').strip()
                if not employee_code:
                    errors.append(f"Row {row_num}: Missing employee code")
                    continue
                
                employee = self.find_employee_by_code(employee_code, current_user)
                
                if not employee:
                    errors.append(f"Row {row_num}: Employee {employee_code} not found")
                    continue
                
                # Parse extra hours data
                try:
                    extra_hours = float(row_data.get('extra_hours', 0))
                    hourly_rate = float(row_data.get('hourly_rate', 500.0))
                    reason = row_data.get('reason', '').strip()
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid numeric format")
                    continue
                
                # Check if record exists
                existing_record = self.get_by_employee_and_date(
                    employee.id, effective_date, business_id
                )
                
                if existing_record and not overwrite_existing:
                    errors.append(f"Row {row_num}: Record exists for employee {employee_code}")
                    continue
                
                # Create or update record
                if extra_hours > 0:  # Only create if there are extra hours
                    self.create_extra_hours_record(
                        employee_id=employee.id,
                        work_date=effective_date,
                        extra_hours=Decimal(str(extra_hours)),
                        overtime_rate=Decimal(str(hourly_rate)),
                        work_description=reason,
                        current_user=current_user,
                        created_by=created_by
                    )
                    imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        return {
            "imported_records": imported_count,
            "errors": errors[:10],  # Limit to first 10 errors
            "total_errors": len(errors)
        }