"""
Salary Variable Repository
Data access layer for salary variable operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.datacapture import SalaryVariable, SalaryVariableType
from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.location import Location
from app.models.business_unit import BusinessUnit
from app.models.business import Business
from app.models.leave_type import LeaveType
from app.schemas.datacapture import (
    SalaryVariableCreate, SalaryVariableUpdate, SalaryVariableResponse,
    SalaryVariableEmployeeResponse, SalaryVariableUpdateRequest
)
from app.utils.business_unit_utils import get_business_unit_options, apply_business_unit_filter


class SalaryVariableRepository:
    """Repository for salary variable operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_salary_variables(
        self,
        business_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get salary variables with filtering and pagination"""
        
        # Base query
        query = self.db.query(SalaryVariable).options(
            joinedload(SalaryVariable.employee)
        ).filter(SalaryVariable.is_active == True)
        
        if business_id:
            query = query.filter(SalaryVariable.business_id == business_id)
        
        if employee_id:
            query = query.filter(SalaryVariable.employee_id == employee_id)
        
        # Apply pagination
        offset = (page - 1) * size
        variables = query.order_by(desc(SalaryVariable.created_at)).offset(offset).limit(size).all()
        
        # Convert to response format
        result = []
        for var in variables:
            result.append({
                "id": var.id,
                "employee_id": var.employee_id,
                "employee_name": var.employee.full_name if var.employee else "Unknown",
                "employee_code": var.employee.employee_code if var.employee else "N/A",
                "variable_name": var.variable_name,
                "variable_amount": var.amount,
                "effective_date": var.effective_date,
                "status": "active" if var.is_active else "inactive",
                "created_at": var.created_at,
                "business_id": var.business_id,
                "is_active": var.is_active,
                "updated_at": var.updated_at,
                "created_by": var.created_by
            })
        
        return result
    
    def create_salary_variable(
        self,
        variable_data: SalaryVariableCreate,
        business_id: int,
        created_by: int
    ) -> Dict[str, Any]:
        """Create new salary variable"""
        
        # Create salary variable
        new_variable = SalaryVariable(
            business_id=business_id,
            employee_id=variable_data.employee_id,
            variable_name=variable_data.variable_name,
            variable_type=variable_data.variable_type,
            amount=variable_data.amount,
            effective_date=variable_data.effective_date,
            end_date=variable_data.end_date,
            is_recurring=variable_data.is_recurring,
            frequency=variable_data.frequency,
            description=variable_data.description,
            is_taxable=variable_data.is_taxable,
            created_by=created_by
        )
        
        self.db.add(new_variable)
        self.db.commit()
        self.db.refresh(new_variable)
        
        # Get employee details
        employee = self.db.query(Employee).filter(Employee.id == variable_data.employee_id).first()
        
        return {
            "id": new_variable.id,
            "employee_id": new_variable.employee_id,
            "employee_name": employee.full_name if employee else "Unknown",
            "employee_code": employee.employee_code if employee else "N/A",
            "variable_name": new_variable.variable_name,
            "variable_amount": new_variable.amount,
            "effective_date": new_variable.effective_date,
            "status": "active",
            "created_at": new_variable.created_at,
            "business_id": new_variable.business_id,
            "is_active": new_variable.is_active,
            "updated_at": new_variable.updated_at,
            "created_by": new_variable.created_by
        }
    
    def update_salary_variable(
        self,
        variable_id: int,
        variable_data: SalaryVariableUpdate,
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update salary variable"""
        
        query = self.db.query(SalaryVariable).filter(SalaryVariable.id == variable_id)
        
        if business_id:
            query = query.filter(SalaryVariable.business_id == business_id)
        
        variable = query.first()
        
        if not variable:
            return None
        
        # Update fields
        update_data = variable_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(variable, field, value)
        
        if updated_by:
            variable.updated_by = updated_by
        
        self.db.commit()
        self.db.refresh(variable)
        
        # Get employee details
        employee = self.db.query(Employee).filter(Employee.id == variable.employee_id).first()
        
        return {
            "id": variable.id,
            "employee_id": variable.employee_id,
            "employee_name": employee.full_name if employee else "Unknown",
            "employee_code": employee.employee_code if employee else "N/A",
            "variable_name": variable.variable_name,
            "variable_amount": variable.amount,
            "effective_date": variable.effective_date,
            "status": "active" if variable.is_active else "inactive",
            "created_at": variable.created_at,
            "business_id": variable.business_id,
            "is_active": variable.is_active,
            "updated_at": variable.updated_at,
            "created_by": variable.created_by
        }
    
    def delete_salary_variable(
        self,
        variable_id: int,
        business_id: Optional[int] = None
    ) -> bool:
        """Delete salary variable (soft delete)"""
        
        query = self.db.query(SalaryVariable).filter(SalaryVariable.id == variable_id)
        
        if business_id:
            query = query.filter(SalaryVariable.business_id == business_id)
        
        variable = query.first()
        
        if not variable:
            return False
        
        # Soft delete
        variable.is_active = False
        self.db.commit()
        return True
    
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
        
        print(f"🔍 Salary Variable Query - BU: '{business_unit}', Leave Option: '{leave_option}', User: {getattr(current_user, 'email', 'None') if current_user else 'None'}")
        
        # Base query for employees
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.location),
            joinedload(Employee.business_unit),
            joinedload(Employee.business)  # Add business relationship for better debugging
        ).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
        
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
            print(f"   📊 Filtered by business_id: {business_id}")
        
        # 🎯 IMPROVED HYBRID APPROACH: Apply business unit filter with better error handling
        if current_user and business_unit and business_unit != "All Business Units":
            user_role = getattr(current_user, 'role', 'admin')
            print(f"   👤 User role: {user_role}")
            
            if user_role == "superadmin" or str(user_role) == "UserRole.SUPERADMIN":
                # For superadmin: filter by business (company)
                business_obj = self.db.query(Business).filter(
                    Business.business_name == business_unit,
                    Business.is_active == True
                ).first()
                
                if business_obj:
                    employee_query = employee_query.filter(Employee.business_id == business_obj.id)
                    print(f"   🏢 Superadmin: Filtering by business '{business_unit}' (ID: {business_obj.id})")
                else:
                    # If business not found, log warning but don't fail completely
                    print(f"   ⚠️ Business '{business_unit}' not found, showing no results")
                    # Return empty result set by adding impossible condition
                    employee_query = employee_query.filter(Employee.id == -1)
            else:
                # For company admin: filter by business unit (division)
                bu_obj = self.db.query(BusinessUnit).filter(
                    BusinessUnit.name == business_unit,
                    BusinessUnit.is_active == True
                ).first()
                
                if bu_obj:
                    employee_query = employee_query.filter(Employee.business_unit_id == bu_obj.id)
                    print(f"   🏬 Admin: Filtering by business unit '{business_unit}' (ID: {bu_obj.id})")
                else:
                    # If business unit not found, log warning but don't fail completely
                    print(f"   ⚠️ Business Unit '{business_unit}' not found, showing no results")
                    # Return empty result set by adding impossible condition
                    employee_query = employee_query.filter(Employee.id == -1)
        elif business_unit and business_unit not in ["All Business Units", ""] and not current_user:
            # Fallback to old logic if no user context
            employee_query = employee_query.filter(Employee.business_unit.has(BusinessUnit.name == business_unit))
            print(f"   🔄 Fallback: Filtering by business unit '{business_unit}'")
        else:
            print(f"   ✅ No business unit filter applied (showing all)")
        
        # Apply location filter
        if location and location not in ["All Locations", ""]:
            employee_query = employee_query.filter(Employee.location.has(Location.name == location))
            print(f"   📍 Filtered by location: {location}")
        
        # Apply department filter
        if department and department not in ["All Departments", ""]:
            employee_query = employee_query.filter(Employee.department.has(Department.name == department))
            print(f"   🏢 Filtered by department: {department}")
        
        # Apply search filter
        if search:
            employee_query = employee_query.filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
            print(f"   🔍 Search filter: {search}")
        
        # 🎯 EMPLOYEE FILTERING BASED ON LEAVE OPTION
        # If a specific leave option is selected, we might want to show only employees 
        # who have that type of salary variable, or show all employees with zero amounts
        if leave_option and leave_option not in ["Leave Encashment", ""]:
            print(f"   🎯 Leave option selected: '{leave_option}' - showing all employees with filtered salary variables")
        
        # Get total count for pagination
        total_count = employee_query.count()
        total_pages = (total_count + size - 1) // size
        print(f"   📊 Total employees found: {total_count}")
        
        # Apply pagination
        offset = (page - 1) * size
        employees = employee_query.offset(offset).limit(size).all()
        
        # Build response matching frontend expectations
        employee_data = []
        
        for employee in employees:
            # Get salary variable data for this employee and month
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
                end_date = start_date + timedelta(days=32)
                end_date = end_date.replace(day=1)
            
            # Get salary variables for this employee in the month
            variables_query = self.db.query(SalaryVariable).filter(
                SalaryVariable.employee_id == employee.id,
                SalaryVariable.effective_date >= start_date,
                SalaryVariable.effective_date < end_date,
                SalaryVariable.is_active == True
            )
            
            # 🎯 APPLY LEAVE OPTION FILTER
            if leave_option and leave_option not in ["Leave Encashment", ""]:
                print(f"   🏖️ Applying leave option filter: '{leave_option}'")
                
                # Create flexible filter conditions based on leave option type
                if "Encashment" in leave_option:
                    # For encashment options, look for encashment-related variables
                    base_leave_type = leave_option.replace(" Encashment", "").strip()
                    variables_query = variables_query.filter(
                        or_(
                            SalaryVariable.variable_name.ilike(f"%{leave_option}%"),
                            SalaryVariable.variable_name.ilike(f"%{base_leave_type}%"),
                            SalaryVariable.variable_name.ilike("%encashment%")
                        )
                    )
                elif leave_option in ["Bonus", "Incentive", "Allowance", "Commission", "Overtime"]:
                    # For salary variable types, filter by variable name or type
                    variables_query = variables_query.filter(
                        or_(
                            SalaryVariable.variable_name.ilike(f"%{leave_option}%"),
                            SalaryVariable.variable_type == leave_option.lower()
                        )
                    )
                else:
                    # Generic filter for other options
                    variables_query = variables_query.filter(
                        SalaryVariable.variable_name.ilike(f"%{leave_option}%")
                    )
            else:
                print(f"   ✅ No leave option filter applied (showing all salary variables)")
            
            variables = variables_query.all()
            print(f"   💰 Found {len(variables)} salary variables for employee {employee.employee_code}")
            
            # Calculate totals
            amount = sum(float(var.amount) for var in variables)
            comments = "; ".join([var.description or "" for var in variables if var.description])
            total = amount  # Total would be calculated based on all variables
            
            # Get actual employee data
            employee_location = employee.location.name if employee.location else "Not Assigned"
            employee_department = employee.department.name if employee.department else "Not Assigned"
            employee_business_unit = employee.business_unit.name if employee.business_unit else "Not Assigned"
            
            employee_data.append({
                "employee_id": employee.id,
                "employee_name": employee.full_name,
                "employee_code": employee.employee_code,
                "location": employee_location,
                "department": employee_department,
                "business_unit": employee_business_unit,
                "amount": amount,
                "comments": comments,
                "total": total
            })
        
        return {
            "employees": employee_data,
            "total_pages": total_pages,
            "current_page": page,
            "total_employees": total_count
        }
    
    def update_salary_variable_employee(
        self,
        update_data: SalaryVariableUpdateRequest,
        business_id: int,
        updated_by: int
    ) -> Dict[str, str]:
        """Update salary variable for an employee"""
        
        # Find employee by code
        employee = self.db.query(Employee).filter(
            Employee.employee_code == update_data.employee_code,
            Employee.business_id == business_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with code {update_data.employee_code} not found")
        
        # Parse month to get effective date
        try:
            month_year = update_data.month.split()
            month_name = month_year[0]
            year = int(month_year[1])
            
            # Convert month name to number
            month_names = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            month_num = month_names.index(month_name) + 1
            effective_date = date(year, month_num, 1)
        except:
            effective_date = date.today()
        
        # Check if variable already exists for this employee and month
        existing_variable = self.db.query(SalaryVariable).filter(
            SalaryVariable.employee_id == employee.id,
            SalaryVariable.effective_date == effective_date,
            SalaryVariable.variable_name == update_data.variable_type,
            SalaryVariable.is_active == True
        ).first()
        
        if existing_variable:
            # Update existing variable
            existing_variable.amount = Decimal(str(update_data.amount))
            existing_variable.description = update_data.comments
            existing_variable.updated_by = updated_by
        else:
            # Create new variable
            new_variable = SalaryVariable(
                business_id=business_id,
                employee_id=employee.id,
                variable_name=update_data.variable_type,
                variable_type=SalaryVariableType.ALLOWANCE,  # Default type
                amount=Decimal(str(update_data.amount)),
                effective_date=effective_date,
                description=update_data.comments,
                is_recurring=False,
                created_by=updated_by
            )
            self.db.add(new_variable)
        
        self.db.commit()
        
        return {
            "message": f"Salary variable updated for employee {employee.full_name}",
            "employee_code": update_data.employee_code,
            "month": update_data.month,
            "amount": str(update_data.amount),
            "variable_type": update_data.variable_type,
            "effective_date": effective_date.isoformat()
        }
    
    def get_salary_variable_filters(
        self,
        business_id: Optional[int] = None,
        current_user = None
    ) -> Dict[str, List[str]]:
        """Get filter options for salary variable requests using HYBRID APPROACH"""
        
        print(f"🔍 Getting salary variable filters - User: {getattr(current_user, 'email', 'None') if current_user else 'None'}")
        
        # Initialize with safe defaults
        result = {
            "business_units": ["All Business Units"],
            "locations": ["All Locations"],
            "departments": ["All Departments"],
            "cost_centers": ["All Cost Centers"],
            "leave_options": ["Leave Encashment", "Bonus", "Incentive", "Allowance", "Commission", "Overtime", "Travel Allowance"]
        }
        
        try:
            # 🎯 HYBRID APPROACH: Use business unit utils for consistent behavior
            if current_user:
                business_unit_options = get_business_unit_options(self.db, current_user, business_id)
                result["business_units"] = business_unit_options
                print(f"   🏢 Business units from hybrid approach: {business_unit_options}")
            else:
                # Fallback to business units if no user context
                business_units_query = self.db.query(BusinessUnit).filter(BusinessUnit.is_active == True)
                if business_id:
                    business_units_query = business_units_query.filter(BusinessUnit.business_id == business_id)
                business_unit_names = [bu.name for bu in business_units_query.all()]
                if business_unit_names:
                    result["business_units"] = ["All Business Units"] + business_unit_names
                print(f"   🏬 Business units from fallback: {result['business_units']}")
        except Exception as e:
            print(f"   ⚠️ Error getting business units: {e}")
            pass  # Use defaults
            
        try:
            # Try to get departments from database
            departments = self.db.query(Department).filter(Department.is_active == True)
            if business_id:
                departments = departments.filter(Department.business_id == business_id)
            department_names = [d.name for d in departments.all()]
            if department_names:
                result["departments"] = ["All Departments"] + department_names
            print(f"   🏢 Departments: {len(department_names)} found")
        except Exception as e:
            print(f"   ⚠️ Error getting departments: {e}")
            pass  # Use defaults
            
        try:
            # Try to get locations from database
            locations = self.db.query(Location).filter(Location.is_active == True)
            if business_id:
                locations = locations.filter(Location.business_id == business_id)
            location_names = [l.name for l in locations.all()]
            if location_names:
                result["locations"] = ["All Locations"] + location_names
            print(f"   📍 Locations: {len(location_names)} found")
        except Exception as e:
            print(f"   ⚠️ Error getting locations: {e}")
            pass  # Use defaults
        
        try:
            # Try to get leave types from database for leave options
            leave_types = self.db.query(LeaveType)
            if business_id:
                leave_types = leave_types.filter(LeaveType.business_id == business_id)
            leave_type_names = [lt.name for lt in leave_types.all()]
            
            # Create comprehensive leave options list
            base_options = ["Leave Encashment", "Bonus", "Incentive", "Allowance", "Commission", "Overtime", "Travel Allowance"]
            
            if leave_type_names:
                # Combine base options with actual leave types from database
                leave_options = base_options + [f"{lt} Encashment" for lt in leave_type_names if "Leave" in lt or "Off" in lt]
                result["leave_options"] = leave_options
                print(f"   🏖️ Leave options with DB leave types: {len(leave_options)} found")
            else:
                # Fallback to comprehensive salary variable types if no leave types found
                result["leave_options"] = base_options + ["Annual Leave Encashment", "Casual Leave Encashment", "Sick Leave Encashment"]
                print(f"   🏖️ Leave options (fallback): {len(result['leave_options'])} found")
                
        except Exception as e:
            print(f"   ⚠️ Error getting leave types: {e}")
            # Fallback to comprehensive salary variable types
            result["leave_options"] = ["Leave Encashment", "Bonus", "Incentive", "Allowance", "Commission", "Overtime", "Travel Allowance", "Annual Leave Encashment", "Casual Leave Encashment"]
        
        # Always ensure all required fields are present
        print(f"   ✅ Final filters: {result}")
        return result