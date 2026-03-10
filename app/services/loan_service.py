"""
Loan Service
Business logic for employee loans management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from app.schemas.reports import EmployeeLoansFilters

logger = logging.getLogger(__name__)


class LoanService:
    """Service for loan business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employee_loans_report(self, filters: EmployeeLoansFilters, current_user) -> Dict[str, Any]:
        """
        Get employee loans report based on filters
        
        Args:
            filters: Report filters
            current_user: Current authenticated user
            
        Returns:
            Dictionary with loans list and summary
        """
        try:
            from app.models.employee import Employee
            from app.models.location import Location
            from app.models.department import Department
            from app.models.cost_center import CostCenter
            from app.models.datacapture import EmployeeLoan, LoanStatus
            from sqlalchemy import and_, or_, func
            from sqlalchemy.orm import joinedload
            from app.api.v1.endpoints.master_setup import get_user_business_id
            
            logger.info(f"Generating employee loans report with filters: {filters}")
            
            # Get business ID for filtering
            business_id = get_user_business_id(current_user, self.db)
            
            # Build base query for loans with employee details
            query = self.db.query(EmployeeLoan).options(
                joinedload(EmployeeLoan.employee).joinedload(Employee.location),
                joinedload(EmployeeLoan.employee).joinedload(Employee.department),
                joinedload(EmployeeLoan.employee).joinedload(Employee.designation),
                joinedload(EmployeeLoan.employee).joinedload(Employee.cost_center)
            ).join(
                Employee, EmployeeLoan.employee_id == Employee.id
            ).filter(
                Employee.employee_status == 'ACTIVE',
                EmployeeLoan.status == LoanStatus.ACTIVE
            )
            
            if business_id:
                query = query.filter(EmployeeLoan.business_id == business_id)
            
            # Apply location filter
            if filters.location and filters.location not in ["All Locations", "", None]:
                query = query.filter(Employee.location.has(Location.name == filters.location))
            
            # Apply department filter
            if filters.department and filters.department not in ["All Departments", "", None]:
                query = query.filter(Employee.department.has(Department.name == filters.department))
            
            # Apply cost center filter
            if filters.cost_center and filters.cost_center not in ["All Cost Centers", "", None]:
                query = query.filter(Employee.cost_center.has(CostCenter.name == filters.cost_center))
            
            # Apply issued during filter
            if filters.issued_during and filters.issued_during != "All Time":
                today = datetime.now().date()
                start_date = None
                
                if filters.issued_during == "Last 30 days":
                    start_date = today - timedelta(days=30)
                elif filters.issued_during == "Last 3 months":
                    start_date = today - timedelta(days=90)
                elif filters.issued_during == "Last 6 months":
                    start_date = today - timedelta(days=180)
                elif filters.issued_during == "Last 1 year":
                    start_date = today - timedelta(days=365)
                
                if start_date:
                    logger.info(f"Filtering loans from {start_date} to {today}")
                    query = query.filter(EmployeeLoan.loan_date >= start_date)
            else:
                logger.info("No date filter applied - showing all loans")
            
            # Apply employee search filter
            if filters.employee_search and filters.employee_search.strip():
                search_input = filters.employee_search.strip()
                
                # If the search input contains " - " (from autocomplete selection), extract the code
                if " - " in search_input:
                    employee_code = search_input.split(" - ")[0].strip()
                    logger.info(f"Extracted employee code from autocomplete: {employee_code}")
                    query = query.filter(Employee.employee_code == employee_code)
                else:
                    # Otherwise, do a general search
                    search_term = f"%{search_input}%"
                    query = query.filter(
                        or_(
                            Employee.first_name.ilike(search_term),
                            Employee.last_name.ilike(search_term),
                            Employee.employee_code.ilike(search_term),
                            func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                        )
                    )
            
            # Get loans
            loans = query.all()
            
            logger.info(f"Found {len(loans)} loans matching filters")
            
            # Build response
            loans_data = []
            total_loan_amount = Decimal('0.00')
            total_outstanding = Decimal('0.00')
            total_paid = Decimal('0.00')
            
            for loan in loans:
                emp = loan.employee
                
                # Calculate interest method display
                interest_method = "Flat" if loan.interest_rate > 0 else "Interest Free"
                
                loan_data = {
                    "id": loan.id,
                    "employee": emp.full_name,
                    "employee_code": emp.employee_code,
                    "designation": emp.designation.name if emp.designation else "N/A",
                    "department": emp.department.name if emp.department else "N/A",
                    "loan_type": loan.loan_type,
                    "loan_amount": float(loan.loan_amount),
                    "issue_date": loan.loan_date.strftime("%d-%b-%Y"),
                    "interest_method": interest_method,
                    "interest_rate": float(loan.interest_rate) if loan.interest_rate else 0.0,
                    "emi_amount": float(loan.emi_amount),
                    "outstanding_amount": float(loan.outstanding_amount),
                    "paid_amount": float(loan.paid_amount),
                    "status": loan.status.value if hasattr(loan.status, 'value') else str(loan.status),
                    "tenure_months": loan.tenure_months,
                    "paid_emis": loan.paid_emis,
                    "remaining_emis": loan.remaining_emis,
                    "purpose": loan.purpose or "",
                    "guarantor_name": loan.guarantor_name or "",
                    "guarantor_relation": loan.guarantor_relation or ""
                }
                
                loans_data.append(loan_data)
                total_loan_amount += Decimal(str(loan.loan_amount))
                total_outstanding += Decimal(str(loan.outstanding_amount))
                total_paid += Decimal(str(loan.paid_amount))
            
            logger.info(f"Returning {len(loans_data)} loans")
            
            return {
                "loans": loans_data,
                "summary": {
                    "total_loans": len(loans_data),
                    "total_loan_amount": float(total_loan_amount),
                    "total_outstanding": float(total_outstanding),
                    "total_paid": float(total_paid)
                },
                "report_type": filters.report_type
            }
            
        except Exception as e:
            logger.error(f"Error generating employee loans report: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to generate employee loans report: {str(e)}")

    def get_loans_list(
        self,
        current_user,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        search: Optional[str] = None,
        employee_id: Optional[int] = None,
        loan_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get loans list with filters - returns ALL employees (with or without loans)
        
        Args:
            current_user: Current authenticated user
            from_date: Filter by loan date from
            to_date: Filter by loan date to
            search: Search term for employee name/code/department
            employee_id: Filter by specific employee
            loan_type: Filter by loan type
            status: Filter by loan status
            page: Page number
            size: Page size
            
        Returns:
            List of loan records (includes employees without loans)
        """
        try:
            from app.models.employee import Employee
            from app.models.datacapture import EmployeeLoan, LoanStatus
            from app.models.designations import Designation
            from app.models.department import Department
            from sqlalchemy import and_, or_, func
            from sqlalchemy.orm import joinedload, outerjoin
            from app.api.v1.endpoints.master_setup import get_user_business_id
            
            logger.info(f"Getting loans list with filters: from_date={from_date}, to_date={to_date}, search={search}")
            
            # Get business ID
            business_id = get_user_business_id(current_user, self.db)
            
            # Base query - get ALL active employees with LEFT JOIN to loans
            query = self.db.query(
                Employee,
                EmployeeLoan
            ).outerjoin(
                EmployeeLoan,
                and_(
                    EmployeeLoan.employee_id == Employee.id,
                    EmployeeLoan.status == LoanStatus.ACTIVE
                )
            ).options(
                joinedload(Employee.designation),
                joinedload(Employee.department)
            ).filter(
                Employee.employee_status == 'ACTIVE'
            )
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            # Apply search filter (searches ALL employees)
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Employee.first_name.ilike(search_term),
                        Employee.last_name.ilike(search_term),
                        Employee.employee_code.ilike(search_term),
                        func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term),
                        Employee.department.has(Department.name.ilike(search_term))
                    )
                )
            
            # Apply employee_id filter
            if employee_id:
                query = query.filter(Employee.id == employee_id)
            
            # Apply date filters (only for employees WITH loans)
            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                    query = query.filter(
                        or_(
                            EmployeeLoan.loan_date >= from_date_obj,
                            EmployeeLoan.loan_date.is_(None)  # Include employees without loans
                        )
                    )
                except ValueError:
                    pass
            
            if to_date:
                try:
                    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
                    query = query.filter(
                        or_(
                            EmployeeLoan.loan_date <= to_date_obj,
                            EmployeeLoan.loan_date.is_(None)  # Include employees without loans
                        )
                    )
                except ValueError:
                    pass
            
            # Apply loan type filter (only affects employees WITH loans)
            if loan_type:
                query = query.filter(
                    or_(
                        EmployeeLoan.loan_type == loan_type,
                        EmployeeLoan.loan_type.is_(None)  # Include employees without loans
                    )
                )
            
            # Apply status filter (only affects employees WITH loans)
            if status:
                query = query.filter(
                    or_(
                        EmployeeLoan.status == LoanStatus[status],
                        EmployeeLoan.status.is_(None)  # Include employees without loans
                    )
                )
            
            # Get results
            results = query.all()
            
            logger.info(f"Found {len(results)} employee-loan records")
            
            # Build response
            loans_data = []
            for employee, loan in results:
                if loan:
                    # Employee HAS a loan
                    interest_method = "Flat" if loan.interest_rate > 0 else "Interest Free"
                    
                    loan_data = {
                        "id": loan.id,
                        "employee_id": employee.id,
                        "employee": employee.full_name,
                        "employee_code": employee.employee_code,
                        "designation": employee.designation.name if employee.designation else "N/A",
                        "department": employee.department.name if employee.department else "N/A",
                        "loan_type": loan.loan_type,
                        "loanAmount": float(loan.loan_amount),
                        "issueDate": loan.loan_date.isoformat() if loan.loan_date else None,
                        "interestMethod": interest_method,
                        "interest_rate": float(loan.interest_rate) if loan.interest_rate else 0.0,
                        "emi_amount": float(loan.emi_amount),
                        "outstanding_amount": float(loan.outstanding_amount),
                        "paid_amount": float(loan.paid_amount),
                        "status": loan.status.value if hasattr(loan.status, 'value') else str(loan.status),
                        "tenure_months": loan.tenure_months,
                        "paid_emis": loan.paid_emis,
                        "remaining_emis": loan.remaining_emis,
                        "has_loans": True
                    }
                else:
                    # Employee does NOT have a loan
                    loan_data = {
                        "id": None,
                        "employee_id": employee.id,
                        "employee": employee.full_name,
                        "employee_code": employee.employee_code,
                        "designation": employee.designation.name if employee.designation else "N/A",
                        "department": employee.department.name if employee.department else "N/A",
                        "loan_type": None,
                        "loanAmount": 0,
                        "issueDate": None,
                        "interestMethod": None,
                        "status": None,
                        "has_loans": False
                    }
                
                loans_data.append(loan_data)
            
            logger.info(f"Returning {len(loans_data)} records (employees with and without loans)")
            
            return loans_data
            
        except Exception as e:
            logger.error(f"Error getting loans list: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to get loans list: {str(e)}")
    
    def get_loan_filters(self, current_user) -> Dict[str, Any]:
        """Get filter options for loans"""
        try:
            from app.models.employee import Employee
            from app.models.datacapture import EmployeeLoan
            from app.models.department import Department
            from app.models.location import Location
            from app.models.business_unit import BusinessUnit
            from sqlalchemy import distinct
            from app.api.v1.endpoints.master_setup import get_user_business_id
            
            business_id = get_user_business_id(current_user, self.db)
            
            # Get unique loan types
            loan_types_query = self.db.query(distinct(EmployeeLoan.loan_type))
            if business_id:
                loan_types_query = loan_types_query.filter(EmployeeLoan.business_id == business_id)
            loan_types = [lt[0] for lt in loan_types_query.all() if lt[0]]
            
            # Get departments
            departments_query = self.db.query(Department.name).filter(Department.is_active == True)
            if business_id:
                departments_query = departments_query.filter(Department.business_id == business_id)
            departments = [d[0] for d in departments_query.all()]
            
            # Get locations
            locations_query = self.db.query(Location.name).filter(Location.is_active == True)
            if business_id:
                locations_query = locations_query.filter(Location.business_id == business_id)
            locations = [l[0] for l in locations_query.all()]
            
            # Get business units
            business_units_query = self.db.query(BusinessUnit.name).filter(BusinessUnit.is_active == True)
            if business_id:
                business_units_query = business_units_query.filter(BusinessUnit.business_id == business_id)
            business_units = [bu[0] for bu in business_units_query.all()]
            
            return {
                "loanTypes": loan_types,
                "departments": departments,
                "locations": locations,
                "businessUnits": business_units,
                "statuses": ["ACTIVE", "COMPLETED", "DEFAULTED", "CANCELLED"]
            }
            
        except Exception as e:
            logger.error(f"Error getting loan filters: {str(e)}")
            return {
                "loanTypes": [],
                "departments": [],
                "locations": [],
                "businessUnits": [],
                "statuses": ["ACTIVE", "COMPLETED", "DEFAULTED", "CANCELLED"]
            }
    
    def search_employees(self, search: str, current_user, limit: int = 10) -> List[Dict[str, Any]]:
        """Search employees for loan assignment"""
        try:
            from app.models.employee import Employee
            from sqlalchemy import or_, func
            from app.api.v1.endpoints.master_setup import get_user_business_id
            
            business_id = get_user_business_id(current_user, self.db)
            
            search_term = f"%{search}%"
            query = self.db.query(Employee).filter(
                Employee.employee_status == 'ACTIVE',
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                )
            )
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employees = query.limit(limit).all()
            
            return [
                {
                    "id": emp.id,
                    "name": emp.full_name,
                    "employee_code": emp.employee_code,
                    "designation": emp.designation.name if emp.designation else "N/A",
                    "department": emp.department.name if emp.department else "N/A"
                }
                for emp in employees
            ]
            
        except Exception as e:
            logger.error(f"Error searching employees: {str(e)}")
            return []

    def get_loan_details(self, loan_id: int, business_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed loan information by ID
        
        Args:
            loan_id: Loan ID
            business_id: Business ID for filtering (optional)
            
        Returns:
            Loan details dictionary or None if not found
        """
        try:
            from app.models.datacapture import EmployeeLoan
            from app.models.employee import Employee
            from sqlalchemy.orm import joinedload
            
            query = self.db.query(EmployeeLoan).options(
                joinedload(EmployeeLoan.employee).joinedload(Employee.designation),
                joinedload(EmployeeLoan.employee).joinedload(Employee.department)
            ).filter(EmployeeLoan.id == loan_id)
            
            if business_id:
                query = query.filter(EmployeeLoan.business_id == business_id)
            
            loan = query.first()
            
            if not loan:
                return None
            
            emp = loan.employee
            interest_method = "Flat" if loan.interest_rate > 0 else "Interest Free"
            
            return {
                "id": loan.id,
                "employee_id": emp.id,
                "employee": emp.full_name,
                "employee_code": emp.employee_code,
                "designation": emp.designation.name if emp.designation else "N/A",
                "department": emp.department.name if emp.department else "N/A",
                "loan_type": loan.loan_type,
                "loan_amount": float(loan.loan_amount),
                "interest_rate": float(loan.interest_rate) if loan.interest_rate else 0.0,
                "tenure_months": loan.tenure_months,
                "emi_amount": float(loan.emi_amount),
                "loan_date": loan.loan_date.isoformat() if loan.loan_date else None,
                "first_emi_date": loan.first_emi_date.isoformat() if loan.first_emi_date else None,
                "last_emi_date": loan.last_emi_date.isoformat() if loan.last_emi_date else None,
                "interest_method": interest_method,
                "outstanding_amount": float(loan.outstanding_amount),
                "paid_amount": float(loan.paid_amount),
                "status": loan.status.value if hasattr(loan.status, 'value') else str(loan.status),
                "paid_emis": loan.paid_emis,
                "remaining_emis": loan.remaining_emis,
                "purpose": loan.purpose or "",
                "guarantor_name": loan.guarantor_name or "",
                "guarantor_relation": loan.guarantor_relation or "",
                "created_at": loan.created_at.isoformat() if loan.created_at else None,
                "updated_at": loan.updated_at.isoformat() if loan.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting loan details: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_loan(
        self,
        loan_data: Dict[str, Any],
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create new loan record
        
        Args:
            loan_data: Loan data dictionary
            business_id: Business ID
            created_by: User ID who created the loan
            
        Returns:
            Created loan details
        """
        try:
            from app.models.datacapture import EmployeeLoan, LoanStatus
            from app.models.employee import Employee
            from decimal import Decimal
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            from app.api.v1.endpoints.master_setup import get_user_business_id
            
            # Validate employee exists
            employee = self.db.query(Employee).filter(
                Employee.id == loan_data['employee_id']
            ).first()
            
            if not employee:
                raise ValueError(f"Employee with ID {loan_data['employee_id']} not found")
            
            # Get business_id from employee if not provided
            if not business_id:
                business_id = employee.business_id
            
            # Calculate EMI amount
            loan_amount = Decimal(str(loan_data['loan_amount']))
            interest_rate = Decimal(str(loan_data.get('interest_rate', 0)))
            tenure_months = int(loan_data['tenure_months'])
            
            if interest_rate > 0:
                # Simple flat interest calculation
                total_interest = (loan_amount * interest_rate * tenure_months) / (100 * 12)
                total_amount = loan_amount + total_interest
                emi_amount = total_amount / tenure_months
            else:
                # Interest-free loan
                emi_amount = loan_amount / tenure_months
            
            # Parse dates
            loan_date = loan_data['loan_date']
            if isinstance(loan_date, str):
                loan_date = datetime.strptime(loan_date, "%Y-%m-%d").date()
            
            first_emi_date = loan_data['first_emi_date']
            if isinstance(first_emi_date, str):
                first_emi_date = datetime.strptime(first_emi_date, "%Y-%m-%d").date()
            
            # Calculate last EMI date
            last_emi_date = first_emi_date + relativedelta(months=tenure_months - 1)
            
            # Create loan record
            new_loan = EmployeeLoan(
                business_id=business_id,
                employee_id=loan_data['employee_id'],
                loan_type=loan_data['loan_type'],
                loan_amount=loan_amount,
                interest_rate=interest_rate,
                tenure_months=tenure_months,
                emi_amount=emi_amount,
                loan_date=loan_date,
                first_emi_date=first_emi_date,
                last_emi_date=last_emi_date,
                status=LoanStatus.ACTIVE,
                outstanding_amount=loan_amount,
                paid_amount=Decimal('0.00'),
                paid_emis=0,
                remaining_emis=tenure_months,
                purpose=loan_data.get('purpose'),
                guarantor_name=loan_data.get('guarantor_name'),
                guarantor_relation=loan_data.get('guarantor_relation'),
                created_by=created_by
            )
            
            self.db.add(new_loan)
            self.db.commit()
            self.db.refresh(new_loan)
            
            logger.info(f"Created loan ID {new_loan.id} for employee {employee.full_name}")
            
            # Return loan details
            return self.get_loan_details(new_loan.id, business_id)
            
        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating loan: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to create loan: {str(e)}")
    
    def update_loan(
        self,
        loan_id: int,
        loan_data: Dict[str, Any],
        business_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update existing loan record
        
        Args:
            loan_id: Loan ID
            loan_data: Updated loan data
            business_id: Business ID for filtering (optional)
            
        Returns:
            Updated loan details or None if not found
        """
        try:
            from app.models.datacapture import EmployeeLoan
            from decimal import Decimal
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            query = self.db.query(EmployeeLoan).filter(EmployeeLoan.id == loan_id)
            
            if business_id:
                query = query.filter(EmployeeLoan.business_id == business_id)
            
            loan = query.first()
            
            if not loan:
                return None
            
            # Update fields
            if 'loan_type' in loan_data:
                loan.loan_type = loan_data['loan_type']
            
            if 'loan_amount' in loan_data:
                loan.loan_amount = Decimal(str(loan_data['loan_amount']))
            
            if 'interest_rate' in loan_data:
                loan.interest_rate = Decimal(str(loan_data['interest_rate']))
            
            if 'tenure_months' in loan_data:
                loan.tenure_months = int(loan_data['tenure_months'])
            
            if 'loan_date' in loan_data:
                loan_date = loan_data['loan_date']
                if isinstance(loan_date, str):
                    loan.loan_date = datetime.strptime(loan_date, "%Y-%m-%d").date()
                else:
                    loan.loan_date = loan_date
            
            if 'first_emi_date' in loan_data:
                first_emi_date = loan_data['first_emi_date']
                if isinstance(first_emi_date, str):
                    loan.first_emi_date = datetime.strptime(first_emi_date, "%Y-%m-%d").date()
                else:
                    loan.first_emi_date = first_emi_date
            
            if 'purpose' in loan_data:
                loan.purpose = loan_data['purpose']
            
            if 'guarantor_name' in loan_data:
                loan.guarantor_name = loan_data['guarantor_name']
            
            if 'guarantor_relation' in loan_data:
                loan.guarantor_relation = loan_data['guarantor_relation']
            
            # Recalculate EMI if amount, interest, or tenure changed
            if any(k in loan_data for k in ['loan_amount', 'interest_rate', 'tenure_months']):
                if loan.interest_rate > 0:
                    total_interest = (loan.loan_amount * loan.interest_rate * loan.tenure_months) / (100 * 12)
                    total_amount = loan.loan_amount + total_interest
                    loan.emi_amount = total_amount / loan.tenure_months
                else:
                    loan.emi_amount = loan.loan_amount / loan.tenure_months
                
                # Recalculate last EMI date
                loan.last_emi_date = loan.first_emi_date + relativedelta(months=loan.tenure_months - 1)
                
                # Update remaining EMIs
                loan.remaining_emis = loan.tenure_months - loan.paid_emis
                
                # Update outstanding amount
                loan.outstanding_amount = loan.loan_amount - loan.paid_amount
            
            loan.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(loan)
            
            logger.info(f"Updated loan ID {loan_id}")
            
            return self.get_loan_details(loan_id, business_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating loan: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to update loan: {str(e)}")
    
    def delete_loan(self, loan_id: int, business_id: Optional[int] = None) -> bool:
        """
        Delete loan record
        
        Args:
            loan_id: Loan ID
            business_id: Business ID for filtering (optional)
            
        Returns:
            True if deleted, False if not found
        """
        try:
            from app.models.datacapture import EmployeeLoan
            
            query = self.db.query(EmployeeLoan).filter(EmployeeLoan.id == loan_id)
            
            if business_id:
                query = query.filter(EmployeeLoan.business_id == business_id)
            
            loan = query.first()
            
            if not loan:
                return False
            
            self.db.delete(loan)
            self.db.commit()
            
            logger.info(f"Deleted loan ID {loan_id}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting loan: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to delete loan: {str(e)}")
    
    def export_loans_csv(
        self,
        current_user,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        search: Optional[str] = None,
        loan_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Export loans to CSV format
        
        Args:
            current_user: Current authenticated user
            from_date: Filter by loan date from
            to_date: Filter by loan date to
            search: Search term
            loan_type: Filter by loan type
            status: Filter by loan status
            
        Returns:
            CSV content as string
        """
        try:
            import csv
            from io import StringIO
            
            # Get loans data (without pagination)
            loans = self.get_loans_list(
                current_user=current_user,
                from_date=from_date,
                to_date=to_date,
                search=search,
                loan_type=loan_type,
                status=status,
                page=1,
                size=10000  # Large number to get all records
            )
            
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Employee Code',
                'Employee Name',
                'Designation',
                'Department',
                'Loan Type',
                'Loan Amount',
                'Issue Date',
                'Interest Method',
                'Interest Rate (%)',
                'EMI Amount',
                'Outstanding Amount',
                'Paid Amount',
                'Status',
                'Tenure (Months)',
                'Paid EMIs',
                'Remaining EMIs'
            ])
            
            # Write data rows
            for loan in loans:
                if loan.get('has_loans', True):  # Only export employees with loans
                    writer.writerow([
                        loan.get('employee_code', ''),
                        loan.get('employee', ''),
                        loan.get('designation', ''),
                        loan.get('department', ''),
                        loan.get('loan_type', ''),
                        loan.get('loanAmount', 0),
                        loan.get('issueDate', ''),
                        loan.get('interestMethod', ''),
                        loan.get('interest_rate', 0),
                        loan.get('emi_amount', 0),
                        loan.get('outstanding_amount', 0),
                        loan.get('paid_amount', 0),
                        loan.get('status', ''),
                        loan.get('tenure_months', 0),
                        loan.get('paid_emis', 0),
                        loan.get('remaining_emis', 0)
                    ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting loans CSV: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to export loans CSV: {str(e)}")
