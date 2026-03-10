"""
Maintenance Repository
Data access layer for maintenance operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text, desc
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from app.models.employee import Employee, EmployeeStatus, EmployeeSalary
from app.models.datacapture import EmployeeDeduction
from app.models.department import Department
from app.models.location import Location
from app.models.cost_center import CostCenter
from app.models.designations import Designation
from app.models.grades import Grade
from app.models.shift_policy import ShiftPolicy
from app.models.weekoff_policy import WeekOffPolicy

logger = logging.getLogger(__name__)


class MaintenanceRepository:
    """Repository for maintenance data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def recalculate_salary_totals(
        self,
        business_id: Optional[int] = None,
        employee_ids: Optional[List[int]] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Recalculate salary totals for employees"""
        try:
            # Get employees to process
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            if employee_ids:
                query = query.filter(Employee.id.in_(employee_ids))
            
            employees = query.all()
            
            total_employees = len(employees)
            updated_employees = 0
            failed_employees = 0
            errors = []
            
            for employee in employees:
                try:
                    # Recalculate salary totals for this employee
                    self._recalculate_employee_salary(employee, updated_by)
                    updated_employees += 1
                    
                except Exception as e:
                    failed_employees += 1
                    errors.append({
                        "employee_id": employee.id,
                        "employee_code": employee.employee_code,
                        "employee_name": employee.full_name,
                        "error": str(e)
                    })
                    logger.error(f"Failed to recalculate salary for employee {employee.employee_code}: {str(e)}")
            
            # Commit all changes
            self.db.commit()
            
            return {
                "total_employees": total_employees,
                "updated_employees": updated_employees,
                "failed_employees": failed_employees,
                "errors": errors
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to recalculate salary totals: {str(e)}")
    
    def _recalculate_employee_salary(self, employee: Employee, updated_by: Optional[int] = None):
        """Recalculate salary totals for a single employee"""
        try:
            # Get latest salary details
            salary_details = self.db.query(EmployeeSalary).filter(
                EmployeeSalary.employee_id == employee.id
            ).order_by(desc(EmployeeSalary.created_at)).first()
            
            if not salary_details:
                # Create default salary details if none exist
                salary_details = EmployeeSalary(
                    employee_id=employee.id,
                    basic_salary=Decimal('0.0'),
                    gross_salary=Decimal('0.0'),
                    ctc=Decimal('0.0'),
                    effective_from=datetime.now().date(),
                    is_active=True,
                    created_at=datetime.now()
                )
                self.db.add(salary_details)
                self.db.flush()
            
            # Calculate totals from salary components (if any)
            # For now, we'll ensure the basic calculations are consistent
            basic_salary = salary_details.basic_salary or Decimal('0.0')
            
            # Calculate allowances (simplified - in real implementation, sum from components)
            allowances = Decimal('0.0')  # Simplified for now
            
            # Calculate gross salary
            gross_salary = basic_salary + allowances
            
            # Get deductions
            deductions_query = self.db.query(EmployeeDeduction).filter(
                EmployeeDeduction.employee_id == employee.id
            )
            total_deductions = deductions_query.with_entities(
                func.coalesce(func.sum(EmployeeDeduction.amount), 0)
            ).scalar() or Decimal('0.0')
            
            # Calculate CTC (simplified)
            ctc = gross_salary + (gross_salary * Decimal('0.12'))  # Add 12% for employer contributions
            
            # Update salary details
            salary_details.gross_salary = gross_salary
            salary_details.ctc = ctc
            salary_details.updated_at = datetime.now()
            
            logger.debug(f"Recalculated salary for {employee.employee_code}: Basic={basic_salary}, Gross={gross_salary}, CTC={ctc}")
            
        except Exception as e:
            raise Exception(f"Failed to recalculate salary for employee {employee.employee_code}: {str(e)}")
    
    def update_work_profile_records(
        self,
        business_id: Optional[int] = None,
        employee_ids: Optional[List[int]] = None,
        fix_duplicates: bool = True,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update work profile records for employees"""
        try:
            # Get employees to process
            query = self.db.query(Employee).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            
            if business_id:
                query = query.filter(Employee.business_id == business_id)
            
            if employee_ids:
                query = query.filter(Employee.id.in_(employee_ids))
            
            employees = query.all()
            
            total_employees = len(employees)
            updated_employees = 0
            created_profiles = 0
            fixed_duplicates = 0
            failed_employees = 0
            errors = []
            
            # Get default values for missing profile fields
            default_location = self.db.query(Location).filter(
                Location.business_id == business_id,
                Location.is_active == True
            ).first()
            
            default_department = self.db.query(Department).filter(
                Department.business_id == business_id,
                Department.is_active == True
            ).first()
            
            default_designation = self.db.query(Designation).filter(
                Designation.business_id == business_id
            ).first()
            
            default_cost_center = self.db.query(CostCenter).filter(
                CostCenter.business_id == business_id,
                CostCenter.is_active == True
            ).first()
            
            default_shift_policy = self.db.query(ShiftPolicy).filter(
                ShiftPolicy.business_id == business_id,
                ShiftPolicy.is_default == True
            ).first()
            
            default_weekoff_policy = self.db.query(WeekOffPolicy).filter(
                WeekOffPolicy.business_id == business_id,
                WeekOffPolicy.is_default == True
            ).first()
            
            for employee in employees:
                try:
                    profile_updated = False
                    
                    # Check and fix missing work profile fields
                    if not employee.location_id and default_location:
                        employee.location_id = default_location.id
                        profile_updated = True
                        created_profiles += 1
                    
                    if not employee.department_id and default_department:
                        employee.department_id = default_department.id
                        profile_updated = True
                    
                    if not employee.designation_id and default_designation:
                        employee.designation_id = default_designation.id
                        profile_updated = True
                    
                    if not employee.cost_center_id and default_cost_center:
                        employee.cost_center_id = default_cost_center.id
                        profile_updated = True
                    
                    if not employee.shift_policy_id and default_shift_policy:
                        employee.shift_policy_id = default_shift_policy.id
                        profile_updated = True
                    
                    if not employee.weekoff_policy_id and default_weekoff_policy:
                        employee.weekoff_policy_id = default_weekoff_policy.id
                        profile_updated = True
                    
                    # Fix duplicates if requested
                    if fix_duplicates:
                        # Check for duplicate employee codes
                        duplicate_count = self.db.query(Employee).filter(
                            Employee.employee_code == employee.employee_code,
                            Employee.id != employee.id,
                            Employee.business_id == business_id
                        ).count()
                        
                        if duplicate_count > 0:
                            # Generate unique employee code
                            base_code = employee.employee_code
                            counter = 1
                            while self.db.query(Employee).filter(
                                Employee.employee_code == f"{base_code}_{counter}",
                                Employee.business_id == business_id
                            ).first():
                                counter += 1
                            
                            employee.employee_code = f"{base_code}_{counter}"
                            profile_updated = True
                            fixed_duplicates += 1
                    
                    if profile_updated:
                        employee.updated_by = updated_by
                        employee.updated_at = datetime.now()
                        updated_employees += 1
                    
                except Exception as e:
                    failed_employees += 1
                    errors.append({
                        "employee_id": employee.id,
                        "employee_code": employee.employee_code,
                        "employee_name": employee.full_name,
                        "error": str(e)
                    })
                    logger.error(f"Failed to update work profile for employee {employee.employee_code}: {str(e)}")
            
            # Commit all changes
            self.db.commit()
            
            return {
                "total_employees": total_employees,
                "updated_employees": updated_employees,
                "created_profiles": created_profiles,
                "fixed_duplicates": fixed_duplicates,
                "failed_employees": failed_employees,
                "errors": errors
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update work profile records: {str(e)}")
    
    def get_maintenance_status(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get maintenance status and statistics"""
        try:
            # Employee statistics
            employee_query = self.db.query(Employee)
            if business_id:
                employee_query = employee_query.filter(Employee.business_id == business_id)
            
            total_employees = employee_query.count()
            active_employees = employee_query.filter(Employee.employee_status == EmployeeStatus.ACTIVE).count()
            
            # Work profile completeness
            incomplete_profiles = employee_query.filter(
                Employee.employee_status == EmployeeStatus.ACTIVE,
                or_(
                    Employee.location_id.is_(None),
                    Employee.department_id.is_(None),
                    Employee.designation_id.is_(None)
                )
            ).count()
            
            # Employees without salary data completeness
            employees_without_salary = employee_query.filter(
                Employee.employee_status == EmployeeStatus.ACTIVE,
                ~Employee.id.in_(
                    self.db.query(EmployeeSalary.employee_id).distinct()
                )
            ).count()
            
            # Recent maintenance activities (last 30 days)
            recent_updates = employee_query.filter(
                Employee.updated_at >= datetime.now() - timedelta(days=30)
            ).count()
            
            return {
                "employee_statistics": {
                    "total_employees": total_employees,
                    "active_employees": active_employees,
                    "inactive_employees": total_employees - active_employees
                },
                "data_completeness": {
                    "incomplete_work_profiles": incomplete_profiles,
                    "employees_without_salary": employees_without_salary,
                    "profile_completeness_percentage": round(
                        ((active_employees - incomplete_profiles) / active_employees * 100) if active_employees > 0 else 0, 2
                    )
                },
                "recent_activity": {
                    "recent_updates": recent_updates,
                    "last_maintenance_check": datetime.now().isoformat()
                },
                "recommendations": self._get_maintenance_recommendations(
                    incomplete_profiles, employees_without_salary
                )
            }
            
        except Exception as e:
            raise Exception(f"Failed to get maintenance status: {str(e)}")
    
    def _get_maintenance_recommendations(
        self,
        incomplete_profiles: int,
        employees_without_salary: int
    ) -> List[Dict[str, Any]]:
        """Generate maintenance recommendations based on current status"""
        recommendations = []
        
        if incomplete_profiles > 0:
            recommendations.append({
                "type": "work_profile",
                "priority": "high" if incomplete_profiles > 10 else "medium",
                "title": "Incomplete Work Profiles",
                "description": f"{incomplete_profiles} employees have incomplete work profiles",
                "action": "Run 'Update Work Profile Records' maintenance task"
            })
        
        if employees_without_salary > 0:
            recommendations.append({
                "type": "salary_data",
                "priority": "high" if employees_without_salary > 5 else "medium",
                "title": "Missing Salary Data",
                "description": f"{employees_without_salary} employees don't have salary information",
                "action": "Run 'Recalculate Salary Totals' maintenance task"
            })
        
        if not recommendations:
            recommendations.append({
                "type": "general",
                "priority": "low",
                "title": "System Health Good",
                "description": "No critical maintenance issues detected",
                "action": "Continue regular monitoring"
            })
        
        return recommendations
    
    def validate_data_integrity(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Validate data integrity and identify potential issues"""
        try:
            issues = []
            
            # Check for employees without required fields
            employee_query = self.db.query(Employee)
            if business_id:
                employee_query = employee_query.filter(Employee.business_id == business_id)
            
            # Missing email addresses
            missing_emails = employee_query.filter(
                Employee.employee_status == EmployeeStatus.ACTIVE,
                or_(Employee.email.is_(None), Employee.email == "")
            ).count()
            
            if missing_emails > 0:
                issues.append({
                    "type": "missing_data",
                    "severity": "medium",
                    "description": f"{missing_emails} active employees missing email addresses",
                    "table": "employees",
                    "field": "email"
                })
            
            # Duplicate employee codes
            duplicate_codes = self.db.query(Employee.employee_code).filter(
                Employee.business_id == business_id if business_id else True
            ).group_by(Employee.employee_code).having(func.count(Employee.id) > 1).all()
            
            if duplicate_codes:
                issues.append({
                    "type": "duplicate_data",
                    "severity": "high",
                    "description": f"{len(duplicate_codes)} duplicate employee codes found",
                    "table": "employees",
                    "field": "employee_code",
                    "duplicates": [code[0] for code in duplicate_codes]
                })
            
            # Orphaned salary records
            orphaned_salaries = self.db.query(EmployeeSalary).filter(
                ~EmployeeSalary.employee_id.in_(
                    self.db.query(Employee.id).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
                )
            ).count()
            
            if orphaned_salaries > 0:
                issues.append({
                    "type": "orphaned_data",
                    "severity": "medium",
                    "description": f"{orphaned_salaries} salary records for inactive/deleted employees",
                    "table": "salary_details",
                    "field": "employee_id"
                })
            
            # Invalid foreign key references
            invalid_departments = employee_query.filter(
                Employee.department_id.isnot(None),
                ~Employee.department_id.in_(
                    self.db.query(Department.id).filter(Department.is_active == True)
                )
            ).count()
            
            if invalid_departments > 0:
                issues.append({
                    "type": "invalid_reference",
                    "severity": "high",
                    "description": f"{invalid_departments} employees reference inactive/deleted departments",
                    "table": "employees",
                    "field": "department_id"
                })
            
            return {
                "validation_date": datetime.now().isoformat(),
                "total_issues": len(issues),
                "issues_by_severity": {
                    "high": len([i for i in issues if i["severity"] == "high"]),
                    "medium": len([i for i in issues if i["severity"] == "medium"]),
                    "low": len([i for i in issues if i["severity"] == "low"])
                },
                "issues": issues,
                "overall_health": "good" if len(issues) == 0 else "needs_attention" if any(i["severity"] == "high" for i in issues) else "fair"
            }
            
        except Exception as e:
            raise Exception(f"Failed to validate data integrity: {str(e)}")
    
    def cleanup_orphaned_records(
        self,
        business_id: Optional[int] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Clean up orphaned records in the database"""
        try:
            cleanup_results = []
            
            # Find orphaned salary details
            orphaned_salary_query = self.db.query(EmployeeSalary).filter(
                ~EmployeeSalary.employee_id.in_(
                    self.db.query(Employee.id).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
                )
            )
            
            if business_id:
                # Note: EmployeeSalary doesn't have business_id, so we join with Employee
                orphaned_salary_query = orphaned_salary_query.join(Employee).filter(
                    Employee.business_id == business_id
                )
            
            orphaned_salaries = orphaned_salary_query.all()
            
            if orphaned_salaries:
                cleanup_results.append({
                    "table": "employee_salaries",
                    "count": len(orphaned_salaries),
                    "action": "delete" if not dry_run else "would_delete",
                    "records": [{"id": s.id, "employee_id": s.employee_id} for s in orphaned_salaries[:10]]  # Show first 10
                })
                
                if not dry_run:
                    for salary in orphaned_salaries:
                        self.db.delete(salary)
            
            # Find orphaned employee deductions
            orphaned_deductions_query = self.db.query(EmployeeDeduction).filter(
                ~EmployeeDeduction.employee_id.in_(
                    self.db.query(Employee.id).filter(Employee.employee_status == EmployeeStatus.ACTIVE)
                )
            )
            
            if business_id:
                orphaned_deductions_query = orphaned_deductions_query.filter(
                    EmployeeDeduction.business_id == business_id
                )
            
            orphaned_deductions = orphaned_deductions_query.all()
            
            if orphaned_deductions:
                cleanup_results.append({
                    "table": "employee_deductions",
                    "count": len(orphaned_deductions),
                    "action": "delete" if not dry_run else "would_delete",
                    "records": [{"id": d.id, "employee_id": d.employee_id} for d in orphaned_deductions[:10]]
                })
                
                if not dry_run:
                    for deduction in orphaned_deductions:
                        self.db.delete(deduction)
            
            if not dry_run:
                self.db.commit()
            
            total_orphaned = sum(result["count"] for result in cleanup_results)
            
            return {
                "cleanup_date": datetime.now().isoformat(),
                "dry_run": dry_run,
                "total_orphaned": total_orphaned,
                "cleanup_results": cleanup_results
            }
            
        except Exception as e:
            if not dry_run:
                self.db.rollback()
            raise Exception(f"Failed to cleanup orphaned records: {str(e)}")
    
    def optimize_database_performance(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            optimization_results = []
            
            # Update table statistics (PostgreSQL specific)
            tables_to_analyze = [
                "employees", "employee_salaries", "employee_deductions",
                "departments", "locations", "cost_centers"
            ]
            
            for table in tables_to_analyze:
                try:
                    self.db.execute(text(f"ANALYZE {table}"))
                    optimization_results.append({
                        "operation": "analyze",
                        "table": table,
                        "status": "success"
                    })
                except Exception as e:
                    optimization_results.append({
                        "operation": "analyze",
                        "table": table,
                        "status": "failed",
                        "error": str(e)
                    })
            
            self.db.commit()
            
            return {
                "optimization_date": datetime.now().isoformat(),
                "operations_performed": len(optimization_results),
                "successful_operations": len([r for r in optimization_results if r["status"] == "success"]),
                "failed_operations": len([r for r in optimization_results if r["status"] == "failed"]),
                "results": optimization_results
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to optimize database performance: {str(e)}")
    
    def generate_maintenance_report(
        self,
        business_id: Optional[int] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive maintenance report"""
        try:
            # Get all maintenance information
            status_info = self.get_maintenance_status(business_id)
            validation_result = self.validate_data_integrity(business_id)
            cleanup_preview = self.cleanup_orphaned_records(business_id, dry_run=True)
            
            report = {
                "report_date": datetime.now().isoformat(),
                "business_id": business_id,
                "summary": {
                    "overall_health": validation_result["overall_health"],
                    "total_employees": status_info["employee_statistics"]["total_employees"],
                    "active_employees": status_info["employee_statistics"]["active_employees"],
                    "data_issues": validation_result["total_issues"],
                    "orphaned_records": cleanup_preview["total_orphaned"]
                },
                "detailed_status": status_info,
                "data_validation": validation_result,
                "cleanup_preview": cleanup_preview
            }
            
            if include_recommendations:
                report["recommendations"] = status_info["recommendations"]
            
            return report
            
        except Exception as e:
            raise Exception(f"Failed to generate maintenance report: {str(e)}")