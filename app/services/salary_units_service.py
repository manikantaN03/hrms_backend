"""
Salary Units Service
Business logic for salary units management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.repositories.salary_units_repository import SalaryUnitsRepository
from app.schemas.datacapture import (
    SalaryUnitCreate, SalaryUnitUpdate, SalaryUnitResponse
)


class SalaryUnitsService:
    """Service layer for salary units operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = SalaryUnitsRepository(db)
    
    def get_salary_units_employees(
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
        Get employees with salary units data for frontend table
        
        Args:
            business_id: Business ID filter
            month: Month in format "October 2025"
            business_unit: Business unit filter
            location: Location filter
            department: Department filter
            component: Component filter
            arrear: Arrear flag
            search: Search term for employee name/code
            page: Page number
            size: Page size
            
        Returns:
            List of employee salary units data
        """
        try:
            # Get employees with salary units data
            employees = self.repository.get_employees_with_salary_units(
                business_id=business_id,
                month=month,
                business_unit=business_unit,
                location=location,
                department=department,
                component=component,
                arrear=arrear,
                search=search,
                page=page,
                size=size,
                current_user=current_user
            )
            
            # Format response for frontend
            response_data = []
            offset = (page - 1) * size
            
            for i, emp_data in enumerate(employees):
                # Calculate total from all salary units
                total_amount = emp_data.get("amount", 0.0)
                
                response_data.append({
                    "sn": offset + i + 1,
                    "name": emp_data["name"],
                    "id": emp_data["employee_code"],
                    "location": emp_data["location"],
                    "department": emp_data["department"],
                    "amount": emp_data.get("amount", 0.0),
                    "comments": emp_data.get("comments", ""),
                    "total": total_amount
                })
            
            return response_data
            
        except Exception as e:
            raise Exception(f"Failed to get salary units employees: {str(e)}")
    
    def get_salary_units_filters(
        self,
        business_id: Optional[int] = None,
        current_user = None
    ) -> Dict[str, List[str]]:
        """
        Get filter options for salary units module
        
        Args:
            business_id: Business ID filter
            
        Returns:
            Dictionary with filter options
        """
        try:
            return self.repository.get_filter_options(business_id=business_id, current_user=current_user)
            
        except Exception as e:
            raise Exception(f"Failed to get salary units filters: {str(e)}")
    
    def update_salary_units_employee(
        self,
        employee_code: str,
        month: str,
        amount: float,
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
            month: Month in format "October 2025"
            amount: Salary units amount
            comments: Comments
            component: Component type
            arrear: Arrear flag
            business_id: Business ID
            updated_by: User ID who updated
            
        Returns:
            Update result
        """
        try:
            # Parse month to get effective date
            effective_date = self._parse_month_to_date(month)
            
            # Update salary units
            result = self.repository.update_employee_salary_units(
                employee_code=employee_code,
                effective_date=effective_date,
                amount=Decimal(str(amount)),
                comments=comments,
                component=component,
                arrear=arrear,
                business_id=business_id,
                updated_by=updated_by
            )
            
            return {
                "message": f"Salary units updated for employee {result['employee_name']}",
                "employee_code": employee_code,
                "month": month,
                "amount": str(amount),
                "component": component,
                "effective_date": effective_date.isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to update salary units: {str(e)}")
    
    def import_travel_kms(
        self,
        period: str,
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
        Import travel kilometers data for salary units
        
        Args:
            period: Period in format "OCT-2025"
            location: Location filter
            department: Department filter
            component: Component type
            distance_type: Distance type (Calculated/Approved)
            comments: Comments
            overwrite_existing: Whether to overwrite existing data
            business_id: Business ID
            created_by: User ID who created
            
        Returns:
            Import result
        """
        try:
            # Parse period to get effective date
            effective_date = self._parse_period_to_date(period)
            
            # Import travel data
            result = self.repository.import_travel_kilometers(
                effective_date=effective_date,
                location=location,
                department=department,
                component=component,
                distance_type=distance_type,
                comments=comments,
                overwrite_existing=overwrite_existing,
                business_id=business_id,
                created_by=created_by
            )
            
            return {
                "message": f"Travel kilometers imported successfully for {period}",
                "period": period,
                "component": component,
                "distance_type": distance_type,
                "employees_affected": str(result["employees_affected"]),
                "records_created": str(result["records_created"]),
                "overwrite_existing": str(overwrite_existing),
                "created_by_id": str(created_by) if created_by else "1"
            }
            
        except Exception as e:
            raise Exception(f"Failed to import travel kms: {str(e)}")
    
    def export_salary_units_csv(
        self,
        month: str = "October 2025",
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        business_id: Optional[int] = None
    ) -> str:
        """
        Export salary units data as CSV
        
        Args:
            month: Month in format "October 2025"
            location: Location filter
            cost_center: Cost center filter
            department: Department filter
            business_id: Business ID
            
        Returns:
            CSV content as string
        """
        try:
            # Parse month to get effective date
            effective_date = self._parse_month_to_date(month)
            
            # Get export data
            export_data = self.repository.get_export_data(
                effective_date=effective_date,
                location=location,
                cost_center=cost_center,
                department=department,
                business_id=business_id
            )
            
            # Generate CSV content
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'SN', 'Employee Name', 'Employee Code', 'Location', 'Department',
                'Amount', 'Comments', 'Total', 'Month', 'Component'
            ])
            
            # Write data rows
            for i, row in enumerate(export_data, start=1):
                writer.writerow([
                    i,
                    row["employee_name"],
                    row["employee_code"],
                    row["location"],
                    row["department"],
                    row["amount"],
                    row["comments"],
                    row["total"],
                    month,
                    row["component"]
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Failed to export salary units CSV: {str(e)}")
    
    def import_salary_units_csv(
        self,
        csv_content: str,
        month: str = "October 2025",
        overwrite_existing: bool = False,
        consider_arrear: bool = False,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import salary units data from CSV content
        
        Args:
            csv_content: CSV content as string
            month: Month in format "October 2025"
            overwrite_existing: Whether to overwrite existing data
            consider_arrear: Whether to consider as arrear
            business_id: Business ID
            created_by: User ID who created
            
        Returns:
            Import result
        """
        try:
            # Parse month to get effective date
            effective_date = self._parse_month_to_date(month)
            
            # Import CSV data
            result = self.repository.import_csv_data(
                csv_content=csv_content,
                effective_date=effective_date,
                overwrite_existing=overwrite_existing,
                consider_arrear=consider_arrear,
                business_id=business_id,
                created_by=created_by
            )
            
            return {
                "message": f"CSV import completed for {month}",
                "imported_records": result["imported_records"],
                "errors": result["errors"][:10],  # Limit errors to first 10
                "total_errors": len(result["errors"]),
                "overwrite_existing": overwrite_existing,
                "consider_arrear": consider_arrear
            }
            
        except Exception as e:
            raise Exception(f"Failed to import salary units CSV: {str(e)}")
    
    def _parse_month_to_date(self, month: str) -> date:
        """
        Parse month string to date
        
        Args:
            month: Month in format "October 2025"
            
        Returns:
            Date object for first day of month
        """
        try:
            month_year = month.split()
            month_name = month_year[0]
            year = int(month_year[1])
            
            # Convert month name to number
            month_names = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            month_num = month_names.index(month_name) + 1
            
            return date(year, month_num, 1)
        except:
            return date.today().replace(day=1)
    
    def _parse_period_to_date(self, period: str) -> date:
        """
        Parse period string to date
        
        Args:
            period: Period in format "OCT-2025"
            
        Returns:
            Date object for first day of month
        """
        try:
            month_year = period.split('-')
            month_abbr = month_year[0]
            year = int(month_year[1])
            
            # Convert month abbreviation to number
            month_abbrs = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            month_num = month_abbrs.index(month_abbr) + 1
            
            return date(year, month_num, 1)
        except:
            return date.today().replace(day=1)