"""
Hold Salary Repository
Repository for handling hold salary data operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date
from decimal import Decimal

from app.models.payroll import HoldSalary
from app.models.employee import Employee
from app.repositories.base_repository import BaseRepository


class HoldSalaryRepository(BaseRepository[HoldSalary]):
    """Repository for hold salary operations"""
    
    def __init__(self, db: Session):
        super().__init__(HoldSalary, db)
    
    def get_by_business_id(
        self, 
        business_id: int, 
        page: int = 1, 
        size: int = 20,
        employee_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        employee_search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get hold salaries by business ID with pagination and filters"""
        query = self.db.query(HoldSalary).options(
            joinedload(HoldSalary.employee),
            joinedload(HoldSalary.creator)
        ).filter(HoldSalary.business_id == business_id)
        
        # Apply filters
        if employee_id:
            query = query.filter(HoldSalary.employee_id == employee_id)
        
        if is_active is not None:
            query = query.filter(HoldSalary.is_active == is_active)
        
        # Apply employee search
        if employee_search:
            query = query.join(Employee, HoldSalary.employee_id == Employee.id)
            search_term = f"%{employee_search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        holds = query.order_by(desc(HoldSalary.created_at)).offset(offset).limit(size).all()
        
        return {
            "items": holds,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_statistics(self, business_id: int) -> Dict[str, Any]:
        """Get hold salary statistics for a business"""
        base_query = self.db.query(HoldSalary).filter(
            HoldSalary.business_id == business_id
        )
        
        total_holds = base_query.count()
        active_holds = base_query.filter(HoldSalary.is_active == True).count()
        inactive_holds = base_query.filter(HoldSalary.is_active == False).count()
        
        return {
            "total_holds": total_holds,
            "active_holds": active_holds,
            "inactive_holds": inactive_holds
        }
    
    def create_hold_salary(
        self,
        business_id: int,
        employee_id: int,
        created_by: int,
        hold_start_date: date,
        reason: str,
        notes: Optional[str] = None,
        hold_end_date: Optional[date] = None
    ) -> HoldSalary:
        """Create a new hold salary record"""
        hold_salary = HoldSalary(
            business_id=business_id,
            employee_id=employee_id,
            created_by=created_by,
            hold_start_date=hold_start_date,
            hold_end_date=hold_end_date,
            reason=reason,
            notes=notes,
            is_active=True
        )
        
        self.db.add(hold_salary)
        self.db.commit()
        self.db.refresh(hold_salary)
        
        return hold_salary
    
    def update_hold_salary(
        self,
        hold_id: int,
        business_id: int,
        hold_start_date: Optional[date] = None,
        hold_end_date: Optional[date] = None,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[HoldSalary]:
        """Update a hold salary record"""
        hold_salary = self.db.query(HoldSalary).filter(
            and_(
                HoldSalary.id == hold_id,
                HoldSalary.business_id == business_id
            )
        ).first()
        
        if not hold_salary:
            return None
        
        if hold_start_date is not None:
            hold_salary.hold_start_date = hold_start_date
        if hold_end_date is not None:
            hold_salary.hold_end_date = hold_end_date
        if reason is not None:
            hold_salary.reason = reason
        if notes is not None:
            hold_salary.notes = notes
        if is_active is not None:
            hold_salary.is_active = is_active
        
        hold_salary.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(hold_salary)
        
        return hold_salary
    
    def delete_hold_salary(self, hold_id: int, business_id: int) -> bool:
        """Delete a hold salary record"""
        hold_salary = self.db.query(HoldSalary).filter(
            and_(
                HoldSalary.id == hold_id,
                HoldSalary.business_id == business_id
            )
        ).first()
        
        if not hold_salary:
            return False
        
        self.db.delete(hold_salary)
        self.db.commit()
        
        return True
    
    def get_active_hold_for_employee(self, business_id: int, employee_id: int) -> Optional[HoldSalary]:
        """Get active hold salary record for an employee"""
        return self.db.query(HoldSalary).filter(
            and_(
                HoldSalary.business_id == business_id,
                HoldSalary.employee_id == employee_id,
                HoldSalary.is_active == True
            )
        ).first()
    
    def get_employees_for_hold_salary(
        self,
        business_id: int,
        search_term: Optional[str] = None,
        exclude_on_hold: bool = True
    ) -> List[Employee]:
        """Get employees available for hold salary"""
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(Employee).options(
            joinedload(Employee.department, innerjoin=False),
            joinedload(Employee.designation, innerjoin=False),
            joinedload(Employee.location, innerjoin=False)
        ).filter(
            and_(
                Employee.business_id == business_id,
                Employee.is_active == True
            )
        )
        
        # Apply search filter
        if search_term and search_term.strip():
            search_pattern = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_pattern),
                    Employee.last_name.ilike(search_pattern),
                    Employee.employee_code.ilike(search_pattern),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_pattern)
                )
            )
        
        # Exclude employees who already have active hold salary
        if exclude_on_hold:
            try:
                from sqlalchemy import select
                active_hold_employee_ids = select(HoldSalary.employee_id).where(
                    and_(
                        HoldSalary.business_id == business_id,
                        HoldSalary.is_active == True
                    )
                )
                
                query = query.filter(~Employee.id.in_(active_hold_employee_ids))
            except Exception as e:
                print(f"Warning: Could not exclude employees on hold: {e}")
        
        try:
            return query.order_by(Employee.employee_code).limit(50).all()
        except Exception as e:
            print(f"Error in get_employees_for_hold_salary: {e}")
            # Fallback query without joins
            return self.db.query(Employee).filter(
                and_(
                    Employee.business_id == business_id,
                    Employee.is_active == True
                )
            ).order_by(Employee.employee_code).limit(50).all()
    
    def get_hold_salary_summary(self, business_id: int) -> List[Dict[str, Any]]:
        """Get hold salary summary for display"""
        holds = self.db.query(HoldSalary).options(
            joinedload(HoldSalary.employee)
        ).filter(
            and_(
                HoldSalary.business_id == business_id,
                HoldSalary.is_active == True
            )
        ).order_by(HoldSalary.hold_start_date).all()
        
        summary = []
        for hold in holds:
            # Safely get employee details
            department_name = None
            designation_name = None
            location_name = None
            
            if hold.employee:
                # Safely get related object names
                if hasattr(hold.employee, 'department') and hold.employee.department:
                    department_name = hold.employee.department.name
                if hasattr(hold.employee, 'designation') and hold.employee.designation:
                    designation_name = hold.employee.designation.name
                if hasattr(hold.employee, 'location') and hold.employee.location:
                    location_name = hold.employee.location.name
            
            summary.append({
                "id": hold.id,
                "employee_code": hold.employee.employee_code,
                "employee_name": f"{hold.employee.first_name} {hold.employee.last_name}",
                "hold_start_date": hold.hold_start_date.isoformat(),
                "hold_end_date": hold.hold_end_date.isoformat() if hold.hold_end_date else None,
                "reason": hold.reason,
                "notes": hold.notes,
                "is_active": hold.is_active,
                "department": department_name,
                "designation": designation_name,
                "location": location_name
            })
        
        return summary