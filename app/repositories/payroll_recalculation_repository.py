"""
Payroll Recalculation Repository
Repository for handling payroll recalculation data operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date

from app.models.payroll import PayrollRecalculation
from app.models.employee import Employee
from app.repositories.base_repository import BaseRepository


class PayrollRecalculationRepository(BaseRepository[PayrollRecalculation]):
    """Repository for payroll recalculation operations"""
    
    def __init__(self, db: Session):
        super().__init__(PayrollRecalculation, db)
    
    def get_by_business_id(
        self, 
        business_id: int, 
        page: int = 1, 
        size: int = 20,
        period_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get payroll recalculations by business ID with pagination and filters"""
        query = self.db.query(PayrollRecalculation).options(
            joinedload(PayrollRecalculation.period),
            joinedload(PayrollRecalculation.creator)
        ).filter(PayrollRecalculation.business_id == business_id)
        
        # Apply filters
        if period_id:
            query = query.filter(PayrollRecalculation.period_id == period_id)
        
        if status:
            query = query.filter(PayrollRecalculation.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        recalculations = query.order_by(desc(PayrollRecalculation.created_at)).offset(offset).limit(size).all()
        
        return {
            "items": recalculations,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_statistics(self, business_id: int) -> Dict[str, int]:
        """Get recalculation statistics for a business"""
        base_query = self.db.query(PayrollRecalculation).filter(
            PayrollRecalculation.business_id == business_id
        )
        
        return {
            "total_jobs": base_query.count(),
            "pending_jobs": base_query.filter(PayrollRecalculation.status == "pending").count(),
            "running_jobs": base_query.filter(PayrollRecalculation.status == "running").count(),
            "completed_jobs": base_query.filter(PayrollRecalculation.status == "completed").count(),
            "failed_jobs": base_query.filter(PayrollRecalculation.status == "failed").count()
        }
    
    def create_recalculation(
        self,
        business_id: int,
        period_id: int,
        created_by: int,
        date_from: date,
        date_to: date,
        all_employees: bool = True,
        selected_employees: Optional[List[int]] = None
    ) -> PayrollRecalculation:
        """Create a new payroll recalculation job"""
        recalculation = PayrollRecalculation(
            business_id=business_id,
            period_id=period_id,
            created_by=created_by,
            date_from=date_from,
            date_to=date_to,
            all_employees=all_employees,
            selected_employees=selected_employees,
            status="pending",
            progress_percentage=0,
            total_employees=0,
            processed_employees=0,
            failed_employees=0
        )
        
        self.db.add(recalculation)
        self.db.commit()
        self.db.refresh(recalculation)
        
        return recalculation
    
    def update_progress(
        self,
        recalculation_id: int,
        progress_percentage: int,
        processed_employees: int = None,
        failed_employees: int = None,
        status: str = None,
        success_message: str = None,
        error_message: str = None
    ) -> Optional[PayrollRecalculation]:
        """Update recalculation progress"""
        recalculation = self.get_by_id(recalculation_id)
        if not recalculation:
            return None
        
        recalculation.progress_percentage = progress_percentage
        
        if processed_employees is not None:
            recalculation.processed_employees = processed_employees
        
        if failed_employees is not None:
            recalculation.failed_employees = failed_employees
        
        if status:
            recalculation.status = status
            
            if status == "running" and not recalculation.started_at:
                recalculation.started_at = datetime.now()
            elif status in ["completed", "failed"]:
                recalculation.completed_at = datetime.now()
        
        if success_message:
            recalculation.success_message = success_message
        
        if error_message:
            recalculation.error_message = error_message
        
        self.db.commit()
        self.db.refresh(recalculation)
        
        return recalculation
    
    def get_employees_for_recalculation(
        self,
        business_id: int,
        all_employees: bool,
        selected_employees: Optional[List[int]] = None
    ) -> List[Employee]:
        """Get employees for recalculation based on selection criteria"""
        query = self.db.query(Employee).filter(
            and_(
                Employee.business_id == business_id,
                Employee.is_active == True
            )
        )
        
        if not all_employees and selected_employees:
            query = query.filter(Employee.id.in_(selected_employees))
        
        return query.all()
    
    def get_active_recalculations(self, business_id: int) -> List[PayrollRecalculation]:
        """Get currently running recalculations"""
        return self.db.query(PayrollRecalculation).filter(
            and_(
                PayrollRecalculation.business_id == business_id,
                PayrollRecalculation.status.in_(["pending", "running"])
            )
        ).all()
    
    def get_recent_recalculations_count(
        self,
        business_id: int,
        minutes: int = 30
    ) -> int:
        """Get count of recent recalculations within specified minutes"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return self.db.query(PayrollRecalculation).filter(
            and_(
                PayrollRecalculation.business_id == business_id,
                PayrollRecalculation.all_employees == True,
                PayrollRecalculation.created_at >= cutoff_time
            )
        ).count()
    
    def get_by_id(self, recalculation_id: int) -> Optional[PayrollRecalculation]:
        """Get recalculation by ID"""
        return self.db.query(PayrollRecalculation).options(
            joinedload(PayrollRecalculation.period),
            joinedload(PayrollRecalculation.creator)
        ).filter(PayrollRecalculation.id == recalculation_id).first()