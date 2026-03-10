"""
Loan Repository
Handles database operations for employee loans
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, extract
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.datacapture import EmployeeLoan, LoanStatus
from app.models.employee import Employee
from app.models.business import Business


class LoanRepository:
    """Repository for loan database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_loans_with_filters(
        self,
        current_user = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
        employee_id: Optional[int] = None,
        loan_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get loans with filters and pagination"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        from app.utils.business_unit_utils import get_user_business_context
        
        # Get business context
        business_id = None
        if current_user:
            is_superadmin, user_business_id = get_user_business_context(current_user, self.db)
            if not is_superadmin and user_business_id:
                business_id = user_business_id
        
        query = self.db.query(EmployeeLoan).join(Employee, EmployeeLoan.employee_id == Employee.id)
        
        # Left join with Department and Designation for search
        query = query.outerjoin(Department, Employee.department_id == Department.id)
        query = query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        # Apply date filters
        if from_date:
            query = query.filter(EmployeeLoan.loan_date >= from_date)
        if to_date:
            query = query.filter(EmployeeLoan.loan_date <= to_date)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    Department.name.ilike(search_term),
                    Designation.name.ilike(search_term),
                    EmployeeLoan.loan_type.ilike(search_term)
                )
            )
        
        # Apply other filters
        if employee_id:
            query = query.filter(EmployeeLoan.employee_id == employee_id)
        if loan_type:
            query = query.filter(EmployeeLoan.loan_type == loan_type)
        if status:
            query = query.filter(EmployeeLoan.status == status)
        
        # Apply pagination
        offset = (page - 1) * size
        results = query.order_by(desc(EmployeeLoan.created_at)).offset(offset).limit(size).all()
        
        # Format results
        loans = []
        for loan in results:
            employee = loan.employee
            full_name = f"{employee.first_name} {employee.last_name}".strip()
            loans.append({
                'id': loan.id,
                'employee': full_name,
                'employee_code': employee.employee_code,
                'designation': employee.designation.name if employee.designation else 'N/A',
                'department': employee.department.name if employee.department else 'N/A',
                'loanAmount': float(loan.loan_amount),
                'issueDate': loan.loan_date.strftime('%Y-%m-%d'),
                'interestMethod': f"{loan.interest_rate}% per annum" if loan.interest_rate > 0 else "Interest Free",
                'loan_type': loan.loan_type,
                'emi_amount': float(loan.emi_amount),
                'outstanding_amount': float(loan.outstanding_amount),
                'status': loan.status.value,
                'tenure_months': loan.tenure_months,
                'paid_emis': loan.paid_emis,
                'remaining_emis': loan.remaining_emis
            })
        
        return loans
    
    def search_all_employees_with_loan_status(
        self,
        search: str,
        current_user = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Search all employees and show their loan status - Enhanced search functionality"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        from app.utils.business_unit_utils import get_user_business_context
        
        # Get business context
        business_id = None
        if current_user:
            is_superadmin, user_business_id = get_user_business_context(current_user, self.db)
            if not is_superadmin and user_business_id:
                business_id = user_business_id
        
        search_term = f"%{search}%"
        
        # Query all employees matching search criteria
        employee_query = self.db.query(Employee)
        
        # Join with Department and Designation
        employee_query = employee_query.outerjoin(Department, Employee.department_id == Department.id)
        employee_query = employee_query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        # Apply search filter
        employee_query = employee_query.filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term),
                Department.name.ilike(search_term),
                Designation.name.ilike(search_term)
            )
        )
        
        # Apply pagination
        offset = (page - 1) * size
        employees = employee_query.order_by(Employee.first_name, Employee.last_name).offset(offset).limit(size).all()
        
        # For each employee, get their loan information
        results = []
        for employee in employees:
            full_name = f"{employee.first_name} {employee.last_name}".strip()
            
            # Get the most recent loan for this employee
            latest_loan = self.db.query(EmployeeLoan).filter(
                EmployeeLoan.employee_id == employee.id
            ).order_by(desc(EmployeeLoan.created_at)).first()
            
            if latest_loan:
                # Employee has loans - show latest loan info
                results.append({
                    'id': latest_loan.id,
                    'employee': full_name,
                    'employee_code': employee.employee_code,
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'department': employee.department.name if employee.department else 'N/A',
                    'loanAmount': float(latest_loan.loan_amount),
                    'issueDate': latest_loan.loan_date.strftime('%Y-%m-%d'),
                    'interestMethod': f"{latest_loan.interest_rate}% per annum" if latest_loan.interest_rate > 0 else "Interest Free",
                    'loan_type': latest_loan.loan_type,
                    'emi_amount': float(latest_loan.emi_amount),
                    'outstanding_amount': float(latest_loan.outstanding_amount),
                    'status': latest_loan.status.value,
                    'tenure_months': latest_loan.tenure_months,
                    'paid_emis': latest_loan.paid_emis,
                    'remaining_emis': latest_loan.remaining_emis,
                    'has_loans': True,
                    'employee_id': employee.id
                })
            else:
                # Employee has no loans - show employee info with no loan data
                results.append({
                    'id': None,  # No loan ID
                    'employee': full_name,
                    'employee_code': employee.employee_code,
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'department': employee.department.name if employee.department else 'N/A',
                    'loanAmount': 0,
                    'issueDate': 'No Loans',
                    'interestMethod': 'No Loans',
                    'loan_type': 'No Loans',
                    'emi_amount': 0,
                    'outstanding_amount': 0,
                    'status': 'NO_LOANS',
                    'tenure_months': 0,
                    'paid_emis': 0,
                    'remaining_emis': 0,
                    'has_loans': False,
                    'employee_id': employee.id  # Include employee ID for creating new loans
                })
        
        return results
    
    def get_loan_by_id(self, loan_id: int, business_id: Optional[int] = None) -> Optional[EmployeeLoan]:
        """Get loan by ID"""
        query = self.db.query(EmployeeLoan).filter(EmployeeLoan.id == loan_id)
        
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        return query.first()
    
    def create_loan(self, loan_data: Dict[str, Any]) -> EmployeeLoan:
        """Create new loan"""
        loan = EmployeeLoan(**loan_data)
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan
    
    def update_loan(self, loan_id: int, loan_data: Dict[str, Any], business_id: Optional[int] = None) -> Optional[EmployeeLoan]:
        """Update existing loan"""
        query = self.db.query(EmployeeLoan).filter(EmployeeLoan.id == loan_id)
        
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        loan = query.first()
        if loan:
            for key, value in loan_data.items():
                if hasattr(loan, key):
                    setattr(loan, key, value)
            
            self.db.commit()
            self.db.refresh(loan)
        
        return loan
    
    def delete_loan(self, loan_id: int, business_id: Optional[int] = None) -> bool:
        """Delete loan"""
        query = self.db.query(EmployeeLoan).filter(EmployeeLoan.id == loan_id)
        
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        loan = query.first()
        if loan:
            self.db.delete(loan)
            self.db.commit()
            return True
        
        return False
    
    def get_total_count(
        self,
        business_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
        employee_id: Optional[int] = None,
        loan_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Get total count of loans with filters"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        
        query = self.db.query(EmployeeLoan).join(Employee, EmployeeLoan.employee_id == Employee.id)
        
        # Left join with Department and Designation for search
        query = query.outerjoin(Department, Employee.department_id == Department.id)
        query = query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        # Apply date filters
        if from_date:
            query = query.filter(EmployeeLoan.loan_date >= from_date)
        if to_date:
            query = query.filter(EmployeeLoan.loan_date <= to_date)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    Department.name.ilike(search_term),
                    Designation.name.ilike(search_term),
                    EmployeeLoan.loan_type.ilike(search_term)
                )
            )
        
        # Apply other filters
        if employee_id:
            query = query.filter(EmployeeLoan.employee_id == employee_id)
        if loan_type:
            query = query.filter(EmployeeLoan.loan_type == loan_type)
        if status:
            query = query.filter(EmployeeLoan.status == status)
        
        return query.count()
    
    def get_loan_types(self, current_user = None) -> List[str]:
        """Get distinct loan types"""
        
        # Import here to avoid circular imports
        from app.utils.business_unit_utils import get_user_business_context
        
        query = self.db.query(EmployeeLoan.loan_type).distinct()
        
        # Determine business context
        if current_user:
            is_superadmin, user_business_id = get_user_business_context(current_user, self.db)
            if not is_superadmin and user_business_id:
                query = query.filter(EmployeeLoan.business_id == user_business_id)
        
        return [row[0] for row in query.all() if row[0]]
    
    def get_employee_loans(self, employee_id: int, business_id: Optional[int] = None) -> List[EmployeeLoan]:
        """Get all loans for a specific employee"""
        query = self.db.query(EmployeeLoan).filter(EmployeeLoan.employee_id == employee_id)
        
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        return query.order_by(desc(EmployeeLoan.created_at)).all()
    
    def get_active_loans_summary(self, business_id: Optional[int] = None) -> Dict[str, Any]:
        """Get summary of active loans"""
        query = self.db.query(EmployeeLoan).filter(EmployeeLoan.status == LoanStatus.ACTIVE)
        
        if business_id:
            query = query.filter(EmployeeLoan.business_id == business_id)
        
        loans = query.all()
        
        total_loans = len(loans)
        total_amount = sum(float(loan.loan_amount) for loan in loans)
        total_outstanding = sum(float(loan.outstanding_amount) for loan in loans)
        
        return {
            'total_active_loans': total_loans,
            'total_loan_amount': total_amount,
            'total_outstanding_amount': total_outstanding,
            'total_paid_amount': total_amount - total_outstanding
        }