"""
Biometric Code Repository
Data access layer for biometric code management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from datetime import datetime
import csv
import io
import logging

from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.location import Location

logger = logging.getLogger(__name__)
from app.utils.business_unit_utils import (
    get_business_unit_options,
    apply_business_unit_filter
)


class BiometricCodeRepository:
    """Repository for biometric code data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employees_with_biometric_codes(
        self,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        current_user = None
    ) -> List[Dict[str, Any]]:
        """Get employees with their biometric codes"""
        try:
            from app.models.business_unit import BusinessUnit
            from app.models.cost_center import CostCenter
            
            # Base query with proper joins
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            # Apply business filter
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            # Apply business unit filter - HYBRID APPROACH
            if current_user:
                query = apply_business_unit_filter(query, self.db, current_user, business_unit)
            else:
                # Fallback to old logic if no current_user provided
                if business_unit and business_unit != "All Business Units":
                    bu_obj = self.db.query(BusinessUnit).filter(BusinessUnit.name == business_unit).first()
                    if bu_obj:
                        query = query.filter(Employee.business_unit_id == bu_obj.id)
            
            # Apply location filter
            if location and location != "All Locations":
                location_obj = self.db.query(Location).filter(Location.name == location).first()
                if location_obj:
                    query = query.filter(Employee.location_id == location_obj.id)
            
            # Apply cost center filter
            if cost_center and cost_center != "All Cost Centers":
                cc_obj = self.db.query(CostCenter).filter(CostCenter.name == cost_center).first()
                if cc_obj:
                    query = query.filter(Employee.cost_center_id == cc_obj.id)
            
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
            
            # Apply pagination
            offset = (page - 1) * size
            employees = query.order_by(Employee.employee_code).offset(offset).limit(size).all()
            
            # Convert to response format with manual lookups
            result = []
            for emp in employees:
                # Get department name
                dept_name = "N/A"
                if emp.department_id:
                    dept = self.db.query(Department).filter(Department.id == emp.department_id).first()
                    if dept:
                        dept_name = dept.name
                
                # Get location name
                location_name = "N/A"
                if emp.location_id:
                    location = self.db.query(Location).filter(Location.id == emp.location_id).first()
                    if location:
                        location_name = location.name
                
                # Get business unit name
                business_unit_name = "N/A"
                if emp.business_unit_id:
                    bu = self.db.query(BusinessUnit).filter(BusinessUnit.id == emp.business_unit_id).first()
                    if bu:
                        business_unit_name = bu.name
                
                # Get cost center name
                cost_center_name = "N/A"
                if emp.cost_center_id:
                    cc = self.db.query(CostCenter).filter(CostCenter.id == emp.cost_center_id).first()
                    if cc:
                        cost_center_name = cc.name
                
                result.append({
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}".strip(),
                    "code": emp.employee_code,
                    "location": location_name,
                    "department": dept_name,
                    "business_unit": business_unit_name,
                    "cost_center": cost_center_name,
                    "biometric": emp.biometric_code or "",
                    "employee_id": emp.id,
                    "business_id": emp.business_id or 1
                })
            
            logger.debug(f"Repository returning {len(result)} employees")
            return result
            
        except Exception as e:
            logger.error(f"Repository error: {str(e)}")
            return []  # Return empty list instead of raising exception
    
    def update_employee_biometric_code(
        self,
        employee_code: str,
        biometric_code: str,
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update biometric code for an employee"""
        try:
            # Find employee
            query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            employee = query.first()
            if not employee:
                raise ValueError(f"Employee with code {employee_code} not found")
            
            # Update biometric code
            old_biometric_code = employee.biometric_code
            employee.biometric_code = biometric_code.strip() if biometric_code else None
            employee.updated_by = updated_by
            employee.updated_at = datetime.now()
            
            self.db.commit()
            
            return {
                "message": "Biometric code updated successfully",
                "employee_code": employee_code,
                "employee_name": employee.full_name,
                "old_biometric_code": old_biometric_code,
                "new_biometric_code": employee.biometric_code,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update biometric code: {str(e)}")
    
    def bulk_update_biometric_codes(
        self,
        updates: List[Dict[str, Any]],
        business_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Bulk update biometric codes for multiple employees"""
        try:
            successful_updates = 0
            failed_updates = 0
            errors = []
            
            for update_data in updates:
                try:
                    employee_code = update_data.get("employee_code")
                    biometric_code = update_data.get("biometric_code", "")
                    
                    if not employee_code:
                        errors.append({
                            "employee_code": employee_code,
                            "error": "Employee code is required"
                        })
                        failed_updates += 1
                        continue
                    
                    # Find employee
                    query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
                    if business_id:
                        query = query.filter(Employee.business_id == business_id)
                    
                    employee = query.first()
                    if not employee:
                        errors.append({
                            "employee_code": employee_code,
                            "error": "Employee not found"
                        })
                        failed_updates += 1
                        continue
                    
                    # Update biometric code
                    employee.biometric_code = biometric_code.strip() if biometric_code else None
                    employee.updated_by = updated_by
                    employee.updated_at = datetime.now()
                    
                    successful_updates += 1
                    
                except Exception as e:
                    errors.append({
                        "employee_code": update_data.get("employee_code", "Unknown"),
                        "error": str(e)
                    })
                    failed_updates += 1
            
            self.db.commit()
            
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
            raise Exception(f"Failed to bulk update biometric codes: {str(e)}")
    
    def get_filter_options(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """Get filter options for biometric code module"""
        try:
            from app.models.business_unit import BusinessUnit
            from app.models.cost_center import CostCenter
            
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
            
            # Get cost centers from database
            cc_query = self.db.query(CostCenter.name).filter(CostCenter.is_active == True)
            if business_id:
                cc_query = cc_query.filter(CostCenter.business_id == business_id)
            cost_centers = [cc[0] for cc in cc_query.distinct().all()]
            
            # Get departments from database
            dept_query = self.db.query(Department.name).filter(Department.is_active == True)
            if business_id:
                dept_query = dept_query.filter(Department.business_id == business_id)
            departments = [dept[0] for dept in dept_query.distinct().all()]
            
            return {
                "business_units": ["All Business Units"] + business_units,
                "locations": ["All Locations"] + locations,
                "cost_centers": ["All Cost Centers"] + cost_centers,
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
                result.append({
                    "id": emp.id,
                    "name": emp.full_name,
                    "code": emp.employee_code,
                    "biometric_code": emp.biometric_code or ""
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to search employees: {str(e)}")
    
    def export_biometric_codes_csv(
        self,
        current_user = None,
        business_id: Optional[int] = None,
        business_unit: Optional[str] = None,
        location: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """Export biometric codes as CSV with hybrid business unit logic"""
        try:
            # Get all employees with filters
            employees = self.get_employees_with_biometric_codes(
                current_user=current_user,
                business_id=business_id,
                business_unit=business_unit,
                location=location,
                department=department,
                page=1,
                size=10000  # Get all records
            )
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                "Employee Code",
                "Employee Name", 
                "Location",
                "Department",
                "Biometric Code"
            ])
            
            # Write data
            for emp in employees:
                writer.writerow([
                    emp["code"],
                    emp["name"],
                    emp["location"],
                    emp["department"],
                    emp["biometric"]
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Failed to export biometric codes CSV: {str(e)}")
    
    def import_biometric_codes_csv(
        self,
        csv_content: str,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import biometric codes from CSV"""
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            successful_imports = 0
            failed_imports = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    employee_code = row.get("Employee Code", "").strip()
                    biometric_code = row.get("Biometric Code", "").strip()
                    
                    if not employee_code:
                        errors.append({
                            "row": row_num,
                            "employee_code": employee_code,
                            "error": "Employee code is required"
                        })
                        failed_imports += 1
                        continue
                    
                    # Find employee
                    query = self.db.query(Employee).filter(Employee.employee_code == employee_code)
                    if business_id:
                        query = query.filter(Employee.business_id == business_id)
                    
                    employee = query.first()
                    if not employee:
                        errors.append({
                            "row": row_num,
                            "employee_code": employee_code,
                            "error": "Employee not found"
                        })
                        failed_imports += 1
                        continue
                    
                    # Check if biometric code already exists
                    if employee.biometric_code and not overwrite_existing:
                        errors.append({
                            "row": row_num,
                            "employee_code": employee_code,
                            "error": "Biometric code already exists (use overwrite option)"
                        })
                        failed_imports += 1
                        continue
                    
                    # Update biometric code
                    employee.biometric_code = biometric_code if biometric_code else None
                    employee.updated_by = created_by
                    employee.updated_at = datetime.now()
                    
                    successful_imports += 1
                    
                except Exception as e:
                    errors.append({
                        "row": row_num,
                        "employee_code": row.get("Employee Code", "Unknown"),
                        "error": str(e)
                    })
                    failed_imports += 1
            
            self.db.commit()
            
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
            raise Exception(f"Failed to import biometric codes CSV: {str(e)}")