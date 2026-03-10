"""
Create Sample Employee Data
Matches the frontend employee data structure exactly
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.models.employee import Employee, EmployeeProfile, EmployeeDocument, EmployeeSalary
from app.models.business import Business
from app.models.department import Department
from app.models.designations import Designation
from app.models.location import Location
from app.models.cost_center import CostCenter
from app.models.grades import Grade
from app.models.shift_policy import ShiftPolicy
from app.models.weekoff_policy import WeekOffPolicy
from app.models.user import User
from app.core.database import get_db_context
from app.core.config import settings
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_sample_employees():
    """Create sample employees matching frontend data structure"""
    logger.info("Creating sample employees...")
    
    try:
        with get_db_context() as db:
            # Get required references
            business = db.query(Business).first()
            if not business:
                logger.error("No business found")
                return False
            
            superadmin = db.query(User).filter(User.email == settings.SUPERADMIN_EMAIL).first()
            if not superadmin:
                logger.error("Superadmin not found")
                return False
            
            # Get departments, designations, locations
            dept_product = db.query(Department).filter(Department.name == "Product Development Team").first()
            dept_hr = db.query(Department).filter(Department.name == "Human Resources").first()
            dept_tech = db.query(Department).filter(Department.name == "Technical Support").first()
            
            desig_ase = db.query(Designation).filter(Designation.name == "Associate Software Engineer").first()
            desig_hr = db.query(Designation).filter(Designation.name == "HR Executive").first()
            desig_manager = db.query(Designation).filter(Designation.name == "Manager").first()
            
            loc_hyd = db.query(Location).filter(Location.name == "Hyderabad").first()
            loc_blr = db.query(Location).filter(Location.name == "Bangalore").first()
            
            cost_center = db.query(CostCenter).filter(CostCenter.name == "Engineering").first()
            grade = db.query(Grade).filter(Grade.name == "Associate").first()
            shift_policy = db.query(ShiftPolicy).filter(ShiftPolicy.title == "Day Shift (9 AM - 6 PM)").first()
            weekoff_policy = db.query(WeekOffPolicy).filter(WeekOffPolicy.title == "Saturday-Sunday Off").first()
            
            # Sample employees data matching frontend structure
            employees_data = [
                {
                    "employee_code": "LEV013",
                    "first_name": "Sai Charan",
                    "last_name": "Vemulapudi",
                    "middle_name": "",
                    "email": "saicharan.vemulapudi@levitica.com",
                    "mobile": "+91-9876543210",
                    "alternate_mobile": "+91-9876543211",
                    "date_of_birth": date(1998, 3, 15),
                    "gender": "male",
                    "marital_status": "single",
                    "blood_group": "O+",
                    "nationality": "Indian",
                    "religion": "Hindu",
                    "date_of_joining": date(2025, 5, 12),
                    "date_of_confirmation": date(2025, 11, 12),
                    "employee_status": "active",
                    "department": dept_product,
                    "designation": desig_ase,
                    "location": loc_hyd,
                    "cost_center": cost_center,
                    "grade": grade,
                    "shift_policy": shift_policy,
                    "weekoff_policy": weekoff_policy,
                    "biometric_code": "BIO013",
                    "send_mobile_login": True,
                    "send_web_login": True
                },
                {
                    "employee_code": "LEV014",
                    "first_name": "Priya",
                    "last_name": "Sharma",
                    "middle_name": "",
                    "email": "priya.sharma@levitica.com",
                    "mobile": "+91-9876543220",
                    "alternate_mobile": "+91-9876543221",
                    "date_of_birth": date(1995, 7, 22),
                    "gender": "female",
                    "marital_status": "married",
                    "blood_group": "A+",
                    "nationality": "Indian",
                    "religion": "Hindu",
                    "date_of_joining": date(2024, 8, 15),
                    "date_of_confirmation": date(2025, 2, 15),
                    "employee_status": "active",
                    "department": dept_hr,
                    "designation": desig_hr,
                    "location": loc_hyd,
                    "cost_center": cost_center,
                    "grade": grade,
                    "shift_policy": shift_policy,
                    "weekoff_policy": weekoff_policy,
                    "biometric_code": "BIO014",
                    "send_mobile_login": True,
                    "send_web_login": True
                },
                {
                    "employee_code": "LEV015",
                    "first_name": "Rajesh",
                    "last_name": "Kumar",
                    "middle_name": "",
                    "email": "rajesh.kumar@levitica.com",
                    "mobile": "+91-9876543230",
                    "alternate_mobile": "+91-9876543231",
                    "date_of_birth": date(1990, 12, 10),
                    "gender": "male",
                    "marital_status": "married",
                    "blood_group": "B+",
                    "nationality": "Indian",
                    "religion": "Hindu",
                    "date_of_joining": date(2023, 3, 1),
                    "date_of_confirmation": date(2023, 9, 1),
                    "employee_status": "active",
                    "department": dept_tech,
                    "designation": desig_manager,
                    "location": loc_blr,
                    "cost_center": cost_center,
                    "grade": grade,
                    "shift_policy": shift_policy,
                    "weekoff_policy": weekoff_policy,
                    "biometric_code": "BIO015",
                    "send_mobile_login": True,
                    "send_web_login": True
                },
                {
                    "employee_code": "LEV016",
                    "first_name": "Anita",
                    "last_name": "Reddy",
                    "middle_name": "",
                    "email": "anita.reddy@levitica.com",
                    "mobile": "+91-9876543240",
                    "alternate_mobile": "+91-9876543241",
                    "date_of_birth": date(1992, 5, 8),
                    "gender": "female",
                    "marital_status": "single",
                    "blood_group": "AB+",
                    "nationality": "Indian",
                    "religion": "Hindu",
                    "date_of_joining": date(2024, 1, 10),
                    "date_of_confirmation": date(2024, 7, 10),
                    "employee_status": "active",
                    "department": dept_product,
                    "designation": desig_ase,
                    "location": loc_hyd,
                    "cost_center": cost_center,
                    "grade": grade,
                    "shift_policy": shift_policy,
                    "weekoff_policy": weekoff_policy,
                    "biometric_code": "BIO016",
                    "send_mobile_login": True,
                    "send_web_login": True
                },
                {
                    "employee_code": "LEV017",
                    "first_name": "Vikram",
                    "last_name": "Singh",
                    "middle_name": "",
                    "email": "vikram.singh@levitica.com",
                    "mobile": "+91-9876543250",
                    "alternate_mobile": "+91-9876543251",
                    "date_of_birth": date(1988, 11, 25),
                    "gender": "male",
                    "marital_status": "married",
                    "blood_group": "O-",
                    "nationality": "Indian",
                    "religion": "Sikh",
                    "date_of_joining": date(2022, 6, 20),
                    "date_of_confirmation": date(2022, 12, 20),
                    "employee_status": "active",
                    "department": dept_tech,
                    "designation": desig_ase,
                    "location": loc_blr,
                    "cost_center": cost_center,
                    "grade": grade,
                    "shift_policy": shift_policy,
                    "weekoff_policy": weekoff_policy,
                    "biometric_code": "BIO017",
                    "send_mobile_login": True,
                    "send_web_login": True
                }
            ]
            
            created_employees = []
            
            for emp_data in employees_data:
                # Check if employee already exists
                existing = db.query(Employee).filter(Employee.employee_code == emp_data["employee_code"]).first()
                if existing:
                    logger.info(f"Employee {emp_data['employee_code']} already exists, skipping...")
                    created_employees.append(existing)
                    continue
                
                # Create employee
                employee = Employee(
                    business_id=business.id,
                    employee_code=emp_data["employee_code"],
                    first_name=emp_data["first_name"],
                    last_name=emp_data["last_name"],
                    middle_name=emp_data["middle_name"],
                    email=emp_data["email"],
                    mobile=emp_data["mobile"],
                    alternate_mobile=emp_data["alternate_mobile"],
                    date_of_birth=emp_data["date_of_birth"],
                    gender=emp_data["gender"],
                    marital_status=emp_data["marital_status"],
                    blood_group=emp_data["blood_group"],
                    nationality=emp_data["nationality"],
                    religion=emp_data["religion"],
                    date_of_joining=emp_data["date_of_joining"],
                    date_of_confirmation=emp_data["date_of_confirmation"],
                    employee_status=emp_data["employee_status"],
                    department_id=emp_data["department"].id if emp_data["department"] else None,
                    designation_id=emp_data["designation"].id if emp_data["designation"] else None,
                    location_id=emp_data["location"].id if emp_data["location"] else None,
                    cost_center_id=emp_data["cost_center"].id if emp_data["cost_center"] else None,
                    grade_id=emp_data["grade"].id if emp_data["grade"] else None,
                    shift_policy_id=emp_data["shift_policy"].id if emp_data["shift_policy"] else None,
                    weekoff_policy_id=emp_data["weekoff_policy"].id if emp_data["weekoff_policy"] else None,
                    biometric_code=emp_data["biometric_code"],
                    send_mobile_login=emp_data["send_mobile_login"],
                    send_web_login=emp_data["send_web_login"],
                    is_active=True,
                    created_by=superadmin.id,
                    created_at=datetime.now()
                )
                
                db.add(employee)
                db.commit()
                db.refresh(employee)
                
                # Create employee profile with extended information
                profile = EmployeeProfile(
                    employee_id=employee.id,
                    present_address_line1=f"Flat {employee.id}01, Green Valley Apartments, Kondapur",
                    present_city="Hyderabad" if emp_data["location"] == loc_hyd else "Bangalore",
                    present_state="Telangana" if emp_data["location"] == loc_hyd else "Karnataka",
                    present_country="India",
                    present_pincode="500032" if emp_data["location"] == loc_hyd else "560001",
                    permanent_address_line1=f"H.No {employee.id}-123, Main Road",
                    permanent_city="Vijayawada",
                    permanent_state="Andhra Pradesh",
                    permanent_country="India",
                    permanent_pincode="520001",
                    pan_number=f"ABCDE{employee.id:04d}F",
                    aadhaar_number=f"1234-5678-{employee.id:04d}",
                    uan_number=f"123456789{employee.id:03d}",
                    esi_number=f"ESI123456{employee.id:03d}",
                    bank_name="HDFC Bank",
                    bank_account_number=f"123456789012345{employee.id}",
                    bank_ifsc_code="HDFC0001234",
                    bank_branch="Kondapur Branch",
                    emergency_contact_name=f"{emp_data['first_name']} Father",
                    emergency_contact_relationship="Father",
                    emergency_contact_mobile=f"+91-987654{employee.id:04d}",
                    emergency_contact_address="Emergency Contact Address",
                    profile_image_url="/assets/img/users/user-01.jpg",
                    bio=f"Experienced {emp_data['designation'].name if emp_data['designation'] else 'Employee'} with expertise in software development.",
                    skills='["Python", "JavaScript", "React", "FastAPI", "PostgreSQL"]',
                    certifications='["AWS Certified", "Python Certification"]',
                    created_at=datetime.now()
                )
                
                # Add wedding date for married employees
                if emp_data["marital_status"] == "married":
                    import random
                    # Generate a random wedding date between 2-8 years ago
                    years_ago = random.randint(2, 8)
                    wedding_year = datetime.now().year - years_ago
                    wedding_month = random.randint(1, 12)
                    wedding_day = random.randint(1, 28)  # Safe day range for all months
                    profile.wedding_date = date(wedding_year, wedding_month, wedding_day)
                
                db.add(profile)
                
                # Create sample documents
                documents = [
                    {
                        "document_type": "resume",
                        "document_name": f"{employee.employee_code}_Resume.pdf",
                        "file_path": f"/documents/employee_{employee.id}_resume.pdf"
                    },
                    {
                        "document_type": "id_proof",
                        "document_name": f"{employee.employee_code}_PAN.jpg",
                        "file_path": f"/documents/employee_{employee.id}_pan.jpg"
                    },
                    {
                        "document_type": "education",
                        "document_name": f"{employee.employee_code}_Education.jpg",
                        "file_path": f"/documents/employee_{employee.id}_education.jpg"
                    }
                ]
                
                for doc_data in documents:
                    document = EmployeeDocument(
                        employee_id=employee.id,
                        document_type=doc_data["document_type"],
                        document_name=doc_data["document_name"],
                        file_path=doc_data["file_path"],
                        file_size=1024000,  # 1MB
                        mime_type="application/pdf" if doc_data["document_name"].endswith(".pdf") else "image/jpeg",
                        uploaded_at=datetime.now(),
                        uploaded_by=superadmin.id
                    )
                    db.add(document)
                
                # Create salary record
                salary = EmployeeSalary(
                    employee_id=employee.id,
                    basic_salary=25000,
                    gross_salary=50000,
                    ctc=60000,
                    effective_from=emp_data["date_of_joining"],
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(salary)
                
                db.commit()
                created_employees.append(employee)
                logger.info(f"Created employee: {employee.employee_code} - {employee.full_name}")
            
            logger.info(f"Successfully created {len(created_employees)} employees")
            return True
    
    except Exception as e:
        logger.error(f"Failed to create sample employees: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    logger.info("Starting sample employee creation...")
    
    if create_sample_employees():
        logger.info("✓ Sample employees created successfully!")
    else:
        logger.error("✗ Failed to create sample employees")
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)