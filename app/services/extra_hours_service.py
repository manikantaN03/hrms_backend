"""
Extra Hours Service
Business logic for extra hours management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
import io
import csv

from app.repositories.extra_hours_repository import ExtraHoursRepository
from app.models.employee import Employee
from app.core.exceptions import ValidationError, NotFoundError


class ExtraHoursService:
    """Service class for extra hours operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ExtraHoursRepository(db)
    
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
    
    def get_employees_with_extra_hours(
        self,
        month: str = "AUG-2025",
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> List[Dict[str, Any]]:
        """Get employees with their extra hours data"""
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Convert filter names to IDs if needed
        location_id = None
        department_id = None
        business_unit_id = None
        
        if business_unit and business_unit != "All Business Units":
            from app.models.business_unit import BusinessUnit
            bu_obj = self.db.query(BusinessUnit).filter(
                BusinessUnit.name == business_unit,
                BusinessUnit.is_active == True
            ).first()
            if bu_obj:
                business_unit_id = bu_obj.id
        
        if location and location != "All Locations":
            from app.models.location import Location
            # Handle duplicate location names by getting the first active one
            location_obj = self.db.query(Location).filter(
                Location.name == location,
                Location.is_active == True
            ).first()
            if location_obj:
                location_id = location_obj.id
        
        if department and department != "All Departments":
            from app.models.department import Department
            # Get active department
            dept_obj = self.db.query(Department).filter(
                Department.name == department,
                Department.is_active == True
            ).first()
            if dept_obj:
                department_id = dept_obj.id
        
        # Get employees with extra hours data
        result = self.repository.get_employees_with_extra_hours(
            business_unit=business_unit,
            location=location,
            department=department,
            search_term=search,
            year=year,
            month=month_num,
            page=page,
            size=size,
            current_user=current_user
        )
        
        employees = result["employees"]
        extra_hours_by_employee = result["extra_hours_by_employee"]
        
        # Build response
        employee_responses = []
        
        for employee in employees:
            # Get extra hours records for this employee
            extra_hours_records = extra_hours_by_employee.get(employee.id, [])
            
            # Calculate totals
            total_extra_hours = sum(float(record.extra_hours) for record in extra_hours_records)
            total_amount = sum(float(record.total_amount) for record in extra_hours_records)
            
            employee_responses.append({
                "id": employee.employee_code,
                "name": employee.full_name,
                "designation": employee.designation.name if employee.designation else "Associate Software Engineer",
                "total_extra_hours": total_extra_hours,
                "total_amount": total_amount
            })
        
        return employee_responses
    
    def get_filter_options(self, current_user = None) -> Dict[str, List[str]]:
        """Get filter options for dropdowns"""
        
        filter_options = self.repository.get_filter_options(current_user=current_user)
        
        return {
            "businessUnits": filter_options["businessUnits"],
            "locations": filter_options["locations"],
            "departments": filter_options["departments"]
        }
    
    def search_employees(
        self,
        search_term: str,
        current_user = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search employees for autocomplete"""
        
        employees = self.repository.search_employees_by_name(search_term, current_user=current_user, limit=limit)
        
        return [
            {"id": emp.employee_code, "name": emp.full_name}
            for emp in employees
        ]
    
    def create_extra_hours_record(
        self,
        employee_code: str,
        work_date: date,
        extra_hours: float,
        hourly_rate: float = 500.0,
        reason: str = "",
        current_user = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create extra hours record for an employee"""
        
        # Verify employee exists
        employee = self.repository.find_employee_by_code(employee_code, current_user=current_user)
        
        if not employee:
            raise NotFoundError(f"Employee with code {employee_code} not found")
        
        # Create extra hours record
        result = self.repository.create_extra_hours_record(
            employee_id=employee.id,
            work_date=work_date,
            extra_hours=Decimal(str(extra_hours)),
            overtime_rate=Decimal(str(hourly_rate)),
            work_description=reason,
            current_user=current_user,
            created_by=created_by
        )
        
        return {
            "message": f"Extra hours record created for employee {employee.full_name}",
            "employee_code": employee_code,
            "work_date": work_date.isoformat(),
            "extra_hours": str(extra_hours),
            "hourly_rate": str(hourly_rate),
            "total_amount": str(result.total_amount),
            "created_at": datetime.now().isoformat()
        }
    
    def export_employee_data(
        self,
        employee_code: str,
        current_user = None
    ) -> Dict[str, Any]:
        """Export employee extra hours data"""
        
        # Find employee
        employee = self.repository.find_employee_by_code(employee_code, current_user=current_user)
        
        if not employee:
            raise NotFoundError(f"Employee with code {employee_code} not found")
        
        return {
            "id": employee.employee_code,
            "name": employee.full_name,
            "designation": employee.designation.name if employee.designation else "Associate Software Engineer"
        }
    
    def generate_csv_export(
        self,
        month: str = "AUG-2025",
        location: Optional[str] = None,
        department: Optional[str] = None,
        current_user = None
    ) -> str:
        """Generate CSV content for export"""
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Convert filter names to IDs
        location_id = None
        department_id = None
        
        if location and location != "All Locations":
            from app.models.location import Location
            # Handle duplicate location names by getting the first active one
            location_obj = self.db.query(Location).filter(
                Location.name == location,
                Location.is_active == True
            ).first()
            if location_obj:
                location_id = location_obj.id
        
        if department and department != "All Departments":
            from app.models.department import Department
            # Get active department
            dept_obj = self.db.query(Department).filter(
                Department.name == department,
                Department.is_active == True
            ).first()
            if dept_obj:
                department_id = dept_obj.id
        
        # Get export data
        export_data = self.repository.get_extra_hours_for_export(
            location=location,
            department=department,
            year=year,
            month=month_num,
            current_user=current_user
        )
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'SN', 'Employee Name', 'Employee Code', 'Designation', 
            'Extra Hours', 'Hourly Rate', 'Total Amount', 'Month'
        ])
        
        # Write data rows
        for data in export_data:
            writer.writerow([
                data["sn"],
                data["employee_name"],
                data["employee_code"],
                data["designation"],
                data["extra_hours"],
                data["hourly_rate"],
                data["total_amount"],
                month
            ])
        
        return output.getvalue()
    
    def import_csv_data(
        self,
        csv_content: str,
        month: str = "AUG-2025",
        overwrite_existing: bool = False,
        current_user = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Import extra hours data from CSV content"""
        
        # Parse month
        year, month_num = self.parse_month_string(month)
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Convert CSV rows to import format
        import_data = []
        for row in csv_reader:
            import_data.append({
                'employee_code': row.get('Employee Code', ''),
                'extra_hours': row.get('Extra Hours', '0'),
                'hourly_rate': row.get('Hourly Rate', '500.0'),
                'reason': row.get('Reason', '')
            })
        
        # Perform bulk import
        result = self.repository.bulk_import_extra_hours(
            import_data=import_data,
            year=year,
            month=month_num,
            created_by=created_by or 1,
            overwrite_existing=overwrite_existing,
            current_user=current_user
        )
        
        return {
            "message": f"CSV import completed for {month}",
            "imported_records": result["imported_records"],
            "errors": result["errors"],
            "total_errors": result["total_errors"],
            "overwrite_existing": overwrite_existing
        }