"""
Extra Days Repository
Data access layer for extra days operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from datetime import date, datetime
from decimal import Decimal

from app.repositories.base_repository import BaseRepository
from app.models.datacapture import ExtraDay, ExtraHour, EmployeeSalaryUnit
from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.location import Location
from app.models.designations import Designation


class ExtraDaysRepository(BaseRepository[ExtraDay]):
    """Repository for extra days operations"""
    
    def __init__(self, db: Session):
        super().__init__(ExtraDay, db)
    
    def get_by_employee_and_date(self, employee_id: int, work_date: date, business_id: Optional[int] = None) -> Optional[ExtraDay]:
        """Get extra day record by employee and work date"""
        # First try without business_id filter to find any existing record
        query = self.db.query(ExtraDay).filter(
            ExtraDay.employee_id == employee_id,
            ExtraDay.work_date == work_date
        )
        
        existing_record = query.first()
        
        # If no record found and business_id is specified, try with business_id filter
        if not existing_record and business_id:
            query = self.db.query(ExtraDay).filter(
                ExtraDay.employee_id == employee_id,
                ExtraDay.work_date == work_date,
                ExtraDay.business_id == business_id
            )
            existing_record = query.first()
        
        return existing_record
    
    def get_by_employee_and_month(self, employee_id: int, year: int, month: int, business_id: Optional[int] = None) -> List[ExtraDay]:
        """Get extra days records for employee in specific month"""
        query = self.db.query(ExtraDay).filter(
            ExtraDay.employee_id == employee_id,
            func.extract('year', ExtraDay.work_date) == year,
            func.extract('month', ExtraDay.work_date) == month
        )
        
        if business_id:
            query = query.filter(ExtraDay.business_id == business_id)
        
        return query.all()
    
    def get_employees_with_extra_days(
        self,
        business_id: Optional[int] = None,
        location_id: Optional[int] = None,
        department_id: Optional[int] = None,
        business_unit_name: Optional[str] = None,
        search_term: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> Dict[str, Any]:
        """Get employees with their extra days, overtime, and arrear data for a specific month"""
        
        # Base query for employees - Make business_id filtering optional for cross-business access
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.location),
            joinedload(Employee.designation),
            joinedload(Employee.business_unit)
        ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
        
        # Only filter by business_id if specifically requested and not None
        if business_id is not None:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        # Apply location filter
        if location_id:
            employee_query = employee_query.filter(Employee.location_id == location_id)
        
        # Apply department filter
        if department_id:
            employee_query = employee_query.filter(Employee.department_id == department_id)
        
        # 🎯 HYBRID APPROACH: Apply business unit filter using utility function
        if current_user and business_unit_name and business_unit_name not in ["All Business Units", "", None]:
            # Import here to avoid circular dependency
            from app.utils.business_unit_utils import apply_business_unit_filter
            employee_query = apply_business_unit_filter(
                employee_query, 
                self.db, 
                current_user, 
                business_unit_name, 
                Employee
            )
        elif business_unit_name and business_unit_name not in ["All Business Units", "", None]:
            # Fallback to old logic if no user context
            from app.models.business_unit import BusinessUnit
            employee_query = employee_query.filter(Employee.business_unit.has(BusinessUnit.name == business_unit_name))
        
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
        
        # Get employee IDs for data queries
        employee_ids = [emp.id for emp in employees]
        
        # 1. Get extra days data
        extra_days_query = self.db.query(ExtraDay).filter(
            ExtraDay.employee_id.in_(employee_ids)
        )
        
        if business_id:
            extra_days_query = extra_days_query.filter(ExtraDay.business_id == business_id)
        
        if year and month:
            extra_days_query = extra_days_query.filter(
                func.extract('year', ExtraDay.work_date) == year,
                func.extract('month', ExtraDay.work_date) == month
            )
        
        extra_days_records = extra_days_query.all()
        
        # 2. Get overtime (extra hours) data
        extra_hours_query = self.db.query(ExtraHour).filter(
            ExtraHour.employee_id.in_(employee_ids)
        )
        
        if business_id:
            extra_hours_query = extra_hours_query.filter(ExtraHour.business_id == business_id)
        
        if year and month:
            extra_hours_query = extra_hours_query.filter(
                func.extract('year', ExtraHour.work_date) == year,
                func.extract('month', ExtraHour.work_date) == month
            )
        
        extra_hours_records = extra_hours_query.all()
        
        # 3. Get arrear (employee salary unit) data
        arrear_query = self.db.query(EmployeeSalaryUnit).filter(
            EmployeeSalaryUnit.employee_id.in_(employee_ids),
            EmployeeSalaryUnit.is_arrear == True
        )
        
        if business_id:
            arrear_query = arrear_query.filter(EmployeeSalaryUnit.business_id == business_id)
        
        if year and month:
            arrear_query = arrear_query.filter(
                func.extract('year', EmployeeSalaryUnit.effective_date) == year,
                func.extract('month', EmployeeSalaryUnit.effective_date) == month
            )
        
        arrear_records = arrear_query.all()
        
        # Group data by employee
        extra_days_by_employee = {}
        extra_hours_by_employee = {}
        arrear_by_employee = {}
        
        for record in extra_days_records:
            if record.employee_id not in extra_days_by_employee:
                extra_days_by_employee[record.employee_id] = []
            extra_days_by_employee[record.employee_id].append(record)
        
        for record in extra_hours_records:
            if record.employee_id not in extra_hours_by_employee:
                extra_hours_by_employee[record.employee_id] = []
            extra_hours_by_employee[record.employee_id].append(record)
        
        for record in arrear_records:
            if record.employee_id not in arrear_by_employee:
                arrear_by_employee[record.employee_id] = []
            arrear_by_employee[record.employee_id].append(record)
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return {
            "employees": employees,
            "extra_days_by_employee": extra_days_by_employee,
            "extra_hours_by_employee": extra_hours_by_employee,
            "arrear_by_employee": arrear_by_employee,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def create_or_update_extra_day(
        self,
        employee_id: int,
        work_date: date,
        hours_worked: Decimal,
        hourly_rate: Decimal,
        work_description: Optional[str] = None,
        location: Optional[str] = None,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> ExtraDay:
        """Create or update extra day record"""
        
        # Ensure business_id is set
        if not business_id:
            business_id = 1  # Default business_id
        
        # Ensure created_by is set
        if not created_by:
            created_by = 1  # Default created_by
        
        # Check if record exists
        existing_record = self.get_by_employee_and_date(employee_id, work_date, business_id)
        
        if existing_record:
            # Update existing record
            existing_record.hours_worked = hours_worked
            existing_record.hourly_rate = hourly_rate
            existing_record.total_amount = hours_worked * hourly_rate
            existing_record.work_description = work_description
            existing_record.location = location
            existing_record.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(existing_record)
            return existing_record
        else:
            # Create new record
            total_amount = hours_worked * hourly_rate
            
            new_record = ExtraDay(
                business_id=business_id,
                employee_id=employee_id,
                work_date=work_date,
                hours_worked=hours_worked,
                hourly_rate=hourly_rate,
                total_amount=total_amount,
                work_description=work_description,
                location=location,
                created_by=created_by
            )
            
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)
            return new_record
    
    def create_or_update_extra_hour(
        self,
        employee_id: int,
        work_date: date,
        extra_hours: Decimal,
        overtime_rate: Decimal,
        work_description: Optional[str] = None,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> ExtraHour:
        """Create or update extra hour record for overtime"""
        
        # Ensure business_id is set
        if not business_id:
            business_id = 1
        
        # Ensure created_by is set
        if not created_by:
            created_by = 1
        
        # Check if record exists - Use flexible lookup to find existing records
        existing_record = self.db.query(ExtraHour).filter(
            ExtraHour.employee_id == employee_id,
            ExtraHour.work_date == work_date
        ).first()
        
        # If no record found, try with business_id filter
        if not existing_record:
            existing_record = self.db.query(ExtraHour).filter(
                ExtraHour.employee_id == employee_id,
                ExtraHour.work_date == work_date,
                ExtraHour.business_id == business_id
            ).first()
        
        if existing_record:
            # Update existing record
            existing_record.extra_hours = extra_hours
            existing_record.overtime_rate = overtime_rate
            existing_record.total_amount = extra_hours * overtime_rate
            existing_record.work_description = work_description
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
                extra_hours=extra_hours,
                overtime_rate=overtime_rate,
                total_amount=total_amount,
                work_description=work_description,
                created_by=created_by
            )
            
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)
            return new_record
    
    def create_or_update_salary_variable(
        self,
        employee_id: int,
        variable_name: str,
        variable_type: str,
        amount: Decimal,
        effective_date: date,
        description: Optional[str] = None,
        is_arrear: bool = False,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> EmployeeSalaryUnit:
        """Create or update employee salary unit record for arrear payments"""
        
        # Ensure business_id is set
        if not business_id:
            business_id = 1
        
        # Ensure created_by is set
        if not created_by:
            created_by = 1
        
        # Check if record exists for this month - Use flexible lookup
        existing_record = self.db.query(EmployeeSalaryUnit).filter(
            EmployeeSalaryUnit.employee_id == employee_id,
            EmployeeSalaryUnit.unit_name == variable_name,
            EmployeeSalaryUnit.effective_date == effective_date
        ).first()
        
        # If no record found, try with business_id filter
        if not existing_record:
            existing_record = self.db.query(EmployeeSalaryUnit).filter(
                EmployeeSalaryUnit.employee_id == employee_id,
                EmployeeSalaryUnit.unit_name == variable_name,
                EmployeeSalaryUnit.effective_date == effective_date,
                EmployeeSalaryUnit.business_id == business_id
            ).first()
        
        if existing_record:
            # Update existing record
            existing_record.amount = amount
            existing_record.comments = description
            existing_record.is_arrear = is_arrear
            existing_record.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(existing_record)
            return existing_record
        else:
            # Create new record
            new_record = EmployeeSalaryUnit(
                business_id=business_id,
                employee_id=employee_id,
                unit_name=variable_name,
                unit_type=variable_type,
                amount=amount,
                effective_date=effective_date,
                comments=description,
                is_arrear=is_arrear,
                created_by=created_by
            )
            
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)
            return new_record
    
    def get_filter_options(self, business_id: Optional[int] = None, current_user = None) -> Dict[str, List[str]]:
        """Get filter options for dropdowns"""
        
        try:
            # Determine business filtering based on user role
            filter_business_id = None
            if current_user:
                if current_user.role.value == "SUPERADMIN" or str(current_user.role) == "UserRole.SUPERADMIN":
                    # Superadmin sees all data - no business filtering
                    filter_business_id = None
                else:
                    # Company admin - get business_id from their owned businesses
                    if hasattr(current_user, 'businesses') and current_user.businesses:
                        # Use the first business they own
                        filter_business_id = current_user.businesses[0].id
                    else:
                        # Fallback to provided business_id or None
                        filter_business_id = business_id
            else:
                # No user context - use provided business_id
                filter_business_id = business_id
            
            print(f"🔍 Extra Days Filter options - User: {current_user.email if current_user else 'None'}, Role: {current_user.role if current_user else 'None'}, Business ID: {filter_business_id}")
            
            # Import required models
            from app.models.business_unit import BusinessUnit
            from app.models.cost_center import CostCenter
            
            # Get departments from database
            departments_query = self.db.query(Department).filter(Department.is_active == True)
            if filter_business_id:
                departments_query = departments_query.filter(Department.business_id == filter_business_id)
            department_names = [d.name for d in departments_query.all()]
            
            # Get locations from database
            locations_query = self.db.query(Location).filter(Location.is_active == True)
            if filter_business_id:
                locations_query = locations_query.filter(Location.business_id == filter_business_id)
            location_names = [l.name for l in locations_query.all()]
            
            # 🎯 HYBRID APPROACH: Use business unit utils for consistent behavior
            try:
                if current_user:
                    from app.utils.business_unit_utils import get_business_unit_options
                    business_unit_options = get_business_unit_options(self.db, current_user, filter_business_id)
                    business_unit_names = business_unit_options[1:]  # Remove "All Business Units"
                    print(f"   🏢 Business units found: {len(business_unit_names)}")
                else:
                    # Fallback to business units if no user context
                    business_units_query = self.db.query(BusinessUnit).filter(BusinessUnit.is_active == True)
                    if filter_business_id:
                        business_units_query = business_units_query.filter(BusinessUnit.business_id == filter_business_id)
                    business_unit_names = [bu.name for bu in business_units_query.all()]
                    print(f"   🏢 Business units found (fallback): {len(business_unit_names)}")
                
                # If no business units found, use default
                if not business_unit_names:
                    business_unit_names = ["Default Business Unit"]
            except Exception as e:
                print(f"Error fetching business units: {e}")
                business_unit_names = ["Default Business Unit"]
            
            # Get cost centers from database
            cost_centers_query = self.db.query(CostCenter).filter(CostCenter.is_active == True)
            if filter_business_id:
                cost_centers_query = cost_centers_query.filter(CostCenter.business_id == filter_business_id)
            cost_center_names = [cc.name for cc in cost_centers_query.all()]
            
            # If no data found, provide fallback options
            if not location_names:
                location_names = ["Default Location"]
            
            if not department_names:
                department_names = ["Default Department"]
            
            if not cost_center_names:
                cost_center_names = ["Default Cost Center", "HRA", "Travel", "Medical"]
            
            return {
                "businessUnits": ["All Business Units"] + business_unit_names,
                "locations": ["All Locations"] + location_names,
                "departments": ["All Departments"] + department_names,
                "costCenters": ["All Cost Centers"] + cost_center_names
            }
            
        except Exception as e:
            print(f"Database error in get_filter_options: {str(e)}")
            # Fallback to basic options if database query fails
            return {
                "businessUnits": ["All Business Units", "Default Business Unit"],
                "locations": ["All Locations", "Default Location"],
                "departments": ["All Departments", "Default Department"],
                "costCenters": ["All Cost Centers", "Default Cost Center", "HRA", "Travel", "Medical"]
            }
    
    def search_employees_by_name(
        self,
        search_term: str,
        business_id: Optional[int] = None,
        limit: int = 5
    ) -> List[Employee]:
        """Search employees by name for autocomplete"""
        
        query = self.db.query(Employee).filter(
            Employee.employee_status == EmployeeStatus.ACTIVE,
            or_(
                Employee.first_name.ilike(f"%{search_term}%"),
                Employee.last_name.ilike(f"%{search_term}%")
            )
        )
        
        # Only filter by business_id if specifically requested and not None
        if business_id is not None:
            query = query.filter(Employee.business_id == business_id)
        
        return query.limit(limit).all()
    
    def get_extra_days_for_export(
        self,
        business_id: Optional[int] = None,
        location_id: Optional[int] = None,
        department_id: Optional[int] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get extra days data for CSV export"""
        
        # Get employees with their extra days - Make business_id filtering optional
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.location),
            joinedload(Employee.designation)
        ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
        
        # Only filter by business_id if specifically requested and not None
        if business_id is not None:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        if location_id:
            employee_query = employee_query.filter(Employee.location_id == location_id)
        
        if department_id:
            employee_query = employee_query.filter(Employee.department_id == department_id)
        
        employees = employee_query.all()
        
        # Get extra days for these employees
        employee_ids = [emp.id for emp in employees]
        extra_days_query = self.db.query(ExtraDay).filter(
            ExtraDay.employee_id.in_(employee_ids)
        )
        
        if business_id:
            extra_days_query = extra_days_query.filter(ExtraDay.business_id == business_id)
        
        if year and month:
            extra_days_query = extra_days_query.filter(
                func.extract('year', ExtraDay.work_date) == year,
                func.extract('month', ExtraDay.work_date) == month
            )
        
        extra_days_records = extra_days_query.all()
        
        # Group by employee
        extra_days_by_employee = {}
        for record in extra_days_records:
            if record.employee_id not in extra_days_by_employee:
                extra_days_by_employee[record.employee_id] = []
            extra_days_by_employee[record.employee_id].append(record)
        
        # Build export data
        export_data = []
        for i, employee in enumerate(employees, start=1):
            extra_days_list = extra_days_by_employee.get(employee.id, [])
            
            # Calculate totals
            total_extra_days = sum(float(ed.hours_worked) for ed in extra_days_list)
            comments = "; ".join([ed.work_description for ed in extra_days_list if ed.work_description])
            
            # Format joining date
            joining_date = "Jul 07, 2025"
            if employee.date_of_joining:
                joining_date = employee.date_of_joining.strftime("%b %d, %Y")
            
            export_data.append({
                "sn": i,
                "employee_name": employee.full_name,
                "employee_code": employee.employee_code,
                "designation": employee.designation.name if employee.designation else "Associate Software Engineer",
                "joining_date": joining_date,
                "extra_days": total_extra_days,
                "arrear": 0.0,  # Not implemented yet
                "ot": 0.0,      # Not implemented yet
                "comments": comments
            })
        
        return export_data
    
    def bulk_import_extra_days(
        self,
        import_data: List[Dict[str, Any]],
        business_id: int,
        year: int,
        month: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Bulk import extra days from CSV data"""
        
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
                
                employee = self.db.query(Employee).filter(
                    Employee.employee_code == employee_code,
                    Employee.employee_status == EmployeeStatus.ACTIVE
                ).first()
                
                # If not found and business_id was specified, try with business_id filter
                if not employee and business_id:
                    employee = self.db.query(Employee).filter(
                        Employee.employee_code == employee_code,
                        Employee.business_id == business_id,
                        Employee.employee_status == EmployeeStatus.ACTIVE
                    ).first()
                
                if not employee:
                    errors.append(f"Row {row_num}: Employee {employee_code} not found")
                    continue
                
                # Parse extra days data
                try:
                    extra_days = float(row_data.get('extra_days', 0))
                    comments = row_data.get('comments', '').strip()
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
                if extra_days > 0:  # Only create if there are extra days
                    self.create_or_update_extra_day(
                        employee_id=employee.id,
                        work_date=effective_date,
                        hours_worked=Decimal(str(extra_days)),
                        hourly_rate=Decimal("500.00"),  # Default hourly rate
                        work_description=comments,
                        business_id=business_id,
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