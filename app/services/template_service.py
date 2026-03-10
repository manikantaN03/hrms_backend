"""
Template Processing Service for HR Letters
Handles dynamic field replacement in letter templates
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.business import Business
from app.models.business_info import BusinessInformation


class TemplateService:
    """Service for processing letter templates with dynamic field codes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_template(
        self, 
        template_content: str, 
        employee_id: int, 
        business_id: int,
        letter_date: Optional[date] = None
    ) -> str:
        """
        Process template content by replacing dynamic field codes with actual values
        
        Args:
            template_content: Template string with {field_name} placeholders
            employee_id: ID of the employee for the letter
            business_id: ID of the business
            letter_date: Date of the letter (defaults to today)
            
        Returns:
            Processed content with field codes replaced
        """
        if not template_content:
            return template_content
        
        try:
            # Get employee data
            employee_data = self._get_employee_data(employee_id)
            
            # Get business data
            business_data = self._get_business_data(business_id)
            
            # Get date data
            date_data = self._get_date_data(letter_date)
            
            # Combine all data
            field_data = {**employee_data, **business_data, **date_data}
            
            # Replace field codes in template
            processed_content = self._replace_field_codes(template_content, field_data)
            
            return processed_content
            
        except Exception as e:
            # If processing fails, return original template with error note
            return f"{template_content}\n\n[Template processing error: {str(e)}]"
    
    def _get_employee_data(self, employee_id: int) -> Dict[str, str]:
        """Get employee-related field data"""
        try:
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
            
            if not employee:
                return {
                    'employee_name': '[Employee Not Found]',
                    'employee_code': '[Code Not Found]',
                    'department': '[Department Not Found]',
                    'designation': '[Designation Not Found]'
                }
            
            # Get full name
            full_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
            if not full_name:
                full_name = '[Name Not Available]'
            
            return {
                'employee_name': full_name,
                'employee_code': employee.employee_code or '[Code Not Set]',
                'department': employee.department or '[Department Not Set]',
                'designation': employee.designation or '[Designation Not Set]'
            }
        except Exception as e:
            # Return fallback values if database query fails
            return {
                'employee_name': '[Employee Data Error]',
                'employee_code': '[Code Error]',
                'department': '[Department Error]',
                'designation': '[Designation Error]'
            }
    
    def _get_business_data(self, business_id: int) -> Dict[str, str]:
        """Get business-related field data"""
        try:
            business = self.db.query(Business).filter(Business.id == business_id).first()
            
            if not business:
                return {
                    'report_title': '[Business Not Found]',
                    'report_header_1': '[Header 1 Not Found]',
                    'report_header_2': '[Header 2 Not Found]'
                }
            
            # Use business name as report title
            report_title = business.name or '[Business Name Not Set]'
            
            # For now, use simple default headers since BusinessInformation might not have data
            # In a real implementation, you would query the BusinessInformation table
            header_1 = f"{business.name} - Official Communication" if business.name else '[Header 1 Not Set]'
            header_2 = "Human Resources Department" 
            
            return {
                'report_title': report_title,
                'report_header_1': header_1,
                'report_header_2': header_2
            }
        except Exception as e:
            # Return fallback values if database query fails
            return {
                'report_title': '[Business Data Error]',
                'report_header_1': '[Header 1 Error]',
                'report_header_2': '[Header 2 Error]'
            }
    
    def _get_date_data(self, letter_date: Optional[date] = None) -> Dict[str, str]:
        """Get date-related field data"""
        if letter_date is None:
            letter_date = date.today()
        
        # Format date in a readable format
        formatted_date = letter_date.strftime('%B %d, %Y')  # e.g., "January 13, 2026"
        
        return {
            'date_of_issue': formatted_date
        }
    
    def _replace_field_codes(self, template: str, field_data: Dict[str, str]) -> str:
        """Replace field codes in template with actual values"""
        processed_template = template
        
        for field_name, field_value in field_data.items():
            # Replace {field_name} with actual value
            field_placeholder = f"{{{field_name}}}"
            processed_template = processed_template.replace(field_placeholder, str(field_value))
        
        return processed_template
    
    def get_available_fields(self) -> Dict[str, str]:
        """Get list of available field codes with descriptions"""
        return {
            'date_of_issue': 'Date when the letter is issued',
            'report_title': 'Business name from company setup',
            'report_header_1': 'Header line 1 from business information',
            'report_header_2': 'Header line 2 from business information',
            'employee_name': 'Full name of the employee',
            'employee_code': 'Employee\'s unique identification code',
            'department': 'Employee\'s department',
            'designation': 'Employee\'s job title/designation'
        }
    
    def preview_template(
        self, 
        template_content: str, 
        employee_id: int, 
        business_id: int,
        letter_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Preview how template will look with actual data
        
        Returns:
            Dictionary with original template and processed preview
        """
        processed_content = self.process_template(
            template_content, employee_id, business_id, letter_date
        )
        
        return {
            'original_template': template_content,
            'processed_preview': processed_content,
            'available_fields': self.get_available_fields()
        }