"""
Statutory Bonus Service
Service for handling statutory bonus business logic
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.repositories.statutory_bonus_repository import StatutoryBonusRepository
from app.models.payroll import StatutoryBonus, PayrollPeriod
from app.models.employee import Employee
from app.schemas.payroll import StatutoryBonusCreate


class StatutoryBonusService:
    """Service for statutory bonus operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = StatutoryBonusRepository(db)
    
    def get_bonuses(
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
        """Get statutory bonuses with pagination and filters"""
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
        bonus_list = []
        for bonus in result["items"]:
            # Safely get employee details
            employee_name = None
            employee_code = None
            department_name = None
            designation_name = None
            location_name = None
            
            if bonus.employee:
                employee_name = f"{bonus.employee.first_name} {bonus.employee.last_name}"
                employee_code = bonus.employee.employee_code
                
                # Safely get related object names
                if hasattr(bonus.employee, 'department') and bonus.employee.department:
                    department_name = bonus.employee.department.name
                if hasattr(bonus.employee, 'designation') and bonus.employee.designation:
                    designation_name = bonus.employee.designation.name
                if hasattr(bonus.employee, 'location') and bonus.employee.location:
                    location_name = bonus.employee.location.name
            
            bonus_data = {
                "id": bonus.id,
                "bonus_rate": float(bonus.bonus_rate),
                "eligibility_cutoff": float(bonus.eligibility_cutoff),
                "min_wages": float(bonus.min_wages),
                "min_bonus": float(bonus.min_bonus),
                "max_bonus": float(bonus.max_bonus),
                "base_salary": float(bonus.base_salary),
                "bonus_amount": float(bonus.bonus_amount),
                "is_processed": bonus.is_processed,
                "processed_date": bonus.processed_date.isoformat() if bonus.processed_date else None,
                "employee_name": employee_name,
                "employee_code": employee_code,
                "department": department_name,
                "designation": designation_name,
                "location": location_name,
                "period_name": bonus.period.name if bonus.period else None,
                "created_at": bonus.created_at.isoformat()
            }
            bonus_list.append(bonus_data)
        
        # Get statistics
        statistics = self.repository.get_statistics(business_id, period_id)
        
        return {
            "bonuses": bonus_list,
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
                "pages": result["pages"]
            },
            "statistics": statistics
        }
    
    def generate_bonus_summary(
        self,
        business_id: int,
        period_id: int,
        bonus_rate: Decimal = Decimal('8.33'),
        eligibility_cutoff: Decimal = Decimal('21000'),
        min_wages: Decimal = Decimal('7000'),
        min_bonus: Decimal = Decimal('100'),
        max_bonus: Decimal = Decimal('0'),
        salary_components: Optional[List[str]] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Generate statutory bonus summary for employees"""
        
        # Validate period
        period = self.db.query(PayrollPeriod).filter(
            PayrollPeriod.id == period_id,
            PayrollPeriod.business_id == business_id
        ).first()
        
        if not period:
            raise ValueError("Payroll period not found")
        
        if period.status == "closed":
            raise ValueError("Cannot generate bonus for closed period")
        
        # Get eligible employees
        employees = self.repository.get_employees_for_bonus(
            business_id=business_id,
            location=location,
            department=department,
            cost_center=cost_center,
            employee_search=employee_search,
            employee_ids=employee_ids
        )
        
        if not employees:
            raise ValueError("No eligible employees found")
        
        # Calculate bonus for each employee
        bonus_summary = []
        total_payable = Decimal('0')
        eligible_count = 0
        
        for employee in employees:
            # Get employee's base salary (simplified calculation)
            base_salary = self._get_employee_base_salary(employee, salary_components)
            
            # Check eligibility
            if base_salary <= eligibility_cutoff:
                # Calculate bonus amount
                bonus_amount = self._calculate_bonus_amount(
                    base_salary=base_salary,
                    bonus_rate=bonus_rate,
                    min_wages=min_wages,
                    min_bonus=min_bonus,
                    max_bonus=max_bonus
                )
                
                if bonus_amount > 0:
                    # Safely get related object names
                    department_name = None
                    designation_name = None
                    location_name = None
                    
                    if hasattr(employee, 'department') and employee.department:
                        department_name = employee.department.name
                    if hasattr(employee, 'designation') and employee.designation:
                        designation_name = employee.designation.name
                    if hasattr(employee, 'location') and employee.location:
                        location_name = employee.location.name
                    
                    bonus_summary.append({
                        "employee_id": employee.id,
                        "employee_code": employee.employee_code,
                        "employee_name": f"{employee.first_name} {employee.last_name}",
                        "department": department_name,
                        "designation": designation_name,
                        "location": location_name,
                        "base_salary": float(base_salary),
                        "bonus_amount": float(bonus_amount)
                    })
                    
                    total_payable += bonus_amount
                    eligible_count += 1
        
        return {
            "eligible_employees": eligible_count,
            "total_payable": float(total_payable),
            "bonus_summary": bonus_summary,
            "period_name": period.name,
            "configuration": {
                "bonus_rate": float(bonus_rate),
                "eligibility_cutoff": float(eligibility_cutoff),
                "min_wages": float(min_wages),
                "min_bonus": float(min_bonus),
                "max_bonus": float(max_bonus),
                "salary_components": salary_components or []
            }
        }
    
    def create_bonuses(
        self,
        business_id: int,
        created_by: int,
        period_id: int,
        bonus_rate: Decimal = Decimal('8.33'),
        eligibility_cutoff: Decimal = Decimal('21000'),
        min_wages: Decimal = Decimal('7000'),
        min_bonus: Decimal = Decimal('100'),
        max_bonus: Decimal = Decimal('0'),
        salary_components: Optional[List[str]] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Create statutory bonus records for employees"""
        
        # First delete any existing unprocessed bonuses for this period
        deleted_count = self.repository.delete_bonuses_by_period(
            business_id=business_id,
            period_id=period_id,
            employee_ids=employee_ids
        )
        
        # Generate bonus summary
        summary = self.generate_bonus_summary(
            business_id=business_id,
            period_id=period_id,
            bonus_rate=bonus_rate,
            eligibility_cutoff=eligibility_cutoff,
            min_wages=min_wages,
            min_bonus=min_bonus,
            max_bonus=max_bonus,
            salary_components=salary_components,
            location=location,
            department=department,
            cost_center=cost_center,
            employee_search=employee_search,
            employee_ids=employee_ids
        )
        
        # Create bonus records
        created_bonuses = []
        for bonus_item in summary["bonus_summary"]:
            bonus = self.repository.create_bonus(
                business_id=business_id,
                period_id=period_id,
                employee_id=bonus_item["employee_id"],
                created_by=created_by,
                bonus_rate=bonus_rate,
                eligibility_cutoff=eligibility_cutoff,
                min_wages=min_wages,
                min_bonus=min_bonus,
                max_bonus=max_bonus,
                base_salary=Decimal(str(bonus_item["base_salary"])),
                bonus_amount=Decimal(str(bonus_item["bonus_amount"])),
                salary_components=salary_components
            )
            created_bonuses.append(bonus)
        
        return {
            "success": True,
            "message": f"Statutory bonus created for {len(created_bonuses)} employees",
            "processed_employees": len(created_bonuses),
            "total_amount": summary["total_payable"],
            "deleted_previous": deleted_count,
            "bonus_ids": [bonus.id for bonus in created_bonuses]
        }
    
    def process_bonuses(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Process statutory bonuses (mark as processed)"""
        processed_count = self.repository.process_bonuses(
            business_id=business_id,
            period_id=period_id,
            employee_ids=employee_ids
        )
        
        if processed_count == 0:
            raise ValueError("No bonuses found to process")
        
        return {
            "success": True,
            "message": f"Processed {processed_count} statutory bonuses",
            "processed_count": processed_count
        }
    
    def delete_bonuses(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Delete unprocessed statutory bonuses"""
        deleted_count = self.repository.delete_bonuses_by_period(
            business_id=business_id,
            period_id=period_id,
            employee_ids=employee_ids
        )
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} statutory bonus records",
            "deleted_count": deleted_count
        }
    
    def get_bonus_summary_by_period(
        self,
        business_id: int,
        period_id: int,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing bonus summary for a period"""
        summary = self.repository.get_bonus_summary(
            business_id=business_id,
            period_id=period_id,
            location=location,
            department=department,
            cost_center=cost_center,
            employee_search=employee_search
        )
        
        total_payable = sum(item["bonus_amount"] for item in summary)
        
        return {
            "eligible_employees": len(summary),
            "total_payable": total_payable,
            "bonus_summary": summary
        }
    
    def _get_employee_base_salary(
        self,
        employee: Employee,
        salary_components: Optional[List[str]] = None
    ) -> Decimal:
        """Calculate employee's base salary based on selected components"""
        # This is a simplified calculation
        # In a real system, this would fetch actual salary components
        
        base_salary = Decimal('0')
        
        # Mock salary components calculation
        if not salary_components:
            # Default to basic salary if no components selected
            base_salary = Decimal('8700')  # Mock basic salary
        else:
            component_values = {
                "basic": Decimal('8700'),
                "hra": Decimal('2610'),  # 30% of basic
                "sa": Decimal('1740'),   # 20% of basic
                "mda": Decimal('1000'),
                "conveyance": Decimal('800'),
                "telephone": Decimal('500')
            }
            
            for component in salary_components:
                if component in component_values:
                    base_salary += component_values[component]
        
        return base_salary
    
    def _calculate_bonus_amount(
        self,
        base_salary: Decimal,
        bonus_rate: Decimal,
        min_wages: Decimal,
        min_bonus: Decimal,
        max_bonus: Decimal
    ) -> Decimal:
        """Calculate statutory bonus amount"""
        # Calculate bonus based on rate
        calculated_bonus = (base_salary * bonus_rate) / Decimal('100')
        
        # Apply minimum bonus
        bonus_amount = max(calculated_bonus, min_bonus)
        
        # Apply maximum bonus if specified
        if max_bonus > 0:
            bonus_amount = min(bonus_amount, max_bonus)
        
        # Ensure minimum wages consideration
        if base_salary < min_wages:
            bonus_amount = min_bonus
        
        return bonus_amount.quantize(Decimal('0.01'))