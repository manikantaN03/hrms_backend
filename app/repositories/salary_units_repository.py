"""
Salary Units Repository
Database operations for salary units management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, date, timedelta
from decimal import Decimal
import io
import csv

from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.location import Location
from app.models.business_unit import BusinessUnit
from app.models.business import Business
from app.models.datacapture import SalaryUnit, EmployeeSalaryUnit
from app.utils.business_unit_utils import get_business_unit_options, apply_business_unit_filter


class SalaryUnitsRepository:
    """Repository for salary units database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employees_with_salary_units(
        self,
        business_id: Optional[int] = None,
        month: str = "October 2025",
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        component: Optional[str] = None,
        arrear: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> List[Dict[str, Any]]:
        """
        Get employees with their salary units data
        
        Args:
            business_id: Business ID filter
            month: Month filter
            business_unit: Business unit filter
            location: Location filter
            department: Department filter
            component: Component filter
            arrear: Arrear flag
            search: Search term
            page: Page number
            size: Page size
            current_user: Current user for hybrid filtering
            
        Returns:
            List of employee salary units data
        """
        print(f"🔍 Salary Units Query - Component: '{component}', Month: '{month}', BU: '{business_unit}'")
        
        try:
            # Parse month to get date range
            try:
                month_year = month.split()
                month_name = month_year[0]
                year = int(month_year[1])
                
                # Convert month name to number
                month_names = ["January", "February", "March", "April", "May", "June",
                              "July", "August", "September", "October", "November", "December"]
                month_num = month_names.index(month_name) + 1
                start_date = date(year, month_num, 1)
                
                # Get next month for end date
                if month_num == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month_num + 1, 1)
            except:
                start_date = date.today().replace(day=1)
                end_date = start_date.replace(day=28) + timedelta(days=4)
                end_date = end_date.replace(day=1)
            
            # Base query for employees
            query = self.db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.location),
                joinedload(Employee.business_unit),
                joinedload(Employee.business)
            ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            # 🎯 HYBRID APPROACH: Apply business unit filter using utility function
            if current_user:
                query = apply_business_unit_filter(
                    query, 
                    self.db, 
                    current_user, 
                    business_unit, 
                    Employee
                )
            else:
                # Fallback to old logic if no user context
                if business_unit and business_unit not in ["All Business Units", ""]:
                    query = query.filter(Employee.business_unit.has(BusinessUnit.name == business_unit))
            
            # Apply location filter
            if location and location not in ["All Locations", ""]:
                query = query.filter(Employee.location.has(Location.name == location))
            
            # Apply department filter
            if department and department not in ["All Departments", ""]:
                query = query.filter(Employee.department.has(Department.name == department))
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
            
            # Build response with salary units data
            result = []
            
            for employee in employees:
                # Get salary units for this employee and month
                salary_units_query = self.db.query(EmployeeSalaryUnit).filter(
                    EmployeeSalaryUnit.employee_id == employee.id,
                    EmployeeSalaryUnit.effective_date >= start_date,
                    EmployeeSalaryUnit.effective_date < end_date,
                    EmployeeSalaryUnit.is_active == True
                )
                
                # 🎯 IMPROVED COMPONENT FILTERING
                if component and component not in ["Component", ""]:
                    print(f"   🔧 Filtering salary units by component: '{component}' for employee {employee.employee_code}")
                    
                    # Use flexible matching for component names
                    salary_units_query = salary_units_query.filter(
                        or_(
                            EmployeeSalaryUnit.unit_name == component,
                            EmployeeSalaryUnit.unit_name.ilike(f"%{component}%"),
                            EmployeeSalaryUnit.unit_type.ilike(f"%{component.lower()}%")
                        )
                    )
                else:
                    print(f"   ✅ No component filter applied for employee {employee.employee_code}")
                
                if arrear:
                    salary_units_query = salary_units_query.filter(
                        EmployeeSalaryUnit.is_arrear == True
                    )
                    print(f"   🔄 Filtering for arrear payments only")
                
                salary_units = salary_units_query.all()
                print(f"   💰 Found {len(salary_units)} salary units for employee {employee.employee_code}")
                
                # Calculate totals
                total_amount = sum(float(unit.amount) for unit in salary_units)
                comments = "; ".join([unit.comments or "" for unit in salary_units if unit.comments])
                
                # Show component details for debugging
                if salary_units:
                    unit_details = [f"{unit.unit_name}(₹{unit.amount})" for unit in salary_units]
                    print(f"      Components: {', '.join(unit_details)}")
                
                result.append({
                    "employee_id": employee.id,
                    "name": employee.full_name,
                    "employee_code": employee.employee_code,
                    "location": employee.location.name if employee.location else "Hyderabad",
                    "department": employee.department.name if employee.department else "Technical Support",
                    "amount": total_amount,
                    "comments": comments,
                    "component": component or "Travel Allowance"
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Database error in get_employees_with_salary_units: {str(e)}")
    
    def get_filter_options(
        self,
        business_id: Optional[int] = None,
        current_user = None
    ) -> Dict[str, List[str]]:
        """
        Get filter options for salary units
        
        Args:
            business_id: Business ID filter
            current_user: Current user for hybrid filtering
            
        Returns:
            Dictionary with filter options
        """
        try:
            # Get departments from database
            departments_query = self.db.query(Department).filter(Department.is_active == True)
            if business_id:
                departments_query = departments_query.filter(Department.business_id == business_id)
            department_names = [d.name for d in departments_query.all()]
            
            # Get locations from database
            locations_query = self.db.query(Location).filter(Location.is_active == True)
            if business_id:
                locations_query = locations_query.filter(Location.business_id == business_id)
            location_names = [l.name for l in locations_query.all()]
            
            # 🎯 HYBRID APPROACH: Use business unit utils for consistent behavior
            try:
                if current_user:
                    business_unit_options = get_business_unit_options(self.db, current_user, business_id)
                    business_unit_names = business_unit_options[1:]  # Remove "All Business Units"
                else:
                    # Fallback to business units if no user context
                    business_units_query = self.db.query(BusinessUnit).filter(BusinessUnit.is_active == True)
                    if business_id:
                        business_units_query = business_units_query.filter(BusinessUnit.business_id == business_id)
                    business_unit_names = [bu.name for bu in business_units_query.all()]
                
                # If no business units found, use default
                if not business_unit_names:
                    business_unit_names = ["Default Business Unit"]
            except Exception as e:
                print(f"Error fetching business units: {e}")
                business_unit_names = ["Default Business Unit"]
            
            # Get component options from salary units
            try:
                print(f"   🔧 Fetching component options for business_id: {business_id}")
                
                # Get distinct component names from salary units
                components_query = self.db.query(EmployeeSalaryUnit.unit_name).filter(
                    EmployeeSalaryUnit.is_active == True
                ).distinct()
                
                if business_id:
                    components_query = components_query.filter(EmployeeSalaryUnit.business_id == business_id)
                
                component_names = [c.unit_name for c in components_query.all() if c.unit_name]
                
                # Also get component types for additional options
                types_query = self.db.query(EmployeeSalaryUnit.unit_type).filter(
                    EmployeeSalaryUnit.is_active == True
                ).distinct()
                
                if business_id:
                    types_query = types_query.filter(EmployeeSalaryUnit.business_id == business_id)
                
                component_types = [t.unit_type.title() for t in types_query.all() if t.unit_type]
                
                # Combine unique component names and types
                all_components = list(set(component_names + component_types))
                
                print(f"   📊 Found {len(component_names)} component names and {len(component_types)} component types")
                print(f"   🏷️ Component names: {component_names[:5]}...")  # Show first 5
                print(f"   🏷️ Component types: {component_types}")
                
                component_names = all_components
                
            except Exception as e:
                print(f"Error fetching components: {e}")
                component_names = []
            
            # If no components found, use defaults
            if not component_names:
                component_names = ["Travel Allowance", "Conveyance", "Food Allowance", "Mobile Allowance"]
            
            return {
                "businessUnits": ["All Business Units"] + business_unit_names,
                "locations": ["All Locations"] + location_names,
                "departments": ["All Departments"] + department_names,
                "components": ["Component"] + component_names
            }
            
        except Exception as e:
            raise Exception(f"Database error in get_filter_options: {str(e)}")
    
    def update_employee_salary_units(
        self,
        employee_code: str,
        effective_date: date,
        amount: Decimal,
        comments: str = "",
        component: str = "Component",
        arrear: bool = False,
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update salary units for an employee
        
        Args:
            employee_code: Employee code
            effective_date: Effective date
            amount: Amount
            comments: Comments
            component: Component type
            arrear: Arrear flag
            business_id: Business ID
            updated_by: User ID who updated
            
        Returns:
            Update result
        """
        try:
            # Find employee
            employee = self.db.query(Employee).filter(
                Employee.employee_code == employee_code,
                Employee.business_id == business_id if business_id else True
            ).first()
            
            if not employee:
                raise ValueError(f"Employee with code {employee_code} not found")
            
            # Check if salary unit exists for this employee, date, and component
            existing_unit = self.db.query(EmployeeSalaryUnit).filter(
                EmployeeSalaryUnit.employee_id == employee.id,
                EmployeeSalaryUnit.effective_date == effective_date,
                EmployeeSalaryUnit.unit_name == component,
                EmployeeSalaryUnit.is_active == True
            ).first()
            
            if existing_unit:
                # Update existing
                existing_unit.amount = amount
                existing_unit.comments = comments
                existing_unit.is_arrear = arrear
                existing_unit.updated_by = updated_by
                existing_unit.updated_at = datetime.now()
                self.db.commit()
                unit_id = existing_unit.id
            else:
                # Create new salary unit
                new_unit = EmployeeSalaryUnit(
                    business_id=business_id or employee.business_id,
                    employee_id=employee.id,
                    unit_name=component,
                    unit_type="allowance",
                    amount=amount,
                    effective_date=effective_date,
                    comments=comments,
                    is_arrear=arrear,
                    is_active=True,
                    created_by=updated_by
                )
                self.db.add(new_unit)
                self.db.commit()
                self.db.refresh(new_unit)
                unit_id = new_unit.id
            
            return {
                "unit_id": unit_id,
                "employee_name": employee.full_name,
                "employee_code": employee_code,
                "amount": amount,
                "component": component,
                "effective_date": effective_date
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in update_employee_salary_units: {str(e)}")
    
    def import_travel_kilometers(
        self,
        effective_date: date,
        location: str = "All Locations",
        department: str = "All Departments",
        component: str = "Type of Distance",
        distance_type: str = "Calculated",
        comments: str = "",
        overwrite_existing: bool = False,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import travel kilometers data
        
        Args:
            effective_date: Effective date
            location: Location filter
            department: Department filter
            component: Component type
            distance_type: Distance type
            comments: Comments
            overwrite_existing: Whether to overwrite existing
            business_id: Business ID
            created_by: User ID who created
            
        Returns:
            Import result
        """
        try:
            # Get employees based on filters
            employees_query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            if business_id:
                employees_query = employees_query.filter(Employee.business_id == business_id)
            
            if location != "All Locations":
                employees_query = employees_query.join(Location).filter(Location.name == location)
            if department != "All Departments":
                employees_query = employees_query.join(Department).filter(Department.name == department)
            
            employees = employees_query.all()
            
            records_created = 0
            
            for employee in employees:
                # Mock travel calculation - in real system, would calculate from travel records
                travel_amount = Decimal("2000.00")  # Mock amount based on distance
                
                if overwrite_existing:
                    # Delete existing travel units for this employee and date
                    self.db.query(EmployeeSalaryUnit).filter(
                        EmployeeSalaryUnit.employee_id == employee.id,
                        EmployeeSalaryUnit.effective_date == effective_date,
                        EmployeeSalaryUnit.unit_name.like(f"Travel%"),
                        EmployeeSalaryUnit.is_active == True
                    ).update({"is_active": False})
                
                # Create new travel salary unit
                travel_unit = EmployeeSalaryUnit(
                    business_id=business_id or employee.business_id,
                    employee_id=employee.id,
                    unit_name=f"Travel - {distance_type}",
                    unit_type="travel",
                    amount=travel_amount,
                    effective_date=effective_date,
                    comments=f"{comments} - {distance_type} distance",
                    is_active=True,
                    created_by=created_by
                )
                
                self.db.add(travel_unit)
                records_created += 1
            
            self.db.commit()
            
            return {
                "employees_affected": len(employees),
                "records_created": records_created
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in import_travel_kilometers: {str(e)}")
    
    def get_export_data(
        self,
        effective_date: date,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        business_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get data for export
        
        Args:
            effective_date: Effective date
            location: Location filter
            cost_center: Cost center filter
            department: Department filter
            business_id: Business ID
            
        Returns:
            List of export data
        """
        try:
            # Get employees with filters
            employees_query = self.db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.location)
            ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                employees_query = employees_query.filter(Employee.business_id == business_id)
            if location and location != "All Locations":
                employees_query = employees_query.join(Location).filter(Location.name == location)
            if department and department != "All Departments":
                employees_query = employees_query.join(Department).filter(Department.name == department)
            
            employees = employees_query.all()
            
            export_data = []
            
            for employee in employees:
                # Get salary units for this employee and date
                salary_units = self.db.query(EmployeeSalaryUnit).filter(
                    EmployeeSalaryUnit.employee_id == employee.id,
                    EmployeeSalaryUnit.effective_date == effective_date,
                    EmployeeSalaryUnit.is_active == True
                ).all()
                
                total_amount = sum(float(unit.amount) for unit in salary_units)
                comments = "; ".join([unit.comments or "" for unit in salary_units if unit.comments])
                components = ", ".join([unit.unit_name for unit in salary_units])
                
                export_data.append({
                    "employee_name": employee.full_name,
                    "employee_code": employee.employee_code,
                    "location": employee.location.name if employee.location else "Hyderabad",
                    "department": employee.department.name if employee.department else "Technical Support",
                    "amount": total_amount,
                    "comments": comments,
                    "total": total_amount,
                    "component": components or "Travel Allowance"
                })
            
            return export_data
            
        except Exception as e:
            raise Exception(f"Database error in get_export_data: {str(e)}")
    
    def import_csv_data(
        self,
        csv_content: str,
        effective_date: date,
        overwrite_existing: bool = False,
        consider_arrear: bool = False,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import salary units data from CSV
        
        Args:
            csv_content: CSV content
            effective_date: Effective date
            overwrite_existing: Whether to overwrite existing
            consider_arrear: Whether to consider as arrear
            business_id: Business ID
            created_by: User ID who created
            
        Returns:
            Import result
        """
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            imported_records = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Get employee by code
                    employee_code = row.get('Employee Code', '').strip()
                    if not employee_code:
                        errors.append(f"Row {row_num}: Missing employee code")
                        continue
                    
                    employee = self.db.query(Employee).filter(
                        Employee.employee_code == employee_code,
                        Employee.business_id == business_id if business_id else True
                    ).first()
                    
                    if not employee:
                        errors.append(f"Row {row_num}: Employee {employee_code} not found")
                        continue
                    
                    # Parse salary units data
                    amount = row.get('Amount', '0').strip()
                    comments = row.get('Comments', '').strip()
                    component = row.get('Component', 'Travel Allowance').strip()
                    
                    try:
                        amount_decimal = Decimal(str(amount))
                    except:
                        errors.append(f"Row {row_num}: Invalid amount format")
                        continue
                    
                    # Create or update salary unit
                    if overwrite_existing:
                        # Delete existing units for this employee, date, and component
                        self.db.query(EmployeeSalaryUnit).filter(
                            EmployeeSalaryUnit.employee_id == employee.id,
                            EmployeeSalaryUnit.effective_date == effective_date,
                            EmployeeSalaryUnit.unit_name == component,
                            EmployeeSalaryUnit.is_active == True
                        ).update({"is_active": False})
                    
                    # Create new salary unit
                    new_unit = EmployeeSalaryUnit(
                        business_id=business_id or employee.business_id,
                        employee_id=employee.id,
                        unit_name=component,
                        unit_type="imported",
                        amount=amount_decimal,
                        effective_date=effective_date,
                        comments=f"{comments} {'(Arrear)' if consider_arrear else ''}",
                        is_arrear=consider_arrear,
                        is_active=True,
                        created_by=created_by
                    )
                    
                    self.db.add(new_unit)
                    imported_records += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue
            
            self.db.commit()
            
            return {
                "imported_records": imported_records,
                "errors": errors
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in import_csv_data: {str(e)}")