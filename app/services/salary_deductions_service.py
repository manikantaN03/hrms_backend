"""
Salary Deductions Service
Business logic layer for salary deductions management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.repositories.salary_deductions_repository import SalaryDeductionsRepository
from app.schemas.reports import SalaryDeductionsFilters


class SalaryDeductionsService:
    """Service for salary deductions business logic"""
    
    def __init__(self, db: Session):
        self.repository = SalaryDeductionsRepository(db)
        self.db = db
    
    def get_salary_deductions_report(self, filters: SalaryDeductionsFilters) -> Dict[str, Any]:
        """
        Get salary deductions report based on filters
        
        Args:
            filters: Report filters including month, location, department, cost_center, deduction, employee_search
            
        Returns:
            Dictionary with employees list and summary
        """
        try:
            from app.models.employee import Employee
            from app.models.location import Location
            from app.models.department import Department
            from app.models.cost_center import CostCenter
            from app.models.datacapture import EmployeeDeduction
            from sqlalchemy import and_, or_, func, extract
            from datetime import datetime
            import logging
            
            logger = logging.getLogger(__name__)
            
            # CRITICAL: Validate business_id is present for security
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for security")
            
            logger.info(f"[SALARY DEDUCTIONS] Generating report for business_id={business_id}, filters: {filters}")
            
            # Parse month (format: "MAY-2025")
            try:
                month_str, year_str = filters.month.split('-')
                month_num = datetime.strptime(month_str, '%b').month
                year_num = int(year_str)
                logger.info(f"Parsed month: {month_num}, year: {year_num}")
            except Exception as e:
                logger.error(f"Error parsing month: {e}")
                # Default to current month if parsing fails
                now = datetime.now()
                month_num = now.month
                year_num = now.year
                logger.info(f"Using default month: {month_num}, year: {year_num}")
            
            # Build base query for active employees with eager loading
            from sqlalchemy.orm import joinedload
            
            query = self.db.query(Employee).options(
                joinedload(Employee.location),
                joinedload(Employee.department),
                joinedload(Employee.designation),
                joinedload(Employee.cost_center)
            ).filter(
                Employee.employee_status == 'ACTIVE',
                Employee.business_id == business_id  # CRITICAL: Business isolation
            )
            
            # Apply location filter
            if filters.location and filters.location not in ["All Locations", "", None]:
                query = query.filter(Employee.location.has(Location.name == filters.location))
            
            # Apply department filter
            if filters.department and filters.department not in ["All Departments", "", None]:
                query = query.filter(Employee.department.has(Department.name == filters.department))
            
            # Apply cost center filter
            if filters.cost_center and filters.cost_center not in ["All Cost Centers", "", None]:
                query = query.filter(Employee.cost_center.has(CostCenter.name == filters.cost_center))
            
            # Apply employee search filter
            if filters.employee_search and filters.employee_search.strip():
                search_input = filters.employee_search.strip()
                
                # If the search input contains " - " (from autocomplete selection), extract the code
                if " - " in search_input:
                    employee_code = search_input.split(" - ")[0].strip()
                    logger.info(f"Extracted employee code from autocomplete: {employee_code}")
                    query = query.filter(Employee.employee_code == employee_code)
                else:
                    # Otherwise, do a general search
                    search_term = f"%{search_input}%"
                    query = query.filter(
                        or_(
                            Employee.first_name.ilike(search_term),
                            Employee.last_name.ilike(search_term),
                            Employee.employee_code.ilike(search_term),
                            func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                        )
                    )
            
            # Get employees
            employees = query.all()
            
            logger.info(f"Found {len(employees)} employees matching filters")
            
            # Build response
            employees_data = []
            total_amount = Decimal('0.00')
            
            for emp in employees:
                # Query deductions for this employee in the selected month
                deduction_query = self.db.query(
                    func.sum(EmployeeDeduction.amount).label('total_amount')
                ).filter(
                    EmployeeDeduction.employee_id == emp.id,
                    EmployeeDeduction.is_active == True,
                    extract('year', EmployeeDeduction.effective_date) == year_num,
                    extract('month', EmployeeDeduction.effective_date) == month_num
                )
                
                # Apply deduction type filter if specified
                # Map frontend deduction names to database deduction names
                deduction_name_map = {
                    "Group Insurance": "Medical Insurance",  # Fixed: GI -> Medical Insurance
                    "Provident Fund": "Voluntary PF",  # Fixed: PF -> Voluntary PF
                    "Employee State Insurance": "ESI",
                    "Professional Tax": "Professional Tax",
                    "Income Tax": "Income Tax",
                    "Loan Deduction": "Loan Deduction",
                    "Advance Deduction": "ADVANCE",
                    "Canteen Deduction": "CANTEEN",
                    "Transport Deduction": "TRANSPORT",
                    "Gratuity": "Gratuity"
                }
                
                if filters.deduction and filters.deduction not in ["-select-", "", None]:
                    # Map the frontend name to database name
                    db_deduction_name = deduction_name_map.get(filters.deduction, filters.deduction)
                    logger.info(f"Filtering by deduction: {filters.deduction} -> {db_deduction_name}")
                    deduction_query = deduction_query.filter(
                        EmployeeDeduction.deduction_name == db_deduction_name
                    )
                
                deduction_result = deduction_query.first()
                deduction_amount = float(deduction_result.total_amount) if deduction_result.total_amount else 0.00
                
                # If a specific deduction is selected and employee has no such deduction, skip
                if filters.deduction and filters.deduction not in ["-select-", "", None]:
                    if deduction_amount == 0.00:
                        continue
                
                # If deduction is "-select-", show all employees even with 0 deductions
                employee_data = {
                    "employee_code": emp.employee_code,
                    "employee_name": emp.full_name,
                    "department": emp.department.name if emp.department else "N/A",
                    "designation": emp.designation.name if emp.designation else "N/A",
                    "deduction_amount": deduction_amount
                }
                
                employees_data.append(employee_data)
                total_amount += Decimal(str(deduction_amount))
            
            logger.info(f"Returning {len(employees_data)} employees with total amount: {total_amount}")
            
            return {
                "employees": employees_data,
                "summary": {
                    "total_employees": len(employees_data),
                    "total_amount": float(total_amount)
                }
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating salary deductions report: {str(e)}")
            raise Exception(f"Failed to generate salary deductions report: {str(e)}")
    
    def get_employees_with_salary_deductions(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get employees with salary deductions"""
        return self.repository.get_employees_with_salary_deductions(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            cost_center=cost_center,
            department=department,
            search=search,
            page=page,
            size=size
        )
    
    def get_filter_options(self, business_id: Optional[int] = None) -> Dict[str, List[str]]:
        """Get filter options"""
        return self.repository.get_filter_options(business_id=business_id)
    
    def update_employee_salary_deductions(
        self,
        employee_code: str,
        gi_deduction: Optional[float] = None,
        gratuity_deduction: Optional[float] = None,
        pf_deduction: Optional[float] = None,
        esi_deduction: Optional[float] = None,
        professional_tax: Optional[float] = None,
        income_tax: Optional[float] = None,
        other_deductions: Optional[float] = None,
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Update employee salary deductions"""
        return self.repository.update_employee_salary_deductions(
            employee_code=employee_code,
            gi_deduction=gi_deduction,
            gratuity_deduction=gratuity_deduction,
            pf_deduction=pf_deduction,
            esi_deduction=esi_deduction,
            professional_tax=professional_tax,
            income_tax=income_tax,
            other_deductions=other_deductions,
            business_id=business_id,
            updated_by=updated_by
        )
    
    def search_employees(
        self,
        search: str,
        business_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search employees"""
        return self.repository.search_employees(
            search=search,
            business_id=business_id,
            limit=limit
        )
    
    def export_salary_deductions_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export salary deductions as CSV"""
        return self.repository.export_salary_deductions_csv(
            business_id=business_id,
            business_unit=business_unit,
            location=location,
            cost_center=cost_center,
            department=department
        )
    
    def import_salary_deductions_csv(
        self,
        csv_content: str,
        business_id: int,
        created_by: int,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import salary deductions from CSV"""
        return self.repository.import_salary_deductions_csv(
            csv_content=csv_content,
            business_id=business_id,
            created_by=created_by,
            overwrite_existing=overwrite_existing
        )
    
    def bulk_update_salary_deductions(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: int = None
    ) -> Dict[str, Any]:
        """Bulk update salary deductions"""
        return self.repository.bulk_update_salary_deductions(
            updates=updates,
            business_id=business_id,
            updated_by=updated_by
        )