"""
Gratuity Service
Service for handling gratuity business logic
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.repositories.gratuity_repository import GratuityRepository
from app.models.payroll import Gratuity, PayrollPeriod
from app.models.employee import Employee
from app.schemas.payroll import GratuityCreate


class GratuityService:
    """Service for gratuity operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = GratuityRepository(db)
    
    def get_gratuities(
        self,
        business_id: int,
        page: int = 1,
        size: int = 20,
        period_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get gratuities with pagination and filters"""
        result = self.repository.get_by_business_id(
            business_id=business_id,
            page=page,
            size=size,
            period_id=period_id,
            employee_id=employee_id,
            location=location,
            department=department,
            cost_center=cost_center
        )
        
        # Build response
        gratuity_list = []
        for gratuity in result["items"]:
            # Safely get employee details
            employee_name = None
            employee_code = None
            department_name = None
            designation_name = None
            location_name = None
            
            if gratuity.employee:
                employee_name = f"{gratuity.employee.first_name} {gratuity.employee.last_name}"
                employee_code = gratuity.employee.employee_code
                
                # Safely get related object names
                if hasattr(gratuity.employee, 'department') and gratuity.employee.department:
                    department_name = gratuity.employee.department.name
                if hasattr(gratuity.employee, 'designation') and gratuity.employee.designation:
                    designation_name = gratuity.employee.designation.name
                if hasattr(gratuity.employee, 'location') and gratuity.employee.location:
                    location_name = gratuity.employee.location.name
            
            gratuity_data = {
                "id": gratuity.id,
                "min_years": gratuity.min_years,
                "payable_days": gratuity.payable_days,
                "month_days": gratuity.month_days,
                "exit_only": gratuity.exit_only,
                "year_rounding": gratuity.year_rounding,
                "years_of_service": float(gratuity.years_of_service),
                "base_salary": float(gratuity.base_salary),
                "gratuity_amount": float(gratuity.gratuity_amount),
                "is_processed": gratuity.is_processed,
                "processed_date": gratuity.processed_date.isoformat() if gratuity.processed_date else None,
                "employee_name": employee_name,
                "employee_code": employee_code,
                "department": department_name,
                "designation": designation_name,
                "location": location_name,
                "period_name": gratuity.period.name if gratuity.period else None,
                "created_at": gratuity.created_at.isoformat()
            }
            gratuity_list.append(gratuity_data)
        
        # Get statistics
        statistics = self.repository.get_statistics(business_id, period_id)
        
        return {
            "gratuities": gratuity_list,
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
                "pages": result["pages"]
            },
            "statistics": statistics
        }
    
    def generate_gratuity_summary(
        self,
        business_id: int,
        period_id: int,
        min_years: int = 5,
        payable_days: int = 15,
        month_days: int = 26,
        exit_only: bool = False,
        year_rounding: str = "round_down",
        salary_components: Optional[List[str]] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Generate gratuity summary for employees"""
        
        # Validate period
        period = self.db.query(PayrollPeriod).filter(
            PayrollPeriod.id == period_id,
            PayrollPeriod.business_id == business_id
        ).first()
        
        if not period:
            raise ValueError("Payroll period not found")
        
        if period.status == "closed":
            raise ValueError("Cannot generate gratuity for closed period")
        
        # Get eligible employees
        employees = self.repository.get_employees_for_gratuity(
            business_id=business_id,
            min_years=min_years,
            exit_only=exit_only,
            location=location,
            department=department,
            cost_center=cost_center,
            employee_search=employee_search,
            employee_ids=employee_ids
        )
        
        print(f"DEBUG: Found {len(employees)} employees for business_id={business_id}")
        for emp in employees:
            print(f"DEBUG: Employee {emp.id} - {emp.first_name} {emp.last_name}, DOJ: {emp.date_of_joining}")
        
        if not employees:
            raise ValueError("No eligible employees found")
        
        # Calculate gratuity for each employee
        gratuity_summary = []
        total_payable = Decimal('0')
        eligible_count = 0
        
        for employee in employees:
            # Get employee's years of service
            years_of_service = self._get_employee_years_of_service(employee)
            
            print(f"DEBUG: Employee {employee.id} years_of_service: {years_of_service}, min_years: {min_years}")
            
            # Apply year rounding
            if year_rounding == "round_up":
                years_of_service = years_of_service.quantize(Decimal('1'), rounding='ROUND_UP')
            else:  # round_down
                years_of_service = years_of_service.quantize(Decimal('1'), rounding='ROUND_DOWN')
            
            print(f"DEBUG: After rounding: {years_of_service}")
            
            # Check eligibility
            if years_of_service >= min_years:
                # Get employee's base salary
                base_salary = self._get_employee_base_salary(employee, salary_components)
                
                print(f"DEBUG: Employee {employee.id} is eligible! Base salary: {base_salary}")
                
                # Calculate gratuity amount
                gratuity_amount = self._calculate_gratuity_amount(
                    base_salary=base_salary,
                    years_of_service=years_of_service,
                    payable_days=payable_days,
                    month_days=month_days
                )
                
                print(f"DEBUG: Gratuity amount: {gratuity_amount}")
                
                # Include employee even if gratuity is 0 (to show in results)
                # Safely get related object names
                department_name = None
                designation_name = None
                location_name = None
                
                if hasattr(employee, 'department') and employee.department:
                    department_name = employee.department.name if hasattr(employee.department, 'name') else str(employee.department)
                if hasattr(employee, 'designation') and employee.designation:
                    designation_name = employee.designation.name if hasattr(employee.designation, 'name') else str(employee.designation)
                if hasattr(employee, 'location') and employee.location:
                    location_name = employee.location.name if hasattr(employee.location, 'name') else str(employee.location)
                
                gratuity_summary.append({
                    "employee_id": employee.id,
                    "employee_code": employee.employee_code,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "department": department_name,
                    "designation": designation_name,
                    "location": location_name,
                    "base_salary": float(base_salary),
                    "years_of_service": float(years_of_service),
                    "gratuity_amount": float(gratuity_amount)
                })
                
                total_payable += gratuity_amount
                eligible_count += 1
        
        return {
            "eligible_employees": eligible_count,
            "total_payable": float(total_payable),
            "gratuity_summary": gratuity_summary,
            "period_name": period.name,
            "configuration": {
                "min_years": min_years,
                "payable_days": payable_days,
                "month_days": month_days,
                "exit_only": exit_only,
                "year_rounding": year_rounding,
                "salary_components": salary_components or []
            }
        }
    
    def create_gratuities(
        self,
        business_id: int,
        created_by: int,
        period_id: int,
        min_years: int = 5,
        payable_days: int = 15,
        month_days: int = 26,
        exit_only: bool = False,
        year_rounding: str = "round_down",
        salary_components: Optional[List[str]] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Create gratuity records for employees"""
        
        # First delete any existing unprocessed gratuities for this period
        deleted_count = self.repository.delete_gratuities_by_period(
            business_id=business_id,
            period_id=period_id,
            employee_ids=employee_ids
        )
        
        # Generate gratuity summary
        summary = self.generate_gratuity_summary(
            business_id=business_id,
            period_id=period_id,
            min_years=min_years,
            payable_days=payable_days,
            month_days=month_days,
            exit_only=exit_only,
            year_rounding=year_rounding,
            salary_components=salary_components,
            location=location,
            department=department,
            cost_center=cost_center,
            employee_search=employee_search,
            employee_ids=employee_ids
        )
        
        # Create gratuity records
        created_gratuities = []
        for gratuity_item in summary["gratuity_summary"]:
            gratuity = self.repository.create_gratuity(
                business_id=business_id,
                period_id=period_id,
                employee_id=gratuity_item["employee_id"],
                created_by=created_by,
                min_years=min_years,
                payable_days=payable_days,
                month_days=month_days,
                exit_only=exit_only,
                year_rounding=year_rounding,
                years_of_service=Decimal(str(gratuity_item["years_of_service"])),
                base_salary=Decimal(str(gratuity_item["base_salary"])),
                gratuity_amount=Decimal(str(gratuity_item["gratuity_amount"])),
                salary_components=salary_components
            )
            created_gratuities.append(gratuity)
        
        return {
            "success": True,
            "message": f"Gratuity created for {len(created_gratuities)} employees",
            "processed_employees": len(created_gratuities),
            "total_amount": summary["total_payable"],
            "deleted_previous": deleted_count,
            "gratuity_ids": [gratuity.id for gratuity in created_gratuities]
        }
    
    def process_gratuities(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Process gratuities (mark as processed)"""
        processed_count = self.repository.process_gratuities(
            business_id=business_id,
            period_id=period_id,
            employee_ids=employee_ids
        )
        
        if processed_count == 0:
            raise ValueError("No gratuities found to process")
        
        return {
            "success": True,
            "message": f"Processed {processed_count} gratuities",
            "processed_count": processed_count
        }
    
    def delete_gratuities(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Delete unprocessed gratuities"""
        deleted_count = self.repository.delete_gratuities_by_period(
            business_id=business_id,
            period_id=period_id,
            employee_ids=employee_ids
        )
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} gratuity records",
            "deleted_count": deleted_count
        }
    
    def get_gratuity_summary_by_period(
        self,
        business_id: int,
        period_id: int,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing gratuity summary for a period"""
        summary = self.repository.get_gratuity_summary(
            business_id=business_id,
            period_id=period_id,
            location=location,
            department=department,
            cost_center=cost_center,
            employee_search=employee_search
        )
        
        total_payable = sum(item["gratuity_amount"] for item in summary)
        
        return {
            "eligible_employees": len(summary),
            "total_payable": total_payable,
            "gratuity_summary": summary
        }
    
    def _get_employee_years_of_service(self, employee: Employee) -> Decimal:
        """Calculate employee's years of service"""
        return self.repository.get_employee_years_of_service(employee)
    
    def _get_employee_base_salary(
        self,
        employee: Employee,
        salary_components: Optional[List[str]] = None
    ) -> Decimal:
        """Calculate employee's base salary based on selected components from database"""
        from app.models.employee import EmployeeSalary
        
        # Get the employee's salary record with the highest gross salary (most complete record)
        salary_record = self.db.query(EmployeeSalary).filter(
            EmployeeSalary.employee_id == employee.id,
            EmployeeSalary.is_active == True
        ).order_by(EmployeeSalary.gross_salary.desc()).first()
        
        if not salary_record:
            # If no salary record found, return 0
            return Decimal('0')
        
        base_salary = Decimal('0')
        
        # If no components selected, default to basic salary
        if not salary_components:
            return Decimal(str(salary_record.basic_salary))
        
        # Map frontend component keys to database fields
        component_mapping = {
            # Frontend keys
            "basic": salary_record.basic_salary,
            "hra": salary_record.house_rent_allowance,
            "sa": salary_record.special_allowance,
            "mda": salary_record.medical_allowance,
            "conveyance": salary_record.conveyance_allowance,
            "telephone": salary_record.telephone_allowance,
            # Full name keys (for backward compatibility)
            "Basic Salary": salary_record.basic_salary,
            "House Rent Allowance": salary_record.house_rent_allowance,
            "Special Allowance": salary_record.special_allowance,
            "Medical Allowance": salary_record.medical_allowance,
            "Conveyance Allowance": salary_record.conveyance_allowance,
            "Telephone Allowance": salary_record.telephone_allowance
        }
        
        # Sum up selected components
        for component in salary_components:
            if component in component_mapping:
                component_value = component_mapping[component]
                if component_value:
                    base_salary += Decimal(str(component_value))
        
        return base_salary
    
    def _calculate_gratuity_amount(
        self,
        base_salary: Decimal,
        years_of_service: Decimal,
        payable_days: int,
        month_days: int
    ) -> Decimal:
        """Calculate gratuity amount using the standard formula"""
        # Gratuity Formula: (Base Salary × Payable Days × Years of Service) / Month Days
        gratuity_amount = (base_salary * payable_days * years_of_service) / month_days
        
        return gratuity_amount.quantize(Decimal('0.01'))