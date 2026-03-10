"""
Leave Balance Repository
Handles leave balance and correction operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import date, datetime
from decimal import Decimal

from app.models.leave_balance import LeaveBalance, LeaveCorrection
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.repositories.base_repository import BaseRepository


class LeaveBalanceRepository(BaseRepository[LeaveBalance]):
    """Repository for leave balance operations"""
    
    def __init__(self, db: Session):
        super().__init__(LeaveBalance, db)
    
    def get_employee_balance(
        self, 
        employee_id: int, 
        leave_type_id: int, 
        year: int, 
        month: int
    ) -> Optional[LeaveBalance]:
        """Get employee leave balance for specific period"""
        return self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.balance_year == year,
                LeaveBalance.balance_month == month,
                LeaveBalance.is_active == True
            )
        ).first()
    
    def get_employee_balances_by_month(
        self, 
        employee_id: int, 
        year: int, 
        month: int
    ) -> List[LeaveBalance]:
        """Get all leave type balances for employee in specific month"""
        return self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.balance_year == year,
                LeaveBalance.balance_month == month,
                LeaveBalance.is_active == True
            )
        ).all()
    
    def get_business_balances(
        self, 
        business_id: int, 
        year: int, 
        month: int,
        employee_ids: Optional[List[int]] = None
    ) -> List[LeaveBalance]:
        """Get leave balances for all employees in business for specific month"""
        query = self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.business_id == business_id,
                LeaveBalance.balance_year == year,
                LeaveBalance.balance_month == month,
                LeaveBalance.is_active == True
            )
        )
        
        if employee_ids:
            query = query.filter(LeaveBalance.employee_id.in_(employee_ids))
        
        return query.all()
    
    def create_or_update_balance(
        self,
        employee_id: int,
        business_id: int,
        leave_type_id: int,
        year: int,
        month: int,
        opening_balance: Decimal = Decimal('0'),
        activity_balance: Decimal = Decimal('0'),
        correction_balance: Decimal = Decimal('0')
    ) -> LeaveBalance:
        """Create or update leave balance"""
        existing = self.get_employee_balance(employee_id, leave_type_id, year, month)
        
        closing_balance = opening_balance + activity_balance + correction_balance
        
        if existing:
            existing.opening_balance = opening_balance
            existing.activity_balance = activity_balance
            existing.correction_balance = correction_balance
            existing.closing_balance = closing_balance
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            balance = LeaveBalance(
                employee_id=employee_id,
                business_id=business_id,
                leave_type_id=leave_type_id,
                balance_year=year,
                balance_month=month,
                balance_date=date(year, month, 1),
                opening_balance=opening_balance,
                activity_balance=activity_balance,
                correction_balance=correction_balance,
                closing_balance=closing_balance
            )
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
            return balance
    
    def update_correction_balance(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
        month: int,
        correction_amount: Decimal
    ) -> Optional[LeaveBalance]:
        """Update correction balance for employee"""
        balance = self.get_employee_balance(employee_id, leave_type_id, year, month)
        if balance:
            balance.correction_balance += correction_amount
            balance.closing_balance = (
                balance.opening_balance + 
                balance.activity_balance + 
                balance.correction_balance
            )
            balance.updated_at = datetime.utcnow()
            self.db.commit()
            return balance
        return None


class LeaveCorrectionRepository(BaseRepository[LeaveCorrection]):
    """Repository for leave correction operations"""
    
    def __init__(self, db: Session):
        super().__init__(LeaveCorrection, db)
    
    def get_employee_corrections(
        self, 
        employee_id: int, 
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[LeaveCorrection]:
        """Get employee leave corrections"""
        query = self.db.query(LeaveCorrection).filter(
            LeaveCorrection.employee_id == employee_id
        )
        
        if year:
            query = query.filter(LeaveCorrection.correction_year == year)
        
        if month:
            query = query.filter(LeaveCorrection.correction_month == month)
        
        return query.order_by(desc(LeaveCorrection.created_at)).all()
    
    def get_business_corrections(
        self, 
        business_id: int, 
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[LeaveCorrection]:
        """Get all corrections for business"""
        query = self.db.query(LeaveCorrection).filter(
            LeaveCorrection.business_id == business_id
        )
        
        if year:
            query = query.filter(LeaveCorrection.correction_year == year)
        
        if month:
            query = query.filter(LeaveCorrection.correction_month == month)
        
        return query.order_by(desc(LeaveCorrection.created_at)).all()
    
    def create_correction(
        self,
        employee_id: int,
        business_id: int,
        leave_balance_id: int,
        correction_amount: Decimal,
        previous_balance: Decimal,
        new_balance: Decimal,
        reason: str,
        year: int,
        month: int,
        correction_date: date,
        created_by: int
    ) -> LeaveCorrection:
        """Create leave correction record"""
        correction = LeaveCorrection(
            employee_id=employee_id,
            business_id=business_id,
            leave_balance_id=leave_balance_id,
            correction_amount=correction_amount,
            previous_balance=previous_balance,
            new_balance=new_balance,
            correction_reason=reason,
            correction_year=year,
            correction_month=month,
            correction_date=correction_date,
            created_by=created_by
        )
        
        self.db.add(correction)
        self.db.commit()
        self.db.refresh(correction)
        return correction