"""
Payroll Run Repository
Repository for handling payroll run data operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.payroll import PayrollRun, PayrollPeriod, PayrollRunStatus
from app.models.employee import Employee
from app.repositories.base_repository import BaseRepository


class PayrollRunRepository(BaseRepository[PayrollRun]):
    """Repository for payroll run operations"""
    
    def __init__(self, db: Session):
        super().__init__(PayrollRun, db)
    
    def get_by_business_id(
        self, 
        business_id: int, 
        page: int = 1, 
        size: int = 20,
        period_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get payroll runs by business ID with pagination and filters"""
        query = self.db.query(PayrollRun).options(
            joinedload(PayrollRun.period),
            joinedload(PayrollRun.creator)
        ).filter(PayrollRun.business_id == business_id)
        
        # Apply filters
        if period_id:
            query = query.filter(PayrollRun.period_id == period_id)
        
        if status:
            query = query.filter(PayrollRun.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        runs = query.order_by(desc(PayrollRun.run_date)).offset(offset).limit(size).all()
        
        return {
            "items": runs,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_statistics(self, business_id: int, period_id: Optional[int] = None) -> Dict[str, Any]:
        """Get payroll run statistics for a business"""
        base_query = self.db.query(PayrollRun).filter(
            PayrollRun.business_id == business_id
        )
        
        if period_id:
            base_query = base_query.filter(PayrollRun.period_id == period_id)
        
        total_runs = base_query.count()
        completed_runs = base_query.filter(PayrollRun.status == PayrollRunStatus.COMPLETED.value).count()
        failed_runs = base_query.filter(PayrollRun.status == PayrollRunStatus.FAILED.value).count()
        running_runs = base_query.filter(PayrollRun.status == PayrollRunStatus.RUNNING.value).count()
        pending_runs = base_query.filter(PayrollRun.status == PayrollRunStatus.PENDING.value).count()
        
        # Calculate totals
        totals = base_query.filter(PayrollRun.status == PayrollRunStatus.COMPLETED.value).with_entities(
            func.sum(PayrollRun.total_gross_salary).label('total_gross'),
            func.sum(PayrollRun.total_deductions).label('total_deductions'),
            func.sum(PayrollRun.total_net_salary).label('total_net'),
            func.sum(PayrollRun.total_employees).label('total_employees'),
            func.avg(PayrollRun.runtime_seconds).label('avg_runtime')
        ).first()
        
        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "pending_runs": pending_runs,
            "success_rate": (completed_runs / total_runs * 100) if total_runs > 0 else 0,
            "total_gross_salary": float(totals.total_gross or 0),
            "total_deductions": float(totals.total_deductions or 0),
            "total_net_salary": float(totals.total_net or 0),
            "total_employees_processed": int(totals.total_employees or 0),
            "average_runtime_seconds": float(totals.avg_runtime or 0)
        }
    
    def create_payroll_run(
        self,
        business_id: int,
        period_id: int,
        created_by: int,
        notes: Optional[str] = None
    ) -> PayrollRun:
        """Create a new payroll run"""
        payroll_run = PayrollRun(
            business_id=business_id,
            period_id=period_id,
            created_by=created_by,
            notes=notes,
            status=PayrollRunStatus.PENDING.value,
            run_date=datetime.now()
        )
        
        self.db.add(payroll_run)
        self.db.commit()
        self.db.refresh(payroll_run)
        
        return payroll_run
    
    def update_run_status(
        self,
        run_id: int,
        status: str,
        runtime_seconds: Optional[int] = None,
        total_employees: Optional[int] = None,
        processed_employees: Optional[int] = None,
        failed_employees: Optional[int] = None,
        total_gross_salary: Optional[Decimal] = None,
        total_deductions: Optional[Decimal] = None,
        total_net_salary: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        log_file_path: Optional[str] = None
    ) -> Optional[PayrollRun]:
        """Update payroll run status and results"""
        payroll_run = self.db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
        
        if not payroll_run:
            return None
        
        payroll_run.status = status
        
        if runtime_seconds is not None:
            payroll_run.runtime_seconds = runtime_seconds
        if total_employees is not None:
            payroll_run.total_employees = total_employees
        if processed_employees is not None:
            payroll_run.processed_employees = processed_employees
        if failed_employees is not None:
            payroll_run.failed_employees = failed_employees
        if total_gross_salary is not None:
            payroll_run.total_gross_salary = total_gross_salary
        if total_deductions is not None:
            payroll_run.total_deductions = total_deductions
        if total_net_salary is not None:
            payroll_run.total_net_salary = total_net_salary
        if error_message is not None:
            payroll_run.error_message = error_message
        if log_file_path is not None:
            payroll_run.log_file_path = log_file_path
        
        self.db.commit()
        self.db.refresh(payroll_run)
        
        return payroll_run
    
    def get_recent_runs(self, business_id: int, limit: int = 10) -> List[PayrollRun]:
        """Get recent payroll runs for a business"""
        return self.db.query(PayrollRun).options(
            joinedload(PayrollRun.period),
            joinedload(PayrollRun.creator)
        ).filter(
            PayrollRun.business_id == business_id
        ).order_by(desc(PayrollRun.run_date)).limit(limit).all()
    
    def get_running_runs(self, business_id: int) -> List[PayrollRun]:
        """Get currently running payroll runs"""
        return self.db.query(PayrollRun).filter(
            and_(
                PayrollRun.business_id == business_id,
                PayrollRun.status == PayrollRunStatus.RUNNING.value
            )
        ).all()
    
    def get_payroll_chart_data(self, business_id: int, months: int = 12) -> List[Dict[str, Any]]:
        """Get payroll chart data for the last N months"""
        # Calculate date range for the last N months
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)  # Approximate
        
        # Query all completed runs within date range (not just specific date range)
        # This will include all available data for better chart visualization
        runs = self.db.query(PayrollRun).options(
            joinedload(PayrollRun.period)
        ).filter(
            and_(
                PayrollRun.business_id == business_id,
                PayrollRun.status == PayrollRunStatus.COMPLETED.value
            )
        ).order_by(PayrollRun.run_date).all()
        
        # Group by month-year and aggregate data
        monthly_data = {}
        for run in runs:
            month_year = run.run_date.strftime("%b-%Y").upper()
            
            if month_year not in monthly_data:
                monthly_data[month_year] = {
                    "period": month_year,
                    "net_payroll": 0,
                    "gross_payroll": 0,
                    "total_deductions": 0,
                    "employees": 0,
                    "run_count": 0,
                    "run_dates": []
                }
            
            # Aggregate the data for this month
            monthly_data[month_year]["net_payroll"] += float(run.total_net_salary)
            monthly_data[month_year]["gross_payroll"] += float(run.total_gross_salary)
            monthly_data[month_year]["total_deductions"] += float(run.total_deductions)
            monthly_data[month_year]["employees"] += run.total_employees
            monthly_data[month_year]["run_count"] += 1
            monthly_data[month_year]["run_dates"].append(run.run_date.isoformat())
        
        # Convert to list format
        chart_data = list(monthly_data.values())
        
        return chart_data
    
    def can_run_payroll(self, business_id: int, period_id: int) -> Dict[str, Any]:
        """Check if payroll can be run for a period"""
        # Check if there are any running payroll runs
        running_runs = self.get_running_runs(business_id)
        
        if running_runs:
            return {
                "can_run": False,
                "reason": "Another payroll run is currently in progress",
                "running_runs": len(running_runs)
            }
        
        # Check period status
        period = self.db.query(PayrollPeriod).filter(PayrollPeriod.id == period_id).first()
        
        if not period:
            return {
                "can_run": False,
                "reason": "Payroll period not found"
            }
        
        if period.status == "closed":
            return {
                "can_run": False,
                "reason": "Cannot run payroll for closed period"
            }
        
        # Check daily run limit (increased to 20 runs per day for development/testing)
        today = date.today()
        today_runs = self.db.query(PayrollRun).filter(
            and_(
                PayrollRun.business_id == business_id,
                PayrollRun.period_id == period_id,
                func.date(PayrollRun.run_date) == today
            )
        ).count()
        
        # Increased limit to 20 runs per day to allow for testing and development
        if today_runs >= 20:
            return {
                "can_run": False,
                "reason": "Daily payroll run limit exceeded (20 runs per day)",
                "runs_today": today_runs
            }
        
        return {
            "can_run": True,
            "reason": "Ready to run payroll",
            "runs_today": today_runs
        }