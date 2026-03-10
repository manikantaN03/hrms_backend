"""
IT Declaration Repository
Handles database operations for employee IT declarations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, extract
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.datacapture import ITDeclaration, ITDeclarationStatus
from app.models.employee import Employee
from app.models.business import Business


class ITDeclarationRepository:
    """Repository for IT declaration database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_declarations_with_filters(
        self,
        business_id: Optional[int] = None,
        financial_year: Optional[str] = None,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get IT declarations with filters and pagination"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        
        query = self.db.query(ITDeclaration).join(Employee, ITDeclaration.employee_id == Employee.id)
        
        # Left join with Department and Designation for search
        query = query.outerjoin(Department, Employee.department_id == Department.id)
        query = query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        # Apply financial year filter
        if financial_year:
            query = query.filter(ITDeclaration.financial_year == financial_year)
        
        # Apply employee filter
        if employee_id:
            query = query.filter(ITDeclaration.employee_id == employee_id)
        
        # Apply status filter
        if status:
            query = query.filter(ITDeclaration.status == status)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
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
        results = query.order_by(desc(ITDeclaration.created_at)).offset(offset).limit(size).all()
        
        # Format results
        declarations = []
        for declaration in results:
            employee = declaration.employee
            full_name = f"{employee.first_name} {employee.last_name}".strip()
            declarations.append({
                'id': declaration.id,
                'employee_id': declaration.employee_id,
                'employee_name': full_name,
                'employee_code': employee.employee_code,
                'designation': employee.designation.name if employee.designation else 'N/A',
                'department': employee.department.name if employee.department else 'N/A',
                'financial_year': declaration.financial_year,
                'status': declaration.status.value,
                'total_80c': float(declaration.total_80c),
                'pf_amount': float(declaration.pf_amount),
                'life_insurance': float(declaration.life_insurance),
                'elss_mutual_funds': float(declaration.elss_mutual_funds),
                'home_loan_principal': float(declaration.home_loan_principal),
                'tuition_fees': float(declaration.tuition_fees),
                'other_80c': float(declaration.other_80c),
                'section_80d_medical': float(declaration.section_80d_medical),
                'section_24_home_loan_interest': float(declaration.section_24_home_loan_interest),
                'section_80g_donations': float(declaration.section_80g_donations),
                'hra_exemption': float(declaration.hra_exemption),
                'rent_paid': float(declaration.rent_paid),
                'landlord_name': declaration.landlord_name,
                'landlord_pan': declaration.landlord_pan,
                'submitted_at': declaration.submitted_at.isoformat() if declaration.submitted_at else None,
                'created_at': declaration.created_at.isoformat() if declaration.created_at else None
            })
        
        return declarations
    
    def get_declaration_by_id(self, declaration_id: int, business_id: Optional[int] = None) -> Optional[ITDeclaration]:
        """Get IT declaration by ID"""
        query = self.db.query(ITDeclaration).filter(ITDeclaration.id == declaration_id)
        
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        return query.first()
    
    def get_declaration_by_employee_year(
        self, 
        employee_id: int, 
        financial_year: str, 
        business_id: Optional[int] = None
    ) -> Optional[ITDeclaration]:
        """Get IT declaration by employee and financial year"""
        query = self.db.query(ITDeclaration).filter(
            ITDeclaration.employee_id == employee_id,
            ITDeclaration.financial_year == financial_year
        )
        
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        return query.first()
    
    def create_declaration(self, declaration_data: Dict[str, Any]) -> ITDeclaration:
        """Create new IT declaration"""
        declaration = ITDeclaration(**declaration_data)
        self.db.add(declaration)
        self.db.commit()
        self.db.refresh(declaration)
        return declaration
    
    def update_declaration(
        self, 
        declaration_id: int, 
        declaration_data: Dict[str, Any], 
        business_id: Optional[int] = None
    ) -> Optional[ITDeclaration]:
        """Update existing IT declaration"""
        query = self.db.query(ITDeclaration).filter(ITDeclaration.id == declaration_id)
        
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        declaration = query.first()
        if declaration:
            for key, value in declaration_data.items():
                if hasattr(declaration, key):
                    setattr(declaration, key, value)
            
            # Recalculate total_80c
            declaration.total_80c = (
                declaration.pf_amount + 
                declaration.life_insurance + 
                declaration.elss_mutual_funds + 
                declaration.home_loan_principal + 
                declaration.tuition_fees + 
                declaration.other_80c
            )
            
            self.db.commit()
            self.db.refresh(declaration)
        
        return declaration
    
    def delete_declaration(self, declaration_id: int, business_id: Optional[int] = None) -> bool:
        """Delete IT declaration"""
        query = self.db.query(ITDeclaration).filter(ITDeclaration.id == declaration_id)
        
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        declaration = query.first()
        if declaration:
            self.db.delete(declaration)
            self.db.commit()
            return True
        
        return False
    
    def get_total_count(
        self,
        business_id: Optional[int] = None,
        financial_year: Optional[str] = None,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """Get total count of IT declarations with filters"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        
        query = self.db.query(ITDeclaration).join(Employee, ITDeclaration.employee_id == Employee.id)
        
        # Left join with Department and Designation for search
        query = query.outerjoin(Department, Employee.department_id == Department.id)
        query = query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        # Apply financial year filter
        if financial_year:
            query = query.filter(ITDeclaration.financial_year == financial_year)
        
        # Apply employee filter
        if employee_id:
            query = query.filter(ITDeclaration.employee_id == employee_id)
        
        # Apply status filter
        if status:
            query = query.filter(ITDeclaration.status == status)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    Department.name.ilike(search_term),
                    Designation.name.ilike(search_term)
                )
            )
        
        return query.count()
    
    def get_financial_years(self, current_user = None) -> List[str]:
        """Get distinct financial years"""
        
        # Import here to avoid circular imports
        from app.utils.business_unit_utils import get_user_business_context
        
        query = self.db.query(ITDeclaration.financial_year).distinct()
        
        # Determine business context
        if current_user:
            is_superadmin, user_business_id = get_user_business_context(current_user, self.db)
            if not is_superadmin and user_business_id:
                query = query.filter(ITDeclaration.business_id == user_business_id)
        
        return [row[0] for row in query.all() if row[0]]
    
    def get_employee_declarations(self, employee_id: int, business_id: Optional[int] = None) -> List[ITDeclaration]:
        """Get all IT declarations for a specific employee"""
        query = self.db.query(ITDeclaration).filter(ITDeclaration.employee_id == employee_id)
        
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        return query.order_by(desc(ITDeclaration.financial_year)).all()
    
    def search_all_employees_with_declaration_status(
        self,
        business_id: Optional[int] = None,
        financial_year: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Search ALL employees and show their IT declaration status"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        
        # Base query for all employees
        query = self.db.query(Employee)
        
        # Left join with Department and Designation
        query = query.outerjoin(Department, Employee.department_id == Department.id)
        query = query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
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
        employees = query.order_by(Employee.employee_code).offset(offset).limit(size).all()
        
        # Get IT declarations for these employees
        employee_ids = [emp.id for emp in employees]
        declarations_query = self.db.query(ITDeclaration).filter(
            ITDeclaration.employee_id.in_(employee_ids)
        )
        
        if financial_year:
            declarations_query = declarations_query.filter(ITDeclaration.financial_year == financial_year)
        
        declarations = declarations_query.all()
        
        # Create a mapping of employee_id to declaration
        declaration_map = {}
        for declaration in declarations:
            key = f"{declaration.employee_id}_{declaration.financial_year}"
            declaration_map[key] = declaration
        
        # Format results
        results = []
        for employee in employees:
            full_name = f"{employee.first_name} {employee.last_name}".strip()
            
            # Check if employee has declaration for the financial year
            declaration_key = f"{employee.id}_{financial_year}" if financial_year else None
            declaration = declaration_map.get(declaration_key) if declaration_key else None
            
            if declaration:
                # Employee has IT declaration
                results.append({
                    'id': declaration.id,
                    'employee_id': employee.id,
                    'employee_name': full_name,
                    'employee_code': employee.employee_code,
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'department': employee.department.name if employee.department else 'N/A',
                    'financial_year': declaration.financial_year,
                    'status': declaration.status.value,
                    'total_80c': float(declaration.total_80c),
                    'pf_amount': float(declaration.pf_amount),
                    'life_insurance': float(declaration.life_insurance),
                    'elss_mutual_funds': float(declaration.elss_mutual_funds),
                    'home_loan_principal': float(declaration.home_loan_principal),
                    'tuition_fees': float(declaration.tuition_fees),
                    'other_80c': float(declaration.other_80c),
                    'section_80d_medical': float(declaration.section_80d_medical),
                    'section_24_home_loan_interest': float(declaration.section_24_home_loan_interest),
                    'section_80g_donations': float(declaration.section_80g_donations),
                    'hra_exemption': float(declaration.hra_exemption),
                    'rent_paid': float(declaration.rent_paid),
                    'landlord_name': declaration.landlord_name,
                    'landlord_pan': declaration.landlord_pan,
                    'submitted_at': declaration.submitted_at.isoformat() if declaration.submitted_at else None,
                    'created_at': declaration.created_at.isoformat() if declaration.created_at else None,
                    'has_declaration': True
                })
            else:
                # Employee has no IT declaration
                results.append({
                    'id': None,
                    'employee_id': employee.id,
                    'employee_name': full_name,
                    'employee_code': employee.employee_code,
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'department': employee.department.name if employee.department else 'N/A',
                    'financial_year': financial_year or 'N/A',
                    'status': 'No Declaration',
                    'total_80c': 0.0,
                    'pf_amount': 0.0,
                    'life_insurance': 0.0,
                    'elss_mutual_funds': 0.0,
                    'home_loan_principal': 0.0,
                    'tuition_fees': 0.0,
                    'other_80c': 0.0,
                    'section_80d_medical': 0.0,
                    'section_24_home_loan_interest': 0.0,
                    'section_80g_donations': 0.0,
                    'hra_exemption': 0.0,
                    'rent_paid': 0.0,
                    'landlord_name': None,
                    'landlord_pan': None,
                    'submitted_at': None,
                    'created_at': None,
                    'has_declaration': False
                })
        
        return results
    
    def get_all_employees_count_with_declaration_status(
        self,
        business_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> int:
        """Get total count of ALL employees for search"""
        
        from app.models.department import Department
        from app.models.designations import Designation
        
        # Base query for all employees
        query = self.db.query(Employee)
        
        # Left join with Department and Designation
        query = query.outerjoin(Department, Employee.department_id == Department.id)
        query = query.outerjoin(Designation, Employee.designation_id == Designation.id)
        
        # Apply business filter
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    Department.name.ilike(search_term),
                    Designation.name.ilike(search_term)
                )
            )
        
        return query.count()

    def get_declarations_summary(self, business_id: Optional[int] = None, financial_year: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of IT declarations"""
        query = self.db.query(ITDeclaration)
        
        if business_id:
            query = query.filter(ITDeclaration.business_id == business_id)
        
        if financial_year:
            query = query.filter(ITDeclaration.financial_year == financial_year)
        
        declarations = query.all()
        
        total_declarations = len(declarations)
        draft_count = len([d for d in declarations if d.status == ITDeclarationStatus.DRAFT])
        submitted_count = len([d for d in declarations if d.status == ITDeclarationStatus.SUBMITTED])
        approved_count = len([d for d in declarations if d.status == ITDeclarationStatus.APPROVED])
        
        total_80c_amount = sum(float(d.total_80c) for d in declarations)
        total_hra_amount = sum(float(d.hra_exemption) for d in declarations)
        
        return {
            'total_declarations': total_declarations,
            'draft_count': draft_count,
            'submitted_count': submitted_count,
            'approved_count': approved_count,
            'total_80c_amount': total_80c_amount,
            'total_hra_amount': total_hra_amount
        }