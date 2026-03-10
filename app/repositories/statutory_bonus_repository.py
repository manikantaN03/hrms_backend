"""
Statutory Bonus Repository
Repository for handling statutory bonus data operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date
from decimal import Decimal

from app.models.payroll import StatutoryBonus
from app.models.employee import Employee, EmployeeStatus
from app.repositories.base_repository import BaseRepository


class StatutoryBonusRepository(BaseRepository[StatutoryBonus]):
    """Repository for statutory bonus operations"""
    
    def __init__(self, db: Session):
        super().__init__(StatutoryBonus, db)
    
    def get_by_business_id(
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
        """Get statutory bonuses by business ID with pagination and filters"""
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        
        query = self.db.query(StatutoryBonus).options(
            joinedload(StatutoryBonus.period),
            joinedload(StatutoryBonus.employee).joinedload(Employee.location),
            joinedload(StatutoryBonus.employee).joinedload(Employee.department),
            joinedload(StatutoryBonus.employee).joinedload(Employee.cost_center),
            joinedload(StatutoryBonus.creator)
        ).filter(StatutoryBonus.business_id == business_id)
        
        # Apply filters
        if period_id:
            query = query.filter(StatutoryBonus.period_id == period_id)
        
        if employee_id:
            query = query.filter(StatutoryBonus.employee_id == employee_id)
        
        # Apply employee-based filters using direct ID filtering
        if location or department or cost_center:
            # Join with Employee first
            query = query.join(Employee, StatutoryBonus.employee_id == Employee.id)
            
            if location and location != "All Locations":
                # Get location ID first, then filter
                location_obj = self.db.query(Location).filter(Location.name == location).first()
                if location_obj:
                    query = query.filter(Employee.location_id == location_obj.id)
            
            if department and department != "All Departments":
                # Get department ID first, then filter
                department_obj = self.db.query(Department).filter(Department.name == department).first()
                if department_obj:
                    query = query.filter(Employee.department_id == department_obj.id)
            
            if cost_center and cost_center != "All Cost Centers":
                # Get cost center ID first, then filter
                cost_center_obj = self.db.query(CostCenter).filter(CostCenter.name == cost_center).first()
                if cost_center_obj:
                    query = query.filter(Employee.cost_center_id == cost_center_obj.id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        bonuses = query.order_by(desc(StatutoryBonus.created_at)).offset(offset).limit(size).all()
        
        return {
            "items": bonuses,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_statistics(self, business_id: int, period_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statutory bonus statistics for a business"""
        base_query = self.db.query(StatutoryBonus).filter(
            StatutoryBonus.business_id == business_id
        )
        
        if period_id:
            base_query = base_query.filter(StatutoryBonus.period_id == period_id)
        
        total_amount = base_query.with_entities(func.sum(StatutoryBonus.bonus_amount)).scalar() or Decimal('0')
        processed_count = base_query.filter(StatutoryBonus.is_processed == True).count()
        pending_count = base_query.filter(StatutoryBonus.is_processed == False).count()
        
        return {
            "total_bonuses": base_query.count(),
            "processed_bonuses": processed_count,
            "pending_bonuses": pending_count,
            "total_amount": float(total_amount)
        }
    
    def create_bonus(
        self,
        business_id: int,
        period_id: int,
        employee_id: int,
        created_by: int,
        bonus_rate: Decimal,
        eligibility_cutoff: Decimal,
        min_wages: Decimal,
        min_bonus: Decimal,
        max_bonus: Decimal,
        base_salary: Decimal,
        bonus_amount: Decimal,
        salary_components: Optional[List[str]] = None
    ) -> StatutoryBonus:
        """Create a new statutory bonus record"""
        bonus = StatutoryBonus(
            business_id=business_id,
            period_id=period_id,
            employee_id=employee_id,
            created_by=created_by,
            bonus_rate=bonus_rate,
            eligibility_cutoff=eligibility_cutoff,
            min_wages=min_wages,
            min_bonus=min_bonus,
            max_bonus=max_bonus,
            base_salary=base_salary,
            bonus_amount=bonus_amount,
            salary_components=salary_components,
            is_processed=False
        )
        
        self.db.add(bonus)
        self.db.commit()
        self.db.refresh(bonus)
        
        return bonus
    
    def get_employees_for_bonus(
        self,
        business_id: int,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None,
        employee_ids: Optional[List[int]] = None
    ) -> List[Employee]:
        """Get employees eligible for bonus based on filters"""
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        
        query = self.db.query(Employee).filter(
            and_(
                Employee.business_id == business_id,
                Employee.employee_status == EmployeeStatus.ACTIVE
            )
        )
        
        # Apply filters using direct ID filtering
        if location and location != "All Locations":
            location_obj = self.db.query(Location).filter(Location.name == location).first()
            if location_obj:
                query = query.filter(Employee.location_id == location_obj.id)
        
        if department and department != "All Departments":
            department_obj = self.db.query(Department).filter(Department.name == department).first()
            if department_obj:
                query = query.filter(Employee.department_id == department_obj.id)
        
        if cost_center and cost_center != "All Cost Centers":
            cost_center_obj = self.db.query(CostCenter).filter(CostCenter.name == cost_center).first()
            if cost_center_obj:
                query = query.filter(Employee.cost_center_id == cost_center_obj.id)
        
        if employee_search:
            search_term = f"%{employee_search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                )
            )
        
        if employee_ids:
            query = query.filter(Employee.id.in_(employee_ids))
        
        return query.all()
    
    def delete_bonuses_by_period(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> int:
        """Delete statutory bonuses for a period"""
        query = self.db.query(StatutoryBonus).filter(
            and_(
                StatutoryBonus.business_id == business_id,
                StatutoryBonus.period_id == period_id,
                StatutoryBonus.is_processed == False  # Only delete unprocessed bonuses
            )
        )
        
        if employee_ids:
            query = query.filter(StatutoryBonus.employee_id.in_(employee_ids))
        
        deleted_count = query.count()
        query.delete()
        self.db.commit()
        
        return deleted_count
    
    def process_bonuses(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> int:
        """Mark bonuses as processed"""
        query = self.db.query(StatutoryBonus).filter(
            and_(
                StatutoryBonus.business_id == business_id,
                StatutoryBonus.period_id == period_id,
                StatutoryBonus.is_processed == False
            )
        )
        
        if employee_ids:
            query = query.filter(StatutoryBonus.employee_id.in_(employee_ids))
        
        processed_count = query.count()
        query.update({
            "is_processed": True,
            "processed_date": datetime.now()
        })
        self.db.commit()
        
        return processed_count
    
    def get_bonus_summary(
        self,
        business_id: int,
        period_id: int,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get bonus summary for display"""
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        
        query = self.db.query(StatutoryBonus).options(
            joinedload(StatutoryBonus.employee).joinedload(Employee.location),
            joinedload(StatutoryBonus.employee).joinedload(Employee.department),
            joinedload(StatutoryBonus.employee).joinedload(Employee.cost_center),
            joinedload(StatutoryBonus.employee).joinedload(Employee.designation)
        ).filter(
            and_(
                StatutoryBonus.business_id == business_id,
                StatutoryBonus.period_id == period_id
            )
        )
        
        # Apply employee-based filters using direct ID filtering
        employee_joined = False
        if location or department or cost_center or employee_search:
            query = query.join(Employee, StatutoryBonus.employee_id == Employee.id)
            employee_joined = True
            
            if location and location != "All Locations":
                location_obj = self.db.query(Location).filter(Location.name == location).first()
                if location_obj:
                    query = query.filter(Employee.location_id == location_obj.id)
            
            if department and department != "All Departments":
                department_obj = self.db.query(Department).filter(Department.name == department).first()
                if department_obj:
                    query = query.filter(Employee.department_id == department_obj.id)
            
            if cost_center and cost_center != "All Cost Centers":
                cost_center_obj = self.db.query(CostCenter).filter(CostCenter.name == cost_center).first()
                if cost_center_obj:
                    query = query.filter(Employee.cost_center_id == cost_center_obj.id)
            
            if employee_search:
                search_term = f"%{employee_search}%"
                query = query.filter(
                    or_(
                        Employee.first_name.ilike(search_term),
                        Employee.last_name.ilike(search_term),
                        Employee.employee_code.ilike(search_term),
                        func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                    )
                )
        
        # Order by employee code - use proper reference based on whether we joined
        if employee_joined:
            bonuses = query.order_by(Employee.employee_code).all()
        else:
            # When using joinedload, we need to order after fetching
            bonuses = query.all()
            bonuses = sorted(bonuses, key=lambda b: b.employee.employee_code if b.employee else "")
        
        summary = []
        for bonus in bonuses:
            summary.append({
                "id": bonus.id,
                "employee_code": bonus.employee.employee_code,
                "employee_name": f"{bonus.employee.first_name} {bonus.employee.last_name}",
                "base_salary": float(bonus.base_salary),
                "bonus_amount": float(bonus.bonus_amount),
                "is_processed": bonus.is_processed,
                "department": bonus.employee.department.name if bonus.employee.department else None,
                "designation": bonus.employee.designation.name if bonus.employee.designation else None,
                "location": bonus.employee.location.name if bonus.employee.location else None
            })
        
        return summary