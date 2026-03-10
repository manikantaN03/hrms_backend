"""
PDF Data Mapper Service
Maps onboarding form data to advanced PDF service format
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PDFDataMapper:
    """Maps database models to PDF service data format"""
    
    @staticmethod
    def map_onboarding_form_to_pdf_data(
        form,
        offer_letter,
        salary_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Map onboarding form and offer letter to PDF data format
        
        Args:
            form: OnboardingForm model instance
            offer_letter: OfferLetter model instance
            salary_data: Optional salary breakdown data
            
        Returns:
            Dictionary formatted for advanced PDF service
        """
        try:
            # Extract candidate details
            candidate_name = form.candidate_name or '[Candidate Name]'
            
            # Get position from offer letter if available
            position = '[Position]'
            joining_date_obj = None
            ctc_value = None
            gross_salary_value = None
            basic_salary_value = None
            
            if offer_letter:
                position = offer_letter.position_title or '[Position]'
                joining_date_obj = offer_letter.joining_date
                
                # Get salary values from offer letter
                if offer_letter.ctc:
                    # CTC might be stored as string like "300000" or "3,00,000"
                    ctc_str = str(offer_letter.ctc).replace(',', '')
                    try:
                        ctc_value = float(ctc_str)
                    except:
                        ctc_value = None
                
                if offer_letter.gross_salary:
                    gross_str = str(offer_letter.gross_salary).replace(',', '')
                    try:
                        gross_salary_value = float(gross_str)
                    except:
                        gross_salary_value = None
                
                if offer_letter.basic_salary:
                    basic_str = str(offer_letter.basic_salary).replace(',', '')
                    try:
                        basic_salary_value = float(basic_str)
                    except:
                        basic_salary_value = None
            
            # Format dates
            offer_date = datetime.now().strftime('%B %d, %Y')
            
            if joining_date_obj:
                joining_date = joining_date_obj.strftime('%B %d, %Y')
            else:
                joining_date = '[Joining Date]'
            
            # Calculate CTC and training salary
            # CTC = Gross Salary * 12 (as per user requirement)
            if gross_salary_value:
                ctc = PDFDataMapper._format_currency(gross_salary_value * 12)
                training_salary = PDFDataMapper._format_currency(gross_salary_value)
            elif ctc_value:
                # If we have CTC but not gross, calculate gross from CTC
                gross_salary_value = ctc_value / 12
                ctc = PDFDataMapper._format_currency(ctc_value)
                training_salary = PDFDataMapper._format_currency(gross_salary_value)
            elif salary_data and salary_data.get('gross_salary'):
                # Use salary_data if available
                gross_salary_value = salary_data.get('gross_salary')
                ctc = PDFDataMapper._format_currency(gross_salary_value * 12)
                training_salary = PDFDataMapper._format_currency(gross_salary_value)
            else:
                # Default fallback
                ctc = '3,00,000'
                training_salary = '17,500'
            
            # Extract notice period (default to 30 days)
            notice_period = '30'
            
            # Build candidate address
            candidate_address = PDFDataMapper._build_address(form)
            
            # Prepare salary breakdown
            if gross_salary_value and not salary_data:
                # Calculate salary breakdown from gross salary
                salary_data = PDFDataMapper._calculate_salary_breakdown(gross_salary_value, basic_salary_value)
            
            salary_breakdown = PDFDataMapper._prepare_salary_breakdown(salary_data) if salary_data else PDFDataMapper._get_default_salary_breakdown()
            
            # Build candidate data dictionary
            candidate_data = {
                'candidate_name': candidate_name,
                'position': position,
                'offer_date': offer_date,
                'joining_date': joining_date,
                'ctc': ctc,
                'training_salary': training_salary,
                'notice_period': notice_period,
                'candidate_address': candidate_address,
                'salary_breakdown': salary_breakdown
            }
            
            logger.info(f"Mapped PDF data for candidate: {candidate_name}, position: {position}, CTC: {ctc}, Training: {training_salary}")
            return candidate_data
            
        except Exception as e:
            logger.error(f"Error mapping PDF data: {e}")
            import traceback
            traceback.print_exc()
            return PDFDataMapper._get_default_candidate_data()
    
    @staticmethod
    def _calculate_salary_breakdown(gross_salary: float, basic_salary: float = None) -> Dict:
        """Calculate salary breakdown from gross salary"""
        try:
            # If basic not provided, calculate as 50% of gross (common practice)
            if not basic_salary:
                basic_salary = gross_salary * 0.50
            
            # Calculate other components (common Indian salary structure)
            hra = basic_salary * 0.40  # 40% of basic
            special_allowance = gross_salary - basic_salary - hra
            
            # Other allowances (can be customized)
            conveyance = 1600
            telephone = 800
            medical = 1250
            
            # Deductions
            employee_pf = basic_salary * 0.12  # 12% of basic
            professional_tax = 200
            
            # Employer contributions
            employer_pf = basic_salary * 0.12
            gratuity = gross_salary * 0.0481  # 4.81% of gross
            
            # Insurance (example)
            group_insurance = 500
            
            # Calculate totals
            total_earnings = gross_salary
            total_deductions = employee_pf + professional_tax
            net_take_home = total_earnings - total_deductions
            total_ctc_monthly = gross_salary + employer_pf + gratuity + group_insurance
            
            return {
                'basic_salary': basic_salary,
                'hra': hra,
                'special_allowance': special_allowance,
                'conveyance_allowance': conveyance,
                'telephone_allowance': telephone,
                'medical_allowance': medical,
                'gross_salary': gross_salary,
                'employee_pf': employee_pf,
                'professional_tax': professional_tax,
                'employer_pf': employer_pf,
                'gratuity': gratuity,
                'group_insurance': group_insurance,
                'net_take_home': net_take_home,
                'total_ctc_monthly': total_ctc_monthly,
                'total_ctc': total_ctc_monthly * 12
            }
        except Exception as e:
            logger.error(f"Error calculating salary breakdown: {e}")
            return None
    
    @staticmethod
    def _prepare_salary_breakdown(salary_data: Dict) -> Dict[str, str]:
        """Prepare salary breakdown from salary calculation data"""
        try:
            if not salary_data:
                return PDFDataMapper._get_default_salary_breakdown()
            
            # Extract components - use actual values from salary_data
            basic = salary_data.get('basic_salary', 0)
            hra = salary_data.get('hra', 0)
            special = salary_data.get('special_allowance', 0)
            medical = salary_data.get('medical_allowance', 0)
            conveyance = salary_data.get('conveyance_allowance', 0)
            telephone = salary_data.get('telephone_allowance', 0)
            gross = salary_data.get('gross_salary', 0)
            
            # Deductions
            employee_pf = salary_data.get('employee_pf', 0)
            professional_tax = salary_data.get('professional_tax', 0)
            
            # Employer contributions
            employer_pf = salary_data.get('employer_pf', 0)
            gratuity = salary_data.get('gratuity', 0)
            group_insurance = salary_data.get('group_insurance', 0)
            
            # Totals
            net_take_home = salary_data.get('net_take_home', gross - employee_pf - professional_tax)
            total_ctc_monthly = salary_data.get('total_ctc_monthly', 0)
            
            return {
                'basic_monthly': PDFDataMapper._format_currency(basic),
                'basic_annual': PDFDataMapper._format_currency(basic * 12),
                'hra_monthly': PDFDataMapper._format_currency(hra),
                'hra_annual': PDFDataMapper._format_currency(hra * 12),
                'special_monthly': PDFDataMapper._format_currency(special),
                'special_annual': PDFDataMapper._format_currency(special * 12),
                'medical_monthly': PDFDataMapper._format_currency(medical),
                'medical_annual': PDFDataMapper._format_currency(medical * 12),
                'conveyance_monthly': PDFDataMapper._format_currency(conveyance),
                'conveyance_annual': PDFDataMapper._format_currency(conveyance * 12),
                'telephone_monthly': PDFDataMapper._format_currency(telephone),
                'telephone_annual': PDFDataMapper._format_currency(telephone * 12),
                'gross_monthly': PDFDataMapper._format_currency(gross),
                'gross_annual': PDFDataMapper._format_currency(gross * 12),
                'employee_pf': PDFDataMapper._format_currency(employee_pf),
                'professional_tax': PDFDataMapper._format_currency(professional_tax),
                'gratuity': PDFDataMapper._format_currency(gratuity),
                'net_take_home': PDFDataMapper._format_currency(net_take_home),
                'employer_pf': PDFDataMapper._format_currency(employer_pf),
                'group_insurance': PDFDataMapper._format_currency(group_insurance),
                'total_ctc_monthly': PDFDataMapper._format_currency(total_ctc_monthly),
            }
        except Exception as e:
            logger.error(f"Error preparing salary breakdown: {e}")
            return PDFDataMapper._get_default_salary_breakdown()
    
    @staticmethod
    def _build_address(form) -> str:
        """Build formatted address from form data"""
        try:
            address_parts = []
            
            # Try to get address from form submission if available
            if hasattr(form, 'submissions') and form.submissions:
                submission = form.submissions[0]  # Get latest submission
                
                # Try present address first
                if hasattr(submission, 'present_address') and submission.present_address:
                    return submission.present_address
                
                # Try permanent address
                if hasattr(submission, 'permanent_address') and submission.permanent_address:
                    return submission.permanent_address
            
            # Fallback: Try to build from form fields (if they exist)
            if hasattr(form, 'current_address') and form.current_address:
                address_parts.append(form.current_address)
            elif hasattr(form, 'permanent_address') and form.permanent_address:
                address_parts.append(form.permanent_address)
            
            # Add city, state, pincode if available
            city = getattr(form, 'city', None)
            state = getattr(form, 'state', None)
            pincode = getattr(form, 'pincode', None)
            
            location_parts = []
            if city:
                location_parts.append(city)
            if state:
                location_parts.append(state)
            if pincode:
                location_parts.append(str(pincode))
            
            if location_parts:
                address_parts.append(', '.join(location_parts))
            
            # Return formatted address or default
            return '\n'.join(address_parts) if address_parts else 'Address'
            
        except Exception as e:
            logger.error(f"Error building address: {e}")
            return 'Address'
    
    @staticmethod
    def _format_currency(amount: float) -> str:
        """Format amount as Indian currency string"""
        try:
            if amount is None:
                return '0'
            
            # Convert to int if whole number
            if isinstance(amount, float) and amount.is_integer():
                amount = int(amount)
            
            # Format with Indian comma style
            amount_str = f"{amount:,.0f}" if isinstance(amount, (int, float)) else str(amount)
            
            # Replace commas with Indian style (lakhs, crores)
            # For simplicity, using standard comma format
            return amount_str.replace(',', ',')
            
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return '0'
    
    @staticmethod
    def _get_default_salary_breakdown() -> Dict[str, str]:
        """Get default salary breakdown"""
        return {
            'basic_monthly': '12,500',
            'basic_annual': '1,50,000',
            'hra_monthly': '3,750',
            'hra_annual': '45,000',
            'special_monthly': '6,250',
            'special_annual': '75,000',
            'medical_monthly': '1,250',
            'medical_annual': '15,000',
            'conveyance_monthly': '750',
            'conveyance_annual': '9,000',
            'telephone_monthly': '500',
            'telephone_annual': '6,000',
            'gross_monthly': '25,000',
            'gross_annual': '3,00,000',
        }
    
    @staticmethod
    def _get_default_candidate_data() -> Dict[str, Any]:
        """Get default candidate data for fallback"""
        return {
            'candidate_name': '[Candidate Name]',
            'position': '[Position]',
            'offer_date': datetime.now().strftime('%B %d, %Y'),
            'joining_date': '[Joining Date]',
            'ctc': '3,00,000',
            'training_salary': '17,500',
            'notice_period': '30',
            'salary_breakdown': PDFDataMapper._get_default_salary_breakdown()
        }


# Create singleton instance
pdf_data_mapper = PDFDataMapper()
