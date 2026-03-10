from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.repositories.user_management_repository import UserManagementRepository


class UserManagementService:
    def __init__(self, db: Session):
        self.repo = UserManagementRepository(db)

    def get_filter_options(self, business_id: int) -> Dict[str, List[str]]:
        """Get available filter options for employee selection"""
        return self.repo.get_filter_options(business_id)

    def get_filtered_employee_count(
        self, 
        business_id: int,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> int:
        """Get count of employees matching filter criteria"""
        return self.repo.get_filtered_employee_count(
            business_id=business_id,
            location=location,
            cost_center=cost_center,
            department=department
        )

    async def send_mobile_login_details(
        self,
        business_id: int,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        include_logged_in: bool = False
    ) -> Dict[str, int]:
        """Send mobile login details via email to filtered employees"""
        from app.services.email_service import email_service
        from app.models.business import Business
        import random
        
        employees = self.repo.get_filtered_employees(
            business_id=business_id,
            location=location,
            cost_center=cost_center,
            department=department,
            include_logged_in=include_logged_in
        )
        
        # Get business details
        business = self.repo.db.query(Business).filter(Business.id == business_id).first()
        company_name = business.business_name if business else "Levitica Technologies"
        company_id = business.business_code if business and hasattr(business, 'business_code') and business.business_code else "LEV001"
        
        emails_sent = 0
        failed_count = 0
        
        # Send emails to all filtered employees
        for employee in employees:
            if employee.email and employee.mobile:
                try:
                    # Generate login PIN (last 6 digits of mobile)
                    login_pin = employee.mobile[-6:] if len(employee.mobile) >= 6 else str(random.randint(100000, 999999))
                    
                    # Send email asynchronously
                    result = await email_service.send_mobile_login_email(
                        employee_name=f"{employee.first_name} {employee.last_name}",
                        employee_code=employee.employee_code,
                        employee_email=employee.email,
                        mobile=employee.mobile,
                        company_name=company_name,
                        company_id=company_id,
                        login_pin=login_pin
                    )
                    
                    if result:
                        emails_sent += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    print(f"Failed to send email to {employee.email}: {str(e)}")
                    failed_count += 1
        
        return {
            "employees_notified": len(employees),
            "sms_count": 0,  # Not implemented yet
            "whatsapp_count": 0,  # Not implemented yet
            "emails_sent": emails_sent,
            "failed_count": failed_count
        }

    async def send_web_login_invitations(
        self,
        business_id: int,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, int]:
        """Create web portal accounts and send invitation emails to filtered employees"""
        from app.services.email_service import email_service
        from app.models.business import Business
        import random
        
        employees = self.repo.get_filtered_employees(
            business_id=business_id,
            location=location,
            cost_center=cost_center,
            department=department,
            include_logged_in=False  # Don't include already logged in users for web portal
        )
        
        # Get business details
        business = self.repo.db.query(Business).filter(Business.id == business_id).first()
        company_name = business.business_name if business else "Levitica Technologies"
        company_id = business.business_code if business and hasattr(business, 'business_code') and business.business_code else "LEV001"
        
        accounts_created = 0
        emails_sent = 0
        failed_count = 0
        
        # Send emails to all filtered employees
        for employee in employees:
            if employee.email:
                try:
                    # Generate login PIN from employee code digits
                    code_digits = ''.join(filter(str.isdigit, employee.employee_code))
                    login_pin = code_digits[-6:].zfill(6) if code_digits else str(random.randint(100000, 999999))
                    
                    # Send email asynchronously
                    result = await email_service.send_web_login_email(
                        employee_name=f"{employee.first_name} {employee.last_name}",
                        employee_code=employee.employee_code,
                        employee_email=employee.email,
                        company_name=company_name,
                        company_id=company_id,
                        login_pin=login_pin,
                        temporary_password=None  # No temporary password for initial send
                    )
                    
                    if result:
                        emails_sent += 1
                        accounts_created += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    print(f"Failed to send email to {employee.email}: {str(e)}")
                    failed_count += 1
        
        return {
            "employees_notified": len(employees),
            "accounts_created": accounts_created,
            "emails_sent": emails_sent,
            "failed_count": failed_count
        }


def get_user_management_service(db: Session) -> UserManagementService:
    return UserManagementService(db)