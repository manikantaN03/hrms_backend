""""
Bank Details Repository
Data access layer for bank details management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from datetime import datetime
import csv
import io
import re

from app.models.employee import Employee, EmployeeStatus, EmployeeProfile
from app.models.department import Department
from app.models.location import Location
from app.models.business_unit import BusinessUnit
from app.models.cost_center import CostCenter


class BankDetailsRepository:
    """Repository for bank details data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employees_with_bank_details(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """Get employees with their bank details and pagination metadata"""
        try:
            # Base query with proper joins
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            # Apply business filter
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            # Apply business unit filter
            if business_unit and business_unit != "All Business Units":
                bu_obj = self.db.query(BusinessUnit).filter(BusinessUnit.name == business_unit).first()
                if bu_obj:
                    query = query.filter(Employee.business_unit_id == bu_obj.id)
            
            # Apply location filter
            if location and location != "All Locations":
                location_obj = self.db.query(Location).filter(Location.name == location).first()
                if location_obj:
                    query = query.filter(Employee.location_id == location_obj.id)
            
            # Apply department filter
            if department and department != "All Departments":
                dept_obj = self.db.query(Department).filter(Department.name == department).first()
                if dept_obj:
                    query = query.filter(Employee.department_id == dept_obj.id)
            
            # Apply search
            if search:
                query = query.filter(
                    or_(
                        Employee.first_name.ilike(f"%{search}%"),
                        Employee.last_name.ilike(f"%{search}%"),
                        Employee.employee_code.ilike(f"%{search}%")
                    )
                )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * size
            employees = query.order_by(Employee.employee_code).offset(offset).limit(size).all()
            
            # Convert to response format with manual lookups
            result = []
            for emp in employees:
                # Get employee profile for bank details
                profile = self.db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == emp.id).first()
                
                # Get department name
                dept_name = "N/A"
                if emp.department_id:
                    dept = self.db.query(Department).filter(Department.id == emp.department_id).first()
                    if dept:
                        dept_name = dept.name
                
                # Get designation name (using department as fallback for now)
                designation_name = dept_name
                
                result.append({
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}".strip(),
                    "code": emp.employee_code,
                    "designation": designation_name,
                    "bank_name": profile.bank_name if profile and profile.bank_name else "",
                    "ifsc_code": profile.bank_ifsc_code if profile and profile.bank_ifsc_code else "",
                    "account_number": profile.bank_account_number if profile and profile.bank_account_number else "",
                    "bank_branch": profile.bank_branch if profile and profile.bank_branch else "",
                    "verified": bool(profile and profile.bank_name and profile.bank_ifsc_code and profile.bank_account_number),
                    "employee_id": emp.id,
                    "business_id": emp.business_id or 1
                })
            
            # Calculate pagination metadata
            total_pages = (total_count + size - 1) // size
            
            print(f"Repository returning {len(result)} employees with bank details (page {page}/{total_pages}, total: {total_count})")
            
            return {
                "employees": result,
                "pagination": {
                    "current_page": page,
                    "page_size": size,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            print(f"Repository error: {str(e)}")
            return {
                "employees": [],
                "pagination": {
                    "current_page": 1,
                    "page_size": size,
                    "total_pages": 1,
                    "total_count": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
    
    def update_employee_bank_details(
        self,
        employee_code: str,
        bank_name: str,
        ifsc_code: str,
        account_number: str,
        bank_branch: Optional[str] = None,
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update bank details for an employee"""
        try:
            # Find employee
            query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employee = query.first()
            if not employee:
                raise ValueError(f"Employee with code {employee_code} not found")
            
            # Get or create employee profile
            profile = self.db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == employee.id).first()
            if not profile:
                profile = EmployeeProfile(employee_id=employee.id)
                self.db.add(profile)
            
            # Update bank details
            old_bank_name = profile.bank_name
            old_ifsc_code = profile.bank_ifsc_code
            old_account_number = profile.bank_account_number
            old_bank_branch = profile.bank_branch
            
            profile.bank_name = bank_name.strip() if bank_name else None
            profile.bank_ifsc_code = ifsc_code.strip().upper() if ifsc_code else None
            profile.bank_account_number = account_number.strip() if account_number else None
            profile.bank_branch = bank_branch.strip() if bank_branch else None
            
            # Update employee timestamp
            employee.updated_by = updated_by
            employee.updated_at = datetime.now()
            
            self.db.commit()
            
            return {
                "message": "Bank details updated successfully",
                "employee_code": employee_code,
                "employee_name": employee.full_name,
                "old_bank_details": {
                    "bank_name": old_bank_name,
                    "ifsc_code": old_ifsc_code,
                    "account_number": old_account_number,
                    "bank_branch": old_bank_branch
                },
                "new_bank_details": {
                    "bank_name": profile.bank_name,
                    "ifsc_code": profile.bank_ifsc_code,
                    "account_number": profile.bank_account_number,
                    "bank_branch": profile.bank_branch
                },
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update bank details: {str(e)}")
    
    def verify_bank_details(
        self,
        employee_code: str,
        business_id: Optional[int] = None,
        verified_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verify bank details for an employee"""
        try:
            # Find employee
            query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employee = query.first()
            if not employee:
                raise ValueError(f"Employee with code {employee_code} not found")
            
            # Get employee profile
            profile = self.db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == employee.id).first()
            if not profile:
                raise ValueError(f"No profile found for employee {employee_code}")
            
            # Check if all required bank details are present
            if not all([profile.bank_name, profile.bank_ifsc_code, profile.bank_account_number]):
                raise ValueError("Incomplete bank details - cannot verify")
            
            # Validate IFSC code format
            if not self._validate_ifsc_format(profile.bank_ifsc_code):
                raise ValueError("Invalid IFSC code format")
            
            # Validate account number format
            if not self._validate_account_number_format(profile.bank_account_number):
                raise ValueError("Invalid account number format")
            
            return {
                "message": "Bank details verified successfully",
                "employee_code": employee_code,
                "employee_name": employee.full_name,
                "bank_details": {
                    "bank_name": profile.bank_name,
                    "ifsc_code": profile.bank_ifsc_code,
                    "account_number": profile.bank_account_number,
                    "bank_branch": profile.bank_branch
                },
                "verified_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to verify bank details: {str(e)}")
    
    def validate_ifsc_code(self, ifsc_code: str) -> Dict[str, Any]:
        """Validate IFSC code format"""
        try:
            if not ifsc_code:
                return {"valid": False, "message": "IFSC code is required"}
            
            # Clean and format IFSC code
            ifsc_clean = ifsc_code.strip().upper()
            
            # Validate format: 4 letters + 7 characters (letters/numbers)
            if not self._validate_ifsc_format(ifsc_clean):
                return {
                    "valid": False, 
                    "message": "Invalid IFSC format. Should be 4 letters followed by 7 alphanumeric characters"
                }
            
            # Extract bank code (first 4 letters)
            bank_code = ifsc_clean[:4]
            
            # Basic bank code validation (you can expand this with actual bank data)
            known_banks = {
                "SBIN": "State Bank of India",
                "HDFC": "HDFC Bank",
                "ICIC": "ICICI Bank",
                "AXIS": "Axis Bank",
                "PUNB": "Punjab National Bank",
                "UBIN": "Union Bank of India",
                "CNRB": "Canara Bank",
                "BARB": "Bank of Baroda"
            }
            
            bank_name = known_banks.get(bank_code, "Unknown Bank")
            
            return {
                "valid": True,
                "message": "Valid IFSC code",
                "ifsc_code": ifsc_clean,
                "bank_code": bank_code,
                "bank_name": bank_name
            }
            
        except Exception as e:
            return {"valid": False, "message": f"Error validating IFSC: {str(e)}"}
    
    def _validate_ifsc_format(self, ifsc_code: str) -> bool:
        """Validate IFSC code format"""
        if not ifsc_code or len(ifsc_code) != 11:
            return False
        
        # Pattern: 4 letters + 7 alphanumeric characters
        pattern = r'^[A-Z]{4}[A-Z0-9]{7}$'
        return bool(re.match(pattern, ifsc_code))
    
    def _validate_account_number_format(self, account_number: str) -> bool:
        """Validate account number format"""
        if not account_number:
            return False
        
        # Remove spaces and check if it's numeric and reasonable length
        account_clean = account_number.replace(" ", "")
        return account_clean.isdigit() and 8 <= len(account_clean) <= 20
    
    def get_filter_options(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """Get filter options for bank details module"""
        try:
            # Get business units from database
            bu_query = self.db.query(BusinessUnit.name).filter(BusinessUnit.is_active == True)
            if business_id:
                bu_query = bu_query.filter(BusinessUnit.business_id == business_id)
            business_units = [bu[0] for bu in bu_query.distinct().all()]
            
            # Get locations from database
            location_query = self.db.query(Location.name).filter(Location.is_active == True)
            if business_id:
                location_query = location_query.filter(Location.business_id == business_id)
            locations = [loc[0] for loc in location_query.distinct().all()]
            
            # Get departments from database
            dept_query = self.db.query(Department.name).filter(Department.is_active == True)
            if business_id:
                dept_query = dept_query.filter(Department.business_id == business_id)
            departments = [dept[0] for dept in dept_query.distinct().all()]
            
            return {
                "business_units": ["All Business Units"] + business_units,
                "locations": ["All Locations"] + locations,
                "departments": ["All Departments"] + departments
            }
            
        except Exception as e:
            raise Exception(f"Failed to get filter options: {str(e)}")
    
    def search_employees(
        self,
        search: str,
        business_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search employees for autocomplete"""
        try:
            query = self.db.query(Employee).filter(
                Employee.employee_status == EmployeeStatus.ACTIVE,
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%"),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{search}%")
                )
            )
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employees = query.limit(limit).all()
            
            result = []
            for emp in employees:
                # Get profile for bank details
                profile = self.db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == emp.id).first()
                
                result.append({
                    "id": emp.id,
                    "name": emp.full_name,
                    "code": emp.employee_code,
                    "bank_name": profile.bank_name if profile else "",
                    "ifsc_code": profile.bank_ifsc_code if profile else "",
                    "account_number": profile.bank_account_number if profile else ""
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to search employees: {str(e)}")
    
    def export_bank_details_csv(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export bank details as CSV"""
        try:
            # Get all employees with filters
            result = self.get_employees_with_bank_details(
                business_id=business_id,
                business_unit=business_unit,
                location=location,
                department=department,
                page=1,
                size=10000  # Get all records
            )
            
            # Extract employees list from result dict
            employees = result.get("employees", [])
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                "Employee Code",
                "Employee Name", 
                "Designation",
                "Bank Name",
                "IFSC Code",
                "Account Number",
                "Bank Branch",
                "Verified"
            ])
            
            # Write data
            for emp in employees:
                writer.writerow([
                    emp["code"],
                    emp["name"],
                    emp["designation"],
                    emp["bank_name"],
                    emp["ifsc_code"],
                    emp["account_number"],
                    emp["bank_branch"],
                    "Yes" if emp["verified"] else "No"
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Failed to export bank details CSV: {str(e)}")
    
    def import_bank_details_csv(
        self,
        csv_content: str,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import bank details from CSV"""
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            successful_imports = 0
            failed_imports = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    employee_code = row.get("Employee Code", "").strip()
                    bank_name = row.get("Bank Name", "").strip()
                    ifsc_code = row.get("IFSC Code", "").strip()
                    account_number = row.get("Account Number", "").strip()
                    bank_branch = row.get("Bank Branch", "").strip()
                    
                    if not employee_code:
                        errors.append({
                            "row": row_num,
                            "employee_code": employee_code,
                            "error": "Employee code is required"
                        })
                        failed_imports += 1
                        continue
                    
                    if not all([bank_name, ifsc_code, account_number]):
                        errors.append({
                            "row": row_num,
                            "employee_code": employee_code,
                            "error": "Bank name, IFSC code, and account number are required"
                        })
                        failed_imports += 1
                        continue
                    
                    # Update bank details
                    self.update_employee_bank_details(
                        employee_code=employee_code,
                        bank_name=bank_name,
                        ifsc_code=ifsc_code,
                        account_number=account_number,
                        bank_branch=bank_branch,
                        business_id=business_id,
                        updated_by=created_by
                    )
                    
                    successful_imports += 1
                    
                except Exception as e:
                    errors.append({
                        "row": row_num,
                        "employee_code": row.get("Employee Code", "Unknown"),
                        "error": str(e)
                    })
                    failed_imports += 1
            
            return {
                "message": "Import completed",
                "total_records": successful_imports + failed_imports,
                "successful_imports": successful_imports,
                "failed_imports": failed_imports,
                "errors": errors,
                "imported_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to import bank details CSV: {str(e)}")
    
    def bulk_update_bank_details(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Bulk update bank details for multiple employees"""
        try:
            successful_updates = 0
            failed_updates = 0
            errors = []
            
            for update_data in updates:
                try:
                    employee_code = update_data.get("employee_code")
                    bank_name = update_data.get("bank_name", "")
                    ifsc_code = update_data.get("ifsc_code", "")
                    account_number = update_data.get("account_number", "")
                    bank_branch = update_data.get("bank_branch", "")
                    
                    if not employee_code:
                        errors.append({
                            "employee_code": employee_code,
                            "error": "Employee code is required"
                        })
                        failed_updates += 1
                        continue
                    
                    # Update bank details
                    self.update_employee_bank_details(
                        employee_code=employee_code,
                        bank_name=bank_name,
                        ifsc_code=ifsc_code,
                        account_number=account_number,
                        bank_branch=bank_branch,
                        business_id=business_id,
                        updated_by=updated_by
                    )
                    
                    successful_updates += 1
                    
                except Exception as e:
                    errors.append({
                        "employee_code": update_data.get("employee_code", "Unknown"),
                        "error": str(e)
                    })
                    failed_updates += 1
            
            return {
                "message": "Bulk update completed",
                "total_records": len(updates),
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "errors": errors,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to bulk update bank details: {str(e)}") 
