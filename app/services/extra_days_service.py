"""
Extra Days Service
Business logic for extra days management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from decimal import Decimal
import io
import csv

from app.repositories.extra_days_repository import ExtraDaysRepository
from app.models.employee import Employee
from app.models.datacapture import ExtraDay, ExtraHour, EmployeeSalaryUnit
from app.schemas.datacapture import (
    ExtraDaysEmployeeResponse, ExtraDaysUpdateRequest, ExtraDaysFiltersResponse,
    ExtraDaysSearchResponse, ExtraDaysExportResponse, ExtraDaysExportAllResponse,
    ExtraDaysImportResponse
)
from app.core.exceptions import ValidationError, NotFoundError


class ExtraDaysService:
    """Service class for extra days operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ExtraDaysRepository(db)
    
    def parse_month_string(self, month_str: str) -> tuple[int, int]:
        """Parse month string like 'AUG-2025' to year and month numbers"""
        try:
            month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            
            month_part, year_part = month_str.split("-")
            year = int(year_part)
            month = month_names.index(month_part) + 1
            
            return year, month
        except (ValueError, IndexError):
            # Default to current month if parsing fails
            today = date.today()
            return today.year, today.month
    
    def get_employees_with_extra_days(
        self,
        month: str = "AUG-2025",
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        business_id: Optional[int] = None,
        current_user = None
    ) -> List[ExtraDaysEmployeeResponse]:
        """Get employees with their extra days data"""
        
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
        
        print(f"🔍 Extra Days Employees - User: {current_user.email if current_user else 'None'}, Role: {current_user.role if current_user else 'None'}, Business ID: {filter_business_id}, Business Unit: {business_unit}")
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Convert filter names to IDs if needed, but use hybrid approach for business units
        location_id = None
        department_id = None
        business_unit_id = None
        
        if location and location not in ["All Locations", ""]:
            from app.models.location import Location
            location_obj = self.db.query(Location).filter(Location.name == location).first()
            if location_obj:
                location_id = location_obj.id
        
        if department and department not in ["All Departments", ""]:
            from app.models.department import Department
            dept_obj = self.db.query(Department).filter(Department.name == department).first()
            if dept_obj:
                department_id = dept_obj.id
        
        # For business unit, we'll handle the hybrid filtering in the repository
        # Don't convert to ID here, pass the name and user context
        
        # Get employees with extra days data
        result = self.repository.get_employees_with_extra_days(
            business_id=filter_business_id,
            location_id=location_id,
            department_id=department_id,
            business_unit_name=business_unit,  # Pass name instead of ID
            search_term=search,
            year=year,
            month=month_num,
            page=page,
            size=size,
            current_user=current_user  # Pass user context
        )
        
        employees = result["employees"]
        extra_days_by_employee = result["extra_days_by_employee"]
        extra_hours_by_employee = result["extra_hours_by_employee"]
        arrear_by_employee = result["arrear_by_employee"]
        
        # Build response
        employee_responses = []
        
        for employee in employees:
            # Get extra days records for this employee
            extra_days_records = extra_days_by_employee.get(employee.id, [])
            extra_hours_records = extra_hours_by_employee.get(employee.id, [])
            arrear_records = arrear_by_employee.get(employee.id, [])
            
            # Calculate totals for all fields
            total_extra = sum(float(record.hours_worked) for record in extra_days_records)
            total_ot = sum(float(record.extra_hours) for record in extra_hours_records)
            total_arrear = sum(float(record.amount) for record in arrear_records)
            
            # Combine comments from all sources
            all_comments = []
            for record in extra_days_records:
                if record.work_description:
                    all_comments.append(f"Extra: {record.work_description}")
            for record in extra_hours_records:
                if record.work_description:
                    all_comments.append(f"OT: {record.work_description}")
            for record in arrear_records:
                if record.comments:
                    all_comments.append(f"Arrear: {record.comments}")
            
            comments = "; ".join(all_comments)
            
            # Format joining date
            joining_date = "Jul 07, 2025"
            if employee.date_of_joining:
                joining_date = employee.date_of_joining.strftime("%b %d, %Y")
            
            employee_responses.append(ExtraDaysEmployeeResponse(
                id=employee.id,
                name=employee.full_name,
                code=employee.employee_code,
                designation=employee.designation.name if employee.designation else "Associate Software Engineer",
                joining=joining_date,
                extra=total_extra,
                arrear=total_arrear,
                ot=total_ot,
                comments=comments
            ))
        
        return employee_responses
    
    def get_filter_options(self, business_id: Optional[int] = None, current_user = None) -> ExtraDaysFiltersResponse:
        """Get filter options for dropdowns"""
        
        filter_options = self.repository.get_filter_options(business_id, current_user=current_user)
        
        return ExtraDaysFiltersResponse(
            businessUnits=filter_options["businessUnits"],
            locations=filter_options["locations"],
            departments=filter_options["departments"],
            costCenters=filter_options["costCenters"]
        )
    
    def search_employees(
        self,
        search_term: str,
        business_id: Optional[int] = None,
        limit: int = 5
    ) -> List[ExtraDaysSearchResponse]:
        """Search employees for autocomplete"""
        
        employees = self.repository.search_employees_by_name(search_term, business_id, limit)
        
        return [
            ExtraDaysSearchResponse(id=emp.id, name=emp.full_name)
            for emp in employees
        ]
    
    def update_employee_extra_days(
        self,
        update_data: ExtraDaysUpdateRequest,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None,
        current_user = None
    ) -> Dict[str, str]:
        """Update extra days for an employee - handles all four fields"""
        
        # Verify employee exists - First try without business_id filter
        employee = self.db.query(Employee).filter(
            Employee.id == update_data.employee_id,
            Employee.employee_status == "active"
        ).first()
        
        if not employee:
            raise NotFoundError(f"Employee with ID {update_data.employee_id} not found")
        
        # Use the employee's actual business_id for all operations
        actual_business_id = employee.business_id
        
        # Parse month to get effective date
        year, month_num = self.parse_month_string(update_data.month)
        effective_date = date(year, month_num, 1)
        
        # Clear existing records for this month before creating new ones
        # This ensures we replace all month data instead of accumulating
        
        # 1. Handle EXTRA DAYS - Clear existing month records and create new
        self.db.query(ExtraDay).filter(
            ExtraDay.employee_id == update_data.employee_id,
            func.extract('year', ExtraDay.work_date) == year,
            func.extract('month', ExtraDay.work_date) == month_num
        ).delete(synchronize_session=False)
        
        # Create new record if value > 0
        if update_data.extra > 0:
            self.repository.create_or_update_extra_day(
                employee_id=update_data.employee_id,
                work_date=effective_date,
                hours_worked=Decimal(str(update_data.extra)),
                hourly_rate=Decimal("500.00"),  # Default hourly rate
                work_description=update_data.comments,
                business_id=actual_business_id,
                created_by=created_by or 1
            )
        
        # 2. Handle OVERTIME (OT) - Clear existing month records and create new
        self.db.query(ExtraHour).filter(
            ExtraHour.employee_id == update_data.employee_id,
            func.extract('year', ExtraHour.work_date) == year,
            func.extract('month', ExtraHour.work_date) == month_num
        ).delete(synchronize_session=False)
        
        # Create new record if value > 0
        if update_data.ot > 0:
            self.repository.create_or_update_extra_hour(
                employee_id=update_data.employee_id,
                work_date=effective_date,
                extra_hours=Decimal(str(update_data.ot)),
                overtime_rate=Decimal("750.00"),  # Default OT rate (1.5x of 500)
                work_description=update_data.comments,
                business_id=actual_business_id,
                created_by=created_by or 1
            )
        
        # 3. Handle ARREAR - Clear existing month records and create new
        self.db.query(EmployeeSalaryUnit).filter(
            EmployeeSalaryUnit.employee_id == update_data.employee_id,
            EmployeeSalaryUnit.unit_name == "Arrear Payment",
            EmployeeSalaryUnit.is_arrear == True,
            func.extract('year', EmployeeSalaryUnit.effective_date) == year,
            func.extract('month', EmployeeSalaryUnit.effective_date) == month_num
        ).delete(synchronize_session=False)
        
        # Create new record if value > 0
        if update_data.arrear > 0:
            self.repository.create_or_update_salary_variable(
                employee_id=update_data.employee_id,
                variable_name="Arrear Payment",
                variable_type="arrear",
                amount=Decimal(str(update_data.arrear)),
                effective_date=effective_date,
                description=update_data.comments,
                is_arrear=True,
                business_id=actual_business_id,
                created_by=created_by or 1
            )
        
        # Commit all changes
        self.db.commit()
        
        return {
            "message": f"Extra days data updated for employee {employee.full_name}",
            "employee_id": str(update_data.employee_id),
            "month": update_data.month,
            "extra": str(update_data.extra),
            "arrear": str(update_data.arrear),
            "ot": str(update_data.ot),
            "comments": update_data.comments,
            "effective_date": effective_date.isoformat()
        }
    
    def export_employee_data(
        self,
        employee_id: int,
        month: str = "AUG-2025",
        extra: float = 0.0,
        arrear: float = 0.0,
        ot: float = 0.0,
        comments: str = "",
        business_id: Optional[int] = None
    ) -> ExtraDaysExportResponse:
        """Export single employee extra days data"""
        
        # Find employee - Remove business_id filter to avoid mismatch
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.employee_status == "active"
        ).first()
        
        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")
        
        # Format joining date
        joining_date = "Jul 07, 2025"
        if employee.date_of_joining:
            joining_date = employee.date_of_joining.strftime("%b %d, %Y")
        
        return ExtraDaysExportResponse(
            employee_name=employee.full_name,
            employee_code=employee.employee_code,
            designation=employee.designation.name if employee.designation else "Associate Software Engineer",
            joining_date=joining_date,
            extra_days=extra,
            arrear=arrear,
            ot=ot,
            comments=comments,
            month=month
        )
    
    def export_all_employees_data(
        self,
        month: str = "AUG-2025",
        business_id: Optional[int] = None
    ) -> ExtraDaysExportAllResponse:
        """Export all employees extra days data"""
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Get export data
        export_data = self.repository.get_extra_days_for_export(
            business_id=business_id,
            year=year,
            month=month_num
        )
        
        # Convert to response format
        employee_exports = []
        for data in export_data:
            employee_exports.append(ExtraDaysExportResponse(
                employee_name=data["employee_name"],
                employee_code=data["employee_code"],
                designation=data["designation"],
                joining_date=data["joining_date"],
                extra_days=data["extra_days"],
                arrear=data["arrear"],
                ot=data["ot"],
                comments=data["comments"],
                month=month
            ))
        
        return ExtraDaysExportAllResponse(
            employees=employee_exports,
            month=month,
            total_employees=len(employee_exports)
        )
    
    def generate_csv_export(
        self,
        month: str = "AUG-2025",
        location: Optional[str] = None,
        department: Optional[str] = None,
        business_id: Optional[int] = None
    ) -> str:
        """Generate CSV content for export"""
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Convert filter names to IDs
        location_id = None
        department_id = None
        
        if location and location != "All Locations":
            from app.models.location import Location
            location_obj = self.db.query(Location).filter(Location.name == location).first()
            if location_obj:
                location_id = location_obj.id
        
        if department and department != "All Departments":
            from app.models.department import Department
            dept_obj = self.db.query(Department).filter(Department.name == department).first()
            if dept_obj:
                department_id = dept_obj.id
        
        # Get export data
        export_data = self.repository.get_extra_days_for_export(
            business_id=business_id,
            location_id=location_id,
            department_id=department_id,
            year=year,
            month=month_num
        )
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'SN', 'Employee Name', 'Employee Code', 'Designation', 'Joining Date',
            'Extra Days', 'Arrear', 'OT', 'Comments', 'Month'
        ])
        
        # Write data rows
        for data in export_data:
            writer.writerow([
                data["sn"],
                data["employee_name"],
                data["employee_code"],
                data["designation"],
                data["joining_date"],
                data["extra_days"],
                data["arrear"],
                data["ot"],
                data["comments"],
                month
            ])
        
        return output.getvalue()
    
    def import_csv_data(
        self,
        csv_content: str,
        month: str = "AUG-2025",
        overwrite_existing: bool = False,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> ExtraDaysImportResponse:
        """Import extra days data from CSV content"""
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Convert CSV rows to import format
        import_data = []
        for row in csv_reader:
            import_data.append({
                'employee_code': row.get('Employee Code', ''),
                'extra_days': row.get('Extra Days', '0'),
                'comments': row.get('Comments', '')
            })
        
        # Perform bulk import
        result = self.repository.bulk_import_extra_days(
            import_data=import_data,
            business_id=business_id or 1,
            year=year,
            month=month_num,
            created_by=created_by or 1,
            overwrite_existing=overwrite_existing
        )
        
        return ExtraDaysImportResponse(
            message=f"CSV import completed for {month}",
            imported_records=result["imported_records"],
            errors=result["errors"],
            total_errors=result["total_errors"],
            overwrite_existing=overwrite_existing
        )