"""
Salary Calculation Service
Handles all salary calculations for offer letters including ESI, PF, PT, IT, LWF
"""

from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.setup.salary_and_deductions.salary_structure import SalaryStructure


class SalaryCalculationService:
    """Service for calculating salary components for offer letters"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_salary_breakup(
        self,
        gross_salary: float,
        salary_structure_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        business_id: int = 1,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete salary breakup for offer letter
        
        Args:
            gross_salary: Gross salary amount
            salary_structure_id: ID of salary structure to use
            employee_id: Employee ID (if existing employee)
            business_id: Business ID for settings
            options: Calculation options (ESI, PF, PT, IT, LWF flags)
        
        Returns:
            Dictionary with salary breakup details
        """
        try:
            # Default options
            if options is None:
                options = {
                    "esi_deduct": True,
                    "pf_deduct": True,
                    "pt_deduct": True,
                    "it_deduct": False,
                    "lwf_deduct": True
                }
            
            # Get salary structure
            salary_structure = None
            if salary_structure_id:
                salary_structure = self.db.query(SalaryStructure).filter(
                    SalaryStructure.id == salary_structure_id,
                    SalaryStructure.business_id == business_id,
                    SalaryStructure.is_active == True
                ).first()
            
            # Calculate earnings
            earnings = self._calculate_earnings(gross_salary, salary_structure)
            
            # Calculate deductions
            deductions = self._calculate_deductions(
                gross_salary, 
                earnings, 
                business_id, 
                options
            )
            
            # Calculate totals
            total_earnings = sum(earnings.values())
            total_deductions = sum(deductions.values())
            net_salary = total_earnings - total_deductions
            
            # Calculate CTC (including employer contributions)
            employer_contributions = self._calculate_employer_contributions(
                earnings, business_id, options
            )
            ctc = total_earnings + sum(employer_contributions.values())
            
            return {
                "success": True,
                "gross_salary": gross_salary,
                "earnings": earnings,
                "deductions": deductions,
                "employer_contributions": employer_contributions,
                "total_earnings": round(total_earnings, 2),
                "total_deductions": round(total_deductions, 2),
                "net_salary": round(net_salary, 2),
                "ctc": round(ctc, 2),
                "salary_structure_id": salary_structure_id,
                "salary_structure_name": salary_structure.name if salary_structure else "Default"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "gross_salary": gross_salary
            }
    
    def _calculate_earnings(
        self, 
        gross_salary: float, 
        salary_structure: Optional[SalaryStructure] = None
    ) -> Dict[str, float]:
        """Calculate earning components"""
        
        # For now, use default salary structure since SalaryStructureRule doesn't exist
        # Default salary structure (standard Indian payroll)
        basic_salary = gross_salary * 0.50  # 50% of gross
        hra = gross_salary * 0.15  # 15% of gross
        special_allowance = gross_salary * 0.25  # 25% of gross
        medical_allowance = min(1250, gross_salary * 0.05)  # 5% or 1250, whichever is lower
        conveyance_allowance = min(1600, gross_salary * 0.03)  # 3% or 1600, whichever is lower
        telephone_allowance = min(800, gross_salary * 0.02)  # 2% or 800, whichever is lower
        
        # Adjust special allowance to match gross salary
        calculated_total = basic_salary + hra + special_allowance + medical_allowance + conveyance_allowance + telephone_allowance
        if calculated_total != gross_salary:
            special_allowance += (gross_salary - calculated_total)
        
        return {
            "Basic Salary": round(basic_salary, 2),
            "House Rent Allowance": round(hra, 2),
            "Special Allowance": round(special_allowance, 2),
            "Medical Allowance": round(medical_allowance, 2),
            "Conveyance Allowance": round(conveyance_allowance, 2),
            "Telephone Allowance": round(telephone_allowance, 2)
        }
    
    def _calculate_deductions(
        self, 
        gross_salary: float, 
        earnings: Dict[str, float], 
        business_id: int, 
        options: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate deduction components"""
        
        deductions = {}
        basic_salary = earnings.get("Basic Salary", gross_salary * 0.50)
        
        # ESI Deduction
        if options.get("esi_deduct", True):
            esi_amount = self._calculate_esi_deduction(gross_salary, business_id)
            if esi_amount > 0:
                deductions["ESI Deduction"] = esi_amount
        
        # PF Deduction
        if options.get("pf_deduct", True):
            pf_amount = self._calculate_pf_deduction(basic_salary, business_id)
            if pf_amount > 0:
                deductions["PF Deduction"] = pf_amount
        
        # Professional Tax
        if options.get("pt_deduct", True):
            pt_amount = self._calculate_professional_tax(gross_salary, business_id)
            if pt_amount > 0:
                deductions["Professional Tax"] = pt_amount
        
        # Income Tax (if applicable)
        if options.get("it_deduct", False):
            it_amount = self._calculate_income_tax(gross_salary, business_id)
            if it_amount > 0:
                deductions["Income Tax"] = it_amount
        
        # Labour Welfare Fund
        if options.get("lwf_deduct", True):
            lwf_amount = self._calculate_lwf_deduction(gross_salary, business_id)
            if lwf_amount > 0:
                deductions["Labour Welfare Fund"] = lwf_amount
        
        return deductions
    
    def _calculate_employer_contributions(
        self, 
        earnings: Dict[str, float], 
        business_id: int, 
        options: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate employer contributions for CTC"""
        
        contributions = {}
        basic_salary = earnings.get("Basic Salary", 0)
        
        # Employer PF Contribution
        if options.get("pf_deduct", True):
            pf_contribution = self._calculate_employer_pf_contribution(basic_salary, business_id)
            if pf_contribution > 0:
                contributions["Employer PF Contribution"] = pf_contribution
        
        # Employer ESI Contribution
        if options.get("esi_deduct", True):
            esi_contribution = self._calculate_employer_esi_contribution(sum(earnings.values()), business_id)
            if esi_contribution > 0:
                contributions["Employer ESI Contribution"] = esi_contribution
        
        # Gratuity (monthly provision)
        gratuity_annual = basic_salary * 12 * 0.0481  # 4.81% of annual basic
        gratuity_monthly = gratuity_annual / 12  # Convert to monthly
        contributions["Gratuity (Monthly)"] = round(gratuity_monthly, 2)
        
        return contributions
    
    def _calculate_esi_deduction(self, gross_salary: float, business_id: int) -> float:
        """Calculate ESI deduction"""
        try:
            # Default ESI calculation
            if gross_salary <= 21000:  # ESI limit
                return round(gross_salary * 0.75 / 100, 2)  # 0.75% employee contribution
            
            return 0
            
        except Exception:
            return 0
    
    def _calculate_pf_deduction(self, basic_salary: float, business_id: int) -> float:
        """Calculate PF deduction"""
        try:
            # Default PF calculation
            pf_basic = min(basic_salary, 15000)  # PF ceiling
            return round(pf_basic * 12 / 100, 2)  # 12% employee contribution
            
        except Exception:
            return 0
    
    def _calculate_professional_tax(self, gross_salary: float, business_id: int) -> float:
        """Calculate Professional Tax"""
        try:
            # For now, use default PT calculation since the model structure is complex
            # Default PT calculation (Maharashtra rates)
            if gross_salary <= 5000:
                return 0
            elif gross_salary <= 10000:
                return 150
            elif gross_salary <= 15000:
                return 300
            else:
                return 200  # Standard rate
                
        except Exception:
            return 200  # Default PT
    
    def _calculate_income_tax(self, gross_salary: float, business_id: int) -> float:
        """Calculate Income Tax (basic calculation)"""
        try:
            annual_salary = gross_salary * 12
            
            # Basic IT calculation (old regime)
            if annual_salary <= 250000:
                return 0
            elif annual_salary <= 500000:
                monthly_tax = ((annual_salary - 250000) * 0.05) / 12
            elif annual_salary <= 1000000:
                monthly_tax = (12500 + (annual_salary - 500000) * 0.20) / 12
            else:
                monthly_tax = (112500 + (annual_salary - 1000000) * 0.30) / 12
            
            return round(monthly_tax, 2)
            
        except Exception:
            return 0
    
    def _calculate_lwf_deduction(self, gross_salary: float, business_id: int) -> float:
        """Calculate Labour Welfare Fund deduction"""
        try:
            # Default LWF (Maharashtra)
            if gross_salary >= 3000:
                return 0.75  # Employee contribution
            
            return 0
            
        except Exception:
            return 0
    
    def _calculate_employer_pf_contribution(self, basic_salary: float, business_id: int) -> float:
        """Calculate employer PF contribution"""
        try:
            # Default employer PF
            pf_basic = min(basic_salary, 15000)
            return round(pf_basic * 12 / 100, 2)  # 12% employer contribution
            
        except Exception:
            return 0
    
    def _calculate_employer_esi_contribution(self, gross_salary: float, business_id: int) -> float:
        """Calculate employer ESI contribution"""
        try:
            # Default employer ESI
            if gross_salary <= 21000:
                return round(gross_salary * 3.25 / 100, 2)  # 3.25% employer contribution
            
            return 0
            
        except Exception:
            return 0
    
    def get_salary_structures(self, business_id: int) -> list:
        """Get available salary structures for business"""
        try:
            structures = self.db.query(SalaryStructure).filter(
                SalaryStructure.business_id == business_id,
                SalaryStructure.is_active == True
            ).order_by(SalaryStructure.name).all()
            
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "is_default": s.is_default
                }
                for s in structures
            ]
            
        except Exception:
            return []