"""
IT Declaration Service
Business logic for employee IT declaration management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.repositories.it_declaration_repository import ITDeclarationRepository
from app.repositories.employee_repository import EmployeeRepository
from app.models.datacapture import ITDeclaration, ITDeclarationStatus
from app.models.employee import Employee


class ITDeclarationService:
    """Service for IT declaration business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.it_declaration_repo = ITDeclarationRepository(db)
        self.employee_repo = EmployeeRepository(db)
    
    def get_declarations_list(
        self,
        business_id: Optional[int] = None,
        financial_year: Optional[str] = None,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get IT declarations list with filters"""
        
        # If only search is provided (no other filters), search ALL employees
        if search and not any([financial_year, employee_id, status]):
            return self.it_declaration_repo.search_all_employees_with_declaration_status(
                business_id=business_id,
                financial_year=financial_year,
                search=search,
                page=page,
                size=size
            )
        
        return self.it_declaration_repo.get_declarations_with_filters(
            business_id=business_id,
            financial_year=financial_year,
            employee_id=employee_id,
            status=status,
            search=search,
            page=page,
            size=size
        )
    
    def get_declarations_total_count(
        self,
        business_id: Optional[int] = None,
        financial_year: Optional[str] = None,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """Get total count of IT declarations with filters"""
        
        # If only search is provided (no other filters), count ALL employees
        if search and not any([financial_year, employee_id, status]):
            return self.it_declaration_repo.get_all_employees_count_with_declaration_status(
                business_id=business_id,
                search=search
            )
        
        return self.it_declaration_repo.get_total_count(
            business_id=business_id,
            financial_year=financial_year,
            employee_id=employee_id,
            status=status,
            search=search
        )
    
    def get_declaration_filters(self, current_user = None) -> Dict[str, Any]:
        """Get filter options for IT declarations"""
        
        # Get employees using search method
        employee_search_result = self.employee_repo.search_employees(
            current_user=current_user,
            employee_status="active",
            limit=50
        )
        employees = employee_search_result.get('items', [])
        
        # Get financial years
        financial_years = self.it_declaration_repo.get_financial_years(current_user=current_user)
        
        # Default financial years if none exist
        if not financial_years:
            current_year = datetime.now().year
            financial_years = [
                f"{current_year-2}-{str(current_year-1)[2:]}",
                f"{current_year-1}-{str(current_year)[2:]}",
                f"{current_year}-{str(current_year+1)[2:]}",
                f"{current_year+1}-{str(current_year+2)[2:]}"
            ]
        
        # Get unique departments and locations from employees
        departments = list(set([emp.department.name if emp.department else None for emp in employees if emp.department]))
        locations = list(set([emp.location.name if emp.location else None for emp in employees if emp.location]))
        
        return {
            'employees': [
                {
                    'id': emp.id,
                    'name': f"{emp.first_name} {emp.last_name}".strip(),
                    'employee_code': emp.employee_code,
                    'designation': emp.designation.name if emp.designation else 'N/A',
                    'department': emp.department.name if emp.department else 'N/A'
                }
                for emp in employees
            ],
            'financialYears': sorted(financial_years, reverse=True),
            'departments': sorted([d for d in departments if d]),
            'locations': sorted([l for l in locations if l]),
            'statuses': ['draft', 'submitted', 'approved', 'rejected']
        }
    
    def search_employees(self, search: str, current_user = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search employees for IT declaration assignment"""
        
        employee_search_result = self.employee_repo.search_employees(
            query=search,
            current_user=current_user,
            employee_status="active",
            limit=limit
        )
        employees = employee_search_result.get('items', [])
        
        return [
            {
                'id': emp.id,
                'name': f"{emp.first_name} {emp.last_name}".strip(),
                'employee_code': emp.employee_code,
                'designation': emp.designation.name if emp.designation else 'N/A',
                'department': emp.department.name if emp.department else 'N/A'
            }
            for emp in employees
        ]
    
    def get_employee_declaration(
        self, 
        employee_id: int, 
        financial_year: str, 
        business_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get or create IT declaration for employee and financial year"""
        
        # Check if employee exists
        employee = self.employee_repo.get(employee_id)
        if not employee or (business_id and employee.business_id != business_id):
            raise ValueError("Employee not found")
        
        # Use employee's business_id if not provided
        if not business_id:
            business_id = employee.business_id
        
        # Try to get existing declaration
        declaration = self.it_declaration_repo.get_declaration_by_employee_year(
            employee_id, financial_year, business_id
        )
        
        # Create new declaration if not exists
        if not declaration:
            declaration_data = {
                'business_id': business_id,
                'employee_id': employee_id,
                'financial_year': financial_year,
                'status': ITDeclarationStatus.DRAFT,
                'pf_amount': Decimal('0'),
                'life_insurance': Decimal('0'),
                'elss_mutual_funds': Decimal('0'),
                'home_loan_principal': Decimal('0'),
                'tuition_fees': Decimal('0'),
                'other_80c': Decimal('0'),
                'total_80c': Decimal('0'),
                'section_80d_medical': Decimal('0'),
                'section_24_home_loan_interest': Decimal('0'),
                'section_80g_donations': Decimal('0'),
                'hra_exemption': Decimal('0'),
                'rent_paid': Decimal('0')
            }
            declaration = self.it_declaration_repo.create_declaration(declaration_data)
        
        return {
            'id': declaration.id,
            'employee_id': declaration.employee_id,
            'employee_name': f"{employee.first_name} {employee.last_name}".strip(),
            'employee_code': employee.employee_code,
            'designation': employee.designation.name if employee.designation else 'N/A',
            'department': employee.department.name if employee.department else 'N/A',
            'financial_year': declaration.financial_year,
            'status': declaration.status.value,
            'pf_amount': float(declaration.pf_amount),
            'life_insurance': float(declaration.life_insurance),
            'elss_mutual_funds': float(declaration.elss_mutual_funds),
            'home_loan_principal': float(declaration.home_loan_principal),
            'tuition_fees': float(declaration.tuition_fees),
            'other_80c': float(declaration.other_80c),
            'total_80c': float(declaration.total_80c),
            'section_80d_medical': float(declaration.section_80d_medical),
            'section_24_home_loan_interest': float(declaration.section_24_home_loan_interest),
            'section_80g_donations': float(declaration.section_80g_donations),
            'hra_exemption': float(declaration.hra_exemption),
            'rent_paid': float(declaration.rent_paid),
            'landlord_name': declaration.landlord_name,
            'landlord_pan': declaration.landlord_pan,
            'submitted_at': declaration.submitted_at.isoformat() if declaration.submitted_at else None,
            'created_at': declaration.created_at.isoformat() if declaration.created_at else None
        }
    
    def update_declaration_field(
        self,
        employee_id: int,
        financial_year: str,
        field_name: str,
        field_value: Any,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update a specific field in IT declaration"""
        
        # Get or create declaration
        declaration_data = self.get_employee_declaration(employee_id, financial_year, business_id)
        declaration_id = declaration_data['id']
        
        # Convert field_value to Decimal if it's a numeric field
        numeric_fields = [
            'pf_amount', 'life_insurance', 'elss_mutual_funds', 'home_loan_principal',
            'tuition_fees', 'other_80c', 'section_80d_medical', 'section_24_home_loan_interest',
            'section_80g_donations', 'hra_exemption', 'rent_paid'
        ]
        
        if field_name in numeric_fields and isinstance(field_value, (int, float)):
            field_value = Decimal(str(field_value))
        
        # Prepare update data
        update_data = {field_name: field_value}
        
        # Update declaration
        declaration = self.it_declaration_repo.update_declaration(
            declaration_id, update_data, business_id
        )
        
        if not declaration:
            raise ValueError("Declaration not found")
        
        employee = self.employee_repo.get(employee_id)
        
        return {
            'id': declaration.id,
            'employee_id': declaration.employee_id,
            'employee_name': f"{employee.first_name} {employee.last_name}".strip(),
            'employee_code': employee.employee_code,
            'field_name': field_name,
            'field_value': field_value,
            'total_80c': float(declaration.total_80c),
            'status': declaration.status.value,
            'message': f"Successfully updated {field_name}"
        }
    
    def submit_declaration(
        self,
        employee_id: int,
        financial_year: str,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Submit IT declaration for approval"""
        
        # Get declaration
        declaration = self.it_declaration_repo.get_declaration_by_employee_year(
            employee_id, financial_year, business_id
        )
        
        if not declaration:
            raise ValueError("Declaration not found")
        
        if declaration.status != ITDeclarationStatus.DRAFT:
            raise ValueError("Only draft declarations can be submitted")
        
        # Update status and submission date
        update_data = {
            'status': ITDeclarationStatus.SUBMITTED,
            'submitted_at': datetime.now()
        }
        
        declaration = self.it_declaration_repo.update_declaration(
            declaration.id, update_data, business_id
        )
        
        employee = self.employee_repo.get(employee_id)
        
        return {
            'id': declaration.id,
            'employee_name': f"{employee.first_name} {employee.last_name}".strip(),
            'financial_year': declaration.financial_year,
            'status': declaration.status.value,
            'submitted_at': declaration.submitted_at.isoformat(),
            'message': "Declaration submitted successfully"
        }
    
    def get_deduction_limits(self, financial_year: str) -> Dict[str, Any]:
        """Get deduction limits for a financial year"""
        
        # Standard deduction limits (can be made configurable)
        limits = {
            "80C - Children Education Expenses": 150000,
            "80C - Employee Provident Fund": 150000,
            "80C - Housing Loan Principal Repayment": 150000,
            "80C - Insurance Premium": 150000,
            "80C - Mutual Funds": 150000,
            "80C - National Savings Certificate": 150000,
            "80C - Others like Sukanya Samriddhi etc.": 150000,
            "80C - Public Provident Fund": 150000,
            "80CCC - Contribution to Certain Pension Funds": 150000,
            "80CCD (1) - Contribution to National Pension Scheme": 150000,
            "80CCD (1B) - Contribution to National Pension Scheme": 50000,
            "80CCD (2) - Employer's contribution to NPS": 150000,
            "80CCG - Rajiv Gandhi Equity Savings Scheme": 50000,
            "80CCN - Contributions to the Agriwaver Corpus Fund": "No Limit",
            "80D - Medical Insurance (Self/Spouse/Children - Non Senior)": 25000,
            "80D - Medical Insurance (Parents - Non Senior Citizen)": 25000
        }
        
        return {
            'financial_year': financial_year,
            'deduction_limits': limits,
            'total_80c_limit': 150000,
            'nps_additional_limit': 50000
        }
    
    def export_declarations_csv(
        self, 
        business_id: Optional[int] = None, 
        financial_year: Optional[str] = None,
        **filters
    ) -> str:
        """Export IT declarations to CSV format"""
        
        declarations = self.get_declarations_list(
            business_id=business_id, 
            financial_year=financial_year,
            page=1, 
            size=1000, 
            **filters
        )
        
        csv_content = "Employee Code,Employee Name,Designation,Department,Financial Year,Status,Total 80C,PF Amount,Life Insurance,ELSS,Home Loan Principal,Tuition Fees,Other 80C,Medical Insurance,Home Loan Interest,Donations,HRA Exemption,Rent Paid,Submitted At\n"
        
        for declaration in declarations:
            csv_content += f"{declaration['employee_code']},{declaration['employee_name']},{declaration['designation']},{declaration['department']},{declaration['financial_year']},{declaration['status']},{declaration['total_80c']},{declaration['pf_amount']},{declaration['life_insurance']},{declaration['elss_mutual_funds']},{declaration['home_loan_principal']},{declaration['tuition_fees']},{declaration['other_80c']},{declaration['section_80d_medical']},{declaration['section_24_home_loan_interest']},{declaration['section_80g_donations']},{declaration['hra_exemption']},{declaration['rent_paid']},{declaration['submitted_at'] or 'Not Submitted'}\n"
        
        return csv_content
    
    def get_declarations_summary(self, business_id: Optional[int] = None, financial_year: Optional[str] = None) -> Dict[str, Any]:
        """Get IT declarations summary statistics"""
        return self.it_declaration_repo.get_declarations_summary(business_id, financial_year)