"""
Gratuity Repository
Repository for handling gratuity data operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date
from decimal import Decimal

from app.models.payroll import Gratuity
from app.models.employee import Employee, EmployeeStatus
from app.repositories.base_repository import BaseRepository


class GratuityRepository(BaseRepository[Gratuity]):
    """Repository for gratuity operations"""
    
    def __init__(self, db: Session):
        super().__init__(Gratuity, db)
    
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
        """Get gratuities by business ID with pagination and filters"""
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        
        query = self.db.query(Gratuity).options(
            joinedload(Gratuity.period),
            joinedload(Gratuity.employee).joinedload(Employee.location),
            joinedload(Gratuity.employee).joinedload(Employee.department),
            joinedload(Gratuity.employee).joinedload(Employee.cost_center),
            joinedload(Gratuity.creator)
        ).filter(Gratuity.business_id == business_id)
        
        # Apply filters
        if period_id:
            query = query.filter(Gratuity.period_id == period_id)
        
        if employee_id:
            query = query.filter(Gratuity.employee_id == employee_id)
        
        # Apply employee-based filters using direct ID filtering
        if location or department or cost_center:
            query = query.join(Employee, Gratuity.employee_id == Employee.id)
            
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
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        gratuities = query.order_by(desc(Gratuity.created_at)).offset(offset).limit(size).all()
        
        return {
            "items": gratuities,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_statistics(self, business_id: int, period_id: Optional[int] = None) -> Dict[str, Any]:
        """Get gratuity statistics for a business"""
        base_query = self.db.query(Gratuity).filter(
            Gratuity.business_id == business_id
        )
        
        if period_id:
            base_query = base_query.filter(Gratuity.period_id == period_id)
        
        total_amount = base_query.with_entities(func.sum(Gratuity.gratuity_amount)).scalar() or Decimal('0')
        processed_count = base_query.filter(Gratuity.is_processed == True).count()
        pending_count = base_query.filter(Gratuity.is_processed == False).count()
        
        return {
            "total_gratuities": base_query.count(),
            "processed_gratuities": processed_count,
            "pending_gratuities": pending_count,
            "total_amount": float(total_amount)
        }
    
    def create_gratuity(
        self,
        business_id: int,
        period_id: int,
        employee_id: int,
        created_by: int,
        min_years: int,
        payable_days: int,
        month_days: int,
        exit_only: bool,
        year_rounding: str,
        years_of_service: Decimal,
        base_salary: Decimal,
        gratuity_amount: Decimal,
        salary_components: Optional[List[str]] = None
    ) -> Gratuity:
        """Create a new gratuity record"""
        gratuity = Gratuity(
            business_id=business_id,
            period_id=period_id,
            employee_id=employee_id,
            created_by=created_by,
            min_years=min_years,
            payable_days=payable_days,
            month_days=month_days,
            exit_only=exit_only,
            year_rounding=year_rounding,
            years_of_service=years_of_service,
            base_salary=base_salary,
            gratuity_amount=gratuity_amount,
            salary_components=salary_components,
            is_processed=False
        )
        
        self.db.add(gratuity)
        self.db.commit()
        self.db.refresh(gratuity)
        
        return gratuity
    
    def get_employees_for_gratuity(
        self,
        business_id: int,
        min_years: int,
        exit_only: bool = False,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None,
        employee_ids: Optional[List[int]] = None
    ) -> List[Employee]:
        """Get employees eligible for gratuity based on filters"""
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        
        # Base query - if exit_only, get inactive employees, otherwise get active
        if exit_only:
            query = self.db.query(Employee).filter(
                and_(
                    Employee.business_id == business_id,
                    Employee.employee_status != EmployeeStatus.ACTIVE
                )
            )
        else:
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
    
    def delete_gratuities_by_period(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> int:
        """Delete gratuities for a period"""
        query = self.db.query(Gratuity).filter(
            and_(
                Gratuity.business_id == business_id,
                Gratuity.period_id == period_id,
                Gratuity.is_processed == False  # Only delete unprocessed gratuities
            )
        )
        
        if employee_ids:
            query = query.filter(Gratuity.employee_id.in_(employee_ids))
        
        deleted_count = query.count()
        query.delete()
        self.db.commit()
        
        return deleted_count
    
    def process_gratuities(
        self,
        business_id: int,
        period_id: int,
        employee_ids: Optional[List[int]] = None
    ) -> int:
        """Mark gratuities as processed"""
        query = self.db.query(Gratuity).filter(
            and_(
                Gratuity.business_id == business_id,
                Gratuity.period_id == period_id,
                Gratuity.is_processed == False
            )
        )
        
        if employee_ids:
            query = query.filter(Gratuity.employee_id.in_(employee_ids))
        
        processed_count = query.count()
        query.update({
            "is_processed": True,
            "processed_date": datetime.now()
        })
        self.db.commit()
        
        return processed_count
    
    def get_gratuity_summary(
        self,
        business_id: int,
        period_id: int,
        location: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        employee_search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get gratuity summary for display"""
        from app.models.location import Location
        from app.models.department import Department
        from app.models.cost_center import CostCenter
        
        query = self.db.query(Gratuity).options(
            joinedload(Gratuity.employee).joinedload(Employee.location),
            joinedload(Gratuity.employee).joinedload(Employee.department),
            joinedload(Gratuity.employee).joinedload(Employee.cost_center),
            joinedload(Gratuity.employee).joinedload(Employee.designation)
        ).filter(
            and_(
                Gratuity.business_id == business_id,
                Gratuity.period_id == period_id
            )
        )
        
        # Apply employee-based filters using direct ID filtering
        if location or department or cost_center or employee_search:
            query = query.join(Employee, Gratuity.employee_id == Employee.id)
            
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
        
        # Order by employee code using the joined table
        if location or department or cost_center or employee_search:
            # Employee table is already joined
            gratuities = query.order_by(Employee.employee_code).all()
        else:
            # Need to join Employee table for ordering
            query = query.join(Employee, Gratuity.employee_id == Employee.id)
            gratuities = query.order_by(Employee.employee_code).all()
        
        summary = []
        for gratuity in gratuities:
            summary.append({
                "id": gratuity.id,
                "employee_code": gratuity.employee.employee_code,
                "employee_name": f"{gratuity.employee.first_name} {gratuity.employee.last_name}",
                "base_salary": float(gratuity.base_salary),
                "years_of_service": float(gratuity.years_of_service),
                "gratuity_amount": float(gratuity.gratuity_amount),
                "is_processed": gratuity.is_processed,
                "department": gratuity.employee.department.name if gratuity.employee.department else None,
                "designation": gratuity.employee.designation.name if gratuity.employee.designation else None,
                "location": gratuity.employee.location.name if gratuity.employee.location else None
            })
        
        return summary
    
    def get_employee_years_of_service(self, employee: Employee) -> Decimal:
        """Calculate employee's years of service"""
        if not employee.date_of_joining:
            return Decimal('0')
        
        # Calculate years of service from joining date to current date
        today = date.today()
        joining_date = employee.date_of_joining
        
        # Calculate total days
        total_days = (today - joining_date).days
        
        # Convert to years (approximate)
        years = Decimal(str(total_days)) / Decimal('365.25')
        
        return years.quantize(Decimal('0.01'))