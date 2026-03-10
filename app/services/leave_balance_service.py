"""
Leave Balance Service
Business logic for leave balance and correction operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
import logging

from app.repositories.leave_balance_repository import LeaveBalanceRepository, LeaveCorrectionRepository
from app.repositories.employee_repository import EmployeeRepository
from app.models.leave_balance import LeaveBalance, LeaveCorrection
from app.models.leave_type import LeaveType
from app.schemas.attendance import LeaveCorrectionSaveRequest

logger = logging.getLogger(__name__)


class LeaveBalanceService:
    """Service for leave balance operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.leave_balance_repo = LeaveBalanceRepository(db)
        self.leave_correction_repo = LeaveCorrectionRepository(db)
        self.employee_repo = EmployeeRepository(db)
    
    def get_employee_leave_summary(
        self, 
        employee_id: int, 
        year: int, 
        month: int
    ) -> Dict[str, Any]:
        """Get comprehensive leave summary for employee"""
        try:
            # Get employee
            employee = self.employee_repo.get(employee_id)
            if not employee:
                raise ValueError(f"Employee {employee_id} not found")
            
            # Get all leave balances for the month
            balances = self.leave_balance_repo.get_employee_balances_by_month(
                employee_id, year, month
            )
            
            # If no balances exist, create default ones
            if not balances:
                balances = self._create_default_balances(employee_id, employee.business_id, year, month)
            
            # Calculate totals
            total_opening = sum(b.opening_balance for b in balances)
            total_activity = sum(b.activity_balance for b in balances)
            total_correction = sum(b.correction_balance for b in balances)
            total_closing = sum(b.closing_balance for b in balances)
            
            # Get recent corrections
            corrections = self.leave_correction_repo.get_employee_corrections(
                employee_id, year, month
            )
            
            return {
                "employee_id": employee_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "employee_code": employee.employee_code,
                "year": year,
                "month": month,
                "opening_balance": float(total_opening),
                "activity_balance": float(total_activity),
                "correction_balance": float(total_correction),
                "closing_balance": float(total_closing),
                "balances_by_type": [
                    {
                        "leave_type_id": b.leave_type_id,
                        "opening": float(b.opening_balance),
                        "activity": float(b.activity_balance),
                        "correction": float(b.correction_balance),
                        "closing": float(b.closing_balance)
                    }
                    for b in balances
                ],
                "recent_corrections": [
                    {
                        "id": c.id,
                        "amount": float(c.correction_amount),
                        "reason": c.correction_reason,
                        "date": c.correction_date.isoformat(),
                        "created_at": c.created_at.isoformat()
                    }
                    for c in corrections[:5]  # Last 5 corrections
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting leave summary for employee {employee_id}: {str(e)}")
            raise
    
    def get_business_leave_summary(
        self, 
        business_id: int, 
        year: int, 
        month: int,
        employee_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Get leave summary for all employees in business"""
        try:
            # Get employees
            if employee_ids:
                employees = [self.employee_repo.get(emp_id) for emp_id in employee_ids]
                employees = [emp for emp in employees if emp]  # Filter out None values
            else:
                # Query employees directly from database
                from app.models.employee import Employee
                employees = self.db.query(Employee).filter(
                    Employee.business_id == business_id,
                    Employee.is_active == True
                ).all()
            
            summaries = []
            for employee in employees:
                try:
                    summary = self.get_employee_leave_summary(employee.id, year, month)
                    summaries.append(summary)
                except Exception as e:
                    logger.warning(f"Failed to get summary for employee {employee.id}: {str(e)}")
                    # Add basic summary with zeros
                    summaries.append({
                        "employee_id": employee.id,
                        "employee_name": f"{employee.first_name} {employee.last_name}",
                        "employee_code": employee.employee_code,
                        "year": year,
                        "month": month,
                        "opening_balance": 0.0,
                        "activity_balance": 0.0,
                        "correction_balance": 0.0,
                        "closing_balance": 0.0,
                        "balances_by_type": [],
                        "recent_corrections": []
                    })
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting business leave summary: {str(e)}")
            raise
    
    def create_leave_correction(
        self,
        employee_id: int,
        correction_amount: Decimal,
        reason: str,
        year: int,
        month: int,
        correction_date: date,
        created_by: int,
        leave_type_id: int = 1  # Default to first leave type
    ) -> LeaveCorrection:
        """Create leave correction and update balance"""
        try:
            # Get employee
            employee = self.employee_repo.get(employee_id)
            if not employee:
                raise ValueError(f"Employee {employee_id} not found")
            
            # Get or create leave balance
            balance = self.leave_balance_repo.get_employee_balance(
                employee_id, leave_type_id, year, month
            )
            
            if not balance:
                # Create default balance if it doesn't exist
                balance = self.leave_balance_repo.create_or_update_balance(
                    employee_id=employee_id,
                    business_id=employee.business_id,
                    leave_type_id=leave_type_id,
                    year=year,
                    month=month,
                    opening_balance=Decimal('24.0'),  # Default opening balance
                    activity_balance=Decimal('-2.0'),  # Default activity
                    correction_balance=Decimal('0.0')
                )
            
            # Calculate new balance
            previous_balance = balance.closing_balance
            new_balance = previous_balance + correction_amount
            
            # Create correction record
            correction = self.leave_correction_repo.create_correction(
                employee_id=employee_id,
                business_id=employee.business_id,
                leave_balance_id=balance.id,
                correction_amount=correction_amount,
                previous_balance=previous_balance,
                new_balance=new_balance,
                reason=reason,
                year=year,
                month=month,
                correction_date=correction_date,
                created_by=created_by
            )
            
            # Update balance
            self.leave_balance_repo.update_correction_balance(
                employee_id, leave_type_id, year, month, correction_amount
            )
            
            logger.info(f"Created leave correction {correction.id} for employee {employee_id}")
            return correction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating leave correction: {str(e)}")
            raise
    
    def _create_default_balances(
        self, 
        employee_id: int, 
        business_id: int, 
        year: int, 
        month: int
    ) -> List[LeaveBalance]:
        """Create default leave balances for employee"""
        try:
            # Get available leave types (or create default one)
            leave_types = self.db.query(LeaveType).filter(
                LeaveType.business_id == business_id
            ).all()
            
            if not leave_types:
                # Create a default leave type if none exist
                default_leave_type = LeaveType(
                    business_id=business_id,
                    name="Annual Leave",
                    alias="AL"
                )
                self.db.add(default_leave_type)
                self.db.commit()
                self.db.refresh(default_leave_type)
                leave_types = [default_leave_type]
            
            balances = []
            for leave_type in leave_types:
                # Use a default opening balance since LeaveType doesn't have days_per_year field
                default_opening_balance = Decimal('24.0')  # Default 24 days annual leave
                
                balance = self.leave_balance_repo.create_or_update_balance(
                    employee_id=employee_id,
                    business_id=business_id,
                    leave_type_id=leave_type.id,
                    year=year,
                    month=month,
                    opening_balance=default_opening_balance,
                    activity_balance=Decimal('-2.0'),  # Default activity
                    correction_balance=Decimal('0.0')
                )
                balances.append(balance)
            
            return balances
            
        except Exception as e:
            logger.error(f"Error creating default balances: {str(e)}")
            raise
    
    def approve_correction(
        self, 
        correction_id: int, 
        approved_by: int
    ) -> LeaveCorrection:
        """Approve a leave correction (placeholder for future approval workflow)"""
        try:
            correction = self.leave_correction_repo.get(correction_id)
            if not correction:
                raise ValueError(f"Correction {correction_id} not found")
            
            # Future: Add approval logic here
            logger.info(f"Correction {correction_id} approved by user {approved_by}")
            return correction
            
        except Exception as e:
            logger.error(f"Error approving correction: {str(e)}")
            raise
    
    def get_correction_history(
        self, 
        business_id: int, 
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get correction history for business"""
        try:
            corrections = self.leave_correction_repo.get_business_corrections(
                business_id, year, month
            )
            
            history = []
            for correction in corrections:
                employee = self.employee_repo.get(correction.employee_id)
                history.append({
                    "id": correction.id,
                    "employee_id": correction.employee_id,
                    "employee_name": f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
                    "employee_code": employee.employee_code if employee else "N/A",
                    "correction_amount": float(correction.correction_amount),
                    "previous_balance": float(correction.previous_balance),
                    "new_balance": float(correction.new_balance),
                    "reason": correction.correction_reason,
                    "correction_date": correction.correction_date.isoformat(),
                    "created_at": correction.created_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting correction history: {str(e)}")
            raise