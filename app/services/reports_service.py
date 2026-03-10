"""
Reports Service
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from app.repositories.reports_repository import ReportsRepository
from app.schemas.reports import (
    AIReportQueryCreate, AIReportQueryResponse, ReportTemplateCreate, ReportTemplateResponse,
    GeneratedReportCreate, GeneratedReportResponse, SalaryReportCreate, SalaryReportResponse,
    AttendanceReportCreate, AttendanceReportResponse, EmployeeReportCreate, EmployeeReportResponse,
    StatutoryReportCreate, StatutoryReportResponse, AnnualReportCreate, AnnualReportResponse,
    ActivityLogCreate, ActivityLogResponse, UserFeedbackCreate, UserFeedbackResponse,
    SystemAlertCreate, SystemAlertResponse, ReportFilters, ReportDashboard,
    SalarySummary, AttendanceSummary
)
import json
import random
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class ReportsService:
    """Service for all report-related business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ReportsRepository(db)
    
    # AI Reporting Methods
    async def process_ai_query(self, user_id: int, query_data: AIReportQueryCreate, business_id: int) -> AIReportQueryResponse:
        """Process AI report query"""
        try:
            # Create the query record
            db_query = self.repository.create_ai_query(user_id, query_data)
            
            # Simulate AI processing (in real implementation, this would call an AI service)
            response_data = await self._simulate_ai_processing(query_data.query_text, business_id)
            
            # Update with response
            updated_query = self.repository.update_ai_query_status(
                db_query.id, "completed", response_data
            )
            
            return AIReportQueryResponse.from_orm(updated_query)
        except Exception as e:
            logger.error(f"Error in process_ai_query: {str(e)}")
            # Create a failed query record
            try:
                db_query = self.repository.create_ai_query(user_id, query_data)
                error_response = {
                    "query_type": "error",
                    "result": {
                        "message": f"Error processing query: {str(e)}",
                        "suggestions": ["Try a simpler query", "Check your query syntax"]
                    },
                    "visualization": "text",
                    "export_available": False
                }
                updated_query = self.repository.update_ai_query_status(
                    db_query.id, "failed", error_response
                )
                return AIReportQueryResponse.from_orm(updated_query)
            except:
                # If even creating the error record fails, raise the original error
                raise e
    
    async def _simulate_ai_processing(self, query_text: str, business_id: int) -> Dict[str, Any]:
        """Simulate AI processing of query - fetches REAL data from database"""
        from app.models.employee import Employee, EmployeeStatus
        from app.models.attendance import AttendanceRecord, AttendanceStatus
        from app.models.datacapture import EmployeeSalaryUnit
        from sqlalchemy import func, extract
        from datetime import datetime, date
        
        query_lower = query_text.lower()
        current_year = datetime.now().year
        
        try:
            if "employee" in query_lower and ("join" in query_lower or "joined" in query_lower):
                # Get employees who joined this year - REAL DATA with business isolation
                employees_this_year = self.db.query(Employee).filter(
                    extract('year', Employee.date_of_joining) == current_year,
                    Employee.employee_status == EmployeeStatus.ACTIVE,
                    Employee.business_id == business_id  # CRITICAL: Business isolation
                ).all()
                
                total_employees = self.db.query(Employee).filter(
                    Employee.employee_status == EmployeeStatus.ACTIVE,
                    Employee.business_id == business_id  # CRITICAL: Business isolation
                ).count()
                
                recent_joinings = []
                for emp in employees_this_year[:10]:  # Limit to 10
                    recent_joinings.append({
                        "name": f"{emp.first_name} {emp.last_name}",
                        "join_date": emp.date_of_joining.strftime("%Y-%m-%d") if emp.date_of_joining else "N/A",
                        "department": emp.department.name if emp.department else "N/A"
                    })
                
                return {
                    "query_type": "employee_joining",
                    "result": {
                        "total_employees": total_employees,
                        "joined_this_year": len(employees_this_year),
                        "recent_joinings": recent_joinings
                    },
                    "visualization": "table",
                    "export_available": True
                }
                
            elif "salary" in query_lower or "payroll" in query_lower:
                # Get salary data - REAL DATA from employee_salary_units with business isolation
                salary_data = self.db.query(
                    func.avg(EmployeeSalaryUnit.amount).label('avg_salary'),
                    func.sum(EmployeeSalaryUnit.amount).label('total_payroll'),
                    func.count(func.distinct(EmployeeSalaryUnit.employee_id)).label('employee_count')
                ).join(Employee, EmployeeSalaryUnit.employee_id == Employee.id).filter(
                    EmployeeSalaryUnit.is_active == True,
                    Employee.business_id == business_id  # CRITICAL: Business isolation
                ).first()
                
                avg_salary = float(salary_data.avg_salary) if salary_data.avg_salary else 0
                total_payroll = float(salary_data.total_payroll) if salary_data.total_payroll else 0
                employee_count = salary_data.employee_count or 0
                
                # Get salary distribution with business isolation
                salary_ranges = {
                    "0-30k": self.db.query(func.count(func.distinct(EmployeeSalaryUnit.employee_id))).join(
                        Employee, EmployeeSalaryUnit.employee_id == Employee.id
                    ).filter(
                        EmployeeSalaryUnit.amount < 30000,
                        EmployeeSalaryUnit.is_active == True,
                        Employee.business_id == business_id
                    ).scalar() or 0,
                    "30k-50k": self.db.query(func.count(func.distinct(EmployeeSalaryUnit.employee_id))).join(
                        Employee, EmployeeSalaryUnit.employee_id == Employee.id
                    ).filter(
                        EmployeeSalaryUnit.amount >= 30000,
                        EmployeeSalaryUnit.amount < 50000,
                        EmployeeSalaryUnit.is_active == True,
                        Employee.business_id == business_id
                    ).scalar() or 0,
                    "50k-75k": self.db.query(func.count(func.distinct(EmployeeSalaryUnit.employee_id))).join(
                        Employee, EmployeeSalaryUnit.employee_id == Employee.id
                    ).filter(
                        EmployeeSalaryUnit.amount >= 50000,
                        EmployeeSalaryUnit.amount < 75000,
                        EmployeeSalaryUnit.is_active == True,
                        Employee.business_id == business_id
                    ).scalar() or 0,
                    "75k+": self.db.query(func.count(func.distinct(EmployeeSalaryUnit.employee_id))).join(
                        Employee, EmployeeSalaryUnit.employee_id == Employee.id
                    ).filter(
                        EmployeeSalaryUnit.amount >= 75000,
                        EmployeeSalaryUnit.is_active == True,
                        Employee.business_id == business_id
                    ).scalar() or 0
                }
                
                return {
                    "query_type": "salary_analysis",
                    "result": {
                        "average_salary": round(avg_salary, 2),
                        "total_payroll": round(total_payroll, 2),
                        "employee_count": employee_count,
                        "salary_distribution": salary_ranges
                    },
                    "visualization": "chart",
                    "export_available": True
                }
                
            elif "attendance" in query_lower:
                # Get attendance data - REAL DATA from attendance_records with business isolation
                today = date.today()
                
                # Get today's attendance with business isolation
                present_today = self.db.query(AttendanceRecord).join(
                    Employee, AttendanceRecord.employee_id == Employee.id
                ).filter(
                    AttendanceRecord.attendance_date == today,
                    AttendanceRecord.attendance_status.in_([AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY]),
                    Employee.business_id == business_id
                ).count()
                
                absent_today = self.db.query(AttendanceRecord).join(
                    Employee, AttendanceRecord.employee_id == Employee.id
                ).filter(
                    AttendanceRecord.attendance_date == today,
                    AttendanceRecord.attendance_status == AttendanceStatus.ABSENT,
                    Employee.business_id == business_id
                ).count()
                
                # Calculate overall attendance percentage with business isolation
                total_attendance_records = self.db.query(AttendanceRecord).join(
                    Employee, AttendanceRecord.employee_id == Employee.id
                ).filter(
                    extract('year', AttendanceRecord.attendance_date) == current_year,
                    Employee.business_id == business_id
                ).count()
                
                present_records = self.db.query(AttendanceRecord).join(
                    Employee, AttendanceRecord.employee_id == Employee.id
                ).filter(
                    extract('year', AttendanceRecord.attendance_date) == current_year,
                    AttendanceRecord.attendance_status.in_([AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY]),
                    Employee.business_id == business_id
                ).count()
                
                overall_attendance = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
                
                return {
                    "query_type": "attendance_analysis",
                    "result": {
                        "overall_attendance": round(overall_attendance, 2),
                        "present_today": present_today,
                        "absent_today": absent_today,
                        "total_records": total_attendance_records
                    },
                    "visualization": "chart",
                    "export_available": True
                }
                
            elif "department" in query_lower:
                # Get department-wise employee count - REAL DATA with business isolation
                from app.models.department import Department
                
                dept_data = self.db.query(
                    Department.name,
                    func.count(Employee.id).label('employee_count')
                ).join(Employee).filter(
                    Employee.employee_status == EmployeeStatus.ACTIVE,
                    Employee.business_id == business_id  # CRITICAL: Business isolation
                ).group_by(Department.name).all()
                
                departments = []
                for dept in dept_data:
                    departments.append({
                        "department": dept.name,
                        "employee_count": dept.employee_count
                    })
                
                return {
                    "query_type": "department_analysis",
                    "result": {
                        "departments": departments,
                        "total_departments": len(departments)
                    },
                    "visualization": "table",
                    "export_available": True
                }
                
            else:
                # Default response with suggestions
                return {
                    "query_type": "general",
                    "result": {
                        "message": "I can help you with employee, salary, attendance, and department related queries. Please provide more specific details.",
                        "suggestions": [
                            "Show me employees who joined this year",
                            "What is the average salary?",
                            "Show attendance for today",
                            "List all departments with employee count"
                        ]
                    },
                    "visualization": "text",
                    "export_available": False
                }
                
        except Exception as e:
            # Log error and return error response
            logger.error(f"Error processing AI query: {str(e)}")
            return {
                "query_type": "error",
                "result": {
                    "message": f"Error processing query: {str(e)}",
                    "suggestions": [
                        "Try a simpler query",
                        "Check if the database is accessible"
                    ]
                },
                "visualization": "text",
                "export_available": False
            }
    
    def get_user_ai_queries(self, user_id: int, limit: int = 50) -> List[AIReportQueryResponse]:
        """Get user's AI queries"""
        queries = self.repository.get_user_ai_queries(user_id, limit)
        return [AIReportQueryResponse.from_orm(query) for query in queries]
    
    # Report Template Methods
    def create_report_template(self, template_data: ReportTemplateCreate) -> ReportTemplateResponse:
        """Create a new report template"""
        db_template = self.repository.create_report_template(template_data)
        return ReportTemplateResponse.from_orm(db_template)
    
    def get_report_templates(self, category: Optional[str] = None) -> List[ReportTemplateResponse]:
        """Get report templates by category"""
        templates = self.repository.get_report_templates(category)
        return [ReportTemplateResponse.from_orm(template) for template in templates]
    
    # Generated Report Methods
    def generate_report(self, user_id: int, report_data: GeneratedReportCreate) -> GeneratedReportResponse:
        """Generate a new report"""
        db_report = self.repository.create_generated_report(user_id, report_data)
        
        # Simulate report generation (in real implementation, this would be async)
        file_path = f"/reports/{db_report.report_type}_{db_report.id}.xlsx"
        self.repository.update_generated_report_status(db_report.id, "completed", file_path)
        
        return GeneratedReportResponse.from_orm(db_report)
    
    def get_generated_reports(self, user_id: int, limit: int = 100) -> List[GeneratedReportResponse]:
        """Get user's generated reports"""
        reports = self.repository.get_generated_reports(user_id, limit)
        return [GeneratedReportResponse.from_orm(report) for report in reports]
    
    # Salary Report Methods
    def create_salary_report(self, report_data: SalaryReportCreate) -> SalaryReportResponse:
        """Create a new salary report"""
        db_report = self.repository.create_salary_report(report_data)
        return SalaryReportResponse.from_orm(db_report)
    
    def get_salary_reports(self, filters: ReportFilters) -> List[SalaryReportResponse]:
        """Get salary reports with filters"""
        reports = self.repository.get_salary_reports(filters)
        return [SalaryReportResponse.from_orm(report) for report in reports]
    
    def get_salary_summary_report(self, month: str, business_id: int) -> Dict[str, Any]:
        """Get salary summary grouped by cost centers, locations, departments, and grades"""
        try:
            # Parse month (e.g., "SEP-2025" to "2025-09")
            from datetime import datetime
            month_obj = datetime.strptime(month, "%b-%Y")
            period = month_obj.strftime('%Y-%m')
            
            # Get salary reports for the period with business isolation
            salary_reports = self.repository.get_salary_reports_for_summary(period, business_id)
            
            # Initialize summary data
            summary_data = {
                "cost_centers": [],
                "locations": [],
                "departments": [],
                "grades": []
            }
            
            if not salary_reports:
                # Return empty data with predefined categories
                summary_data["cost_centers"] = [
                    {"name": "Associate Software Engineer", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "HR Executive", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0}
                ]
                summary_data["locations"] = [
                    {"name": "Hyderabad", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0}
                ]
                summary_data["departments"] = [
                    {"name": "OD Team", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Product Development Team", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Technical Support", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0}
                ]
                summary_data["grades"] = [
                    {"name": "Associate", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Default Grade", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Engineer", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Executive", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Manager", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Senior Engineer", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Supervisor", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Testing Engineer", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0},
                    {"name": "Trainee", "employees": 0, "payDays": 0.0, "earnings": 0.0, "deductions": 0.0}
                ]
                return summary_data
            
            # Group data by different categories
            cost_center_data = {}
            location_data = {}
            department_data = {}
            grade_data = {}
            
            for result in salary_reports:
                # Extract salary report and related data
                if hasattr(result, 'SalaryReport'):
                    report = result.SalaryReport
                    designation_name = result.designation_name or 'Unknown'
                    location_name = result.location_name or 'Hyderabad'
                    department_name = result.department_name or 'General'
                    grade_name = result.grade_name or 'Default Grade'
                else:
                    # Handle case where result is the report itself
                    report = result
                    designation_name = 'Unknown'
                    location_name = 'Hyderabad'
                    department_name = 'General'
                    grade_name = 'Default Grade'
                
                # Cost Centers (using designation)
                if designation_name not in cost_center_data:
                    cost_center_data[designation_name] = {
                        "name": designation_name,
                        "employees": 0,
                        "payDays": 0.0,
                        "earnings": 0.0,
                        "deductions": 0.0
                    }
                cost_center_data[designation_name]["employees"] += 1
                cost_center_data[designation_name]["payDays"] += 30.0  # Assuming 30 days
                cost_center_data[designation_name]["earnings"] += float(report.gross_salary)
                cost_center_data[designation_name]["deductions"] += float(report.total_deductions)
                
                # Locations
                if location_name not in location_data:
                    location_data[location_name] = {
                        "name": location_name,
                        "employees": 0,
                        "payDays": 0.0,
                        "earnings": 0.0,
                        "deductions": 0.0
                    }
                location_data[location_name]["employees"] += 1
                location_data[location_name]["payDays"] += 30.0
                location_data[location_name]["earnings"] += float(report.gross_salary)
                location_data[location_name]["deductions"] += float(report.total_deductions)
                
                # Departments
                if department_name not in department_data:
                    department_data[department_name] = {
                        "name": department_name,
                        "employees": 0,
                        "payDays": 0.0,
                        "earnings": 0.0,
                        "deductions": 0.0
                    }
                department_data[department_name]["employees"] += 1
                department_data[department_name]["payDays"] += 30.0
                department_data[department_name]["earnings"] += float(report.gross_salary)
                department_data[department_name]["deductions"] += float(report.total_deductions)
                
                # Grades
                if grade_name not in grade_data:
                    grade_data[grade_name] = {
                        "name": grade_name,
                        "employees": 0,
                        "payDays": 0.0,
                        "earnings": 0.0,
                        "deductions": 0.0
                    }
                grade_data[grade_name]["employees"] += 1
                grade_data[grade_name]["payDays"] += 30.0
                grade_data[grade_name]["earnings"] += float(report.gross_salary)
                grade_data[grade_name]["deductions"] += float(report.total_deductions)
            
            # Convert to lists
            summary_data["cost_centers"] = list(cost_center_data.values())
            summary_data["locations"] = list(location_data.values())
            summary_data["departments"] = list(department_data.values())
            summary_data["grades"] = list(grade_data.values())
            
            return summary_data
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating salary summary report: {e}")
            # Return empty data structure on error
            return {
                "cost_centers": [],
                "locations": [],
                "departments": [],
                "grades": []
            }

    def get_bank_transfer_letter(self, filters: 'BankTransferLetterFilters') -> 'BankTransferLetterResponse':
        """Get bank transfer letter data"""
        from app.schemas.reports import BankTransferEmployee, BankTransferLetterResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Parse period from frontend format (e.g., "OCT-2025" to "2025-10")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "OCT-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-10"
                period = filters.period
            
            logger.info(f"[BANK TRANSFER SERVICE] Requesting data for period={period}, business_id={filters.business_id}")
            
            # Get bank transfer data
            transfer_data = self.repository.get_bank_transfer_data(period, filters.dict())
            
            if not transfer_data:
                logger.warning(f"[BANK TRANSFER SERVICE] No data found for period={period}, business_id={filters.business_id}")
                return BankTransferLetterResponse(
                    period=period,
                    total_employees=0,
                    total_amount=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={
                        "message": f"No bank transfer data found for period {filters.period}. Please ensure payroll has been run and employees have bank details configured.",
                        "period": filters.period,
                        "business_id": filters.business_id
                    },
                    bank_wise_summary={},
                    format_type=filters.format_type or "generic"
                )
            
            # Process data into response format
            employees = []
            total_amount = Decimal('0')
            bank_wise_totals = {}
            
            for salary_report, employee, employee_profile, dept_name, desig_name, loc_name, cc_name in transfer_data:
                # Mask account number for display (show last 4 digits)
                full_account = getattr(employee_profile, 'bank_account_number', '') or ''
                masked_account = f"XXXXXXXX{full_account[-4:]}" if len(full_account) >= 4 else full_account
                
                bank_name = getattr(employee_profile, 'bank_name', '') or 'Unknown Bank'
                bank_ifsc = getattr(employee_profile, 'bank_ifsc_code', '') or ''
                
                # Create employee record
                employee_data = BankTransferEmployee(
                    id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    bank_ifsc=bank_ifsc,
                    bank_name=bank_name,
                    bank_account=masked_account,
                    bank_account_full=full_account,
                    net_amount=salary_report.net_salary,
                    gross_amount=salary_report.gross_salary,
                    deductions=salary_report.total_deductions,
                    bank_branch=getattr(employee_profile, 'bank_branch', None),
                    account_type=getattr(employee_profile, 'account_type', 'Savings'),
                    department=dept_name,
                    designation=desig_name,
                    location=loc_name
                )
                
                employees.append(employee_data)
                total_amount += salary_report.net_salary
                
                # Bank-wise summary
                if bank_name not in bank_wise_totals:
                    bank_wise_totals[bank_name] = {
                        'employee_count': 0,
                        'total_amount': Decimal('0')
                    }
                bank_wise_totals[bank_name]['employee_count'] += 1
                bank_wise_totals[bank_name]['total_amount'] += salary_report.net_salary
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_net_amount": float(total_amount),
                "average_amount": float(total_amount / len(employees)) if employees else 0,
                "unique_banks": len(bank_wise_totals),
                "period_formatted": filters.period
            }
            
            # Convert bank-wise totals to serializable format
            bank_wise_summary = {}
            for bank_name, data in bank_wise_totals.items():
                bank_wise_summary[bank_name] = {
                    'employee_count': data['employee_count'],
                    'total_amount': float(data['total_amount'])
                }
            
            return BankTransferLetterResponse(
                period=period,
                total_employees=len(employees),
                total_amount=total_amount,
                employees=employees,
                filters_applied=filters,
                summary=summary,
                bank_wise_summary=bank_wise_summary,
                format_type=filters.format_type or "generic"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating bank transfer letter: {e}")
            
            return BankTransferLetterResponse(
                period=filters.period,
                total_employees=0,
                total_amount=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating bank transfer letter: {str(e)}"},
                bank_wise_summary={},
                format_type=filters.format_type or "generic"
            )

    def get_salary_slips(self, filters: 'SalarySlipFilters') -> 'SalarySlipResponse':
        """Get comprehensive salary slip data"""
        from app.schemas.reports import SalarySlipEmployee, SalarySlipResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Parse period from frontend format (e.g., "SEP-2025" to "2025-09")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "SEP-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-09"
                period = filters.period
            
            logger.info(f"[SALARY SLIPS SERVICE] Requesting data for period={period}, business_id={filters.business_id}")
            
            # Get salary slip data
            slip_data = self.repository.get_salary_slip_data(period, filters.dict())
            
            if not slip_data:
                logger.warning(f"[SALARY SLIPS SERVICE] No data found for period={period}, business_id={filters.business_id}")
                return SalarySlipResponse(
                    period=period,
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={
                        "message": f"No salary data found for period {filters.period}. Please ensure payroll has been run for this period.",
                        "period": filters.period,
                        "business_id": filters.business_id
                    },
                    is_period_closed=False
                )
            
            # Get employee IDs for attendance data
            employee_ids = [data[1].id for data in slip_data]
            
            # Get attendance summary
            attendance_summary = self.repository.get_attendance_summary_for_register(employee_ids, period)
            
            # Get salary units for employees
            from app.models.datacapture import EmployeeSalaryUnit
            salary_units_query = self.db.query(
                EmployeeSalaryUnit.employee_id,
                EmployeeSalaryUnit.unit_type
            ).filter(EmployeeSalaryUnit.employee_id.in_(employee_ids)).all()
            salary_units_map = {emp_id: unit_type for emp_id, unit_type in salary_units_query}
            
            # Get active loans for employees
            from app.models.datacapture import EmployeeLoan, LoanStatus
            loans_query = self.db.query(
                EmployeeLoan.employee_id,
                EmployeeLoan.loan_amount,
                EmployeeLoan.emi_amount,
                EmployeeLoan.outstanding_amount
            ).filter(
                EmployeeLoan.employee_id.in_(employee_ids),
                EmployeeLoan.status == LoanStatus.ACTIVE
            ).all()
            loans_map = {
                emp_id: {
                    "loan_amount": float(loan_amount or 0),
                    "emi_amount": float(emi_amount or 0),
                    "outstanding": float(outstanding or 0)
                }
                for emp_id, loan_amount, emi_amount, outstanding in loans_query
            }
            
            # Get leave balances for employees
            from app.models.leave_balance import LeaveBalance
            leave_balances_query = self.db.query(
                LeaveBalance.employee_id,
                func.sum(LeaveBalance.opening_balance).label('opening'),
                func.sum(LeaveBalance.activity_balance).label('activity'),
                func.sum(LeaveBalance.correction_balance).label('correction'),
                func.sum(LeaveBalance.closing_balance).label('closing')
            ).filter(
                LeaveBalance.employee_id.in_(employee_ids)
            ).group_by(LeaveBalance.employee_id).all()
            leave_balance_map = {
                emp_id: {
                    "opening_balance": float(opening or 0),
                    "earned": float(opening or 0),  # Use opening as earned for display
                    "taken": float(activity or 0),  # activity_balance represents taken leaves
                    "closing_balance": float(closing or 0)
                }
                for emp_id, opening, activity, correction, closing in leave_balances_query
            }
            
            # Check if period is closed by querying PayrollPeriod (before processing employees)
            from app.models.payroll import PayrollPeriod, PayrollPeriodStatus
            from datetime import datetime
            
            is_period_closed = False
            try:
                # Convert period to date range to find matching payroll period
                period_date = datetime.strptime(period, '%Y-%m')
                
                # Find payroll period that contains this month
                payroll_period = self.db.query(PayrollPeriod).filter(
                    PayrollPeriod.start_date <= period_date,
                    PayrollPeriod.end_date >= period_date
                ).first()
                
                if payroll_period:
                    is_period_closed = payroll_period.status == PayrollPeriodStatus.CLOSED
            except Exception as e:
                logger.warning(f"Could not determine period status: {e}")
                is_period_closed = False
            
            # Process data into response format
            employees = []
            total_gross = 0
            total_net = 0
            total_deductions = 0
            
            for salary_report, employee, dept_name, desig_name, loc_name, grade_name, cc_name in slip_data:
                # Get attendance data for this employee
                attendance = attendance_summary.get(employee.id, {})
                
                # Process earnings and deductions
                earnings = salary_report.allowances or {}
                deductions = salary_report.deductions or {}
                
                # Add basic salary to earnings
                earnings['Basic Salary'] = float(salary_report.basic_salary)
                
                # Calculate total earnings
                total_earnings = sum(float(v) for v in earnings.values())
                
                # Create employee record
                employee_data = SalarySlipEmployee(
                    employee_id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    gender=employee.gender if hasattr(employee, 'gender') else None,
                    date_of_birth=employee.date_of_birth if hasattr(employee, 'date_of_birth') else None,
                    date_of_joining=employee.date_of_joining,
                    date_of_exit=employee.date_of_termination if hasattr(employee, 'date_of_termination') else None,
                    designation=desig_name,
                    department=dept_name,
                    location=loc_name,
                    cost_center=cc_name,
                    
                    # Personal Details - from database
                    esi_ip_number=employee.esi_number if hasattr(employee, 'esi_number') else None,
                    pf_uan_number=employee.uan_number if hasattr(employee, 'uan_number') else None,
                    income_tax_pan=employee.pan_number if hasattr(employee, 'pan_number') else None,
                    aadhar_number=employee.aadhaar_number if hasattr(employee, 'aadhaar_number') else None,
                    office_email=employee.email,
                    mobile_number=employee.mobile,
                    bank_name=employee.bank_name if hasattr(employee, 'bank_name') else None,
                    bank_ifsc=employee.bank_ifsc_code if hasattr(employee, 'bank_ifsc_code') else None,
                    bank_account=employee.bank_account_number if hasattr(employee, 'bank_account_number') else None,
                    
                    # Attendance Data - from database
                    presents=attendance.get('presents', 0),
                    absents=attendance.get('absents', 0),
                    week_offs=attendance.get('week_offs', 0),
                    holidays=attendance.get('holidays', 0),
                    paid_leaves=attendance.get('paid_leaves', 0),
                    unpaid_leaves=attendance.get('unpaid_leaves', 0),
                    total_days=attendance.get('total_days', 0),
                    extra_days=attendance.get('extra_days', 0),
                    arrear_days=attendance.get('arrear_days', 0),
                    overtime_days=attendance.get('overtime_days', 0),
                    payable_days=attendance.get('payable_days', 0),
                    unpaid_days=attendance.get('unpaid_days', 0),
                    
                    # Salary Data - from database
                    basic_salary=salary_report.basic_salary,
                    gross_salary=salary_report.gross_salary,
                    net_salary=salary_report.net_salary,
                    total_deductions=salary_report.total_deductions,
                    total_earnings=Decimal(str(total_earnings)),
                    
                    # Detailed Components - from database
                    earnings={k: Decimal(str(v)) for k, v in earnings.items()},
                    deductions={k: Decimal(str(v)) for k, v in deductions.items()},
                    
                    # Additional Info - from database
                    salary_units=salary_units_map.get(employee.id, 'Monthly'),
                    other_info_1=employee.other_info_1 if hasattr(employee, 'other_info_1') else None,
                    other_info_2=employee.other_info_2 if hasattr(employee, 'other_info_2') else None,
                    other_info_3=employee.other_info_3 if hasattr(employee, 'other_info_3') else None,
                    other_info_4=employee.other_info_4 if hasattr(employee, 'other_info_4') else None,
                    other_info_5=employee.other_info_5 if hasattr(employee, 'other_info_5') else None,
                    
                    # Slip Specific Data - from database
                    is_provisional=not is_period_closed,
                    leave_summary=leave_balance_map.get(employee.id, {
                        "opening_balance": 0,
                        "earned": 0,
                        "taken": 0,
                        "closing_balance": 0
                    }),
                    loan_summary=loans_map.get(employee.id, {
                        "loan_amount": 0,
                        "emi_amount": 0,
                        "outstanding": 0
                    }),
                    tax_summary={
                        "taxable_income": float(salary_report.gross_salary),
                        "tax_deducted": float(deductions.get('Income Tax', deductions.get('TDS', deductions.get('tax', 0)))),
                        "tds_ytd": float(deductions.get('Income Tax', deductions.get('TDS', deductions.get('tax', 0)))) * 12
                    },
                    period_date=f"{period}-01"
                )
                
                employees.append(employee_data)
                total_gross += float(salary_report.gross_salary)
                total_net += float(salary_report.net_salary)
                total_deductions += float(salary_report.total_deductions)
            
            # Create summary
            summary = {
                "total_gross_salary": total_gross,
                "total_net_salary": total_net,
                "total_deductions": total_deductions,
                "average_gross_salary": total_gross / len(employees) if employees else 0,
                "average_net_salary": total_net / len(employees) if employees else 0,
                "total_employees_processed": len(employees)
            }
            
            return SalarySlipResponse(
                period=period,
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary,
                is_period_closed=is_period_closed
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating salary slips: {e}")
            
            return SalarySlipResponse(
                period=filters.period,
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating salary slips: {str(e)}"},
                is_period_closed=False
            )

    def get_salary_register(self, filters: 'SalaryRegisterFilters') -> 'SalaryRegisterResponse':
        """Get comprehensive salary register data"""
        from app.schemas.reports import SalaryRegisterEmployee, SalaryRegisterResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Parse period from frontend format (e.g., "JUL-2025" to "2025-07")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUL-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-07"
                period = filters.period
            
            logger.info(f"[SALARY REGISTER SERVICE] Requesting data for period={period}, business_id={filters.business_id}")
            
            # Get salary register data
            register_data = self.repository.get_salary_register_data(period, filters.dict())
            
            if not register_data:
                logger.warning(f"[SALARY REGISTER SERVICE] No data found for period={period}, business_id={filters.business_id}")
                return SalaryRegisterResponse(
                    period=period,
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={
                        "message": f"No salary data found for period {filters.period}. Please ensure payroll has been run for this period.",
                        "period": filters.period,
                        "business_id": filters.business_id
                    }
                )
            
            # Get employee IDs for attendance data
            employee_ids = [data[1].id for data in register_data]
            
            # Get attendance summary
            attendance_summary = self.repository.get_attendance_summary_for_register(employee_ids, period)
            
            # Process data into response format
            employees = []
            total_gross = 0
            total_net = 0
            total_deductions = 0
            
            for salary_report, employee, dept_name, desig_name, loc_name, grade_name, cc_name in register_data:
                # Get attendance data for this employee
                attendance = attendance_summary.get(employee.id, {})
                
                # Create employee record
                employee_data = SalaryRegisterEmployee(
                    employee_id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    gender=getattr(employee, 'gender', None),
                    date_of_birth=getattr(employee, 'date_of_birth', None),
                    date_of_joining=employee.date_of_joining,
                    date_of_exit=getattr(employee, 'date_of_termination', None),
                    designation=desig_name,
                    department=dept_name,
                    location=loc_name,
                    cost_center=cc_name,
                    
                    # Personal Details
                    esi_ip_number=getattr(employee, 'esi_number', None),
                    pf_uan_number=getattr(employee, 'pf_number', None),
                    income_tax_pan=getattr(employee, 'pan_number', None),
                    aadhar_number=getattr(employee, 'aadhar_number', None),
                    office_email=employee.email,
                    mobile_phone=employee.mobile,
                    bank_name=getattr(employee, 'bank_name', None),
                    bank_ifsc=getattr(employee, 'bank_ifsc', None),
                    bank_account=getattr(employee, 'bank_account_number', None),
                    
                    # Attendance Data
                    total_days=attendance.get('total_days', 30),
                    presents=attendance.get('presents', 22),
                    absents=attendance.get('absents', 0),
                    week_offs=attendance.get('week_offs', 8),
                    holidays=attendance.get('holidays', 2),
                    extra_days=attendance.get('extra_days', 0),
                    arrear_days=attendance.get('arrear_days', 0),
                    overtime_days=attendance.get('overtime_days', 0),
                    paid_leaves=attendance.get('paid_leaves', 0),
                    unpaid_leaves=attendance.get('unpaid_leaves', 0),
                    payable_days=attendance.get('payable_days', 22),
                    unpaid_days=attendance.get('unpaid_days', 0),
                    
                    # Salary Data
                    basic_salary=salary_report.basic_salary,
                    gross_salary=salary_report.gross_salary,
                    net_salary=salary_report.net_salary,
                    total_deductions=salary_report.total_deductions,
                    allowances=salary_report.allowances,
                    deductions=salary_report.deductions,
                    
                    # Additional Info
                    salary_units=getattr(employee, 'salary_units', 'Monthly'),
                    other_info_1=getattr(employee, 'other_info_1', None),
                    other_info_2=getattr(employee, 'other_info_2', None),
                    other_info_3=getattr(employee, 'other_info_3', None),
                    other_info_4=getattr(employee, 'other_info_4', None),
                    other_info_5=getattr(employee, 'other_info_5', None)
                )
                
                employees.append(employee_data)
                total_gross += float(salary_report.gross_salary)
                total_net += float(salary_report.net_salary)
                total_deductions += float(salary_report.total_deductions)
            
            # Create summary
            summary = {
                "total_gross_salary": total_gross,
                "total_net_salary": total_net,
                "total_deductions": total_deductions,
                "average_gross_salary": total_gross / len(employees) if employees else 0,
                "average_net_salary": total_net / len(employees) if employees else 0
            }
            
            return SalaryRegisterResponse(
                period=period,
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating salary register: {e}")
            
            return SalaryRegisterResponse(
                period=filters.period,
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating salary register: {str(e)}"}
            )

    def get_cost_to_company_report(self, filters: 'CostToCompanyFilters') -> 'CostToCompanyResponse':
        """Get cost to company report data"""
        from app.schemas.reports import CostToCompanyEmployee, CostToCompanyResponse, CostToCompanySalaryComponent
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[COST TO COMPANY SERVICE] Requesting data for business_id={filters.business_id}")
            
            # Get cost to company data
            ctc_data = self.repository.get_cost_to_company_data(filters.dict())
            
            if not ctc_data:
                logger.warning(f"[COST TO COMPANY SERVICE] No data found for business_id={filters.business_id}")
                return CostToCompanyResponse(
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={
                        "message": "No employee salary data found. Please ensure employees have salary structures configured.",
                        "business_id": filters.business_id
                    }
                )
            
            # Get business ID from first employee (assuming all employees belong to same business)
            business_id = ctc_data[0][1].business_id if ctc_data else 1
            
            # Get salary components for the business
            salary_components = self.repository.get_salary_components_for_business(business_id)
            
            # Create component lookup
            component_lookup = {comp.id: comp for comp in salary_components}
            
            # Process data into response format
            employees = []
            total_ctc = Decimal('0')
            
            for salary_record, employee, dept_name, desig_name, loc_name, cc_name, structure_name in ctc_data:
                # Calculate revision number (simplified - based on count of salary records)
                revision_count = len([s for s in ctc_data if s[1].id == employee.id])
                
                # Generate salary components breakdown
                earnings, deductions, employer_contributions = self._generate_salary_breakdown(
                    salary_record, component_lookup
                )
                
                # Calculate totals
                total_earnings = sum(comp.amount for comp in earnings)
                total_deductions = sum(comp.amount for comp in deductions)
                total_employer_contribs = sum(comp.amount for comp in employer_contributions)
                net_payable = total_earnings - total_deductions
                
                # Create employee record
                employee_data = CostToCompanyEmployee(
                    id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    designation=desig_name,
                    department=dept_name,
                    location=loc_name,
                    cost_center=cc_name,
                    date_of_joining=employee.date_of_joining,
                    
                    # Salary Structure Info
                    salary_structure_name=structure_name or "Default Structure",
                    effective_from=salary_record.effective_from,
                    revision_number=revision_count,
                    
                    # Basic Salary Components
                    basic_salary=salary_record.basic_salary,
                    gross_salary=salary_record.gross_salary,
                    total_ctc=salary_record.ctc,
                    
                    # Detailed Components
                    earnings=earnings,
                    deductions=deductions,
                    employer_contributions=employer_contributions,
                    
                    # Summary Totals
                    total_earnings=total_earnings,
                    total_deductions=total_deductions,
                    total_employer_contributions=total_employer_contribs,
                    net_payable=net_payable
                )
                
                employees.append(employee_data)
                total_ctc += salary_record.ctc
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_ctc": float(total_ctc),
                "average_ctc": float(total_ctc / len(employees)) if employees else 0,
                "revision_type": filters.revision,
                "active_only": filters.active_only
            }
            
            return CostToCompanyResponse(
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating cost to company report: {e}")
            
            return CostToCompanyResponse(
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating cost to company report: {str(e)}"}
            )

    def _generate_salary_breakdown(self, salary_record, component_lookup):
        """Generate detailed salary component breakdown"""
        from app.schemas.reports import CostToCompanySalaryComponent
        
        # Standard salary components breakdown
        earnings = []
        deductions = []
        employer_contributions = []
        
        basic_salary = salary_record.basic_salary
        gross_salary = salary_record.gross_salary
        
        # Basic Salary (always present)
        earnings.append(CostToCompanySalaryComponent(
            component_name="Basic Salary",
            component_alias="Basic",
            component_type="Fixed",
            amount=basic_salary,
            is_employer_contribution=False,
            is_payable=True,
            percentage_of_basic=100.0
        ))
        
        # House Rent Allowance (40% of basic)
        hra_amount = basic_salary * Decimal('0.40')
        earnings.append(CostToCompanySalaryComponent(
            component_name="House Rent Allowance",
            component_alias="HRA",
            component_type="Fixed",
            amount=hra_amount,
            is_employer_contribution=False,
            is_payable=True,
            percentage_of_basic=40.0
        ))
        
        # Special Allowance (to make up gross)
        special_allowance = gross_salary - basic_salary - hra_amount
        if special_allowance > 0:
            earnings.append(CostToCompanySalaryComponent(
                component_name="Special Allowance",
                component_alias="SA",
                component_type="Fixed",
                amount=special_allowance,
                is_employer_contribution=False,
                is_payable=True,
                percentage_of_basic=float((special_allowance / basic_salary) * 100) if basic_salary > 0 else 0
            ))
        
        # Medical Allowance (fixed amount)
        medical_allowance = Decimal('1250')
        earnings.append(CostToCompanySalaryComponent(
            component_name="Medical Allowance",
            component_alias="Medical",
            component_type="Fixed",
            amount=medical_allowance,
            is_employer_contribution=False,
            is_payable=True,
            percentage_of_basic=float((medical_allowance / basic_salary) * 100) if basic_salary > 0 else 0
        ))
        
        # Conveyance Allowance (fixed amount)
        conveyance_allowance = Decimal('1600')
        earnings.append(CostToCompanySalaryComponent(
            component_name="Conveyance Allowance",
            component_alias="Conveyance",
            component_type="Fixed",
            amount=conveyance_allowance,
            is_employer_contribution=False,
            is_payable=True,
            percentage_of_basic=float((conveyance_allowance / basic_salary) * 100) if basic_salary > 0 else 0
        ))
        
        # Deductions
        # Professional Tax
        pt_amount = Decimal('200')
        deductions.append(CostToCompanySalaryComponent(
            component_name="Professional Tax",
            component_alias="PT",
            component_type="Deduction",
            amount=pt_amount,
            is_employer_contribution=False,
            is_payable=False
        ))
        
        # Employee PF (12% of basic)
        epf_amount = basic_salary * Decimal('0.12')
        deductions.append(CostToCompanySalaryComponent(
            component_name="Employee PF",
            component_alias="EPF",
            component_type="Deduction",
            amount=epf_amount,
            is_employer_contribution=False,
            is_payable=False,
            percentage_of_basic=12.0
        ))
        
        # Employee ESI (0.75% of gross, if gross <= 21000)
        if gross_salary <= 21000:
            esi_amount = gross_salary * Decimal('0.0075')
            deductions.append(CostToCompanySalaryComponent(
                component_name="Employee ESI",
                component_alias="ESI",
                component_type="Deduction",
                amount=esi_amount,
                is_employer_contribution=False,
                is_payable=False,
                percentage_of_basic=float((esi_amount / basic_salary) * 100) if basic_salary > 0 else 0
            ))
        
        # Employer Contributions
        # Employer PF (12% of basic)
        employer_pf = basic_salary * Decimal('0.12')
        employer_contributions.append(CostToCompanySalaryComponent(
            component_name="Employer PF",
            component_alias="Employer PF",
            component_type="Employer Contribution",
            amount=employer_pf,
            is_employer_contribution=True,
            is_payable=False,
            percentage_of_basic=12.0
        ))
        
        # Employer ESI (3.25% of gross, if gross <= 21000)
        if gross_salary <= 21000:
            employer_esi = gross_salary * Decimal('0.0325')
            employer_contributions.append(CostToCompanySalaryComponent(
                component_name="Employer ESI",
                component_alias="Employer ESI",
                component_type="Employer Contribution",
                amount=employer_esi,
                is_employer_contribution=True,
                is_payable=False,
                percentage_of_basic=float((employer_esi / basic_salary) * 100) if basic_salary > 0 else 0
            ))
        
        # Gratuity (4.81% of basic)
        gratuity_amount = basic_salary * Decimal('0.0481')
        employer_contributions.append(CostToCompanySalaryComponent(
            component_name="Gratuity",
            component_alias="Gratuity",
            component_type="Employer Contribution",
            amount=gratuity_amount,
            is_employer_contribution=True,
            is_payable=False,
            percentage_of_basic=4.81
        ))
        
        # Bonus (8.33% of basic)
        bonus_amount = basic_salary * Decimal('0.0833')
        employer_contributions.append(CostToCompanySalaryComponent(
            component_name="Bonus",
            component_alias="Bonus",
            component_type="Employer Contribution",
            amount=bonus_amount,
            is_employer_contribution=True,
            is_payable=False,
            percentage_of_basic=8.33
        ))
        
        return earnings, deductions, employer_contributions

    def get_overtime_register(self, filters: 'OvertimeRegisterFilters') -> 'OvertimeRegisterResponse':
        """Get overtime register data"""
        from app.schemas.reports import OvertimeRegisterEmployee, OvertimeRegisterResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Parse period from frontend format (e.g., "JUN-2025" to "2025-06")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUN-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-06"
                period = filters.period
            
            logger.info(f"[OVERTIME REGISTER SERVICE] Requesting data for period={period}, business_id={filters.business_id}")
            
            # Get overtime register data
            overtime_data = self.repository.get_overtime_register_data(period, filters.dict())
            
            if not overtime_data:
                logger.warning(f"[OVERTIME REGISTER SERVICE] No data found for period={period}, business_id={filters.business_id}")
                return OvertimeRegisterResponse(
                    period=period,
                    total_employees=0,
                    total_overtime_hours=0.0,
                    total_overtime_earnings=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={
                        "message": f"No overtime data found for period {filters.period}. Please ensure overtime hours have been recorded and approved for this period.",
                        "period": filters.period,
                        "business_id": filters.business_id
                    }
                )
            
            # Process data into response format
            employees = []
            total_overtime_hours = 0.0
            total_overtime_earnings = Decimal('0')
            
            for extra_hour, employee, employee_profile, dept_name, desig_name, loc_name, cc_name in overtime_data:
                # Calculate normal rate from overtime rate and hours
                # Normal rate = overtime_rate / overtime_multiplier (typically 2.0)
                # This assumes overtime is paid at 2x the normal rate
                normal_rate = float(extra_hour.overtime_rate) / 2.0 if extra_hour.overtime_rate else 0
                
                # Get father's name from employee profile
                father_name = getattr(employee_profile, 'father_name', None) or f"Father of {employee.first_name}"
                
                # Get fixed gross from employee's salary data (from salary_reports or employee_profiles)
                # For now, calculate from overtime rate assuming 8 hours per day, 26 days per month
                fixed_gross = Decimal(str(normal_rate * 8 * 26)) if normal_rate > 0 else Decimal('0')
                
                # Create employee record
                employee_data = OvertimeRegisterEmployee(
                    id=employee.id,
                    employee_code=employee.employee_code,
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    father_name=father_name,
                    sex=getattr(employee, 'gender', 'Male'),
                    designation=desig_name or 'Not Assigned',
                    date=extra_hour.work_date.strftime('%Y-%m-%d'),
                    overtime_hrs=float(extra_hour.extra_hours),
                    fixed_gross=fixed_gross,
                    normal_rate=Decimal(str(normal_rate)),
                    overtime_rate=extra_hour.overtime_rate,
                    overtime_earnings=extra_hour.total_amount,
                    payment_date=filters.payment_date,
                    remarks="",
                    department=dept_name,
                    location=loc_name,
                    cost_center=cc_name
                )
                
                employees.append(employee_data)
                total_overtime_hours += float(extra_hour.extra_hours)
                total_overtime_earnings += extra_hour.total_amount
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_overtime_hours": total_overtime_hours,
                "total_overtime_earnings": float(total_overtime_earnings),
                "average_overtime_hours": total_overtime_hours / len(employees) if employees else 0,
                "average_overtime_earnings": float(total_overtime_earnings / len(employees)) if employees else 0,
                "period_formatted": filters.period
            }
            
            return OvertimeRegisterResponse(
                period=period,
                total_employees=len(employees),
                total_overtime_hours=total_overtime_hours,
                total_overtime_earnings=total_overtime_earnings,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating overtime register: {e}")
            
            return OvertimeRegisterResponse(
                period=filters.period,
                total_employees=0,
                total_overtime_hours=0.0,
                total_overtime_earnings=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating overtime register: {str(e)}"}
            )

    def get_time_salary_report(self, filters: 'TimeSalaryFilters') -> 'TimeSalaryResponse':
        """Get time salary report data"""
        from app.schemas.reports import TimeSalaryEmployee, TimeSalaryResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[TIME SALARY SERVICE] Requesting data for business_id={filters.business_id}, period={filters.period}")
            
            # Parse period from frontend format (e.g., "MAR-2025" to "2025-03")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "MAR-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-03"
                period = filters.period
            
            # Get time salary data
            time_salary_data = self.repository.get_time_salary_data(period, filters.dict())
            
            if not time_salary_data:
                logger.warning(f"[TIME SALARY SERVICE] No data found for business_id={filters.business_id}, period={period}")
                return TimeSalaryResponse(
                    period=period,
                    total_employees=0,
                    total_amount=Decimal('0'),
                    total_hours=0.0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No time salary data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_amount = Decimal('0')
            total_hours = 0.0
            
            for emp_data, attendance in time_salary_data:
                employee = emp_data[0]
                dept_name = emp_data[1]
                desig_name = emp_data[2]
                loc_name = emp_data[3]
                time_rule = emp_data[4]
                component_name = emp_data[5]
                
                # Calculate rates and amounts based on time rules and attendance
                # Default values
                payment_type = "Monthly"
                hourly_rate = Decimal('0')
                daily_rate = Decimal('0')
                monthly_rate = Decimal('0')
                
                # Get basic salary for calculations
                from app.models.employee import EmployeeSalary
                salary_record = self.db.query(EmployeeSalary).filter(
                    EmployeeSalary.employee_id == employee.id,
                    EmployeeSalary.is_active == True
                ).first()
                
                if salary_record:
                    basic_salary = salary_record.basic_salary
                    monthly_rate = basic_salary
                    
                    # Calculate hourly and daily rates
                    # Assuming 8 hours per day, 22 working days per month
                    daily_rate = basic_salary / 22
                    hourly_rate = daily_rate / 8
                    
                    # Determine payment type based on time rule or default to hourly for time-based
                    if time_rule:
                        payment_type = "Hourly"  # Time-based salary is typically hourly
                    else:
                        payment_type = "Monthly"
                
                # Get attendance data
                total_hours_worked = attendance.get('total_hours', 0)
                total_days_worked = attendance.get('present_days', 0)
                overtime_hours = attendance.get('overtime_hours', 0)
                overtime_amount = Decimal(str(attendance.get('overtime_amount', 0)))
                
                # Calculate amounts based on payment type
                if payment_type == "Hourly":
                    regular_amount = hourly_rate * Decimal(str(total_hours_worked))
                elif payment_type == "Daily":
                    regular_amount = daily_rate * Decimal(str(total_days_worked))
                else:  # Monthly
                    regular_amount = monthly_rate
                
                total_emp_amount = regular_amount + overtime_amount
                
                # Create employee record
                employee_data = TimeSalaryEmployee(
                    id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    department=dept_name or 'General',
                    designation=desig_name or 'Associate',
                    location=loc_name or 'Head Office',
                    
                    # Time-based salary details
                    payment_type=payment_type,
                    hourly_rate=hourly_rate,
                    daily_rate=daily_rate,
                    monthly_rate=monthly_rate,
                    
                    # Time calculations
                    total_hours=total_hours_worked,
                    total_days=total_days_worked,
                    overtime_hours=overtime_hours,
                    
                    # Amount calculations
                    regular_amount=regular_amount,
                    overtime_amount=overtime_amount,
                    total_amount=total_emp_amount,
                    
                    # Additional details
                    shift_name=time_rule.shift if time_rule else "Regular",
                    attendance_percentage=round((total_days_worked / 22) * 100, 2) if total_days_worked > 0 else 0
                )
                
                employees.append(employee_data)
                total_amount += total_emp_amount
                total_hours += total_hours_worked
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_amount": float(total_amount),
                "total_hours": total_hours,
                "average_amount": float(total_amount / len(employees)) if employees else 0,
                "average_hours": total_hours / len(employees) if employees else 0,
                "period_formatted": filters.period
            }
            
            return TimeSalaryResponse(
                period=period,
                total_employees=len(employees),
                total_amount=total_amount,
                total_hours=total_hours,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating time salary report: {e}")
            
            return TimeSalaryResponse(
                period=filters.period,
                total_employees=0,
                total_amount=Decimal('0'),
                total_hours=0.0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating time salary report: {str(e)}"}
            )

    def get_statutory_bonus_report(self, filters: 'StatutoryBonusReportFilters') -> 'StatutoryBonusReportResponse':
        """Get statutory bonus report data"""
        from app.schemas.reports import StatutoryBonusReportEmployee, StatutoryBonusReportResponse
        
        try:
            # Parse period from frontend format (e.g., "JUL-2025" to "2025-07")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUL-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-07"
                period = filters.period
            
            # Get statutory bonus report data
            bonus_data = self.repository.get_statutory_bonus_report_data(period, filters.dict())
            
            if not bonus_data:
                return StatutoryBonusReportResponse(
                    period=period,
                    total_employees=0,
                    total_bonus_amount=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No statutory bonus data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_bonus_amount = Decimal('0')
            
            for data_row in bonus_data:
                # Check if this is StatutoryBonus data or SalaryVariable data
                if hasattr(data_row[0], 'bonus_amount'):
                    # StatutoryBonus table data
                    bonus = data_row[0]
                    employee = data_row[1]
                    dept_name = data_row[2]
                    desig_name = data_row[3]
                    loc_name = data_row[4]
                    cc_name = data_row[5]
                    
                    # Get payment date from PayrollPeriod
                    from app.models.payroll import PayrollPeriod
                    period_record = self.db.query(PayrollPeriod).filter(
                        PayrollPeriod.id == bonus.period_id
                    ).first()
                    payment_date = period_record.start_date if period_record else None
                    
                    employee_data = StatutoryBonusReportEmployee(
                        id=employee.id,
                        employee_code=employee.employee_code,
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        department=dept_name or 'IT',
                        designation=desig_name or 'Software Engineer',
                        location=loc_name or 'Hyderabad',
                        cost_center=cc_name or 'Default',
                        comments=f"Statutory bonus as per compliance - {bonus.bonus_rate}% of eligible salary",
                        bonus_amount=bonus.bonus_amount,
                        base_salary=bonus.base_salary,
                        bonus_rate=bonus.bonus_rate,
                        eligibility_status="Eligible",
                        payment_date=payment_date,
                        is_processed=bonus.is_processed
                    )
                    
                    total_bonus_amount += bonus.bonus_amount
                else:
                    # SalaryVariable table data
                    salary_variable = data_row[0]
                    employee = data_row[1]
                    dept_name = data_row[2]
                    desig_name = data_row[3]
                    loc_name = data_row[4]
                    cc_name = data_row[5]
                    
                    # Get employee salary for base salary calculation
                    from app.models.employee import EmployeeSalary
                    salary_record = self.db.query(EmployeeSalary).filter(
                        EmployeeSalary.employee_id == employee.id,
                        EmployeeSalary.is_active == True
                    ).first()
                    
                    base_salary = salary_record.basic_salary if salary_record else Decimal('0')
                    bonus_rate = 8.33  # Standard statutory bonus rate
                    
                    # Determine bonus type from variable name
                    if 'performance' in salary_variable.variable_name.lower():
                        comments = "Performance Bonus"
                    elif 'annual' in salary_variable.variable_name.lower():
                        comments = "Annual Bonus"
                    elif 'statutory' in salary_variable.variable_name.lower():
                        comments = "Statutory Bonus as per compliance"
                    else:
                        comments = f"Bonus payment - {salary_variable.variable_name}"
                    
                    employee_data = StatutoryBonusReportEmployee(
                        id=employee.id,
                        employee_code=employee.employee_code,
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        department=dept_name or 'IT',
                        designation=desig_name or 'Software Engineer',
                        location=loc_name or 'Hyderabad',
                        cost_center=cc_name or 'Default',
                        comments=comments,
                        bonus_amount=salary_variable.amount,
                        base_salary=base_salary,
                        bonus_rate=bonus_rate,
                        eligibility_status="Eligible",
                        payment_date=salary_variable.effective_date,
                        is_processed=True
                    )
                    
                    total_bonus_amount += salary_variable.amount
                
                employees.append(employee_data)
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_bonus_amount": float(total_bonus_amount),
                "average_bonus": float(total_bonus_amount / len(employees)) if employees else 0,
                "processed_count": len([emp for emp in employees if emp.is_processed]),
                "pending_count": len([emp for emp in employees if not emp.is_processed]),
                "period_formatted": filters.period,
                "department_breakdown": self._get_department_breakdown_bonus(employees),
                "location_breakdown": self._get_location_breakdown_bonus(employees),
                "eligibility_summary": {
                    "eligible": len([emp for emp in employees if emp.eligibility_status == "Eligible"]),
                    "not_eligible": len([emp for emp in employees if emp.eligibility_status == "Not Eligible"])
                }
            }
            
            return StatutoryBonusReportResponse(
                period=period,
                total_employees=len(employees),
                total_bonus_amount=total_bonus_amount,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating statutory bonus report: {e}")
            
            return StatutoryBonusReportResponse(
                period=filters.period,
                total_employees=0,
                total_bonus_amount=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating statutory bonus report: {str(e)}"}
            )

    def _get_department_breakdown_bonus(self, employees):
        """Get breakdown by department for bonus"""
        breakdown = {}
        for emp in employees:
            dept = emp.department or 'Unknown'
            if dept not in breakdown:
                breakdown[dept] = {'count': 0, 'total_bonus': 0}
            breakdown[dept]['count'] += 1
            breakdown[dept]['total_bonus'] += float(emp.bonus_amount)
        return breakdown

    def _get_location_breakdown_bonus(self, employees):
        """Get breakdown by location for bonus"""
        breakdown = {}
        for emp in employees:
            loc = emp.location or 'Unknown'
            if loc not in breakdown:
                breakdown[loc] = {'count': 0, 'total_bonus': 0}
            breakdown[loc]['count'] += 1
            breakdown[loc]['total_bonus'] += float(emp.bonus_amount)
        return breakdown

    def get_employee_loans_report(self, filters: 'EmployeeLoansFilters') -> 'EmployeeLoansResponse':
        """Get employee loans report data"""
        from app.schemas.reports import EmployeeLoanData, EmployeeLoansResponse, LoanEMISchedule
        from app.models.designations import Designation
        from app.models.datacapture import LoanEMIPayment
        
        try:
            # Get employee loans report data
            loans_data = self.repository.get_employee_loans_report_data(filters.dict())
            
            if not loans_data:
                return EmployeeLoansResponse(
                    total_loans=0,
                    total_loan_amount=Decimal('0'),
                    total_outstanding_amount=Decimal('0'),
                    loans=[],
                    filters_applied=filters,
                    summary={"message": "No employee loans data found for the selected filters"}
                )
            
            # Process data into response format
            loans = []
            total_loan_amount = Decimal('0')
            total_outstanding_amount = Decimal('0')
            loan_schedules = {}
            
            for loan, employee, dept_name, desig_name, loc_name, cc_name in loans_data:
                # Get designation name
                designation_name = "N/A"
                if employee.designation_id:
                    designation = self.db.query(Designation).filter(
                        Designation.id == employee.designation_id
                    ).first()
                    if designation:
                        designation_name = designation.name
                
                # Format interest method
                if loan.interest_rate and loan.interest_rate > 0:
                    interest_method = f"{loan.interest_rate}% per annum"
                else:
                    interest_method = "Interest Free"
                
                loan_data = EmployeeLoanData(
                    id=loan.id,
                    employee=f"{employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code,
                    designation=designation_name,
                    department=dept_name or 'N/A',
                    loan_type=loan.loan_type,
                    loan_amount=loan.loan_amount,
                    issue_date=loan.loan_date.strftime('%Y-%m-%d'),
                    interest_method=interest_method,
                    emi_amount=loan.emi_amount,
                    outstanding_amount=loan.outstanding_amount,
                    status=loan.status.value if hasattr(loan.status, 'value') else str(loan.status),
                    tenure_months=loan.tenure_months,
                    paid_emis=loan.paid_emis or 0,
                    remaining_emis=loan.remaining_emis or loan.tenure_months,
                    purpose=loan.purpose,
                    guarantor_name=loan.guarantor_name,
                    guarantor_relation=loan.guarantor_relation,
                    first_emi_date=loan.first_emi_date.strftime('%Y-%m-%d') if loan.first_emi_date else None,
                    last_emi_date=loan.last_emi_date.strftime('%Y-%m-%d') if loan.last_emi_date else None
                )
                
                loans.append(loan_data)
                total_loan_amount += loan.loan_amount
                total_outstanding_amount += loan.outstanding_amount
                
                # If "With Loan Schedule" is requested, get EMI schedule
                if filters.report_type == "With Loan Schedule":
                    emi_payments = self.db.query(LoanEMIPayment).filter(
                        LoanEMIPayment.loan_id == loan.id
                    ).order_by(LoanEMIPayment.emi_number).all()
                    
                    schedule = []
                    for emi in emi_payments:
                        schedule.append(LoanEMISchedule(
                            emi_number=emi.emi_number,
                            due_date=emi.due_date.strftime('%Y-%m-%d'),
                            paid_date=emi.paid_date.strftime('%Y-%m-%d') if emi.paid_date else None,
                            emi_amount=emi.emi_amount,
                            principal_amount=emi.principal_amount or Decimal('0'),
                            interest_amount=emi.interest_amount or Decimal('0'),
                            is_paid=emi.is_paid or False,
                            payment_method=emi.payment_method,
                            remarks=emi.remarks
                        ))
                    
                    loan_schedules[loan.id] = schedule
            
            # Create summary
            summary = {
                "total_loans": len(loans),
                "total_loan_amount": float(total_loan_amount),
                "total_outstanding_amount": float(total_outstanding_amount),
                "total_paid_amount": float(total_loan_amount - total_outstanding_amount),
                "average_loan_amount": float(total_loan_amount / len(loans)) if loans else 0,
                "department_breakdown": self._get_department_breakdown_loans(loans),
                "loan_type_breakdown": self._get_loan_type_breakdown(loans),
                "status_breakdown": self._get_loan_status_breakdown(loans),
                "filters_summary": {
                    "location": filters.location,
                    "department": filters.department,
                    "cost_center": filters.cost_center,
                    "issued_during": filters.issued_during,
                    "report_type": filters.report_type
                }
            }
            
            return EmployeeLoansResponse(
                total_loans=len(loans),
                total_loan_amount=total_loan_amount,
                total_outstanding_amount=total_outstanding_amount,
                loans=loans,
                filters_applied=filters,
                summary=summary,
                loan_schedules=loan_schedules if filters.report_type == "With Loan Schedule" else None
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating employee loans report: {e}")
            
            return EmployeeLoansResponse(
                total_loans=0,
                total_loan_amount=Decimal('0'),
                total_outstanding_amount=Decimal('0'),
                loans=[],
                filters_applied=filters,
                summary={"error": f"Error generating employee loans report: {str(e)}"}
            )
    
    def _get_department_breakdown_loans(self, loans):
        """Get breakdown by department for loans"""
        breakdown = {}
        for loan in loans:
            dept = loan.department or 'Unknown'
            if dept not in breakdown:
                breakdown[dept] = {'count': 0, 'total_amount': 0, 'outstanding_amount': 0}
            breakdown[dept]['count'] += 1
            breakdown[dept]['total_amount'] += float(loan.loan_amount)
            breakdown[dept]['outstanding_amount'] += float(loan.outstanding_amount)
        return breakdown
    
    def _get_loan_type_breakdown(self, loans):
        """Get breakdown by loan type"""
        breakdown = {}
        for loan in loans:
            loan_type = loan.loan_type or 'Unknown'
            if loan_type not in breakdown:
                breakdown[loan_type] = {'count': 0, 'total_amount': 0, 'outstanding_amount': 0}
            breakdown[loan_type]['count'] += 1
            breakdown[loan_type]['total_amount'] += float(loan.loan_amount)
            breakdown[loan_type]['outstanding_amount'] += float(loan.outstanding_amount)
        return breakdown
    
    def _get_loan_status_breakdown(self, loans):
        """Get breakdown by loan status"""
        breakdown = {}
        for loan in loans:
            status = loan.status or 'Unknown'
            if status not in breakdown:
                breakdown[status] = {'count': 0, 'total_amount': 0, 'outstanding_amount': 0}
            breakdown[status]['count'] += 1
            breakdown[status]['total_amount'] += float(loan.loan_amount)
            breakdown[status]['outstanding_amount'] += float(loan.outstanding_amount)
        return breakdown

    def get_sap_export_report(self, filters: 'SAPExportFilters') -> 'SAPExportResponse':
        """Get SAP export report data"""
        from app.schemas.reports import SAPExportEmployee, SAPExportResponse
        from app.models.designations import Designation
        from app.models.datacapture import EmployeeDeduction, SalaryVariable
        from app.models.attendance import AttendanceRecord, AttendanceStatus
        from sqlalchemy import func
        from datetime import datetime
        
        try:
            # Parse period from frontend format (e.g., "SEP-2025" to "2025-09")
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "SEP-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
                year = month_obj.year
                month_num = month_obj.month
            else:
                # Backend format: "2025-09"
                period = filters.period
                year, month_num = map(int, period.split('-'))
            
            # Get SAP export data
            sap_data = self.repository.get_sap_export_data(period, filters.dict())
            
            if not sap_data:
                return SAPExportResponse(
                    period=period,
                    total_employees=0,
                    total_gross_salary=Decimal('0'),
                    total_net_salary=Decimal('0'),
                    total_deductions=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No salary data found for the selected period and filters"},
                    export_format=filters.format
                )
            
            # Get SAP mapping configuration
            sap_mapping = self.repository.get_sap_mapping()
            
            # Process data into response format
            employees = []
            total_gross_salary = Decimal('0')
            total_net_salary = Decimal('0')
            total_deductions = Decimal('0')
            
            for salary_report, employee, employee_profile, dept_name, desig_name, loc_name, cc_name in sap_data:
                # Get designation name
                designation_name = "N/A"
                if employee.designation_id:
                    designation = self.db.query(Designation).filter(
                        Designation.id == employee.designation_id
                    ).first()
                    if designation:
                        designation_name = designation.name
                
                # Get attendance data for the period
                attendance_summary = self._get_employee_attendance_summary(employee.id, year, month_num)
                
                # Get salary components from allowances and deductions
                allowances = salary_report.allowances or {}
                deductions = salary_report.deductions or {}
                
                # Get additional deductions from EmployeeDeduction table
                employee_deductions = self.db.query(EmployeeDeduction).filter(
                    EmployeeDeduction.employee_id == employee.id,
                    EmployeeDeduction.is_active == True,
                    func.extract('year', EmployeeDeduction.effective_date) == year,
                    func.extract('month', EmployeeDeduction.effective_date) == month_num
                ).all()
                
                # Process deductions
                for ded in employee_deductions:
                    if ded.deduction_name == "GI":
                        deductions["Group Insurance"] = float(ded.amount)
                    elif ded.deduction_name == "PF":
                        deductions["Provident Fund"] = float(ded.amount)
                    elif ded.deduction_name == "Gratuity":
                        deductions["Gratuity"] = float(ded.amount)
                    elif ded.deduction_name == "Professional Tax":
                        deductions["Professional Tax"] = float(ded.amount)
                
                # Get variable salary components (bonus, leave encashment, etc.)
                variable_salary = self.db.query(SalaryVariable).filter(
                    SalaryVariable.employee_id == employee.id,
                    SalaryVariable.is_active == True,
                    func.extract('year', SalaryVariable.effective_date) == year,
                    func.extract('month', SalaryVariable.effective_date) == month_num
                ).all()
                
                # Process variable salary
                for var_sal in variable_salary:
                    if var_sal.variable_name == "Leave Encashment":
                        allowances["Leave Encashment"] = float(var_sal.amount)
                    elif "bonus" in var_sal.variable_name.lower():
                        allowances["Bonus"] = float(var_sal.amount)
                    elif var_sal.variable_name == "Gratuity":
                        allowances["Gratuity"] = float(var_sal.amount)
                
                employee_data = SAPExportEmployee(
                    employee_id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    department=dept_name or 'N/A',
                    designation=designation_name,
                    location=loc_name or 'N/A',
                    cost_center=cc_name or 'N/A',
                    
                    # Bank Details
                    bank_account=getattr(employee_profile, 'bank_account_number', None) if employee_profile else None,
                    bank_ifsc=getattr(employee_profile, 'bank_ifsc_code', None) if employee_profile else None,
                    bank_name=getattr(employee_profile, 'bank_name', None) if employee_profile else None,
                    
                    # Attendance Data
                    total_days=attendance_summary.get('total_days', 30),
                    payable_days=attendance_summary.get('payable_days', 22),
                    presents=attendance_summary.get('presents', 22),
                    absents=attendance_summary.get('absents', 0),
                    overtime_hours=attendance_summary.get('overtime_hours', 0.0),
                    
                    # Salary Components
                    basic_salary=salary_report.basic_salary,
                    hra=Decimal(str(allowances.get('HRA', 0))),
                    special_allowance=Decimal(str(allowances.get('Special Allowance', 0))),
                    medical_allowance=Decimal(str(allowances.get('Medical Allowance', 0))),
                    conveyance=Decimal(str(allowances.get('Conveyance', 0))),
                    telephone=Decimal(str(allowances.get('Telephone', 0))),
                    bonus=Decimal(str(allowances.get('Bonus', 0))),
                    gratuity=Decimal(str(allowances.get('Gratuity', 0))),
                    leave_encashment=Decimal(str(allowances.get('Leave Encashment', 0))),
                    loan_amount=Decimal(str(allowances.get('Loan', 0))),
                    overtime_hours_amount=Decimal(str(allowances.get('Overtime Hours', 0))),
                    overtime_days_amount=Decimal(str(allowances.get('Overtime Days', 0))),
                    retention_bonus=Decimal(str(allowances.get('Retention Bonus', 0))),
                    
                    # Deductions
                    esi=Decimal(str(deductions.get('ESI', 0))),
                    pf=Decimal(str(deductions.get('Provident Fund', 0))),
                    voluntary_pf=Decimal(str(deductions.get('Voluntary PF', 0))),
                    professional_tax=Decimal(str(deductions.get('Professional Tax', 0))),
                    income_tax=Decimal(str(deductions.get('Income Tax', 0))),
                    loan_repayment=Decimal(str(deductions.get('Loan Repayment', 0))),
                    loan_interest=Decimal(str(deductions.get('Loan Interest', 0))),
                    group_insurance=Decimal(str(deductions.get('Group Insurance', 0))),
                    pf_extra_contribution=Decimal(str(deductions.get('PF Extra Contribution', 0))),
                    labour_welfare=Decimal(str(deductions.get('Labour Welfare', 0))),
                    gratuity_deduction=Decimal(str(deductions.get('Gratuity', 0))),
                    
                    # Totals
                    gross_salary=salary_report.gross_salary,
                    total_deductions=salary_report.total_deductions,
                    net_salary=salary_report.net_salary
                )
                
                employees.append(employee_data)
                total_gross_salary += salary_report.gross_salary
                total_net_salary += salary_report.net_salary
                total_deductions += salary_report.total_deductions
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_gross_salary": float(total_gross_salary),
                "total_net_salary": float(total_net_salary),
                "total_deductions": float(total_deductions),
                "average_gross_salary": float(total_gross_salary / len(employees)) if employees else 0,
                "period_formatted": filters.period,
                "export_format": filters.format,
                "department_breakdown": self._get_department_breakdown_sap(employees),
                "location_breakdown": self._get_location_breakdown_sap(employees),
                "filters_summary": {
                    "business_unit": filters.business_unit,
                    "location": filters.location,
                    "department": filters.department,
                    "cost_center": filters.cost_center
                }
            }
            
            # Convert SAP mapping to dict for response
            sap_mapping_dict = None
            if sap_mapping:
                sap_mapping_dict = {
                    "doc_type": sap_mapping.doc_type,
                    "series": sap_mapping.series,
                    "bpl": sap_mapping.bpl,
                    "currency": sap_mapping.currency,
                    "location_code": sap_mapping.location_code,
                    "basic_salary_acct": sap_mapping.basic_salary_acct,
                    "basic_salary_tax": sap_mapping.basic_salary_tax,
                    "hra_acct": sap_mapping.hra_acct,
                    "hra_tax": sap_mapping.hra_tax,
                    # Add other mapping fields as needed
                }
            
            return SAPExportResponse(
                period=period,
                total_employees=len(employees),
                total_gross_salary=total_gross_salary,
                total_net_salary=total_net_salary,
                total_deductions=total_deductions,
                employees=employees,
                filters_applied=filters,
                summary=summary,
                sap_mapping=sap_mapping_dict,
                export_format=filters.format
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating SAP export report: {e}")
            
            return SAPExportResponse(
                period=filters.period,
                total_employees=0,
                total_gross_salary=Decimal('0'),
                total_net_salary=Decimal('0'),
                total_deductions=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating SAP export report: {str(e)}"},
                export_format=filters.format
            )
    
    def _get_employee_attendance_summary(self, employee_id: int, year: int, month: int) -> Dict[str, Any]:
        """Get attendance summary for an employee for a specific month"""
        from app.models.attendance import AttendanceRecord, AttendanceStatus
        from datetime import datetime
        
        try:
            # Calculate start and end dates for the month
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()
            
            # Get attendance records
            attendance_records = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.attendance_date >= start_date,
                AttendanceRecord.attendance_date < end_date
            ).all()
            
            # Calculate summary
            total_days = 30  # Default month days
            presents = 0
            absents = 0
            overtime_hours = 0.0
            
            for record in attendance_records:
                if record.attendance_status == AttendanceStatus.PRESENT:
                    presents += 1
                    if record.overtime_hours:
                        overtime_hours += float(record.overtime_hours)
                elif record.attendance_status == AttendanceStatus.ABSENT:
                    absents += 1
            
            payable_days = presents
            
            return {
                'total_days': total_days,
                'presents': presents,
                'absents': absents,
                'payable_days': payable_days,
                'overtime_hours': overtime_hours
            }
            
        except Exception:
            # Return default values if attendance data is not available
            return {
                'total_days': 30,
                'presents': 22,
                'absents': 0,
                'payable_days': 22,
                'overtime_hours': 0.0
            }
    
    def get_attendance_register(self, filters: 'AttendanceRegisterFilters') -> 'AttendanceRegisterResponse':
        """Get attendance register data"""
        from app.schemas.reports import AttendanceRegisterEmployee, AttendanceRegisterResponse, AttendanceDayData
        from datetime import datetime, timedelta
        import calendar
        
        try:
            # Get attendance register data
            register_data = self.repository.get_attendance_register_data(filters.dict())
            
            if not register_data['employees']:
                return AttendanceRegisterResponse(
                    records=[],
                    month="NOV-2025",
                    total_records=0,
                    filters_applied=filters,
                    summary={"message": "No employees found for the selected filters"},
                    date_range={"from_date": "", "to_date": ""}
                )
            
            employees_data = register_data['employees']
            attendance_data = register_data['attendance']
            date_range = register_data['date_range']
            
            # Generate month string
            from_date = date_range['from_date']
            month_str = from_date.strftime('%b-%Y').upper()  # NOV-2025 format
            
            # Generate all days in the date range
            current_date = from_date
            all_days = []
            while current_date <= date_range['to_date']:
                all_days.append({
                    'date': current_date.day,
                    'day': current_date.strftime('%a'),  # Mon, Tue, etc
                    'full_date': current_date
                })
                current_date += timedelta(days=1)
            
            # Process employees data
            records = []
            for i, (employee, dept_name, desig_name, loc_name, cc_name) in enumerate(employees_data):
                # Get attendance records for this employee
                employee_attendance = attendance_data.get(employee.id, [])
                
                # Create attendance lookup by date
                attendance_lookup = {}
                for att_record in employee_attendance:
                    attendance_lookup[att_record.attendance_date] = att_record
                
                # Generate daily attendance data
                days_data = []
                presents = 0
                absents = 0
                week_offs = 0
                total_hours = 0.0
                overtime_hours = 0.0
                
                for day_info in all_days:
                    day_date = day_info['full_date']
                    att_record = attendance_lookup.get(day_date)
                    
                    # Determine status
                    status = "-"
                    punch_in = None
                    punch_out = None
                    day_hours = None
                    day_overtime = None
                    
                    if att_record:
                        # Map attendance status
                        if att_record.attendance_status == 'present':
                            status = "P"
                            presents += 1
                        elif att_record.attendance_status == 'absent':
                            status = "A"
                            absents += 1
                        elif att_record.attendance_status == 'on_leave':
                            status = "P"  # Treat leave as present for paid days calculation
                            presents += 1
                        elif att_record.attendance_status == 'weekend':
                            status = "W"
                            week_offs += 1
                        
                        # Add time punch data if requested
                        if filters.show_time_punches and att_record.punch_in_time:
                            punch_in = att_record.punch_in_time.strftime('%H:%M')
                        if filters.show_time_punches and att_record.punch_out_time:
                            punch_out = att_record.punch_out_time.strftime('%H:%M')
                        
                        # Calculate hours
                        if att_record.total_hours:
                            day_hours = float(att_record.total_hours)
                            total_hours += day_hours
                        
                        if att_record.overtime_hours:
                            day_overtime = float(att_record.overtime_hours)
                            overtime_hours += day_overtime
                    else:
                        # Check if it's a weekend (Saturday/Sunday)
                        if day_date.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
                            status = "W"
                            week_offs += 1
                    
                    day_data = AttendanceDayData(
                        date=day_info['date'],
                        day=day_info['day'],
                        status=status,
                        punch_in=punch_in,
                        punch_out=punch_out,
                        total_hours=day_hours,
                        overtime_hours=day_overtime
                    )
                    days_data.append(day_data)
                
                # Calculate paid days (presents + week offs)
                paid_days = float(presents + week_offs)
                
                employee_record = AttendanceRegisterEmployee(
                    sn=i + 1,
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    id=employee.employee_code or f"EMP{employee.id:03d}",
                    des=desig_name or "Associate",
                    employee_id=employee.id,
                    department=dept_name,
                    location=loc_name,
                    cost_center=cc_name,
                    days=days_data,
                    presents=presents,
                    absents=absents,
                    week_offs=week_offs,
                    paid_days=paid_days,
                    total_hours=total_hours if filters.show_time_summary else None,
                    overtime_hours=overtime_hours if filters.show_time_summary else None
                )
                
                records.append(employee_record)
            
            # Create summary
            total_presents = sum(r.presents for r in records)
            total_absents = sum(r.absents for r in records)
            total_week_offs = sum(r.week_offs for r in records)
            
            summary = {
                "total_employees": len(records),
                "total_presents": total_presents,
                "total_absents": total_absents,
                "total_week_offs": total_week_offs,
                "average_attendance": (total_presents / (total_presents + total_absents)) * 100 if (total_presents + total_absents) > 0 else 0,
                "date_range_days": len(all_days),
                "filters_summary": {
                    "location": filters.location,
                    "department": filters.department,
                    "cost_center": filters.cost_center,
                    "record_type": filters.record_type
                }
            }
            
            return AttendanceRegisterResponse(
                records=records,
                month=month_str,
                total_records=len(records),
                filters_applied=filters,
                summary=summary,
                date_range={
                    "from_date": from_date.strftime('%Y-%m-%d'),
                    "to_date": date_range['to_date'].strftime('%Y-%m-%d')
                }
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating attendance register: {e}")
            
            return AttendanceRegisterResponse(
                records=[],
                month="NOV-2025",
                total_records=0,
                filters_applied=filters,
                summary={"error": f"Error generating attendance register: {str(e)}"},
                date_range={"from_date": "", "to_date": ""}
            )

    def _get_department_breakdown_sap(self, employees):
        """Get breakdown by department for SAP export"""
        breakdown = {}
        for emp in employees:
            dept = emp.department or 'Unknown'
            if dept not in breakdown:
                breakdown[dept] = {'count': 0, 'total_gross': 0, 'total_net': 0}
            breakdown[dept]['count'] += 1
            breakdown[dept]['total_gross'] += float(emp.gross_salary)
            breakdown[dept]['total_net'] += float(emp.net_salary)
        return breakdown
    
    def _get_location_breakdown_sap(self, employees):
        """Get breakdown by location for SAP export"""
        breakdown = {}
        for emp in employees:
            loc = emp.location or 'Unknown'
            if loc not in breakdown:
                breakdown[loc] = {'count': 0, 'total_gross': 0, 'total_net': 0}
            breakdown[loc]['count'] += 1
            breakdown[loc]['total_gross'] += float(emp.gross_salary)
            breakdown[loc]['total_net'] += float(emp.net_salary)
        return breakdown

    def get_leave_encashment_report(self, filters: 'LeaveEncashmentReportFilters') -> 'LeaveEncashmentReportResponse':
        """Get leave encashment report data"""
        from app.schemas.reports import LeaveEncashmentReportEmployee, LeaveEncashmentReportResponse
        
        try:
            # Parse period from frontend format (e.g., "OCT-2025" to "2025-10")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "OCT-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-10"
                period = filters.period
            
            # Get leave encashment report data
            encashment_data = self.repository.get_leave_encashment_report_data(period, filters.dict())
            
            if not encashment_data:
                return LeaveEncashmentReportResponse(
                    period=period,
                    total_employees=0,
                    total_amount=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No leave encashment data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_amount = Decimal('0')
            
            for data_row in encashment_data:
                # Check if this is LeaveEncashment data or SalaryVariable data
                if hasattr(data_row[0], 'encashment_amount'):
                    # LeaveEncashment table data
                    encashment = data_row[0]
                    employee = data_row[1]
                    dept_name = data_row[2]
                    desig_name = data_row[3]
                    loc_name = data_row[4]
                    cc_name = data_row[5]
                    
                    employee_data = LeaveEncashmentReportEmployee(
                        id=employee.id,
                        employee_code=employee.employee_code,
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        position=desig_name or 'Associate Software Engineer',
                        department=dept_name or 'General',
                        location=loc_name or 'Hyderabad',
                        cost_center=cc_name or 'Default',
                        description=f"Leave encashment for {encashment.leave_type} - {encashment.encashment_days} days",
                        leave_type=encashment.leave_type,
                        leave_balance=encashment.leave_balance,
                        encashment_days=encashment.encashment_days,
                        daily_salary=encashment.daily_salary,
                        encashment_amount=encashment.encashment_amount,
                        payment_period=encashment.payment_period,
                        balance_as_on=encashment.balance_as_on,
                        is_processed=encashment.is_processed,
                        processed_date=encashment.processed_date
                    )
                    
                    total_amount += encashment.encashment_amount
                else:
                    # SalaryVariable table data
                    salary_variable = data_row[0]
                    employee = data_row[1]
                    dept_name = data_row[2]
                    desig_name = data_row[3]
                    loc_name = data_row[4]
                    cc_name = data_row[5]
                    
                    # Calculate estimated daily salary and days from amount
                    from app.models.employee import EmployeeSalary
                    salary_record = self.db.query(EmployeeSalary).filter(
                        EmployeeSalary.employee_id == employee.id,
                        EmployeeSalary.is_active == True
                    ).first()
                    
                    daily_salary = Decimal('0')
                    encashment_days = Decimal('0')
                    
                    if salary_record:
                        daily_salary = salary_record.basic_salary / 30  # Assuming 30 days in month
                        if daily_salary > 0:
                            encashment_days = salary_variable.amount / daily_salary
                    
                    employee_data = LeaveEncashmentReportEmployee(
                        id=employee.id,
                        employee_code=employee.employee_code,
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        position=desig_name or 'Associate Software Engineer',
                        department=dept_name or 'General',
                        location=loc_name or 'Hyderabad',
                        cost_center=cc_name or 'Default',
                        description=f"Leave encashment for unused paid leave - {salary_variable.variable_name}",
                        leave_type="Annual Leave",
                        leave_balance=encashment_days + 5,  # Estimated balance
                        encashment_days=encashment_days,
                        daily_salary=daily_salary,
                        encashment_amount=salary_variable.amount,
                        payment_period=salary_variable.effective_date,
                        balance_as_on=salary_variable.effective_date,
                        is_processed=True,
                        processed_date=salary_variable.created_at
                    )
                    
                    total_amount += salary_variable.amount
                
                employees.append(employee_data)
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_amount": float(total_amount),
                "average_amount": float(total_amount / len(employees)) if employees else 0,
                "processed_count": len([emp for emp in employees if emp.is_processed]),
                "pending_count": len([emp for emp in employees if not emp.is_processed]),
                "period_formatted": filters.period,
                "department_breakdown": self._get_department_breakdown(employees),
                "location_breakdown": self._get_location_breakdown(employees)
            }
            
            return LeaveEncashmentReportResponse(
                period=period,
                total_employees=len(employees),
                total_amount=total_amount,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating leave encashment report: {e}")
            
            return LeaveEncashmentReportResponse(
                period=filters.period,
                total_employees=0,
                total_amount=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating leave encashment report: {str(e)}"}
            )

    def _get_department_breakdown(self, employees):
        """Get breakdown by department"""
        breakdown = {}
        for emp in employees:
            dept = emp.department or 'Unknown'
            if dept not in breakdown:
                breakdown[dept] = {'count': 0, 'total_amount': 0}
            breakdown[dept]['count'] += 1
            breakdown[dept]['total_amount'] += float(emp.encashment_amount)
        return breakdown

    def _get_location_breakdown(self, employees):
        """Get breakdown by location"""
        breakdown = {}
        for emp in employees:
            loc = emp.location or 'Unknown'
            if loc not in breakdown:
                breakdown[loc] = {'count': 0, 'total_amount': 0}
            breakdown[loc]['count'] += 1
            breakdown[loc]['total_amount'] += float(emp.encashment_amount)
        return breakdown

    def get_rate_salary_report(self, filters: 'RateSalaryFilters') -> 'RateSalaryResponse':
        """Get rate salary report data"""
        from app.schemas.reports import RateSalaryEmployee, RateSalaryResponse
        
        try:
            # Parse period from frontend format (e.g., "JUN-2025" to "2025-06")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUN-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-06"
                period = filters.period
            
            # Get rate salary data
            rate_salary_data = self.repository.get_rate_salary_data(period, filters.dict())
            
            if not rate_salary_data:
                return RateSalaryResponse(
                    period=period,
                    total_employees=0,
                    total_amount=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No rate salary data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_amount = Decimal('0')
            
            for emp_data, working_days in rate_salary_data:
                salary_record = emp_data[0]
                employee = emp_data[1]
                dept_name = emp_data[2]
                desig_name = emp_data[3]
                loc_name = emp_data[4]
                structure_name = emp_data[5]
                
                # Generate rate-based salary components
                rate_components = self._generate_rate_salary_components(
                    salary_record, working_days, filters.salary_component
                )
                
                # Add each component as a separate employee record
                for component in rate_components:
                    employee_data = RateSalaryEmployee(
                        id=employee.id,
                        employee_code=employee.employee_code,
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        department=dept_name or 'General',
                        designation=desig_name or 'Associate',
                        location=loc_name or 'Hyderabad',
                        salary_component=component['name'],
                        rate=component['rate'],
                        unit=component['unit'],
                        amount=component['amount'],
                        basic_salary=salary_record.basic_salary,
                        working_days=working_days,
                        component_type=component['type']
                    )
                    
                    employees.append(employee_data)
                    total_amount += component['amount']
            
            # Filter by salary component if specified
            if filters.salary_component and filters.salary_component != "- Select -":
                employees = [emp for emp in employees if emp.salary_component == filters.salary_component]
                total_amount = sum(emp.amount for emp in employees)
            
            # Create summary
            summary = {
                "total_employees": len(set(emp.id for emp in employees)),  # Unique employees
                "total_records": len(employees),  # Total component records
                "total_amount": float(total_amount),
                "average_amount": float(total_amount / len(employees)) if employees else 0,
                "period_formatted": filters.period,
                "components_breakdown": self._get_components_breakdown(employees)
            }
            
            return RateSalaryResponse(
                period=period,
                total_employees=len(employees),
                total_amount=total_amount,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating rate salary report: {e}")
            
            return RateSalaryResponse(
                period=filters.period,
                total_employees=0,
                total_amount=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating rate salary report: {str(e)}"}
            )

    def _generate_rate_salary_components(self, salary_record, working_days: int, component_filter: str = None):
        """Generate rate-based salary components for an employee"""
        components = []
        
        basic_salary = salary_record.basic_salary
        gross_salary = salary_record.gross_salary
        
        # Calculate daily rates
        basic_daily_rate = basic_salary / 30  # Assuming 30 days in month
        
        # Basic Salary Component
        basic_amount = basic_daily_rate * working_days
        components.append({
            'name': 'Basic',
            'rate': basic_daily_rate,
            'unit': 'Days',
            'amount': basic_amount,
            'type': 'Fixed'
        })
        
        # HRA Component (40% of basic)
        hra_daily_rate = (basic_salary * Decimal('0.40')) / 30
        hra_amount = hra_daily_rate * working_days
        components.append({
            'name': 'HRA',
            'rate': hra_daily_rate,
            'unit': 'Days',
            'amount': hra_amount,
            'type': 'Allowance'
        })
        
        # Special Allowance (to make up gross - basic - hra)
        hra_monthly = basic_salary * Decimal('0.40')
        special_monthly = gross_salary - basic_salary - hra_monthly
        if special_monthly > 0:
            special_daily_rate = special_monthly / 30
            special_amount = special_daily_rate * working_days
            components.append({
                'name': 'Special Allowance',
                'rate': special_daily_rate,
                'unit': 'Days',
                'amount': special_amount,
                'type': 'Allowance'
            })
        
        # Medical Allowance (fixed amount)
        medical_daily_rate = Decimal('1250') / 30
        medical_amount = medical_daily_rate * working_days
        components.append({
            'name': 'Medical Allowance',
            'rate': medical_daily_rate,
            'unit': 'Days',
            'amount': medical_amount,
            'type': 'Allowance'
        })
        
        # Conveyance Allowance (fixed amount)
        conveyance_daily_rate = Decimal('1600') / 30
        conveyance_amount = conveyance_daily_rate * working_days
        components.append({
            'name': 'Conveyance Allowance',
            'rate': conveyance_daily_rate,
            'unit': 'Days',
            'amount': conveyance_amount,
            'type': 'Allowance'
        })
        
        return components

    def _get_components_breakdown(self, employees):
        """Get breakdown of salary components"""
        breakdown = {}
        for emp in employees:
            component = emp.salary_component
            if component not in breakdown:
                breakdown[component] = {
                    'count': 0,
                    'total_amount': 0,
                    'avg_rate': 0
                }
            breakdown[component]['count'] += 1
            breakdown[component]['total_amount'] += float(emp.amount)
            breakdown[component]['avg_rate'] = breakdown[component]['total_amount'] / breakdown[component]['count']
        
        return breakdown

    def get_variable_salary_report(self, filters: 'VariableSalaryFilters') -> 'VariableSalaryResponse':
        """Get variable salary report data"""
        from app.schemas.reports import VariableSalaryEmployee, VariableSalaryResponse
        
        try:
            # Parse period from frontend format (e.g., "JUN-2025" to "2025-06")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUN-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-06"
                period = filters.period
            
            # Get variable salary data
            variable_data = self.repository.get_variable_salary_data(period, filters.dict())
            
            if not variable_data:
                return VariableSalaryResponse(
                    period=period,
                    total_employees=0,
                    total_amount=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No variable salary data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_amount = Decimal('0')
            
            for salary_variable, employee, dept_name, desig_name, loc_name in variable_data:
                # Create employee record
                employee_data = VariableSalaryEmployee(
                    id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    department=dept_name or 'General',
                    designation=desig_name or 'Associate',
                    location=loc_name or 'Hyderabad',
                    salary_component=salary_variable.variable_name,
                    amount=salary_variable.amount,
                    variable_type=salary_variable.variable_type.value if salary_variable.variable_type else 'allowance',
                    effective_date=salary_variable.effective_date,
                    description=salary_variable.description
                )
                
                employees.append(employee_data)
                total_amount += salary_variable.amount
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_amount": float(total_amount),
                "average_amount": float(total_amount / len(employees)) if employees else 0,
                "salary_component": filters.salary_component,
                "period_formatted": filters.period
            }
            
            return VariableSalaryResponse(
                period=period,
                total_employees=len(employees),
                total_amount=total_amount,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating variable salary report: {e}")
            
            return VariableSalaryResponse(
                period=filters.period,
                total_employees=0,
                total_amount=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating variable salary report: {str(e)}"}
            )

    def get_salary_summary(self, period: str) -> SalarySummary:
        """Get salary summary for a period"""
        summary_data = self.repository.get_salary_summary(period)
        return SalarySummary(
            total_employees=summary_data['total_employees'],
            total_gross_salary=Decimal(str(summary_data['total_gross_salary'])),
            total_net_salary=Decimal(str(summary_data['total_net_salary'])),
            total_deductions=Decimal(str(summary_data['total_deductions'])),
            average_salary=Decimal(str(summary_data['average_salary']))
        )
    
    def get_variable_salary_report(self, filters: 'VariableSalaryFilters') -> 'VariableSalaryResponse':
        """Get variable salary report data"""
        from app.schemas.reports import VariableSalaryEmployee, VariableSalaryResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[VARIABLE SALARY SERVICE] Requesting data for business_id={filters.business_id}, period={filters.period}")
            
            # Parse period from frontend format (e.g., "JUN-2025" to "2025-06")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUN-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-06"
                period = filters.period
            
            # Get variable salary data
            variable_salary_data = self.repository.get_variable_salary_data(period, filters.dict())
            
            if not variable_salary_data:
                logger.warning(f"[VARIABLE SALARY SERVICE] No data found for business_id={filters.business_id}, period={period}")
                return VariableSalaryResponse(
                    period=period,
                    total_employees=0,
                    total_amount=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No variable salary data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_amount = Decimal('0')
            
            for salary_variable, employee, dept_name, desig_name, loc_name in variable_salary_data:
                employee_data = VariableSalaryEmployee(
                    id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    department=dept_name or 'General',
                    designation=desig_name or 'Associate',
                    location=loc_name or 'Hyderabad',
                    salary_component=salary_variable.variable_name,
                    amount=salary_variable.amount,
                    variable_type=salary_variable.variable_type.value if hasattr(salary_variable.variable_type, 'value') else str(salary_variable.variable_type),
                    effective_date=salary_variable.effective_date,
                    description=salary_variable.description or f"Variable salary component: {salary_variable.variable_name}"
                )
                
                employees.append(employee_data)
                total_amount += salary_variable.amount
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_amount": float(total_amount),
                "average_amount": float(total_amount / len(employees)) if employees else 0,
                "period_formatted": filters.period,
                "component_breakdown": self._get_variable_component_breakdown(employees)
            }
            
            return VariableSalaryResponse(
                period=period,
                total_employees=len(employees),
                total_amount=total_amount,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating variable salary report: {e}")
            
            return VariableSalaryResponse(
                period=filters.period,
                total_employees=0,
                total_amount=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating variable salary report: {str(e)}"}
            )

    def _get_variable_component_breakdown(self, employees):
        """Get breakdown of variable salary components"""
        breakdown = {}
        for emp in employees:
            component = emp.salary_component
            if component not in breakdown:
                breakdown[component] = {'count': 0, 'total_amount': 0}
            breakdown[component]['count'] += 1
            breakdown[component]['total_amount'] += float(emp.amount)
        return breakdown

    def get_leave_register(self, filters: 'LeaveRegisterFilters') -> 'LeaveRegisterResponse':
        """Get leave register data"""
        from app.schemas.reports import LeaveRegisterEmployee, LeaveRegisterResponse
        
        try:
            # Get leave register data
            leave_data = self.repository.get_leave_register_data(filters.dict())
            
            if not leave_data:
                return LeaveRegisterResponse(
                    total_employees=0,
                    total_records=0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No leave register data found for the selected filters"},
                    year_range=filters.year,
                    month_range=f"Jan to {filters.month}"
                )
            
            # Process data into response format
            employees = []
            unique_employees = set()
            
            for (employee, dept_name, desig_name, loc_name, cc_name, 
                 month_str, days_worked, unpaid_leaves, paid_leaves, wages) in leave_data:
                
                unique_employees.add(employee.id)
                
                # Format wages
                wages_formatted = f"{float(wages):.2f}" if wages > 0 else "0.00"
                
                employee_data = LeaveRegisterEmployee(
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code or f"LEV{employee.id:03d}",
                    month=month_str,
                    days_worked=f"{days_worked:.2f}",
                    maternity="0",  # Default as per frontend
                    unpaid_leaves=f"{unpaid_leaves:.2f}",
                    paid_leaves=f"{paid_leaves:.2f}",
                    wages=wages_formatted,
                    employee_id=employee.id,
                    department=dept_name,
                    location=loc_name,
                    cost_center=cc_name
                )
                
                employees.append(employee_data)
            
            # Sort by employee name and then by month
            month_order = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            employees.sort(key=lambda x: (
                x.employee_name,
                month_order.get(x.month.split('-')[0], 13)
            ))
            
            # Calculate summary
            total_wages = sum(float(emp.wages) for emp in employees)
            total_days_worked = sum(float(emp.days_worked) for emp in employees)
            total_unpaid_leaves = sum(float(emp.unpaid_leaves) for emp in employees)
            total_paid_leaves = sum(float(emp.paid_leaves) for emp in employees)
            
            summary = {
                "total_employees": len(unique_employees),
                "total_records": len(employees),
                "total_wages": total_wages,
                "total_days_worked": total_days_worked,
                "total_unpaid_leaves": total_unpaid_leaves,
                "total_paid_leaves": total_paid_leaves,
                "average_wages": total_wages / len(employees) if employees else 0,
                "filters_summary": {
                    "location": filters.location,
                    "cost_center": filters.cost_center,
                    "year": filters.year,
                    "month_range": f"Jan to {filters.month}"
                }
            }
            
            return LeaveRegisterResponse(
                total_employees=len(unique_employees),
                total_records=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary,
                year_range=filters.year,
                month_range=f"Jan to {filters.month}"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating leave register: {e}")
            
            return LeaveRegisterResponse(
                total_employees=0,
                total_records=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating leave register: {str(e)}"},
                year_range=filters.year,
                month_range=f"Jan to {filters.month}"
            )

    # Attendance Report Methods
    def create_attendance_report(self, report_data: AttendanceReportCreate) -> AttendanceReportResponse:
        """Create a new attendance report"""
        db_report = self.repository.create_attendance_report(report_data)
        return AttendanceReportResponse.from_orm(db_report)
    
    def get_attendance_reports(self, filters: ReportFilters) -> List[AttendanceReportResponse]:
        """Get attendance reports with filters"""
        reports = self.repository.get_attendance_reports(filters)
        return [AttendanceReportResponse.from_orm(report) for report in reports]
    
    def get_attendance_summary(self, start_date: date, end_date: date) -> AttendanceSummary:
        """Get attendance summary for a date range"""
        summary_data = self.repository.get_attendance_summary(start_date, end_date)
        return AttendanceSummary(
            total_employees=summary_data['total_employees'],
            present_count=summary_data['present_count'],
            absent_count=summary_data['absent_count'],
            leave_count=summary_data['leave_count'],
            attendance_percentage=summary_data['attendance_percentage']
        )
    
    # Employee Report Methods
    def create_employee_report(self, report_data: EmployeeReportCreate) -> EmployeeReportResponse:
        """Create a new employee report"""
        db_report = self.repository.create_employee_report(report_data)
        return EmployeeReportResponse.from_orm(db_report)
    
    def get_employee_reports(self, filters: ReportFilters) -> List[EmployeeReportResponse]:
        """Get employee reports with filters"""
        reports = self.repository.get_employee_reports(filters)
        return [EmployeeReportResponse.from_orm(report) for report in reports]
    
    # Statutory Report Methods
    def create_statutory_report(self, report_data: StatutoryReportCreate) -> StatutoryReportResponse:
        """Create a new statutory report"""
        db_report = self.repository.create_statutory_report(report_data)
        return StatutoryReportResponse.from_orm(db_report)
    
    def get_statutory_reports(self, filters: ReportFilters) -> List[StatutoryReportResponse]:
        """Get statutory reports with filters"""
        reports = self.repository.get_statutory_reports(filters)
        return [StatutoryReportResponse.from_orm(report) for report in reports]
    
    # Annual Report Methods
    def create_annual_report(self, report_data: AnnualReportCreate) -> AnnualReportResponse:
        """Create a new annual report"""
        db_report = self.repository.create_annual_report(report_data)
        return AnnualReportResponse.from_orm(db_report)
    
    def get_annual_reports(self, filters: ReportFilters) -> List[AnnualReportResponse]:
        """Get annual reports with filters"""
        reports = self.repository.get_annual_reports(filters)
        return [AnnualReportResponse.from_orm(report) for report in reports]
    
    # Activity Log Methods
    def create_activity_log(self, user_id: int, log_data: ActivityLogCreate) -> ActivityLogResponse:
        """Create a new activity log"""
        db_log = self.repository.create_activity_log(user_id, log_data)
        return ActivityLogResponse.from_orm(db_log)
    
    def get_activity_logs(self, user_id: Optional[int] = None, limit: int = 100) -> List[ActivityLogResponse]:
        """Get activity logs"""
        logs = self.repository.get_activity_logs(user_id, limit)
        return [ActivityLogResponse.from_orm(log) for log in logs]

    def get_activity_logs_report(self, filters: 'ActivityLogFilters') -> 'ActivityLogsReportResponse':
        """Get Activity Logs report data with date range filtering"""
        from app.schemas.reports import (
            ActivityLogsReportResponse, ActivityLogData
        )
        from datetime import datetime
        
        try:
            # Validate business_id is provided
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for Activity Logs report")
            
            # Get activity logs data from repository
            logs_data = self.repository.get_activity_logs_with_filters(filters.dict())
            
            if not logs_data.get("logs"):
                return ActivityLogsReportResponse(
                    logs=[],
                    total_logs=0,
                    filters_applied=filters,
                    date_range={"from_date": filters.from_date or "", "to_date": filters.to_date or ""},
                    message=logs_data.get("message", "No activity logs found")
                )
            
            logs_results = logs_data["logs"]
            
            # Process logs data for frontend display
            processed_logs = []
            
            for log_result in logs_results:
                activity_log = log_result[0]  # ActivityLog object
                user_name = log_result[1] or "Unknown User"  # User name
                
                # Format datetime for frontend display (DD-MMM-YYYY HH:MM AM/PM)
                created_at = activity_log.created_at
                day = created_at.strftime('%d')
                month = created_at.strftime('%b')
                year = created_at.strftime('%Y')
                time_12hr = created_at.strftime('%I:%M %p')
                formatted_datetime = f"{day}-{month}-{year} {time_12hr}"
                
                # Create formatted description based on action and module
                description = self._format_activity_description(
                    activity_log.action, 
                    activity_log.module, 
                    activity_log.details or {},
                    user_name
                )
                
                processed_log = ActivityLogData(
                    id=activity_log.id,
                    description=description,
                    user=user_name,
                    datetime=formatted_datetime,
                    action=activity_log.action,
                    module=activity_log.module,
                    details=activity_log.details,
                    ip_address=activity_log.ip_address,
                    created_at=activity_log.created_at
                )
                
                processed_logs.append(processed_log)
            
            # Create summary
            total_logs = logs_data.get("total_count", len(processed_logs))
            
            return ActivityLogsReportResponse(
                logs=processed_logs,
                total_logs=total_logs,
                filters_applied=filters,
                date_range={"from_date": filters.from_date or "", "to_date": filters.to_date or ""},
                message="Activity logs report generated successfully"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Activity Logs report: {e}")
            
            return ActivityLogsReportResponse(
                logs=[],
                total_logs=0,
                filters_applied=filters,
                date_range={"from_date": filters.from_date or "", "to_date": filters.to_date or ""},
                message=f"Error: {str(e)}"
            )

    def _format_activity_description(self, action: str, module: str, details: dict, user_name: str) -> str:
        """Format activity description for frontend display"""
        
        # Handle specific action types with custom formatting
        if "onboarding" in action.lower() and "approved" in action.lower():
            form_id = details.get('form_id', 'Unknown')
            candidate_name = details.get('candidate_name', 'Unknown')
            return f"Onboarding Form #{form_id} for {candidate_name} was approved"
        
        elif "onboarding" in action.lower() and "deleted" in action.lower():
            form_id = details.get('form_id', 'Unknown')
            return f"Onboarding Form #{form_id} deleted"
        
        elif "payroll" in action.lower() and "modified" in action.lower():
            period = details.get('period', 'Unknown')
            return f"Payroll period modified-{period}"
        
        elif "reporting" in action.lower() and "allowed" in action.lower():
            period = details.get('period', 'Unknown')
            return f"{period} was allowed for reporting"
        
        elif "attendance" in action.lower() and "updated" in action.lower():
            employee_name = details.get('employee_name', 'Unknown Employee')
            employee_code = details.get('employee_code', '')
            date = details.get('date', 'Unknown Date')
            status = details.get('status', 'Present')
            timestamp = details.get('timestamp', '')
            
            employee_display = f"{employee_name} ({employee_code})" if employee_code else employee_name
            return f"Attendance manually updated for '{employee_display}' for {date} as {status} - by {user_name} on {timestamp}"
        
        elif "leave" in action.lower():
            employee_name = details.get('employee_name', 'Unknown Employee')
            leave_type = details.get('leave_type', 'Leave')
            if "approved" in action.lower():
                return f"{leave_type} request for {employee_name} was approved"
            elif "rejected" in action.lower():
                return f"{leave_type} request for {employee_name} was rejected"
        
        elif "salary" in action.lower() and "processed" in action.lower():
            period = details.get('period', 'Unknown Period')
            return f"Salary processed for {period}"
        
        elif "document" in action.lower():
            document_name = details.get('document_name', 'Document')
            employee_name = details.get('employee_name', 'Unknown Employee')
            if "uploaded" in action.lower():
                return f"Document '{document_name}' uploaded for {employee_name}"
            elif "deleted" in action.lower():
                return f"Document '{document_name}' deleted for {employee_name}"
        
        elif "policy" in action.lower() and "updated" in action.lower():
            policy_name = details.get('policy_name', 'Policy')
            return f"Policy '{policy_name}' updated"
        
        elif "access" in action.lower():
            target_user = details.get('target_user', 'User')
            if "granted" in action.lower():
                return f"User access granted to {target_user}"
            elif "revoked" in action.lower():
                return f"User access revoked for {target_user}"
        
        elif "profile" in action.lower() and "updated" in action.lower():
            employee_name = details.get('employee_name', 'Unknown Employee')
            return f"Employee profile updated for {employee_name}"
        
        # Default formatting
        return f"{action} in {module}"
    
    # User Feedback Methods
    def create_user_feedback(self, user_id: int, feedback_data: UserFeedbackCreate) -> UserFeedbackResponse:
        """Create a new user feedback"""
        db_feedback = self.repository.create_user_feedback(user_id, feedback_data)
        return UserFeedbackResponse.from_orm(db_feedback)
    
    def get_user_feedback(self, limit: int = 100) -> List[UserFeedbackResponse]:
        """Get user feedback"""
        feedback = self.repository.get_user_feedback(limit)
        return [UserFeedbackResponse.from_orm(fb) for fb in feedback]
    
    def update_feedback_status(self, feedback_id: int, status: str, resolved_by: Optional[int] = None) -> Optional[UserFeedbackResponse]:
        """Update feedback status"""
        updated_feedback = self.repository.update_feedback_status(feedback_id, status, resolved_by)
        return UserFeedbackResponse.from_orm(updated_feedback) if updated_feedback else None

    def get_user_feedback_report(self, filters: Dict[str, Any]) -> 'UserFeedbackReportResponse':
        """Get User Feedback report data with filtering"""
        from app.schemas.reports import (
            UserFeedbackReportResponse, UserFeedbackData, UserFeedbackFilters
        )
        from datetime import datetime
        
        try:
            # Validate business_id is provided
            business_id = filters.get('business_id')
            if not business_id:
                raise ValueError("business_id is required for User Feedback report")
            
            # Create filters object
            filters_obj = UserFeedbackFilters(
                from_date=filters.get('from_date'),
                to_date=filters.get('to_date'),
                feedback_type=filters.get('feedback_type'),
                status=filters.get('status'),
                rating=filters.get('rating'),
                limit=filters.get('limit', 100)
            )
            
            # Get user feedback data from repository
            feedback_data = self.repository.get_user_feedback_with_filters(filters)
            
            if not feedback_data.get("feedback"):
                return UserFeedbackReportResponse(
                    feedback=[],
                    total_feedback=0,
                    filters_applied=filters_obj,
                    date_range={"from_date": filters.get('from_date') or "", "to_date": filters.get('to_date') or ""},
                    summary={"message": "No user feedback found"},
                    message=feedback_data.get("message", "No user feedback found")
                )
            
            feedback_results = feedback_data["feedback"]
            
            # Process feedback data for frontend display
            processed_feedback = []
            
            for feedback_result in feedback_results:
                user_feedback = feedback_result[0]  # UserFeedback object
                user_name = feedback_result[1] or "Unknown User"  # User name
                
                # Format datetime for frontend display (DD-MMM-YYYY HH:MM AM/PM)
                created_at = user_feedback.created_at
                day = created_at.strftime('%d')
                month = created_at.strftime('%b')
                year = created_at.strftime('%Y')
                time_12hr = created_at.strftime('%I:%M %p')
                formatted_datetime = f"{day}-{month}-{year} {time_12hr}"
                
                # Create status badge class
                status_badge_map = {
                    "open": "badge bg-primary",
                    "in_progress": "badge bg-warning",
                    "resolved": "badge bg-success",
                    "closed": "badge bg-secondary"
                }
                status_badge = status_badge_map.get(user_feedback.status, "badge bg-secondary")
                
                processed_feedback_item = UserFeedbackData(
                    id=user_feedback.id,
                    user_name=user_name,
                    feedback_type=user_feedback.feedback_type,
                    subject=user_feedback.subject,
                    description=user_feedback.description,
                    rating=user_feedback.rating,
                    status=user_feedback.status,
                    created_at=user_feedback.created_at,
                    resolved_at=user_feedback.resolved_at,
                    datetime=formatted_datetime,
                    status_badge=status_badge
                )
                
                processed_feedback.append(processed_feedback_item)
            
            # Create summary statistics
            total_feedback = feedback_data.get("total_count", len(processed_feedback))
            
            # Calculate summary statistics
            status_counts = {}
            type_counts = {}
            rating_counts = {}
            
            for feedback in processed_feedback:
                # Status counts
                status_counts[feedback.status] = status_counts.get(feedback.status, 0) + 1
                
                # Type counts
                type_counts[feedback.feedback_type] = type_counts.get(feedback.feedback_type, 0) + 1
                
                # Rating counts
                if feedback.rating:
                    rating_counts[feedback.rating] = rating_counts.get(feedback.rating, 0) + 1
            
            # Calculate average rating
            total_ratings = sum(rating_counts.values())
            weighted_sum = sum(rating * count for rating, count in rating_counts.items())
            average_rating = round(weighted_sum / total_ratings, 2) if total_ratings > 0 else 0
            
            summary = {
                "total_feedback": total_feedback,
                "status_breakdown": status_counts,
                "type_breakdown": type_counts,
                "rating_breakdown": rating_counts,
                "average_rating": average_rating,
                "total_with_rating": total_ratings,
                "period_summary": f"Showing {len(processed_feedback)} of {total_feedback} feedback entries"
            }
            
            return UserFeedbackReportResponse(
                feedback=processed_feedback,
                total_feedback=total_feedback,
                filters_applied=filters_obj,
                date_range={"from_date": filters.get('from_date') or "", "to_date": filters.get('to_date') or ""},
                summary=summary,
                message="User feedback report generated successfully"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating User Feedback report: {e}")
            
            # Create empty filters object for error response
            filters_obj = UserFeedbackFilters(
                from_date=filters.get('from_date'),
                to_date=filters.get('to_date'),
                feedback_type=filters.get('feedback_type'),
                status=filters.get('status'),
                rating=filters.get('rating'),
                limit=filters.get('limit', 100)
            )
            
            return UserFeedbackReportResponse(
                feedback=[],
                total_feedback=0,
                filters_applied=filters_obj,
                date_range={"from_date": filters.get('from_date') or "", "to_date": filters.get('to_date') or ""},
                summary={"error": f"Error generating user feedback report: {str(e)}"},
                message=f"Error: {str(e)}"
            )
    
    # System Alert Methods
    def create_system_alert(self, alert_data: SystemAlertCreate) -> SystemAlertResponse:
        """Create a new system alert"""
        db_alert = self.repository.create_system_alert(alert_data)
        return SystemAlertResponse.from_orm(db_alert)
    
    def get_system_alerts(self, is_resolved: Optional[bool] = None, limit: int = 100) -> List[SystemAlertResponse]:
        """Get system alerts"""
        alerts = self.repository.get_system_alerts(is_resolved, limit)
        return [SystemAlertResponse.from_orm(alert) for alert in alerts]
    
    def resolve_system_alert(self, alert_id: int, resolved_by: int) -> Optional[SystemAlertResponse]:
        """Resolve system alert"""
        resolved_alert = self.repository.resolve_system_alert(alert_id, resolved_by)
        return SystemAlertResponse.from_orm(resolved_alert) if resolved_alert else None

    def get_system_alerts_report(self, filters: Dict[str, Any]) -> 'SystemAlertsReportResponse':
        """Get System Alerts report data with filtering"""
        from app.schemas.reports import (
            SystemAlertsReportResponse, SystemAlertData, SystemAlertFilters
        )
        from datetime import datetime
        
        try:
            # Validate business_id is provided
            business_id = filters.get('business_id')
            if not business_id:
                raise ValueError("business_id is required for System Alerts report")
            
            # Create filters object
            filters_obj = SystemAlertFilters(
                from_date=filters.get('from_date'),
                to_date=filters.get('to_date'),
                alert_type=filters.get('alert_type'),
                is_resolved=filters.get('is_resolved'),
                module=filters.get('module'),
                limit=filters.get('limit', 100)
            )
            
            # Get system alerts data from repository
            alerts_data = self.repository.get_system_alerts_with_filters(filters)
            
            if not alerts_data.get("alerts"):
                return SystemAlertsReportResponse(
                    alerts=[],
                    total_alerts=0,
                    filters_applied=filters_obj,
                    date_range={"from_date": filters.get('from_date') or "", "to_date": filters.get('to_date') or ""},
                    summary={"message": "No system alerts found"},
                    message=alerts_data.get("message", "No system alerts found")
                )
            
            alerts_results = alerts_data["alerts"]
            
            # Process alerts data for frontend display
            processed_alerts = []
            
            for alert_result in alerts_results:
                system_alert = alert_result[0]  # SystemAlert object
                resolver_name = alert_result[1] or None  # Resolver name
                
                # Format datetime for frontend display (DD-MMM-YYYY HH:MM AM/PM)
                created_at = system_alert.created_at
                day = created_at.strftime('%d')
                month = created_at.strftime('%b')
                year = created_at.strftime('%Y')
                time_12hr = created_at.strftime('%I:%M %p')
                formatted_datetime = f"{day}-{month}-{year} {time_12hr}"
                
                # Create status badge class
                status_badge = "badge bg-success" if system_alert.is_resolved else "badge bg-danger"
                
                # Create alert type badge class
                alert_type_badge_map = {
                    "info": "badge bg-info",
                    "warning": "badge bg-warning",
                    "error": "badge bg-danger",
                    "critical": "badge bg-dark"
                }
                alert_type_badge = alert_type_badge_map.get(system_alert.alert_type, "badge bg-secondary")
                
                processed_alert = SystemAlertData(
                    id=system_alert.id,
                    alert_type=system_alert.alert_type,
                    title=system_alert.title,
                    message=system_alert.message,
                    module=system_alert.module,
                    is_resolved=system_alert.is_resolved,
                    created_at=system_alert.created_at,
                    resolved_at=system_alert.resolved_at,
                    resolved_by=system_alert.resolved_by,
                    resolver_name=resolver_name,
                    datetime=formatted_datetime,
                    status_badge=status_badge,
                    alert_type_badge=alert_type_badge
                )
                
                processed_alerts.append(processed_alert)
            
            # Create summary statistics
            total_alerts = alerts_data.get("total_count", len(processed_alerts))
            
            # Calculate summary statistics
            alert_type_counts = {}
            status_counts = {"resolved": 0, "unresolved": 0}
            module_counts = {}
            
            for alert in processed_alerts:
                # Alert type counts
                alert_type_counts[alert.alert_type] = alert_type_counts.get(alert.alert_type, 0) + 1
                
                # Status counts
                if alert.is_resolved:
                    status_counts["resolved"] += 1
                else:
                    status_counts["unresolved"] += 1
                
                # Module counts
                if alert.module:
                    module_counts[alert.module] = module_counts.get(alert.module, 0) + 1
            
            # Calculate resolution rate
            resolution_rate = round((status_counts["resolved"] / len(processed_alerts)) * 100, 2) if processed_alerts else 0
            
            summary = {
                "total_alerts": total_alerts,
                "alert_type_breakdown": alert_type_counts,
                "status_breakdown": status_counts,
                "module_breakdown": module_counts,
                "resolution_rate": resolution_rate,
                "critical_alerts": alert_type_counts.get("critical", 0),
                "unresolved_critical": len([a for a in processed_alerts if a.alert_type == "critical" and not a.is_resolved]),
                "period_summary": f"Showing {len(processed_alerts)} of {total_alerts} system alerts"
            }
            
            return SystemAlertsReportResponse(
                alerts=processed_alerts,
                total_alerts=total_alerts,
                filters_applied=filters_obj,
                date_range={"from_date": filters.get('from_date') or "", "to_date": filters.get('to_date') or ""},
                summary=summary,
                message="System alerts report generated successfully"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating System Alerts report: {e}")
            
            # Create empty filters object for error response
            filters_obj = SystemAlertFilters(
                from_date=filters.get('from_date'),
                to_date=filters.get('to_date'),
                alert_type=filters.get('alert_type'),
                is_resolved=filters.get('is_resolved'),
                module=filters.get('module'),
                limit=filters.get('limit', 100)
            )
            
            return SystemAlertsReportResponse(
                alerts=[],
                total_alerts=0,
                filters_applied=filters_obj,
                date_range={"from_date": filters.get('from_date') or "", "to_date": filters.get('to_date') or ""},
                summary={"error": f"Error generating system alerts report: {str(e)}"},
                message=f"Error: {str(e)}"
            )
    
    # Dashboard Methods
    def get_reports_dashboard(self) -> ReportDashboard:
        """Get reports dashboard data"""
        try:
            # Get current month data
            current_date = date.today()
            current_period = current_date.strftime('%Y-%m')
            start_of_month = current_date.replace(day=1)
            
            # Get salary summary with error handling
            try:
                salary_summary = self.get_salary_summary(current_period)
            except Exception as e:
                logger.error(f"Error getting salary summary: {e}")
                # Return default salary summary
                salary_summary = SalarySummary(
                    total_employees=0,
                    total_gross_salary=Decimal('0'),
                    total_net_salary=Decimal('0'),
                    total_deductions=Decimal('0'),
                    average_salary=Decimal('0')
                )
            
            # Get attendance summary with error handling
            try:
                attendance_summary = self.get_attendance_summary(start_of_month, current_date)
            except Exception as e:
                logger.error(f"Error getting attendance summary: {e}")
                # Return default attendance summary
                attendance_summary = AttendanceSummary(
                    total_employees=0,
                    present_count=0,
                    absent_count=0,
                    leave_count=0,
                    attendance_percentage=0.0
                )
            
            # Get report counts with error handling
            try:
                total_reports = len(self.repository.get_generated_reports(user_id=None, limit=1000))
                pending_reports = len([r for r in self.repository.get_generated_reports(user_id=None, limit=1000) if r.status == "generating"])
            except Exception as e:
                logger.error(f"Error getting report counts: {e}")
                total_reports = 0
                pending_reports = 0
            
            return ReportDashboard(
                salary_summary=salary_summary,
                attendance_summary=attendance_summary,
                total_reports_generated=total_reports,
                pending_reports=pending_reports
            )
        except Exception as e:
            logger.error(f"Error in get_reports_dashboard: {e}")
            # Return default dashboard data
            return ReportDashboard(
                salary_summary=SalarySummary(
                    total_employees=0,
                    total_gross_salary=Decimal('0'),
                    total_net_salary=Decimal('0'),
                    total_deductions=Decimal('0'),
                    average_salary=Decimal('0')
                ),
                attendance_summary=AttendanceSummary(
                    total_employees=0,
                    present_count=0,
                    absent_count=0,
                    leave_count=0,
                    attendance_percentage=0.0
                ),
                total_reports_generated=0,
                pending_reports=0
            )
    
    # Report Export Methods
    def export_report_data(self, report_type: str, filters: ReportFilters, format: str = "excel") -> Dict[str, Any]:
        """Export report data in specified format"""
        if report_type == "salary":
            data = self.get_salary_reports(filters)
        elif report_type == "attendance":
            data = self.get_attendance_reports(filters)
        elif report_type == "employee":
            data = self.get_employee_reports(filters)
        elif report_type == "statutory":
            data = self.get_statutory_reports(filters)
        elif report_type == "annual":
            data = self.get_annual_reports(filters)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        # In real implementation, this would generate actual files
        return {
            "report_type": report_type,
            "format": format,
            "record_count": len(data),
            "file_path": f"/exports/{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
            "generated_at": datetime.utcnow().isoformat()
        }
    def get_time_register(self, filters: 'TimeRegisterFilters') -> 'TimeRegisterResponse':
        """Get time register data with employee time breakdown"""
        from app.schemas.reports import TimeRegisterEmployee, TimeRegisterResponse
        
        try:
            # Parse period from frontend format (e.g., "NOV-2025" to "2025-11")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "NOV-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-11"
                period = filters.period
            
            # Get time register data
            time_data = self.repository.get_time_register_data(period, filters.dict())
            
            if not time_data:
                return TimeRegisterResponse(
                    period=period,
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_shift_hours = 0
            total_worked_hours = 0
            total_overtime_hours = 0
            
            for employee_data, attendance, overtime in time_data:
                employee = employee_data[0]
                dept_name = employee_data[1]
                desig_name = employee_data[2]
                loc_name = employee_data[3]
                cc_name = employee_data[4]
                
                # Calculate time metrics
                shift_hours = 8.0  # Standard 8-hour shift
                worked_hours = float(attendance.total_hours) if attendance and attendance.total_hours else 0.0
                overtime_hours = float(overtime.total_overtime_hours) if overtime and overtime.total_overtime_hours else 0.0
                present_days = int(attendance.present_days) if attendance and attendance.present_days else 0
                
                # Convert hours to HH:MM format
                def hours_to_hhmm(hours):
                    if hours == 0:
                        return "0:00"
                    total_minutes = int(hours * 60)
                    hours_part = total_minutes // 60
                    minutes_part = total_minutes % 60
                    return f"{hours_part}:{minutes_part:02d}"
                
                # Calculate various time components
                total_shift_minutes = int(shift_hours * present_days * 60)
                total_worked_minutes = int(worked_hours * 60)
                total_overtime_minutes = int(overtime_hours * 60)
                
                # Calculate early/late times (sample calculations)
                early_in_minutes = random.randint(0, 60) if present_days > 0 else 0
                late_in_minutes = random.randint(0, 120) if present_days > 0 else 0
                early_out_minutes = random.randint(0, 90) if present_days > 0 else 0
                late_out_minutes = random.randint(0, 60) if present_days > 0 else 0
                lunch_minutes = present_days * 60  # 1 hour lunch per day
                
                # Create employee record
                employee_record = TimeRegisterEmployee(
                    id=len(employees) + 1,
                    employee=f"{employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code,
                    shift_hrs=hours_to_hhmm(shift_hours * present_days),
                    early_in=hours_to_hhmm(early_in_minutes / 60),
                    late_in=hours_to_hhmm(late_in_minutes / 60),
                    in_hrs=hours_to_hhmm(worked_hours),
                    lunch=hours_to_hhmm(lunch_minutes / 60),
                    out_hrs=hours_to_hhmm(overtime_hours),
                    early_out=hours_to_hhmm(early_out_minutes / 60),
                    late_out=hours_to_hhmm(late_out_minutes / 60),
                    paid_hrs="-",  # As shown in frontend
                    
                    # Additional details
                    employee_id=employee.id,
                    department=dept_name,
                    designation=desig_name,
                    location=loc_name,
                    cost_center=cc_name,
                    
                    # Time in minutes for calculations
                    shift_minutes=total_shift_minutes,
                    early_in_minutes=early_in_minutes,
                    late_in_minutes=late_in_minutes,
                    in_minutes=total_worked_minutes,
                    lunch_minutes=lunch_minutes,
                    out_minutes=total_overtime_minutes,
                    early_out_minutes=early_out_minutes,
                    late_out_minutes=late_out_minutes,
                    paid_minutes=total_worked_minutes
                )
                
                employees.append(employee_record)
                total_shift_hours += shift_hours * present_days
                total_worked_hours += worked_hours
                total_overtime_hours += overtime_hours
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_shift_hours": total_shift_hours,
                "total_worked_hours": total_worked_hours,
                "total_overtime_hours": total_overtime_hours,
                "average_hours_per_employee": total_worked_hours / len(employees) if employees else 0,
                "period_formatted": filters.period
            }
            
            return TimeRegisterResponse(
                period=period,
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating time register: {e}")
            
            return TimeRegisterResponse(
                period=filters.period,
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating time register: {str(e)}"}
            )
    def get_strike_register(self, filters: 'StrikeRegisterFilters') -> 'StrikeRegisterResponse':
        """Get strike register data with employee strike details and deductions"""
        from app.schemas.reports import StrikeRegisterEmployee, StrikeRegisterStrike, StrikeRegisterResponse
        
        try:
            # Parse period from frontend format (e.g., "JUL-2025" to "2025-07")
            from datetime import datetime
            if '-' in filters.period and len(filters.period.split('-')[0]) == 3:
                # Frontend format: "JUL-2025"
                month_obj = datetime.strptime(filters.period, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
            else:
                # Backend format: "2025-07"
                period = filters.period
            
            # Get strike register data
            strike_data = self.repository.get_strike_register_data(period, filters.dict())
            
            if not strike_data:
                return StrikeRegisterResponse(
                    period=period,
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No data found for the selected period and filters"}
                )
            
            # Process data into response format
            employees = []
            total_strikes = 0
            total_deductions = 0
            
            for employee_data, attendance_records, strike_rules, strike_adjustments in strike_data:
                employee = employee_data[0]
                dept_name = employee_data[1]
                desig_name = employee_data[2]
                loc_name = employee_data[3]
                cc_name = employee_data[4]
                
                # Analyze attendance records for strikes
                strikes = []
                employee_total_strikes = 0
                employee_total_deductions = 0
                
                for record in attendance_records:
                    strike_info = self._analyze_attendance_for_strikes(
                        record, strike_rules, strike_adjustments
                    )
                    
                    if strike_info:
                        # Apply deduction filter if specified
                        if filters.deduction and filters.deduction != "- Select -":
                            # Only include strikes with matching deduction type
                            if strike_info.deduction_type and filters.deduction in strike_info.deduction_type:
                                strikes.append(strike_info)
                                employee_total_strikes += strike_info.strike_count
                                employee_total_deductions += float(strike_info.deduction)
                        else:
                            # No deduction filter, include all strikes
                            strikes.append(strike_info)
                            employee_total_strikes += strike_info.strike_count
                            employee_total_deductions += float(strike_info.deduction)
                
                # Only include employee if they have strikes (when deduction filter is applied)
                # OR always include if no deduction filter
                if not filters.deduction or filters.deduction == "- Select -" or len(strikes) > 0:
                    # Create employee record
                    employee_record = StrikeRegisterEmployee(
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        employee_code=employee.employee_code or "",
                        employee_id=employee.id,
                        department=dept_name,
                        designation=desig_name,
                        location=loc_name,
                        cost_center=cc_name,
                        strikes=strikes,
                        total_strikes=employee_total_strikes,
                        total_deductions=Decimal(str(employee_total_deductions))
                    )
                    
                    employees.append(employee_record)
                    total_strikes += employee_total_strikes
                    total_deductions += employee_total_deductions
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_strikes": total_strikes,
                "total_deductions": total_deductions,
                "average_strikes_per_employee": total_strikes / len(employees) if employees else 0,
                "period_formatted": filters.period
            }
            
            return StrikeRegisterResponse(
                period=period,
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating strike register: {e}")
            
            return StrikeRegisterResponse(
                period=filters.period,
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating strike register: {str(e)}"}
            )
    
    def _analyze_attendance_for_strikes(self, attendance_record, strike_rules, strike_adjustments):
        """Analyze attendance record for potential strikes using database strike rules"""
        from app.schemas.reports import StrikeRegisterStrike
        from datetime import datetime, time, timedelta
        
        # If no strike rules configured, return None
        if not strike_rules:
            return None
        
        # Standard work hours (9 AM to 6 PM)
        standard_start = time(9, 0)
        standard_end = time(18, 0)
        
        # Check for various strike conditions based on rules
        strike_type = None
        strike_count = 0
        base_amount = Decimal('500.00')  # Base daily salary for calculation
        deduction_amount = Decimal('0.00')
        deduction_type = None
        
        # Create a mapping of rule types to rules for easy lookup
        rules_by_type = {rule.rule_type: rule for rule in strike_rules}
        
        # Check attendance status first
        if hasattr(attendance_record, 'attendance_status'):
            status = attendance_record.attendance_status.value if hasattr(attendance_record.attendance_status, 'value') else str(attendance_record.attendance_status)
            
            # Absent
            if status == 'ABSENT' and 'Absent' in rules_by_type:
                rule = rules_by_type['Absent']
                strike_type = "Absent"
                strike_count = 1 if rule.strike != "None" else 0
                deduction_type = "Absent Deduction"
                deduction_amount = base_amount  # Full day deduction
        
        # Check punch times if present
        if attendance_record.punch_in_time and attendance_record.punch_out_time:
            punch_in_time = attendance_record.punch_in_time.time() if hasattr(attendance_record.punch_in_time, 'time') else attendance_record.punch_in_time
            punch_out_time = attendance_record.punch_out_time.time() if hasattr(attendance_record.punch_out_time, 'time') else attendance_record.punch_out_time
            
            # Late coming
            if 'Late Coming' in rules_by_type:
                rule = rules_by_type['Late Coming']
                late_minutes = rule.minutes
                threshold_time = (datetime.combine(datetime.today(), standard_start) + timedelta(minutes=late_minutes)).time()
                
                if punch_in_time > threshold_time:
                    strike_type = "Late Coming"
                    strike_count = 1 if rule.strike != "None" else 0
                    deduction_type = "Late Coming Deduction"
                    # Calculate minutes late
                    late_mins = (datetime.combine(datetime.today(), punch_in_time) - datetime.combine(datetime.today(), threshold_time)).seconds // 60
                    deduction_amount = Decimal(str(late_mins * 2))  # Example: 2 rupees per minute
            
            # Early going
            if not strike_type and 'Early Going' in rules_by_type:
                rule = rules_by_type['Early Going']
                early_minutes = rule.minutes
                threshold_time = (datetime.combine(datetime.today(), standard_end) - timedelta(minutes=early_minutes)).time()
                
                if punch_out_time < threshold_time:
                    strike_type = "Early Going"
                    strike_count = 1 if rule.strike != "None" else 0
                    deduction_type = "Early Going Deduction"
                    # Calculate minutes early
                    early_mins = (datetime.combine(datetime.today(), threshold_time) - datetime.combine(datetime.today(), punch_out_time)).seconds // 60
                    deduction_amount = Decimal(str(early_mins * 2))  # Example: 2 rupees per minute
            
            # Short hours
            if not strike_type and attendance_record.total_hours and 'Short Hours' in rules_by_type:
                rule = rules_by_type['Short Hours']
                required_hours = 8  # Standard work hours
                
                if attendance_record.total_hours < required_hours:
                    strike_type = "Short Hours"
                    strike_count = 1 if rule.strike != "None" else 0
                    deduction_type = "Short Hours Deduction"
                    short_hours = required_hours - attendance_record.total_hours
                    deduction_amount = Decimal(str(short_hours * 50))  # Example: 50 rupees per hour
        
        # Half day
        if not strike_type and attendance_record.total_hours and attendance_record.total_hours < 4:
            if 'Half Day' in rules_by_type:
                rule = rules_by_type['Half Day']
                strike_type = "Half Day"
                strike_count = 1 if rule.strike != "None" else 0
                deduction_type = "Half Day Deduction"
                deduction_amount = base_amount / 2
        
        # Check for strike adjustments (manual adjustments)
        if strike_adjustments:
            for adjustment in strike_adjustments:
                if hasattr(adjustment, 'date') and adjustment.date == attendance_record.attendance_date:
                    # Apply manual adjustment
                    strike_type = adjustment.reason if hasattr(adjustment, 'reason') else strike_type
                    strike_count = adjustment.strike_count if hasattr(adjustment, 'strike_count') else strike_count
                    deduction_amount = Decimal(str(adjustment.deduction_amount)) if hasattr(adjustment, 'deduction_amount') else deduction_amount
        
        if strike_type and strike_count > 0:
            return StrikeRegisterStrike(
                date=attendance_record.attendance_date.strftime('%Y-%m-%d') if hasattr(attendance_record.attendance_date, 'strftime') else str(attendance_record.attendance_date),
                shift="Regular",
                strike=strike_type,
                strike_count=strike_count,
                base_amount=base_amount,
                deduction_type=deduction_type,
                deduction=deduction_amount
            )
        
        return None

    def get_travel_register(self, filters: 'TravelRegisterFilters') -> 'TravelRegisterResponse':
        """Get travel register data with employee travel details"""
        from app.schemas.reports import TravelRegisterRecord, TravelRegisterResponse
        
        try:
            # Get travel register data
            travel_data = self.repository.get_travel_register_data(filters.dict())
            
            if not travel_data:
                return TravelRegisterResponse(
                    total_records=0,
                    records=[],
                    filters_applied=filters,
                    summary={"message": "No travel records found for the selected filters"}
                )
            
            # Process data into response format
            records = []
            total_calculated_distance = 0.0
            total_approved_distance = 0.0
            
            for travel_request, employee, dept_name, desig_name, loc_name, cc_name in travel_data:
                # Create travel record
                record = TravelRegisterRecord(
                    id=travel_request.id,
                    employee_id=employee.id,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                    location=loc_name or 'Unknown',
                    department=dept_name or 'Unknown',
                    calculated_distance=float(getattr(travel_request, 'calculated_distance', 0.0)),
                    approved_distance=float(getattr(travel_request, 'approved_distance', 0.0)),
                    status=getattr(travel_request, 'status', 'Pending'),
                    travel_date=getattr(travel_request, 'travel_date', None),
                    from_location=getattr(travel_request, 'from_location', None),
                    to_location=getattr(travel_request, 'to_location', None),
                    purpose=getattr(travel_request, 'purpose', None),
                    travel_allowance=getattr(travel_request, 'travel_allowance', None)
                )
                
                records.append(record)
                total_calculated_distance += record.calculated_distance
                total_approved_distance += record.approved_distance
            
            # Create summary
            summary = {
                "total_records": len(records),
                "total_calculated_distance": round(total_calculated_distance, 2),
                "total_approved_distance": round(total_approved_distance, 2),
                "approved_records": len([r for r in records if r.status == "Approved"]),
                "pending_records": len([r for r in records if r.status == "Pending"]),
                "rejected_records": len([r for r in records if r.status == "Rejected"]),
                "zero_distance_records": len([r for r in records if r.calculated_distance == 0.0])
            }
            
            return TravelRegisterResponse(
                total_records=len(records),
                records=records,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating travel register: {e}")
            
            return TravelRegisterResponse(
                total_records=0,
                records=[],
                filters_applied=filters,
                summary={"error": f"Error generating travel register: {str(e)}"}
            )

    def get_time_punches(self, filters: 'TimePunchesFilters') -> 'TimePunchesResponse':
        """Get time punches data with employee punch details"""
        from app.schemas.reports import TimePunchRecord, TimePunchesEmployee, TimePunchesResponse
        from datetime import datetime, timedelta
        
        try:
            # Get time punches data
            punches_data = self.repository.get_time_punches_data(filters.dict())
            
            if not punches_data:
                return TimePunchesResponse(
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No punch records found for the selected filters"},
                    pagination={"current_page": 1, "total_pages": 1, "per_page": 10}
                )
            
            # Process data into response format
            employees = []
            total_punches = 0
            present_count = 0
            
            # Punch method mapping
            punch_method_map = {
                'biometric': 'Biometric',
                'selfie': 'Selfie',
                'remote': 'Remote',
                'web': 'Web/Chat',
                'qr': 'QR Scan',
                'manual': 'Manual',
                'api': 'API',
                'excel': 'Excel Import'
            }
            
            for employee_data, emp_punches, emp_attendance in punches_data:
                employee = employee_data[0]
                dept_name = employee_data[1] or 'Unknown'
                desig_name = employee_data[2] or 'Software Engineer'
                loc_name = employee_data[3] or 'Unknown'
                
                # Group punches by date
                punches_by_date = {}
                for punch in emp_punches:
                    punch_date = punch.punch_time.date()
                    if punch_date not in punches_by_date:
                        punches_by_date[punch_date] = []
                    punches_by_date[punch_date].append(punch)
                
                # Create employee records for each date
                for punch_date, date_punches in punches_by_date.items():
                    # Find attendance record for this date
                    attendance = next((a for a in emp_attendance if a.attendance_date == punch_date), None)
                    
                    # Calculate times and status
                    in_punches = [p for p in date_punches if p.punch_type == 'in']
                    out_punches = [p for p in date_punches if p.punch_type == 'out']
                    
                    in_time = None
                    out_time = None
                    total_hours = "0 m"
                    status = "Present"
                    
                    if in_punches:
                        in_time = in_punches[0].punch_time.strftime("%I:%M%p").replace("AM", "A").replace("PM", "P")
                    
                    if out_punches:
                        out_time = out_punches[-1].punch_time.strftime("%I:%M%p").replace("AM", "A").replace("PM", "P")
                    
                    # Calculate total hours
                    if in_punches and out_punches:
                        time_diff = out_punches[-1].punch_time - in_punches[0].punch_time
                        hours = int(time_diff.total_seconds() // 3600)
                        minutes = int((time_diff.total_seconds() % 3600) // 60)
                        if hours > 0:
                            total_hours = f"{hours} h {minutes} m"
                        else:
                            total_hours = f"{minutes} m"
                    elif in_punches and not out_punches:
                        total_hours = "0 m"
                    
                    # Determine punch method from first punch
                    punch_method = "Selfie"  # Default
                    if date_punches:
                        first_punch = date_punches[0]
                        # Determine method based on available fields
                        if getattr(first_punch, 'is_biometric', False):
                            punch_method = 'Biometric'
                        elif getattr(first_punch, 'is_manual', False):
                            punch_method = 'Manual'
                        elif 'remote' in (getattr(first_punch, 'device_info', '') or '').lower():
                            punch_method = 'Remote'
                        elif 'web' in (getattr(first_punch, 'device_info', '') or '').lower():
                            punch_method = 'Web/Chat'
                        else:
                            punch_method = 'Selfie'
                    
                    # Create punch records
                    punch_records = []
                    for punch in date_punches:
                        punch_record = TimePunchRecord(
                            punch_time=punch.punch_time.strftime("%I:%M:%S %p"),
                            punch_type=punch.punch_type.upper(),
                            location=getattr(punch, 'location', None) or 'Office',
                            device_info=getattr(punch, 'device_info', None),
                            punch_method=punch_method  # Use the determined method for all punches on this date
                        )
                        punch_records.append(punch_record)
                    
                    # Create employee record
                    employee_record = TimePunchesEmployee(
                        id=employee.id,
                        name=f"{employee.first_name} {employee.last_name}".strip(),
                        code=employee.employee_code or f"EMP{employee.id:03d}",
                        location=loc_name,
                        department=dept_name,
                        role=desig_name,
                        date=punch_date.strftime("%d-%b-%Y"),
                        status=status,
                        in_time=in_time,
                        out_time=out_time,
                        total_hours=total_hours,
                        punch_type=punch_method,
                        progress_color="#377dff",
                        punches=punch_records
                    )
                    
                    employees.append(employee_record)
                    total_punches += len(date_punches)
                    if status == "Present":
                        present_count += 1
            
            # Sort employees by name
            employees.sort(key=lambda x: x.name)
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_punches": total_punches,
                "present_count": present_count,
                "absent_count": len(employees) - present_count,
                "average_punches_per_employee": round(total_punches / len(employees), 2) if employees else 0
            }
            
            # Pagination (simple implementation)
            pagination = {
                "current_page": 1,
                "total_pages": 1,
                "per_page": len(employees),
                "total_records": len(employees)
            }
            
            return TimePunchesResponse(
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary,
                pagination=pagination
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating time punches: {e}")
            
            return TimePunchesResponse(
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating time punches: {str(e)}"},
                pagination={"current_page": 1, "total_pages": 1, "per_page": 10}
            )

    def get_remote_punch(self, filters: 'RemotePunchFilters') -> 'RemotePunchResponse':
        """Get remote punch data with employee remote punch details"""
        from app.schemas.reports import RemotePunchEmployee, RemotePunchRecord, RemotePunchResponse
        
        try:
            # Get remote punch data
            remote_punch_data = self.repository.get_remote_punch_data(filters.dict())
            
            if not remote_punch_data:
                return RemotePunchResponse(
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No remote punch data found for the selected filters"},
                    date_range={"from_date": "", "to_date": ""}
                )
            
            # Process data into response format
            employees = []
            total_punches = 0
            
            for employee_data, punch_records in remote_punch_data:
                employee = employee_data[0]
                dept_name = employee_data[1]
                desig_name = employee_data[2]
                loc_name = employee_data[3]
                cc_name = employee_data[4]
                
                # Process punch records
                punches = []
                for punch in punch_records:
                    # Format coordinates
                    coords = ""
                    if punch.latitude and punch.longitude:
                        coords = f"{punch.latitude}, {punch.longitude}"
                    
                    # Format datetime
                    punch_datetime = punch.punch_time.strftime("%d-%m-%Y %H:%M") if punch.punch_time else ""
                    
                    # Get address (mock for now - in real implementation would use reverse geocoding)
                    address = punch.location or "Address Not Fetched"
                    
                    punch_record = RemotePunchRecord(
                        datetime=punch_datetime,
                        coords=coords,
                        address=address,
                        punch_type=punch.punch_type.upper() if punch.punch_type else "IN",
                        device_info=punch.device_info,
                        location_accuracy=punch.location_accuracy if hasattr(punch, 'location_accuracy') else None
                    )
                    
                    punches.append(punch_record)
                    total_punches += 1
                
                # Create employee record
                employee_record = RemotePunchEmployee(
                    id=employee.id,
                    name=f"{employee.employee_code} - {employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code,
                    department=dept_name,
                    designation=desig_name,
                    location=loc_name,
                    punches=punches
                )
                
                employees.append(employee_record)
            
            # Create summary
            employees_with_punches = len([emp for emp in employees if emp.punches])
            employees_without_punches = len(employees) - employees_with_punches
            
            # Format date range for response
            date_range = {
                "from_date": filters.date_from or "",
                "to_date": filters.date_to or ""
            }
            
            summary = {
                "total_employees": len(employees),
                "employees_with_remote_punches": employees_with_punches,
                "employees_without_remote_punches": employees_without_punches,
                "total_remote_punches": total_punches,
                "average_punches_per_employee": round(total_punches / len(employees), 2) if employees else 0,
                "filters_summary": {
                    "location": filters.location,
                    "department": filters.department,
                    "cost_center": filters.cost_center,
                    "date_range": f"{filters.date_from or 'N/A'} to {filters.date_to or 'N/A'}"
                }
            }
            
            return RemotePunchResponse(
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary,
                date_range=date_range
            )
        
        except Exception as e:
            logger.error(f"Error getting remote punch data: {e}")
            return RemotePunchResponse(
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)},
                date_range={"from_date": "", "to_date": ""}
            )
    
    def get_manual_updates(self, filters: 'ManualUpdatesFilters') -> 'ManualUpdatesResponse':
        """Get manual updates data with attendance corrections and manual entries"""
        from app.schemas.reports import ManualUpdateRecord, ManualUpdatesResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get manual updates data
            manual_updates_data = self.repository.get_manual_updates_data(filters.dict())
            
            if not manual_updates_data:
                return ManualUpdatesResponse(
                    total_records=0,
                    records=[],
                    filters_applied=filters,
                    summary={"message": "No manual updates found for the selected filters"},
                    month_info={"month": filters.month or "Current Month", "total_days": "0"}
                )
            
            # Process data into response format
            records = []
            
            for update_type, update_data in manual_updates_data:
                if update_type == 'manual_entry':
                    # Manual attendance entry
                    attendance_record = update_data[0]
                    employee = update_data[1]
                    dept_name = update_data[2]
                    desig_name = update_data[3]
                    loc_name = update_data[4]
                    cc_name = update_data[5]
                    updated_by_name = update_data[6]
                    
                    # Determine original status (assume it was absent if manually entered)
                    original_status = "Absent"
                    updated_status = attendance_record.attendance_status.value.title() if attendance_record.attendance_status else "Present"
                    
                    # Format updated by name
                    updated_by = updated_by_name or "System"
                    
                    record = ManualUpdateRecord(
                        employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        date=attendance_record.attendance_date.strftime("%Y-%m-%d"),
                        original_status=original_status,
                        updated_status=updated_status,
                        updated_by=updated_by,
                        reason=attendance_record.manual_entry_reason or "Manual entry",
                        update_time=attendance_record.created_at.strftime("%H:%M") if attendance_record.created_at else None
                    )
                    
                elif update_type == 'correction':
                    # Attendance correction
                    correction = update_data[0]
                    employee = update_data[1]
                    dept_name = update_data[2]
                    desig_name = update_data[3]
                    loc_name = update_data[4]
                    cc_name = update_data[5]
                    updated_by_name = update_data[6]
                    attendance_date = update_data[7]
                    
                    # Map correction types to readable statuses
                    correction_type_map = {
                        'late_entry': 'Late',
                        'early_exit': 'Early Exit',
                        'leave': 'On Leave',
                        'absent': 'Absent',
                        'present': 'Present',
                        'half_day': 'Half Day'
                    }
                    
                    original_status = correction_type_map.get(correction.correction_type, correction.correction_type.title())
                    updated_status = "Present"  # Most corrections result in present status
                    
                    # Format updated by name
                    updated_by = updated_by_name or "System"
                    
                    record = ManualUpdateRecord(
                        employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                        employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                        date=attendance_date.strftime("%Y-%m-%d"),
                        original_status=original_status,
                        updated_status=updated_status,
                        updated_by=updated_by,
                        reason=correction.reason or "Attendance correction",
                        update_time=correction.approved_at.strftime("%H:%M") if correction.approved_at else None
                    )
                
                records.append(record)
            
            # Create summary
            total_records = len(records)
            manual_entries = len([r for r in manual_updates_data if r[0] == 'manual_entry'])
            corrections = len([r for r in manual_updates_data if r[0] == 'correction'])
            
            # Get unique employees
            unique_employees = len(set(record.employee_code for record in records))
            
            summary = {
                "total_records": total_records,
                "manual_entries": manual_entries,
                "corrections": corrections,
                "unique_employees": unique_employees,
                "filters_summary": {
                    "location": filters.location,
                    "department": filters.department,
                    "cost_center": filters.cost_center,
                    "month": filters.month or "Current Month"
                }
            }
            
            # Month info
            month_info = {
                "month": filters.month or "Current Month",
                "total_days": "31",  # String format as expected by schema
                "display_format": filters.month or "Current Month"
            }
            
            return ManualUpdatesResponse(
                total_records=total_records,
                records=records,
                filters_applied=filters,
                summary=summary,
                month_info=month_info
            )
        
        except Exception as e:
            logger.error(f"Error getting manual updates data: {e}")
            return ManualUpdatesResponse(
                total_records=0,
                records=[],
                filters_applied=filters,
                summary={"error": str(e)},
                month_info={"month": filters.month or "Current Month", "total_days": "0"}
            )
    
    def get_employee_register(self, filters: 'EmployeeRegisterFilters', options: 'EmployeeRegisterOptions') -> 'EmployeeRegisterResponse':
        """Get employee register data with configurable field options"""
        from app.schemas.reports import EmployeeRegisterRecord, EmployeeRegisterResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get employee register data
            employee_data = self.repository.get_employee_register_data(filters.dict())
            
            if not employee_data:
                return EmployeeRegisterResponse(
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    options_applied=options,
                    summary={"message": "No employees found for the selected filters"}
                )
            
            # Process data into response format based on selected options
            employees = []
            
            for emp_data in employee_data:
                employee = emp_data[0]
                dept_name = emp_data[1]
                desig_name = emp_data[2]
                loc_name = emp_data[3]
                cc_name = emp_data[4]
                grade_name = emp_data[5]
                bank_name = emp_data[6]
                bank_ifsc = emp_data[7]
                bank_account = emp_data[8]
                pan_number = emp_data[9]
                esi_number = emp_data[10]
                pf_uan_number = emp_data[11]
                aadhaar_number = emp_data[12]
                home_phone = emp_data[13]
                personal_email = emp_data[14]
                other_info1 = emp_data[15]
                other_info2 = emp_data[16]
                other_info3 = emp_data[17]
                other_info4 = emp_data[18]
                other_info5 = emp_data[19]
                
                # Create employee record with only selected fields
                record_data = {}
                
                # Basic Details
                if options.employee_code:
                    record_data['employee_code'] = employee.employee_code
                if options.employee_name:
                    record_data['employee_name'] = f"{employee.first_name} {employee.last_name}".strip()
                if options.gender:
                    record_data['gender'] = employee.gender.value.title() if employee.gender else None
                if options.dob:
                    record_data['dob'] = employee.date_of_birth.strftime("%Y-%m-%d") if employee.date_of_birth else None
                if options.doj:
                    record_data['doj'] = employee.date_of_joining.strftime("%Y-%m-%d") if employee.date_of_joining else None
                if options.doe:
                    record_data['doe'] = employee.date_of_termination.strftime("%Y-%m-%d") if employee.date_of_termination else None
                
                # Work Profile
                if options.location:
                    record_data['location'] = loc_name
                if options.cost_center:
                    record_data['cost_center'] = cc_name
                if options.department:
                    record_data['department'] = dept_name
                if options.grade:
                    record_data['grade'] = grade_name
                if options.designation:
                    record_data['designation'] = desig_name
                if options.pan:
                    record_data['pan'] = pan_number
                if options.esi:
                    record_data['esi'] = esi_number
                if options.pf_uan:
                    record_data['pf_uan'] = pf_uan_number
                
                # Personal Details
                if options.aadhaar:
                    record_data['aadhaar'] = aadhaar_number
                if options.office_email:
                    record_data['office_email'] = employee.email
                if options.office_phone:
                    record_data['office_phone'] = employee.mobile  # Using mobile as office phone
                if options.mobile:
                    record_data['mobile'] = employee.mobile
                if options.bank_name:
                    record_data['bank_name'] = bank_name
                if options.bank_ifsc:
                    record_data['bank_ifsc'] = bank_ifsc
                if options.bank_account:
                    record_data['bank_account'] = bank_account
                
                # Extra Info
                if options.home_phone:
                    record_data['home_phone'] = home_phone
                if options.personal_email:
                    record_data['personal_email'] = personal_email
                if options.other_info1:
                    record_data['other_info1'] = other_info1
                if options.other_info2:
                    record_data['other_info2'] = other_info2
                if options.other_info3:
                    record_data['other_info3'] = other_info3
                if options.other_info4:
                    record_data['other_info4'] = other_info4
                if options.other_info5:
                    record_data['other_info5'] = other_info5
                
                employee_record = EmployeeRegisterRecord(**record_data)
                employees.append(employee_record)
            
            # Create summary
            total_employees = len(employees)
            selected_fields = sum(1 for field, value in options.dict().items() if value)
            
            summary = {
                "total_employees": total_employees,
                "selected_fields": selected_fields,
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "records_per_page": filters.records_per_page or "All Records"
                }
            }
            
            return EmployeeRegisterResponse(
                total_employees=total_employees,
                employees=employees,
                filters_applied=filters,
                options_applied=options,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting employee register data: {e}")
            return EmployeeRegisterResponse(
                total_employees=0,
                employees=[],
                filters_applied=filters,
                options_applied=options,
                summary={"error": str(e)}
            )
            date_range = {
                "from_date": filters.date_from or "",
                "to_date": filters.date_to or ""
            }
            
            return RemotePunchResponse(
                total_employees=len(employees),
                employees=employees,
                filters_applied=filters,
                summary=summary,
                date_range=date_range
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating remote punch report: {e}")
            
            return RemotePunchResponse(
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating remote punch report: {str(e)}"},
                date_range={"from_date": "", "to_date": ""}
            )
    def get_employee_addresses(self, filters: 'EmployeeAddressesFilters') -> 'EmployeeAddressesResponse':
        """Get employee addresses data with both present and permanent addresses"""
        from app.schemas.reports import EmployeeAddressRecord, EmployeeAddressesResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get employee addresses data
            employee_data = self.repository.get_employee_addresses_data(filters.dict())
            
            if not employee_data:
                return EmployeeAddressesResponse(
                    total_employees=0,
                    total_addresses=0,
                    addresses=[],
                    filters_applied=filters,
                    summary={"message": "No employees found for the selected filters"}
                )
            
            # Process data into response format
            addresses = []
            employee_count = 0
            
            for emp_data in employee_data:
                employee = emp_data[0]
                employee_profile = emp_data[1]
                dept_name = emp_data[2]
                desig_name = emp_data[3]
                loc_name = emp_data[4]
                cc_name = emp_data[5]
                
                employee_count += 1
                employee_name = f"{employee.first_name} {employee.last_name}".strip()
                
                # Add present address if available
                if (employee_profile.present_address_line1 or 
                    employee_profile.present_city or 
                    employee_profile.present_state):
                    
                    present_address = EmployeeAddressRecord(
                        id=employee.id,
                        name=employee_name,
                        code=employee.employee_code or "",
                        type="Present",
                        line1=employee_profile.present_address_line1 or "",
                        line2=employee_profile.present_address_line2 or "",
                        city=employee_profile.present_city or "",
                        pincode=employee_profile.present_pincode or "",
                        state=employee_profile.present_state or "",
                        country=employee_profile.present_country or "India"
                    )
                    addresses.append(present_address)
                
                # Add permanent address if available
                if (employee_profile.permanent_address_line1 or 
                    employee_profile.permanent_city or 
                    employee_profile.permanent_state):
                    
                    permanent_address = EmployeeAddressRecord(
                        id=employee.id,
                        name=employee_name,
                        code=employee.employee_code or "",
                        type="Permanent",
                        line1=employee_profile.permanent_address_line1 or "",
                        line2=employee_profile.permanent_address_line2 or "",
                        city=employee_profile.permanent_city or "",
                        pincode=employee_profile.permanent_pincode or "",
                        state=employee_profile.permanent_state or "",
                        country=employee_profile.permanent_country or "India"
                    )
                    addresses.append(permanent_address)
            
            # Create summary
            total_addresses = len(addresses)
            present_count = sum(1 for addr in addresses if addr.type == "Present")
            permanent_count = sum(1 for addr in addresses if addr.type == "Permanent")
            
            summary = {
                "total_employees": employee_count,
                "total_addresses": total_addresses,
                "present_addresses": present_count,
                "permanent_addresses": permanent_count,
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "employee_search": filters.employee_search or "All Employees"
                }
            }
            
            return EmployeeAddressesResponse(
                total_employees=employee_count,
                total_addresses=total_addresses,
                addresses=addresses,
                filters_applied=filters,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting employee addresses data: {e}")
            return EmployeeAddressesResponse(
                total_employees=0,
                total_addresses=0,
                addresses=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_employee_events(self, filters: 'EmployeeEventsFilters') -> 'EmployeeEventsResponse':
        """Get employee events report with birthdays, work anniversaries, and wedding anniversaries"""
        from app.schemas.reports import EmployeeEventRecord, EmployeeEventsResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get employee events data
            events_data = self.repository.get_employee_events_data(filters.dict())
            
            if not events_data:
                return EmployeeEventsResponse(
                    total_events=0,
                    events=[],
                    filters_applied=filters,
                    summary={"message": "No events found for the selected filters"}
                )
            
            # Process data into events
            events = []
            
            for employee, employee_profile, dept_name, desig_name, loc_name, cc_name in events_data:
                employee_name = f"{employee.first_name} {employee.last_name}".strip()
                
                # Check if we should include birthdays
                if filters.show_birthdays and employee.date_of_birth:
                    birthday_event = EmployeeEventRecord(
                        date=employee.date_of_birth.strftime("%b %d,%Y"),
                        type="Birthday",
                        icon="bi bi-cake-fill",
                        iconColor="aqua",
                        employee=employee_name,
                        code=employee.employee_code or "",
                        location=loc_name or "Unknown",
                        department=dept_name or "Unknown",
                        designation=desig_name or "Unknown"
                    )
                    events.append(birthday_event)
                
                # Check if we should include work anniversaries
                if filters.show_work_anniversaries and employee.date_of_joining:
                    work_anniversary_event = EmployeeEventRecord(
                        date=employee.date_of_joining.strftime("%b %d,%Y"),
                        type="Work Anniversary",
                        icon="bi bi-briefcase-fill",
                        iconColor="green",
                        employee=employee_name,
                        code=employee.employee_code or "",
                        location=loc_name or "Unknown",
                        department=dept_name or "Unknown",
                        designation=desig_name or "Unknown"
                    )
                    events.append(work_anniversary_event)
                
                # Check if we should include wedding anniversaries
                if filters.show_wedding_anniversaries and employee_profile and employee_profile.wedding_date:
                    wedding_anniversary_event = EmployeeEventRecord(
                        date=employee_profile.wedding_date.strftime("%b %d,%Y"),
                        type="Wedding Anniversary",
                        icon="bi bi-heart-fill",
                        iconColor="red",
                        employee=employee_name,
                        code=employee.employee_code or "",
                        location=loc_name or "Unknown",
                        department=dept_name or "Unknown",
                        designation=desig_name or "Unknown"
                    )
                    events.append(wedding_anniversary_event)
            
            # Sort events by date (month and day)
            def get_sort_key(event):
                try:
                    from datetime import datetime
                    # Parse the date string to get month and day for sorting
                    date_obj = datetime.strptime(event.date, "%b %d,%Y")
                    return (date_obj.month, date_obj.day)
                except:
                    return (12, 31)  # Default to end of year if parsing fails
            
            events.sort(key=get_sort_key)
            
            # Create summary
            total_events = len(events)
            birthday_count = sum(1 for event in events if event.type == "Birthday")
            work_anniversary_count = sum(1 for event in events if event.type == "Work Anniversary")
            wedding_anniversary_count = sum(1 for event in events if event.type == "Wedding Anniversary")
            
            summary = {
                "total_events": total_events,
                "birthdays": birthday_count,
                "work_anniversaries": work_anniversary_count,
                "wedding_anniversaries": wedding_anniversary_count,
                "month_range": f"{filters.from_month} to {filters.to_month}",
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "show_birthdays": filters.show_birthdays,
                    "show_work_anniversaries": filters.show_work_anniversaries,
                    "show_wedding_anniversaries": filters.show_wedding_anniversaries
                }
            }
            
            return EmployeeEventsResponse(
                total_events=total_events,
                events=events,
                filters_applied=filters,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting employee events data: {e}")
            return EmployeeEventsResponse(
                total_events=0,
                events=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_promotion_age_report(self, filters: 'PromotionAgeFilters') -> 'PromotionAgeResponse':
        """Get promotion age report with employees and their promotion ageing"""
        from app.schemas.reports import PromotionAgeEmployee, PromotionAgeResponse
        import logging
        from datetime import datetime, date
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get promotion age data
            employees_data = self.repository.get_promotion_age_data(filters.dict())
            
            if not employees_data:
                return PromotionAgeResponse(
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No employees found for the selected filters"}
                )
            
            # Process data into employee records
            employees = []
            
            for idx, (employee, dept_name, desig_name, loc_name, cc_name, grade_name, last_promotion_date) in enumerate(employees_data):
                employee_name = f"{employee.first_name} {employee.last_name}".strip()
                
                # Use last promotion date or joining date as fallback
                promotion_date = last_promotion_date or employee.date_of_joining
                
                # Calculate ageing
                ageing_str = self._calculate_ageing(promotion_date) if promotion_date else "No promotion data"
                
                # Check if employee matches ageing filter - only apply filter if there's a valid promotion/joining date
                if promotion_date and not self._matches_ageing_filter(promotion_date, filters.ageing):
                    continue
                
                employee_record = PromotionAgeEmployee(
                    sn=len(employees) + 1,  # Sequential number after filtering
                    name=employee_name,
                    designation=desig_name or "Unknown",
                    department=dept_name or "Unknown",
                    location=loc_name or "Unknown",
                    costCenter=cc_name or "Unknown",
                    grade=grade_name or "Unknown",
                    lastPromoted=promotion_date.strftime("%Y-%m-%d") if promotion_date else "N/A",
                    ageing=ageing_str
                )
                employees.append(employee_record)
            
            # Create summary
            total_employees = len(employees)
            
            summary = {
                "total_employees": total_employees,
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "grade": filters.grade or "All Grades",
                    "ageing": filters.ageing or "More than 1 Year"
                }
            }
            
            return PromotionAgeResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting promotion age data: {e}")
            return PromotionAgeResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_increment_ageing_report(self, filters: 'IncrementAgeingFilters') -> 'IncrementAgeingResponse':
        """Get increment ageing report with employees and their increment ageing"""
        from app.schemas.reports import IncrementAgeingEmployee, IncrementAgeingResponse
        import logging
        from datetime import datetime, date
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get increment ageing data
            employees_data = self.repository.get_increment_ageing_data(filters.dict())
            
            if not employees_data:
                return IncrementAgeingResponse(
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No employees found for the selected filters"}
                )
            
            # Process data into employee records
            employees = []
            
            for idx, (employee, dept_name, desig_name, loc_name, cc_name, grade_name, last_increment_date) in enumerate(employees_data):
                employee_name = f"{employee.first_name} {employee.last_name}".strip()
                
                # Calculate ageing and format increment date
                if last_increment_date:
                    ageing_str = self._calculate_increment_ageing(last_increment_date)
                    last_increment_formatted = last_increment_date.strftime("%b %Y")  # "Jan 2023"
                    last_increment_date_str = last_increment_date.strftime("%Y-%m-%d")
                else:
                    ageing_str = "Never"
                    last_increment_formatted = "Never"
                    last_increment_date_str = None
                
                # Check if employee matches ageing filter
                if not self._matches_increment_ageing_filter(last_increment_date, filters.ageing):
                    continue
                
                employee_record = IncrementAgeingEmployee(
                    id=employee.id,
                    name=employee_name,
                    code=employee.employee_code or "",
                    designation=desig_name or "Unknown",
                    department=dept_name or "Unknown",
                    lastIncrement=last_increment_formatted,
                    lastIncrementDate=last_increment_date_str,
                    location=loc_name or "Unknown",
                    costCenter=cc_name or "Unknown",
                    grade=grade_name or "Unknown",
                    ageing=ageing_str
                )
                employees.append(employee_record)
            
            # Create summary
            total_employees = len(employees)
            
            summary = {
                "total_employees": total_employees,
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "grade": filters.grade or "All Grades",
                    "ageing": filters.ageing or "More than 1Year"
                }
            }
            
            return IncrementAgeingResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting increment ageing data: {e}")
            return IncrementAgeingResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )
    
    def _calculate_ageing(self, promotion_date: date) -> str:
        """Calculate ageing from promotion date"""
        if not promotion_date:
            return "No promotion data"
        
        today = date.today()
        
        years = today.year - promotion_date.year
        months = today.month - promotion_date.month
        
        if months < 0:
            years -= 1
            months += 12
        
        # Adjust if day hasn't occurred this month
        if today.day < promotion_date.day:
            months -= 1
            if months < 0:
                years -= 1
                months += 12
        
        if years == 0 and months == 0:
            return "Less than 1 Month"
        elif years == 0:
            return f"{months} Month{'s' if months > 1 else ''}"
        elif months == 0:
            return f"{years} Year{'s' if years > 1 else ''}"
        else:
            return f"{years} Year{'s' if years > 1 else ''} {months} Month{'s' if months > 1 else ''}"

    def _calculate_increment_ageing(self, increment_date: date) -> str:
        """Calculate ageing from increment date"""
        if not increment_date:
            return "Never"
        
        today = date.today()
        
        years = today.year - increment_date.year
        months = today.month - increment_date.month
        
        if months < 0:
            years -= 1
            months += 12
        
        # Adjust if day hasn't occurred this month
        if today.day < increment_date.day:
            months -= 1
            if months < 0:
                years -= 1
                months += 12
        
        if years == 0 and months == 0:
            return "Less than 1 Month"
        elif years == 0:
            return f"{months} Month{'s' if months > 1 else ''} ago"
        elif months == 0:
            return f"{years} Year{'s' if years > 1 else ''} ago"
        else:
            return f"{years} Year{'s' if years > 1 else ''} {months} Month{'s' if months > 1 else ''} ago"
    
    def _matches_ageing_filter(self, promotion_date: date, ageing_filter: str) -> bool:
        """Check if employee matches ageing filter"""
        # "All Employees" filter - show everyone
        if ageing_filter == "All Employees":
            return True
            
        if not promotion_date:
            return False
        
        # Skip future dates
        today = date.today()
        if promotion_date > today:
            return False
        
        years = today.year - promotion_date.year
        months = today.month - promotion_date.month
        
        if months < 0:
            years -= 1
            months += 12
        
        if today.day < promotion_date.day:
            months -= 1
            if months < 0:
                years -= 1
                months += 12
        
        if ageing_filter == "More than 1 Year":
            return years >= 1
        elif ageing_filter == "More than 2 Years":
            return years >= 2
        elif ageing_filter == "More than 3 Years":
            return years >= 3
        
        return True

    def _matches_increment_ageing_filter(self, increment_date: date, ageing_filter: str) -> bool:
        """Check if employee matches increment ageing filter"""
        # "All Employees" filter - show everyone
        if ageing_filter == "All Employees":
            return True
            
        # Handle "Never" case - employees with no increments should match all filters
        if not increment_date:
            return True  # "Never" matches all ageing filters
        
        # Skip future dates
        today = date.today()
        if increment_date > today:
            return False
        
        years = today.year - increment_date.year
        months = today.month - increment_date.month
        
        if months < 0:
            years -= 1
            months += 12
        
        if today.day < increment_date.day:
            months -= 1
            if months < 0:
                years -= 1
                months += 12
        
        # Normalize filter value (handle "More than 1Year" vs "More than 1 Year")
        filter_value = ageing_filter.replace("1Year", "1 Year").strip()
        
        if filter_value == "More than 1 Year":
            return years >= 1
        elif filter_value == "More than 2 Years":
            return years >= 2
        elif filter_value == "More than 3 Years":
            return years >= 3
        
        return True
    def get_employee_joinings_report(self, filters: 'EmployeeJoiningFilters') -> 'EmployeeJoiningResponse':
        """Get employee joinings report with employees and their joining details"""
        from app.schemas.reports import EmployeeJoiningEmployee, EmployeeJoiningResponse
        import logging
        from datetime import datetime, date, timedelta
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get employee joinings data
            employees_data = self.repository.get_employee_joinings_data(filters.dict())
            
            if not employees_data:
                return EmployeeJoiningResponse(
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No employees found for the selected filters"}
                )
            
            # Process data into employee records
            employees = []
            
            for employee, dept_name, desig_name, loc_name, cc_name, grade_name in employees_data:
                employee_name = f"{employee.first_name} {employee.last_name}".strip()
                
                # Format joining date
                joining_date = employee.date_of_joining.strftime("%Y-%m-%d") if employee.date_of_joining else ""
                
                # Calculate confirmation date (typically 6 months after joining)
                confirmation_date = ""
                if employee.date_of_joining:
                    confirmation_date_obj = employee.date_of_joining + timedelta(days=180)  # 6 months
                    confirmation_date = confirmation_date_obj.strftime("%Y-%m-%d")
                
                employee_record = EmployeeJoiningEmployee(
                    id=employee.id,
                    name=employee_name,
                    code=employee.employee_code or "",
                    joining=joining_date,
                    confirmation=confirmation_date,
                    location=loc_name or "Unknown",
                    department=dept_name or "Unknown",
                    designation=desig_name or "Unknown",
                    grade=grade_name or "Unknown",
                    cost_center=cc_name or "Unknown"
                )
                employees.append(employee_record)
            
            # Create summary
            total_employees = len(employees)
            
            # Calculate date range summary
            if employees:
                joining_dates = [emp.joining for emp in employees if emp.joining]
                earliest_joining = min(joining_dates) if joining_dates else "N/A"
                latest_joining = max(joining_dates) if joining_dates else "N/A"
            else:
                earliest_joining = "N/A"
                latest_joining = "N/A"
            
            summary = {
                "total_employees": total_employees,
                "earliest_joining": earliest_joining,
                "latest_joining": latest_joining,
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "grade": filters.grade or "All Grades",
                    "from_date": filters.from_date or "Not specified",
                    "to_date": filters.to_date or "Not specified"
                }
            }
            
            return EmployeeJoiningResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting employee joinings data: {e}")
            return EmployeeJoiningResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )
    def get_employee_exits_report(self, filters: 'EmployeeExitFilters') -> 'EmployeeExitResponse':
        """Get employee exits report with employees and their exit details"""
        from app.schemas.reports import EmployeeExitEmployee, EmployeeExitResponse
        import logging
        from datetime import datetime, date
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get employee exits data
            employees_data = self.repository.get_employee_exits_data(filters.dict())
            
            if not employees_data:
                return EmployeeExitResponse(
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No employees found for the selected filters"}
                )
            
            # Process data into employee records
            employees = []
            
            for employee, dept_name, desig_name, loc_name, cc_name, grade_name, separation_type, exit_date, exit_reason_text in employees_data:
                employee_name = f"{employee.first_name} {employee.last_name}".strip()
                
                # Format joining date
                joining_date = employee.date_of_joining.strftime("%Y-%m-%d") if employee.date_of_joining else ""
                
                # Determine exit date (prefer separation request date over employee termination date)
                exit_date_formatted = ""
                if exit_date:
                    exit_date_formatted = exit_date.strftime("%Y-%m-%d")
                elif employee.date_of_termination:
                    exit_date_formatted = employee.date_of_termination.strftime("%Y-%m-%d")
                
                # Determine exit reason
                exit_reason = ""
                if exit_reason_text:
                    exit_reason = exit_reason_text
                elif separation_type:
                    # Convert enum to readable format
                    exit_reason = separation_type.replace('_', ' ').title()
                else:
                    exit_reason = "Not specified"
                
                employee_record = EmployeeExitEmployee(
                    id=employee.id,
                    name=employee_name,
                    code=employee.employee_code or "",
                    location=loc_name or "Unknown",
                    department=dept_name or "Unknown",
                    designation=desig_name or "Unknown",
                    joining=joining_date,
                    exit=exit_date_formatted,
                    reason=exit_reason
                )
                employees.append(employee_record)
            
            # Create summary
            total_employees = len(employees)
            
            # Calculate date range summary
            if employees:
                exit_dates = [emp.exit for emp in employees if emp.exit]
                earliest_exit = min(exit_dates) if exit_dates else "N/A"
                latest_exit = max(exit_dates) if exit_dates else "N/A"
            else:
                earliest_exit = "N/A"
                latest_exit = "N/A"
            
            # Count by exit reasons
            reason_counts = {}
            for emp in employees:
                reason = emp.reason or "Not specified"
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            summary = {
                "total_employees": total_employees,
                "earliest_exit": earliest_exit,
                "latest_exit": latest_exit,
                "exit_reason_breakdown": reason_counts,
                "filters_summary": {
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "exit_reason": filters.exit_reason or "All Reasons",
                    "from_date": filters.from_date or "Not specified",
                    "to_date": filters.to_date or "Not specified"
                }
            }
            
            return EmployeeExitResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error getting employee exits data: {e}")
            return EmployeeExitResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_vaccination_status_report(self, filters: 'VaccinationStatusFilters') -> 'VaccinationStatusResponse':
        """Get vaccination status report with employees and their vaccination details"""
        from app.schemas.reports import VaccinationStatusEmployee, VaccinationStatusResponse
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'status': filters.status,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_vaccination_status_data(filters_dict)
            
            # Convert to response format
            employees = []
            vaccinated_count = 0
            not_vaccinated_count = 0
            
            for emp_data in employees_data:
                vaccination_status = emp_data.vaccination_status or 'Not Vaccinated'
                
                employee = VaccinationStatusEmployee(
                    id=emp_data.id,
                    empCode=emp_data.employee_code,
                    name=emp_data.name or 'Unknown',
                    location=emp_data.location or 'Unknown',
                    department=emp_data.department or 'Unknown',
                    status=vaccination_status
                )
                employees.append(employee)
                
                # Count vaccination status
                if vaccination_status == 'Vaccinated':
                    vaccinated_count += 1
                else:
                    not_vaccinated_count += 1
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "vaccinated_count": vaccinated_count,
                "not_vaccinated_count": not_vaccinated_count,
                "vaccination_percentage": round((vaccinated_count / len(employees) * 100), 2) if employees else 0
            }
            
            return VaccinationStatusResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error getting vaccination status data: {e}")
            return VaccinationStatusResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_workman_status_report(self, filters: 'WorkmanStatusFilters') -> 'WorkmanStatusResponse':
        """Get workman status report with employees and their workman installation details"""
        from app.schemas.reports import WorkmanStatusEmployee, WorkmanStatusResponse
        from datetime import datetime
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'inactive_only': filters.inactive_only,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_workman_status_data(filters_dict)
            
            # Convert to response format
            employees = []
            installed_count = 0
            not_installed_count = 0
            
            for emp_data in employees_data:
                workman_installed = emp_data.workman_installed or False
                workman_version = emp_data.workman_version or 'Not Installed'
                
                # Format last seen timestamp
                if emp_data.workman_last_seen:
                    last_seen = emp_data.workman_last_seen.strftime("%b %d, %Y %H:%M:%S")
                else:
                    last_seen = "Never"
                
                employee = WorkmanStatusEmployee(
                    id=emp_data.id,
                    emp_id=emp_data.employee_code,
                    name=emp_data.name or 'Unknown',
                    location=emp_data.location or 'Unknown',
                    dept=emp_data.department or 'Unknown',
                    installed=workman_installed,
                    version=workman_version,
                    last_seen=last_seen
                )
                employees.append(employee)
                
                # Count installation status
                if workman_installed:
                    installed_count += 1
                else:
                    not_installed_count += 1
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "installed_count": installed_count,
                "not_installed_count": not_installed_count,
                "installation_percentage": round((installed_count / len(employees) * 100), 2) if employees else 0
            }
            
            return WorkmanStatusResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error getting workman status data: {e}")
            return WorkmanStatusResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_employee_assets_report(self, filters: 'EmployeeAssetsFilters') -> 'EmployeeAssetsResponse':
        """Get employee assets report with employees and their assigned assets"""
        from app.schemas.reports import EmployeeAssetsEmployee, EmployeeAssetsResponse, AssetDetail
        from datetime import datetime
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'search': filters.search,
                'warranty_only': filters.warranty_only,
                'active_only': filters.active_only,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_employee_assets_data(filters_dict)
            
            # Convert to response format
            employees = []
            total_assets = 0
            expired_warranties = 0
            
            for emp_data in employees_data:
                employee = emp_data['employee']
                assets = emp_data['assets']
                
                # Convert assets to response format
                asset_details = []
                for asset in assets:
                    # Format dates
                    issued_date = asset.assigned_date.strftime("%b %d, %Y") if asset.assigned_date else "N/A"
                    warranty_expiry = asset.warranty_end_date.strftime("%b %d, %Y") if asset.warranty_end_date else "N/A"
                    
                    # Get asset icon based on type
                    asset_icons = {
                        'laptop': '/assets/img/icons/icon-asset_laptop.png',
                        'desktop': '/assets/img/icons/icon-asset_desktop.png',
                        'monitor': '/assets/img/icons/icon-asset_monitor.png',
                        'mobile': '/assets/img/icons/icon-asset_mobile.png',
                        'tablet': '/assets/img/icons/icon-asset_tablet.png',
                        'printer': '/assets/img/icons/icon-asset_printer.png'
                    }
                    icon = asset_icons.get(asset.asset_type, '/assets/img/icons/icon-asset_other.png')
                    
                    # Check warranty status
                    if asset.is_warranty_expired:
                        expired_warranties += 1
                    
                    asset_detail = AssetDetail(
                        id=asset.id,
                        type=asset.asset_type.title(),
                        name=asset.name,
                        serialNumber=asset.serial_number or "N/A",
                        issuedDate=issued_date,
                        warrantyExpiryDate=warranty_expiry,
                        estimatedValue=float(asset.estimated_value or 0),
                        icon=icon,
                        warranty_status=asset.warranty_status
                    )
                    asset_details.append(asset_detail)
                    total_assets += 1
                
                # Only include employees with assets if they have any
                if asset_details:
                    employee_record = EmployeeAssetsEmployee(
                        id=employee.id,
                        employeeCode=employee.employee_code,
                        employeeName=employee.employee_name or 'Unknown',
                        department=employee.department or 'Unknown',
                        location=employee.location or 'Unknown',
                        assets=asset_details
                    )
                    employees.append(employee_record)
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_assets": total_assets,
                "expired_warranties": expired_warranties,
                "active_warranties": total_assets - expired_warranties
            }
            
            return EmployeeAssetsResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error getting employee assets data: {e}")
            return EmployeeAssetsResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_employee_relatives_report(self, filters: 'EmployeeRelativesFilters') -> 'EmployeeRelativesResponse':
        """Get employee relatives report with employees and their family members"""
        from app.schemas.reports import EmployeeRelativesEmployee, EmployeeRelativesResponse, RelativeDetail
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'active_only': filters.active_only,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_employee_relatives_data(filters_dict)
            
            # Convert to response format
            employees = []
            total_relatives = 0
            
            for i, emp_data in enumerate(employees_data):
                employee = emp_data['employee']
                relatives = emp_data['relatives']
                
                # Convert relatives to response format
                relative_details = []
                for relative in relatives:
                    # Format date of birth
                    dob = relative.date_of_birth.strftime("%d-%b-%Y") if relative.date_of_birth else "N/A"
                    
                    relative_detail = RelativeDetail(
                        relation=relative.relation,
                        relativeName=relative.relative_name,
                        dob=dob,
                        dependent=relative.dependent or "No",
                        phone=relative.phone or "",
                        email=relative.email or "",
                        notes=relative.notes or ""
                    )
                    relative_details.append(relative_detail)
                    total_relatives += 1
                
                # Create employee record (include even if no relatives for frontend compatibility)
                employee_record = EmployeeRelativesEmployee(
                    sn=i + 1,
                    code=employee.employee_code,
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    location=emp_data['location_name'],
                    costCenter=emp_data['cost_center_name'],
                    department=emp_data['department_name'],
                    active=employee.employee_status == 'active',
                    relatives=relative_details
                )
                employees.append(employee_record)
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_relatives": total_relatives,
                "employees_with_relatives": len([emp for emp in employees if emp.relatives]),
                "employees_without_relatives": len([emp for emp in employees if not emp.relatives])
            }
            
            return EmployeeRelativesResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error getting employee relatives data: {e}")
            return EmployeeRelativesResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )

    def get_inactive_employees_report(self, filters: 'InactiveEmployeesFilters') -> 'InactiveEmployeesResponse':
        """Get inactive employees report with employee details"""
        from app.schemas.reports import InactiveEmployee, InactiveEmployeesResponse
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_inactive_employees_data(filters_dict)
            
            # Convert to response format
            employees = []
            
            for emp_data in employees_data:
                employee = emp_data[0]
                employee_profile = emp_data[1]
                department_name = emp_data.department_name or 'Technical Support'
                designation_name = emp_data.designation_name or 'Associate Software Engineer'
                location_name = emp_data.location_name or 'Hyderabad'
                cost_center_name = emp_data.cost_center_name or 'Associate Software Engineer'
                
                # Format joining date
                joining_date = employee.date_of_joining.strftime("%Y-%m-%d") if employee.date_of_joining else "N/A"
                
                # Get profile image URL or use default
                photo_url = "https://randomuser.me/api/portraits/men/1.jpg"  # Default
                if employee_profile and employee_profile.profile_image_url:
                    photo_url = employee_profile.profile_image_url
                else:
                    # Use different default images based on employee ID for variety
                    image_id = (employee.id % 10) + 1
                    gender = "men" if employee.gender == "male" else "women"
                    photo_url = f"https://randomuser.me/api/portraits/{gender}/{image_id}.jpg"
                
                # Create employee record
                employee_record = InactiveEmployee(
                    photo=photo_url,
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    code=employee.employee_code,
                    joiningDate=joining_date,
                    location=location_name,
                    costCenter=cost_center_name,
                    department=department_name,
                    designation=designation_name
                )
                employees.append(employee_record)
            
            # Create summary
            summary = {
                "total_inactive_employees": len(employees),
                "locations": len(set(emp.location for emp in employees)),
                "departments": len(set(emp.department for emp in employees)),
                "cost_centers": len(set(emp.costCenter for emp in employees))
            }
            
            return InactiveEmployeesResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error getting inactive employees data: {e}")
            return InactiveEmployeesResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)}
            )
    def get_export_records_report(self, filters: 'ExportRecordsFilters') -> 'ExportRecordsResponse':
        """Get export records report with employee details for CSV download"""
        from app.schemas.reports import ExportRecordEmployee, ExportRecordsResponse
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'record_type': filters.record_type,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_export_records_data(filters_dict)
            
            # Convert to response format
            employees = []
            
            for emp_data in employees_data:
                employee = emp_data[0]
                employee_profile = emp_data[1]
                department_name = emp_data.department_name or 'IT'
                designation_name = emp_data.designation_name or 'Software Engineer'
                location_name = emp_data.location_name or 'Hyderabad'
                cost_center_name = emp_data.cost_center_name or 'Dev Team'
                
                # Format joining date
                joining_date = employee.date_of_joining.strftime("%Y-%m-%d") if employee.date_of_joining else "N/A"
                
                # Create employee record for export
                employee_record = ExportRecordEmployee(
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    location=location_name,
                    department=department_name,
                    costCenter=cost_center_name,
                    employee_code=employee.employee_code,
                    designation=designation_name,
                    email=employee.email,
                    mobile=employee.mobile,
                    date_of_joining=joining_date,
                    employee_status=employee.employee_status.value if hasattr(employee.employee_status, 'value') else str(employee.employee_status)
                )
                employees.append(employee_record)
            
            # Create summary
            summary = {
                "total_records": len(employees),
                "record_type": filters.record_type,
                "active_employees": len([emp for emp in employees if emp.employee_status == 'active']),
                "inactive_employees": len([emp for emp in employees if emp.employee_status in ['inactive', 'terminated']]),
                "locations": len(set(emp.location for emp in employees)),
                "departments": len(set(emp.department for emp in employees)),
                "cost_centers": len(set(emp.costCenter for emp in employees))
            }
            
            return ExportRecordsResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary,
                total_records=len(employees)
            )
            
        except Exception as e:
            logger.error(f"Error getting export records data: {e}")
            return ExportRecordsResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)},
                total_records=0
            )
    def get_esi_deduction_report(self, filters: 'ESIDeductionFilters') -> 'ESIDeductionResponse':
        """Get ESI deduction report with employee ESI contribution details"""
        from app.schemas.reports import ESIDeductionEmployee, ESIDeductionResponse
        from datetime import datetime
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'month': filters.month,
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'report_type': filters.report_type,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_esi_deduction_data(filters_dict)
            
            # Convert to response format
            employees = []
            total_wages = Decimal('0')
            total_employee_contribution = Decimal('0')
            total_employer_contribution = Decimal('0')
            
            # Parse month for date calculations
            month_obj = datetime.strptime(filters.month, "%b-%Y")
            current_year = month_obj.year
            current_month = month_obj.month
            
            for emp_data in employees_data:
                employee = emp_data[0]
                employee_profile = emp_data[1]
                salary_report = emp_data[2]
                department_name = emp_data.department_name or 'IT'
                designation_name = emp_data.designation_name or 'Software Engineer'
                location_name = emp_data.location_name or 'Hyderabad'
                cost_center_name = emp_data.cost_center_name or 'Development'
                
                # Calculate ESI details
                gross_salary = salary_report.gross_salary if salary_report else Decimal('15000')
                
                # ESI calculation (0.75% employee + 3.25% employer on wages up to 25000)
                esi_eligible_wages = min(gross_salary, Decimal('25000'))
                employee_esi = esi_eligible_wages * Decimal('0.0075')  # 0.75%
                employer_esi = esi_eligible_wages * Decimal('0.0325')  # 3.25%
                
                # Working days (assume 30 for active employees)
                working_days = 30
                
                # ESI IP Number (generate if not available)
                esi_ip = getattr(employee_profile, 'esi_number', None) or f"{employee.id:06d}"
                
                # Last working date (format as DD/MM/YYYY)
                last_working_date = f"01/{current_month:02d}/{current_year}"
                
                # Create employee record
                employee_record = ESIDeductionEmployee(
                    id=employee.id,
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    ip=esi_ip,
                    days=working_days,
                    wages=esi_eligible_wages,
                    employee=employee_esi,
                    employer=employer_esi,
                    reason="-",
                    lastWorking=last_working_date,
                    employee_code=employee.employee_code,
                    designation=designation_name,
                    department=department_name,
                    location=location_name
                )
                employees.append(employee_record)
                
                # Add to totals
                total_wages += esi_eligible_wages
                total_employee_contribution += employee_esi
                total_employer_contribution += employer_esi
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_wages": float(total_wages),
                "total_employee_contribution": float(total_employee_contribution),
                "total_employer_contribution": float(total_employer_contribution),
                "total_esi_contribution": float(total_employee_contribution + total_employer_contribution),
                "period": filters.month,
                "report_type": filters.report_type,
                "esi_rate_employee": "0.75%",
                "esi_rate_employer": "3.25%",
                "esi_wage_ceiling": "₹25,000"
            }
            
            return ESIDeductionResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary,
                total_employees=len(employees),
                total_wages=total_wages,
                total_employee_contribution=total_employee_contribution,
                total_employer_contribution=total_employer_contribution
            )
            
        except Exception as e:
            logger.error(f"Error getting ESI deduction data: {e}")
            return ESIDeductionResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)},
                total_employees=0,
                total_wages=Decimal('0'),
                total_employee_contribution=Decimal('0'),
                total_employer_contribution=Decimal('0')
            )
    def get_esi_coverage_report(self, filters: 'ESICoverageFilters') -> 'ESICoverageResponse':
        """Get ESI coverage report with statistics and employee counts"""
        from app.schemas.reports import ESICoverageStats, ESICoverageResponse
        from datetime import datetime
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'month': filters.month,
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            coverage_data = self.repository.get_esi_coverage_data(filters_dict)
            
            # Create stats object
            stats = ESICoverageStats(
                total_employees=coverage_data['total_employees'],
                esi_deducted=coverage_data['esi_deducted'],
                esi_eligible=coverage_data['esi_eligible'],
                esi_not_eligible=coverage_data['esi_not_eligible'],
                total_esi_amount=Decimal(str(coverage_data['total_esi_amount'])),
                average_esi_per_employee=Decimal(str(coverage_data['average_esi_per_employee']))
            )
            
            # Create summary
            summary = {
                "period": filters.month,
                "coverage_percentage": round((coverage_data['esi_deducted'] / coverage_data['total_employees'] * 100), 2) if coverage_data['total_employees'] > 0 else 0,
                "eligibility_percentage": round((coverage_data['esi_eligible'] / coverage_data['total_employees'] * 100), 2) if coverage_data['total_employees'] > 0 else 0,
                "total_esi_contribution": coverage_data['total_esi_amount'],
                "esi_wage_ceiling": "₹25,000",
                "esi_rate": "0.75% (Employee) + 3.25% (Employer)",
                "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return ESICoverageResponse(
                stats=stats,
                filters_applied=filters,
                summary=summary,
                period=coverage_data['period']
            )
            
        except Exception as e:
            logger.error(f"Error getting ESI coverage data: {e}")
            return ESICoverageResponse(
                stats=ESICoverageStats(),
                filters_applied=filters,
                summary={"error": str(e)},
                period=filters.month
            )
    def get_pf_deduction_report(self, filters: 'PFDeductionFilters') -> 'PFDeductionResponse':
        """Get PF deduction report with employee PF contribution details"""
        from app.schemas.reports import PFDeductionEmployee, PFDeductionResponse
        from datetime import datetime
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'month': filters.month,
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'ignore_ncp_days': filters.ignore_ncp_days,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            employees_data = self.repository.get_pf_deduction_data(filters_dict)
            
            # Convert to response format
            employees = []
            total_gross_wages = Decimal('0')
            total_pf_wages = Decimal('0')
            total_employee_contribution = Decimal('0')
            total_employer_contribution = Decimal('0')
            total_pension_contribution = Decimal('0')
            
            for index, emp_data in enumerate(employees_data, 1):
                employee = emp_data[0]
                employee_profile = emp_data[1]
                salary_report = emp_data[2]
                department_name = emp_data.department_name or 'IT'
                designation_name = emp_data.designation_name or 'Software Engineer'
                location_name = emp_data.location_name or 'Hyderabad'
                cost_center_name = emp_data.cost_center_name or 'Development'
                
                # Calculate PF details
                gross_salary = salary_report.gross_salary if salary_report else Decimal('15000')
                
                # PF calculation (12% employee + 12% employer on basic salary, max 15000)
                basic_salary = salary_report.basic_salary if salary_report else gross_salary * Decimal('0.6')
                
                # NCP Days Adjustment (if not ignoring NCP days)
                adjusted_basic_salary = basic_salary
                if not filters.ignore_ncp_days and salary_report:
                    # Get NCP days and working days from salary report
                    ncp_days = getattr(salary_report, 'ncp_days', 0) or 0
                    working_days = getattr(salary_report, 'working_days', 30) or 30
                    
                    # Adjust basic salary proportionally if there are NCP days
                    if ncp_days > 0 and working_days > 0:
                        actual_working_days = working_days - ncp_days
                        if actual_working_days > 0:
                            # Proportional salary: basic_salary * (actual_working_days / working_days)
                            adjusted_basic_salary = basic_salary * (Decimal(str(actual_working_days)) / Decimal(str(working_days)))
                        else:
                            # If no actual working days, no PF contribution
                            adjusted_basic_salary = Decimal('0')
                
                # Apply PF wage ceiling after NCP adjustment
                pf_eligible_wages = min(adjusted_basic_salary, Decimal('15000'))  # PF wage ceiling
                
                # Employee PF contribution (12% of PF eligible wages)
                employee_pf = pf_eligible_wages * Decimal('0.12')
                
                # Employer contribution split: 8.33% to pension + 3.67% to PF
                pension_contribution = pf_eligible_wages * Decimal('0.0833')  # 8.33%
                employer_pf = pf_eligible_wages * Decimal('0.0367')  # 3.67%
                total_employer_cont = pension_contribution + employer_pf
                
                # UAN Number (generate if not available)
                uan_number = getattr(employee_profile, 'uan_number', None) or f"UAN{employee.id:06d}"
                
                # Create employee record
                employee_record = PFDeductionEmployee(
                    sn=index,
                    employee=f"{employee.first_name} {employee.last_name}".strip(),
                    uan_number=uan_number,
                    gross_wages=gross_salary,
                    wages=gross_salary,  # Same as gross wages for PF calculation
                    pf_wages=pf_eligible_wages,
                    pension_wages=pf_eligible_wages,  # Same as PF wages
                    employee_cont=employee_pf,
                    pension_cont=pension_contribution,
                    employer_cont=total_employer_cont,
                    employee_id=employee.id,
                    employee_code=employee.employee_code,
                    designation=designation_name,
                    department=department_name,
                    location=location_name
                )
                employees.append(employee_record)
                
                # Add to totals
                total_gross_wages += gross_salary
                total_pf_wages += pf_eligible_wages
                total_employee_contribution += employee_pf
                total_employer_contribution += total_employer_cont
                total_pension_contribution += pension_contribution
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_gross_wages": float(total_gross_wages),
                "total_pf_wages": float(total_pf_wages),
                "total_employee_contribution": float(total_employee_contribution),
                "total_employer_contribution": float(total_employer_contribution),
                "total_pension_contribution": float(total_pension_contribution),
                "total_pf_contribution": float(total_employee_contribution + total_employer_contribution),
                "period": filters.month,
                "pf_rate_employee": "12%",
                "pf_rate_employer": "12% (8.33% Pension + 3.67% PF)",
                "pf_wage_ceiling": "₹15,000",
                "ignore_ncp_days": filters.ignore_ncp_days
            }
            
            return PFDeductionResponse(
                employees=employees,
                filters_applied=filters,
                summary=summary,
                total_employees=len(employees),
                total_gross_wages=total_gross_wages,
                total_pf_wages=total_pf_wages,
                total_employee_contribution=total_employee_contribution,
                total_employer_contribution=total_employer_contribution,
                total_pension_contribution=total_pension_contribution
            )
            
        except Exception as e:
            logger.error(f"Error getting PF deduction data: {e}")
            return PFDeductionResponse(
                employees=[],
                filters_applied=filters,
                summary={"error": str(e)},
                total_employees=0,
                total_gross_wages=Decimal('0'),
                total_pf_wages=Decimal('0'),
                total_employee_contribution=Decimal('0'),
                total_employer_contribution=Decimal('0'),
                total_pension_contribution=Decimal('0')
            )
    def get_pf_coverage_report(self, filters: 'PFCoverageFilters') -> 'PFCoverageResponse':
        """Get PF coverage report with statistics and employee counts"""
        from app.schemas.reports import PFCoverageStats, PFCoverageResponse
        from datetime import datetime
        
        try:
            # Convert filters to dict for repository
            filters_dict = {
                'month': filters.month,
                'location': filters.location,
                'cost_center': filters.cost_center,
                'department': filters.department,
                'business_id': filters.business_id  # CRITICAL: Pass business_id for security
            }
            
            # Get data from repository
            coverage_data = self.repository.get_pf_coverage_data(filters_dict)
            
            # Create stats object
            stats = PFCoverageStats(
                total_employees=coverage_data['total_employees'],
                pf_deducted=coverage_data['pf_deducted'],
                pf_eligible=coverage_data['pf_eligible'],
                pf_not_eligible=coverage_data['pf_not_eligible'],
                total_pf_amount=Decimal(str(coverage_data['total_pf_amount'])),
                average_pf_per_employee=Decimal(str(coverage_data['average_pf_per_employee']))
            )
            
            # Create summary
            summary = {
                "period": filters.month,
                "coverage_percentage": round((coverage_data['pf_deducted'] / coverage_data['total_employees'] * 100), 2) if coverage_data['total_employees'] > 0 else 0,
                "eligibility_percentage": round((coverage_data['pf_eligible'] / coverage_data['total_employees'] * 100), 2) if coverage_data['total_employees'] > 0 else 0,
                "total_pf_contribution": coverage_data['total_pf_amount'],
                "pf_wage_ceiling": "₹15,000",
                "pf_rate": "12% (Employee) + 12% (Employer: 8.33% Pension + 3.67% PF)",
                "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return PFCoverageResponse(
                stats=stats,
                filters_applied=filters,
                summary=summary,
                period=coverage_data['period']
            )
            
        except Exception as e:
            logger.error(f"Error getting PF coverage data: {e}")
            return PFCoverageResponse(
                stats=PFCoverageStats(),
                filters_applied=filters,
                summary={"error": str(e)},
                period=filters.month
            )
    def get_income_tax_declaration_report(self, filters: 'IncomeTaxDeclarationFilters') -> 'IncomeTaxDeclarationResponse':
        """Get income tax declaration report data"""
        from app.schemas.reports import IncomeTaxDeclarationEmployee, IncomeTaxDeclarationResponse
        
        try:
            # Get income tax declaration data
            declaration_data = self.repository.get_income_tax_declaration_data(filters.dict())
            
            if not declaration_data:
                return IncomeTaxDeclarationResponse(
                    total_employees=0,
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No income tax declaration data found for the selected filters"},
                    financial_year=filters.financial_year or "2025-26"
                )
            
            # Process data into response format
            employees = []
            total_80c_amount = 0
            total_rent_paid = 0
            total_hra_exemption = 0
            
            for (declaration, employee, dept_name, desig_name, loc_name, cc_name) in declaration_data:
                # Format Chapter VI-A summary
                chapter_via_parts = []
                if declaration.total_80c > 0:
                    chapter_via_parts.append(f"80C - ₹{declaration.total_80c:,.0f}")
                if declaration.section_80d_medical > 0:
                    chapter_via_parts.append(f"80D - ₹{declaration.section_80d_medical:,.0f}")
                if declaration.section_80g_donations > 0:
                    chapter_via_parts.append(f"80G - ₹{declaration.section_80g_donations:,.0f}")
                
                chapter_via = ", ".join(chapter_via_parts) if chapter_via_parts else "No declarations"
                
                # Format rent paid
                rent_formatted = f"₹{declaration.rent_paid:,.0f}" if declaration.rent_paid > 0 else "₹0"
                
                # Determine tax regime (simplified logic)
                regime = "New" if declaration.total_80c == 0 and declaration.section_80d_medical == 0 else "Old"
                
                # Format last updated date
                updated_date = declaration.updated_at or declaration.created_at
                updated_str = updated_date.strftime("%Y-%m-%d") if updated_date else "Not updated"
                
                employee_data = IncomeTaxDeclarationEmployee(
                    id=declaration.id,
                    name=f"{employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                    pan=getattr(employee, 'pan_number', None) or "Not provided",
                    updated=updated_str,
                    chapter_via=chapter_via,
                    rent=rent_formatted,
                    regime=regime,
                    
                    # Backend fields
                    employee_id=employee.id,
                    designation=desig_name,
                    department=dept_name,
                    location=loc_name,
                    financial_year=declaration.financial_year,
                    status=declaration.status.value if declaration.status else "draft",
                    
                    # Detailed amounts
                    total_80c=declaration.total_80c,
                    pf_amount=declaration.pf_amount,
                    life_insurance=declaration.life_insurance,
                    elss_mutual_funds=declaration.elss_mutual_funds,
                    home_loan_principal=declaration.home_loan_principal,
                    tuition_fees=declaration.tuition_fees,
                    other_80c=declaration.other_80c,
                    section_80d_medical=declaration.section_80d_medical,
                    section_24_home_loan_interest=declaration.section_24_home_loan_interest,
                    section_80g_donations=declaration.section_80g_donations,
                    hra_exemption=declaration.hra_exemption,
                    rent_paid=declaration.rent_paid,
                    landlord_name=declaration.landlord_name,
                    landlord_pan=declaration.landlord_pan,
                    
                    # Timestamps
                    submitted_at=declaration.submitted_at,
                    approved_at=declaration.approved_at,
                    created_at=declaration.created_at,
                    updated_at=declaration.updated_at
                )
                
                employees.append(employee_data)
                
                # Update totals
                total_80c_amount += float(declaration.total_80c)
                total_rent_paid += float(declaration.rent_paid)
                total_hra_exemption += float(declaration.hra_exemption)
            
            # Calculate summary statistics
            total_employees = len(employees)
            employees_with_declarations = len([emp for emp in employees if emp.chapter_via != "No declarations"])
            employees_without_declarations = total_employees - employees_with_declarations
            
            # Status breakdown
            status_counts = {}
            for emp in employees:
                status = emp.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Regime breakdown
            old_regime_count = len([emp for emp in employees if emp.regime == "Old"])
            new_regime_count = len([emp for emp in employees if emp.regime == "New"])
            
            summary = {
                "total_employees": total_employees,
                "employees_with_declarations": employees_with_declarations,
                "employees_without_declarations": employees_without_declarations,
                "total_80c_amount": total_80c_amount,
                "total_rent_paid": total_rent_paid,
                "total_hra_exemption": total_hra_exemption,
                "average_80c_per_employee": total_80c_amount / total_employees if total_employees > 0 else 0,
                "status_breakdown": status_counts,
                "regime_breakdown": {
                    "old_regime": old_regime_count,
                    "new_regime": new_regime_count
                },
                "filters_summary": {
                    "location": filters.location,
                    "financial_year": filters.financial_year,
                    "active_employees_only": filters.active_employees_only,
                    "exclude_no_declarations": filters.exclude_no_declarations
                }
            }
            
            return IncomeTaxDeclarationResponse(
                total_employees=total_employees,
                employees=employees,
                filters_applied=filters,
                summary=summary,
                financial_year=filters.financial_year or "2025-26"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating income tax declaration report: {e}")
            
            return IncomeTaxDeclarationResponse(
                total_employees=0,
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating income tax declaration report: {str(e)}"},
                financial_year=filters.financial_year or "2025-26"
            )
    def get_income_tax_computation_report(self, filters: 'IncomeTaxComputationFilters') -> 'IncomeTaxComputationResponse':
        """Get income tax computation report data"""
        from app.schemas.reports import IncomeTaxComputationEmployee, IncomeTaxComputationReport, IncomeTaxComputationResponse
        from datetime import datetime
        
        try:
            # Get income tax computation data
            computation_data = self.repository.get_income_tax_computation_data(filters.dict())
            
            # Get report history
            reports_data = self.repository.get_income_tax_computation_reports(filters.dict())
            
            # Process employees data
            employees = []
            total_tax_liability = 0
            total_tds_amount = 0
            total_gross_salary = 0
            
            for data in computation_data:
                employee = data[0]
                dept_name = data[1]
                desig_name = data[2]
                loc_name = data[3]
                cc_name = data[4]
                gross_salary = data[5] or 0
                basic_salary = data[6] or 0
                net_salary = data[7] or 0
                total_deductions = data[8] or 0
                tds_amount = data[9] or 0
                taxable_income = data[10] or 0
                tax_slab_rate = data[11] or 0
                exemptions = data[12] or 0
                deductions_80c_tds = data[13] or 0
                other_deductions = data[14] or 0
                total_80c_declaration = data[15] or 0
                section_80d_medical = data[16] or 0
                hra_exemption = data[17] or 0
                
                # Calculate tax computation
                # Use declaration data if available, otherwise use TDS data
                deductions_80c = max(float(total_80c_declaration), float(deductions_80c_tds))
                deductions_80d = max(float(section_80d_medical), 0)
                
                # Calculate taxable income
                annual_gross = float(gross_salary) * 12 if gross_salary else 0
                total_exemptions = float(exemptions) + float(hra_exemption)
                total_deductions_calc = deductions_80c + deductions_80d + float(other_deductions)
                
                # Simplified tax calculation (basic tax slabs for India)
                taxable_annual = max(0, annual_gross - total_exemptions - total_deductions_calc)
                
                # Calculate tax liability (simplified Indian tax slabs for FY 2025-26)
                if taxable_annual <= 250000:
                    annual_tax = 0
                    slab_rate = 0
                elif taxable_annual <= 500000:
                    annual_tax = (taxable_annual - 250000) * 0.05
                    slab_rate = 5
                elif taxable_annual <= 750000:
                    annual_tax = 12500 + (taxable_annual - 500000) * 0.10
                    slab_rate = 10
                elif taxable_annual <= 1000000:
                    annual_tax = 37500 + (taxable_annual - 750000) * 0.15
                    slab_rate = 15
                elif taxable_annual <= 1250000:
                    annual_tax = 75000 + (taxable_annual - 1000000) * 0.20
                    slab_rate = 20
                elif taxable_annual <= 1500000:
                    annual_tax = 125000 + (taxable_annual - 1250000) * 0.25
                    slab_rate = 25
                else:
                    annual_tax = 187500 + (taxable_annual - 1500000) * 0.30
                    slab_rate = 30
                
                # Calculate monthly TDS
                # Parse month to determine remaining months in financial year
                try:
                    month_obj = datetime.strptime(filters.month, "%b-%Y")
                    current_month = month_obj.month
                    # Financial year starts from April
                    if current_month >= 4:
                        months_remaining = 12 - (current_month - 4)
                    else:
                        months_remaining = 4 - current_month
                except:
                    months_remaining = 12
                
                months_remaining = max(1, months_remaining)  # At least 1 month
                
                # Calculate TDS for current month
                tds_deducted_ytd = float(tds_amount) if tds_amount else 0
                remaining_tax = max(0, annual_tax - tds_deducted_ytd)
                monthly_tds = remaining_tax / months_remaining if months_remaining > 0 else 0
                
                employee_data = IncomeTaxComputationEmployee(
                    employee_id=employee.id,
                    employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    designation=desig_name,
                    department=dept_name,
                    location=loc_name,
                    
                    # Salary details
                    gross_salary=Decimal(str(gross_salary)),
                    basic_salary=Decimal(str(basic_salary)),
                    
                    # Tax computation
                    taxable_income=Decimal(str(taxable_annual)),
                    total_deductions=Decimal(str(total_deductions_calc)),
                    exemptions=Decimal(str(total_exemptions)),
                    
                    # From IT declarations
                    deductions_80c=Decimal(str(deductions_80c)),
                    deductions_80d=Decimal(str(deductions_80d)),
                    other_deductions=Decimal(str(other_deductions)),
                    hra_exemption=Decimal(str(hra_exemption)),
                    
                    # Tax calculation
                    tax_slab_rate=Decimal(str(slab_rate)),
                    annual_tax_liability=Decimal(str(annual_tax)),
                    monthly_tds=Decimal(str(monthly_tds)),
                    months_remaining=months_remaining,
                    
                    # TDS details
                    tds_deducted_ytd=Decimal(str(tds_deducted_ytd)),
                    tds_current_month=Decimal(str(monthly_tds))
                )
                
                employees.append(employee_data)
                
                # Update totals
                total_tax_liability += annual_tax
                total_tds_amount += tds_deducted_ytd
                total_gross_salary += annual_gross
            
            # Process reports data
            reports = []
            for report_data in reports_data:
                report = IncomeTaxComputationReport(
                    id=report_data["id"],
                    description=report_data["description"],
                    requested_on=report_data["requested_on"],
                    status=report_data["status"],
                    download_url=report_data.get("download_url"),
                    employee_count=report_data.get("employee_count", 0),
                    month=report_data.get("month", filters.month),
                    total_tax_liability=Decimal(str(total_tax_liability)),
                    total_tds_amount=Decimal(str(total_tds_amount)),
                    total_gross_salary=Decimal(str(total_gross_salary))
                )
                reports.append(report)
            
            # Calculate summary statistics
            total_employees = len(employees)
            average_tax_liability = total_tax_liability / total_employees if total_employees > 0 else 0
            average_monthly_tds = sum(float(emp.monthly_tds) for emp in employees) / total_employees if total_employees > 0 else 0
            
            summary = {
                "total_employees": total_employees,
                "total_tax_liability": total_tax_liability,
                "total_tds_amount": total_tds_amount,
                "total_gross_salary": total_gross_salary,
                "average_tax_liability": average_tax_liability,
                "average_monthly_tds": average_monthly_tds,
                "month": filters.month,
                "filters_summary": {
                    "location": filters.location,
                    "cost_center": filters.cost_center,
                    "department": filters.department
                }
            }
            
            return IncomeTaxComputationResponse(
                total_employees=total_employees,
                month=filters.month,
                reports=reports,
                filters_applied=filters,
                summary=summary,
                employees=employees
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating income tax computation report: {e}")
            
            return IncomeTaxComputationResponse(
                total_employees=0,
                month=filters.month,
                reports=[],
                filters_applied=filters,
                summary={"error": f"Error generating income tax computation report: {str(e)}"},
                employees=[]
            )

    def get_labour_welfare_fund_report(self, filters: 'LabourWelfareFundFilters') -> 'LabourWelfareFundResponse':
        """Get Labour Welfare Fund report data"""
        from app.schemas.reports import LabourWelfareFundEmployee, LabourWelfareFundResponse
        from datetime import datetime, date
        from decimal import Decimal
        
        try:
            # Parse period from frontend format (e.g., "JAN-2025" to "2025-01")
            if '-' in filters.month and len(filters.month.split('-')[0]) == 3:
                # Frontend format: "JAN-2025"
                month_obj = datetime.strptime(filters.month, "%b-%Y")
                period = month_obj.strftime('%Y-%m')
                period_date = date(month_obj.year, month_obj.month, 1)
            else:
                # Backend format: "2025-01"
                period = filters.month
                year, month = map(int, period.split('-'))
                period_date = date(year, month, 1)
            
            # Get Labour Welfare Fund data
            lwf_data = self.repository.get_labour_welfare_fund_data(period, filters.dict())
            
            if not lwf_data:
                return LabourWelfareFundResponse(
                    month=filters.month,
                    total_employees=0,
                    total_salary=Decimal('0'),
                    total_deduction=Decimal('0'),
                    total_contribution=Decimal('0'),
                    employees=[],
                    filters_applied=filters,
                    summary={"message": "No data found for the selected period and filters"}
                )
            
            # Get LWF rates for the period
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for Labour Welfare Fund report")
            
            lwf_rates = self.repository.get_lwf_rates_for_period(business_id, period_date)
            
            # Create a mapping of state to LWF rates
            state_rates = {}
            for rate in lwf_rates:
                if rate.state not in state_rates:
                    state_rates[rate.state] = rate
            
            # Default LWF rates if no specific rates found
            default_employee_rate = Decimal('20.00')  # ₹20 per month
            default_employer_rate = Decimal('20.00')  # ₹20 per month
            
            # Process employees data
            employees = []
            total_salary = Decimal('0')
            total_deduction = Decimal('0')
            total_contribution = Decimal('0')
            
            for idx, (salary_report, employee, employee_profile, dept_name, desig_name, loc_name, cc_name) in enumerate(lwf_data, 1):
                # Get employee state from profile or location
                employee_state = getattr(employee_profile, 'state', None) or 'Default'
                
                # Get LWF rates for this employee's state
                lwf_rate = state_rates.get(employee_state)
                if lwf_rate:
                    employee_deduction = lwf_rate.employee_contribution
                    employer_contribution = lwf_rate.employer_contribution
                else:
                    employee_deduction = default_employee_rate
                    employer_contribution = default_employer_rate
                
                # Calculate LWF based on salary (only if salary is above minimum threshold)
                gross_salary = salary_report.gross_salary
                lwf_applicable = gross_salary >= Decimal('15000')  # Minimum threshold for LWF
                
                if not lwf_applicable:
                    employee_deduction = Decimal('0')
                    employer_contribution = Decimal('0')
                
                # Create employee record
                employee_data = LabourWelfareFundEmployee(
                    sn=idx,
                    employee_id=employee.id,
                    employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    location=loc_name or 'Unknown',
                    state=employee_state,
                    salary=gross_salary,
                    deduction=employee_deduction,
                    contribution=employer_contribution,
                    department=dept_name,
                    designation=desig_name,
                    lwf_applicable=lwf_applicable
                )
                
                employees.append(employee_data)
                total_salary += gross_salary
                total_deduction += employee_deduction
                total_contribution += employer_contribution
            
            # Create summary
            summary = {
                "total_employees": len(employees),
                "total_salary": float(total_salary),
                "total_employee_deduction": float(total_deduction),
                "total_employer_contribution": float(total_contribution),
                "total_lwf_amount": float(total_deduction + total_contribution),
                "average_salary": float(total_salary / len(employees)) if employees else 0,
                "lwf_applicable_employees": sum(1 for emp in employees if emp.lwf_applicable),
                "period": filters.month,
                "filters_summary": {
                    "location": filters.location,
                    "cost_center": filters.cost_center,
                    "department": filters.department
                }
            }
            
            return LabourWelfareFundResponse(
                month=filters.month,
                total_employees=len(employees),
                total_salary=total_salary,
                total_deduction=total_deduction,
                total_contribution=total_contribution,
                employees=employees,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Labour Welfare Fund report: {e}")
            
            return LabourWelfareFundResponse(
                month=filters.month,
                total_employees=0,
                total_salary=Decimal('0'),
                total_deduction=Decimal('0'),
                total_contribution=Decimal('0'),
                employees=[],
                filters_applied=filters,
                summary={"error": f"Error generating Labour Welfare Fund report: {str(e)}"}
            )

    def get_tds_return_report(self, filters: 'TDSReturnFilters') -> 'TDSReturnResponse':
        """Get TDS Return report data"""
        from app.schemas.reports import TDSReturnQuarter, TDSReturnChallanDetail, TDSReturnResponse
        from datetime import datetime, date
        from decimal import Decimal
        
        try:
            # Validate business_id is provided
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for TDS Return report")
            
            financial_year = filters.financial_year
            
            # Get TDS return data from database
            tds_returns = self.repository.get_tds_return_data(financial_year, filters.dict())
            
            # Define all quarters
            all_quarters = ["Q1", "Q2", "Q3", "Q4"]
            
            # If specific quarter requested, filter to that quarter
            if filters.quarter:
                all_quarters = [filters.quarter]
            
            # Process quarters
            quarters_data = []
            
            for quarter in all_quarters:
                # Find existing return data for this quarter
                existing_return = None
                for return_record in tds_returns:
                    if return_record.quarter == quarter:
                        existing_return = return_record
                        break
                
                # Get challan data for this quarter
                challan_records = self.repository.get_tds_challan_data_for_period(financial_year, quarter, business_id)
                
                # Get payroll TDS data for comparison
                payroll_data = self.repository.get_payroll_tds_data_for_period(financial_year, quarter, business_id)
                
                # Create challan details for the 3 months in this quarter
                quarter_months = {
                    "Q1": ["April", "May", "June"],
                    "Q2": ["July", "August", "September"],
                    "Q3": ["October", "November", "December"],
                    "Q4": ["January", "February", "March"]
                }
                
                challans = []
                for idx, month in enumerate(quarter_months.get(quarter, [])):
                    # Find challan data for this month
                    month_challan = None
                    for challan in challan_records:
                        if challan.deposit_date and challan.deposit_date.strftime('%B') == month:
                            month_challan = challan
                            break
                    
                    # Get payroll data for this month
                    month_key = f"{idx + 1:02d}" if quarter != "Q4" else f"{idx + 10:02d}"
                    if quarter == "Q4" and idx >= 1:  # Jan, Feb, Mar
                        month_key = f"{idx - 2:02d}" if idx > 0 else "01"
                    
                    payroll_month_data = payroll_data.get("monthly_breakdown", {}).get(month_key, {})
                    
                    challan_detail = TDSReturnChallanDetail(
                        month=month,
                        period=month,
                        nil_return=False,
                        book_entry="No",
                        challan_serial_no=month_challan.challan_number if month_challan else None,
                        minor_head="200",  # TDS payable by taxpayer
                        branch_code=month_challan.branch_code if month_challan else None,
                        challan_date=month_challan.deposit_date if month_challan else None,
                        payment_date=month_challan.deposit_date if month_challan else None,
                        deposit_date=month_challan.deposit_date if month_challan else None,
                        
                        # Tax amounts from challan
                        income_tax=month_challan.tds_amount if month_challan else Decimal('0'),
                        surcharge=Decimal('0'),  # Not stored separately in model
                        cess=Decimal('0'),  # Not stored separately in model
                        interest=month_challan.interest if month_challan else Decimal('0'),
                        others=Decimal('0'),  # Not stored in model
                        fee=Decimal('0'),  # Not stored in model
                        
                        # Payroll amounts for comparison
                        payroll_income_tax=Decimal(str(payroll_month_data.get('total_tds', 0))),
                        payroll_surcharge=Decimal('0'),  # Usually calculated separately
                        payroll_cess=Decimal('0')  # Usually calculated separately
                    )
                    
                    challans.append(challan_detail)
                
                # Create quarter data
                quarter_data = TDSReturnQuarter(
                    quarter=quarter,
                    financial_year=financial_year,
                    return_type=filters.return_type or "24Q",
                    
                    # Return details
                    regular_24q="Y",
                    token_no=existing_return.acknowledgment_number if existing_return else None,
                    employer_address_change="N",
                    responsible_address_change="N",
                    
                    # Challan details
                    challans=challans,
                    
                    # Filing details
                    acknowledgment_number=existing_return.acknowledgment_number if existing_return else None,
                    filing_date=existing_return.filing_date if existing_return else None,
                    is_filed=existing_return.is_filed if existing_return else False,
                    
                    # Summary totals
                    total_deductees=existing_return.total_deductees if existing_return else payroll_data.get('total_employees', 0),
                    total_tds_amount=existing_return.total_tds_amount if existing_return else Decimal(str(payroll_data.get('total_tds', 0))),
                    total_deposited=existing_return.total_deposited if existing_return else Decimal('0')
                )
                
                quarters_data.append(quarter_data)
            
            # Create summary
            total_quarters = len(quarters_data)
            filed_quarters = sum(1 for q in quarters_data if q.is_filed)
            total_tds_amount = sum(q.total_tds_amount for q in quarters_data)
            total_deductees = sum(q.total_deductees for q in quarters_data)
            
            summary = {
                "financial_year": financial_year,
                "return_type": filters.return_type or "24Q",
                "total_quarters": total_quarters,
                "filed_quarters": filed_quarters,
                "pending_quarters": total_quarters - filed_quarters,
                "completion_percentage": round((filed_quarters / total_quarters) * 100, 2) if total_quarters > 0 else 0,
                "total_tds_amount": float(total_tds_amount),
                "total_deductees": total_deductees,
                "filters_summary": {
                    "financial_year": financial_year,
                    "quarter": filters.quarter or "All Quarters",
                    "return_type": filters.return_type or "24Q"
                }
            }
            
            return TDSReturnResponse(
                financial_year=financial_year,
                return_type=filters.return_type or "24Q",
                quarters=quarters_data,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating TDS Return report: {e}")
            
            return TDSReturnResponse(
                financial_year=filters.financial_year,
                return_type=filters.return_type or "24Q",
                quarters=[],
                filters_applied=filters,
                summary={"error": f"Error generating TDS Return report: {str(e)}"}
            )

    def get_income_tax_form16_report(self, filters: 'IncomeTaxForm16Filters') -> 'IncomeTaxForm16Response':
        """Get Income Tax Form 16 report data"""
        from app.schemas.reports import (
            IncomeTaxForm16Response, IncomeTaxForm16Certificate, IncomeTaxForm16Employee,
            IncomeTaxForm16Employer, IncomeTaxForm16PersonResponsible, IncomeTaxForm16Salary,
            IncomeTaxForm16TaxDetails, IncomeTaxForm16Quarter
        )
        from decimal import Decimal
        from datetime import date, datetime
        import calendar
        
        try:
            # Validate business_id is provided
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for Income Tax Form 16 report")
            
            # Get Form 16 data from repository
            form16_data = self.repository.get_income_tax_form16_data(
                financial_year=filters.financial_year,
                employee_id=filters.employee_id,
                employee_code=filters.employee_code,
                location=filters.location,
                department=filters.department,
                cost_center=filters.cost_center,
                business_id=business_id
            )
            
            certificates = []
            total_employees = 0
            total_tds_deducted = Decimal('0')
            total_gross_salary = Decimal('0')
            
            for emp_data in form16_data.get("employees", []):
                total_employees += 1
                
                # Employee details
                employee = IncomeTaxForm16Employee(
                    employee_id=emp_data["employee_id"],
                    employee_code=emp_data["employee_code"],
                    employee_name=emp_data["employee_name"],
                    designation=emp_data["designation"],
                    department=emp_data["department"],
                    location=emp_data["location"],
                    pan_number=emp_data.get("pan_number"),
                    aadhaar_number=emp_data.get("aadhaar_number"),
                    date_of_joining=emp_data.get("date_of_joining"),
                    address_line1=emp_data.get("address_line1"),
                    address_line2=emp_data.get("address_line2"),
                    city=emp_data.get("city"),
                    state=emp_data.get("state"),
                    pincode=emp_data.get("pincode")
                )
                
                # Salary details
                gross_salary = emp_data.get("gross_salary", 0)
                total_gross_salary += Decimal(str(gross_salary))
                
                salary_details = IncomeTaxForm16Salary(
                    gross_salary=Decimal(str(gross_salary)),
                    basic_salary=Decimal(str(gross_salary)) * Decimal('0.5'),  # Assume 50% basic
                    hra=Decimal(str(gross_salary)) * Decimal('0.2'),  # Assume 20% HRA
                    special_allowance=Decimal(str(gross_salary)) * Decimal('0.3'),  # Assume 30% special allowance
                    pf_employee=Decimal(str(gross_salary)) * Decimal('0.12'),  # 12% PF
                    net_salary=Decimal(str(gross_salary)) * Decimal('0.88')  # After PF deduction
                )
                
                # Tax details
                tds_deducted = emp_data.get("tds_deducted", 0)
                total_tds_deducted += Decimal(str(tds_deducted))
                
                section_80c = emp_data.get("section_80c", 0)
                section_80d = emp_data.get("section_80d", 0)
                total_deductions = Decimal(str(section_80c)) + Decimal(str(section_80d))
                
                taxable_income = emp_data.get("taxable_income", gross_salary)
                total_income = Decimal(str(taxable_income)) - total_deductions
                
                # Calculate tax (simplified calculation)
                tax_on_income = self._calculate_income_tax(total_income)
                education_cess = tax_on_income * Decimal('0.04')  # 4% education cess
                total_tax_payable = tax_on_income + education_cess
                
                tax_details = IncomeTaxForm16TaxDetails(
                    gross_total_income=Decimal(str(gross_salary)),
                    income_chargeable_under_head_salary=Decimal(str(taxable_income)),
                    section_80c=Decimal(str(section_80c)),
                    section_80d=Decimal(str(section_80d)),
                    total_deductions=total_deductions,
                    total_income=total_income,
                    tax_on_total_income=tax_on_income,
                    education_cess=education_cess,
                    total_tax_payable=total_tax_payable,
                    tds_deducted=Decimal(str(tds_deducted)),
                    balance_tax=total_tax_payable - Decimal(str(tds_deducted))
                )
                
                # Quarterly TDS details
                quarterly_tds = []
                tds_records = emp_data.get("tds_records", [])
                quarters = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
                
                for record in tds_records:
                    quarter = record.quarter
                    if quarter in quarters:
                        quarterly_tds.append(IncomeTaxForm16Quarter(
                            quarter=quarter,
                            period=f"{quarter} {filters.financial_year}",
                            tds_amount=record.tds_amount,
                            challan_number=record.challan_number,
                            deposit_date=record.deposit_date
                        ))
                
                # Employer details
                employer_info = form16_data.get("employer_info")
                business = form16_data.get("business")
                business_info = form16_data.get("business_info")
                
                employer = IncomeTaxForm16Employer(
                    name=employer_info.name if employer_info else (business.business_name if business else "Company Name"),
                    address_line1=employer_info.address1 if employer_info else (business.address if business else None),
                    address_line2=employer_info.address2 if employer_info else None,
                    address_line3=employer_info.address3 if employer_info else None,
                    place_of_issue=employer_info.place_of_issue if employer_info else (business.city if business else "Mumbai"),
                    tan_number=business_info.tan if business_info else None,
                    pan_number=business_info.pan if business_info else (business.pan if business else None)
                )
                
                # Person responsible details
                person_resp = form16_data.get("person_responsible")
                person_responsible = IncomeTaxForm16PersonResponsible(
                    full_name=person_resp.full_name if person_resp else "HR Manager",
                    designation=person_resp.designation if person_resp else "HR Manager",
                    father_name=person_resp.father_name if person_resp else "Father Name",
                    signature_path=person_resp.signature_path if person_resp else None
                )
                
                # Create certificate
                certificate = IncomeTaxForm16Certificate(
                    financial_year=filters.financial_year,
                    employee=employee,
                    employer=employer,
                    person_responsible=person_responsible,
                    salary_details=salary_details,
                    tax_details=tax_details,
                    quarterly_tds=quarterly_tds,
                    certificate_number=f"FORM16/{filters.financial_year}/{emp_data['employee_code']}",
                    issue_date=date.today(),
                    place_of_issue=employer.place_of_issue
                )
                
                certificates.append(certificate)
            
            # Summary
            summary = {
                "financial_year": filters.financial_year,
                "total_employees": total_employees,
                "total_certificates": len(certificates),
                "total_gross_salary": float(total_gross_salary),
                "total_tds_deducted": float(total_tds_deducted),
                "filters_summary": {
                    "financial_year": filters.financial_year,
                    "employee_filter": filters.employee_code or "All Employees",
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers"
                }
            }
            
            return IncomeTaxForm16Response(
                financial_year=filters.financial_year,
                certificates=certificates,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Income Tax Form 16 report: {e}")
            
            return IncomeTaxForm16Response(
                financial_year=filters.financial_year,
                certificates=[],
                filters_applied=filters,
                summary={"error": f"Error generating Income Tax Form 16 report: {str(e)}"}
            )
    
    def _calculate_income_tax(self, total_income: Decimal) -> Decimal:
        """Calculate income tax based on Indian tax slabs (simplified)"""
        try:
            # Indian tax slabs for FY 2024-25 (old regime)
            if total_income <= Decimal('250000'):
                return Decimal('0')
            elif total_income <= Decimal('500000'):
                return (total_income - Decimal('250000')) * Decimal('0.05')
            elif total_income <= Decimal('1000000'):
                return Decimal('12500') + (total_income - Decimal('500000')) * Decimal('0.20')
            else:
                return Decimal('112500') + (total_income - Decimal('1000000')) * Decimal('0.30')
        except:
            return Decimal('0')

    def get_annual_salary_summary_report(self, filters: 'AnnualSalarySummaryFilters') -> 'AnnualSalarySummaryResponse':
        """Get Annual Salary Summary report data"""
        from app.schemas.reports import (
            AnnualSalarySummaryResponse, AnnualSalarySummaryEmployee, AnnualSalarySummaryDepartment,
            AnnualSalarySummaryLocation, AnnualSalarySummaryGrade, AnnualSalarySummaryOverall
        )
        from decimal import Decimal
        from collections import defaultdict
        
        try:
            # Validate business_id is provided
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for Annual Salary Summary report")
            
            # Get Annual Salary Summary data from repository
            annual_data = self.repository.get_annual_salary_summary_data(
                financial_year=filters.financial_year,
                location=filters.location,
                department=filters.department,
                cost_center=filters.cost_center,
                employee_grade=filters.employee_grade,
                business_id=business_id
            )
            
            employees = []
            department_totals = defaultdict(lambda: {
                'count': 0, 'gross': Decimal('0'), 'net': Decimal('0'), 'deductions': Decimal('0')
            })
            location_totals = defaultdict(lambda: {
                'count': 0, 'gross': Decimal('0'), 'net': Decimal('0'), 'deductions': Decimal('0')
            })
            grade_totals = defaultdict(lambda: {
                'count': 0, 'gross': Decimal('0'), 'net': Decimal('0'), 'deductions': Decimal('0')
            })
            
            # Overall totals
            total_employees = 0
            total_annual_gross = Decimal('0')
            total_annual_net = Decimal('0')
            total_annual_deductions = Decimal('0')
            total_annual_basic = Decimal('0')
            total_annual_hra = Decimal('0')
            total_annual_pf = Decimal('0')
            total_annual_esi = Decimal('0')
            total_annual_tds = Decimal('0')
            
            for emp_data in annual_data.get("employees", []):
                total_employees += 1
                
                # Calculate totals
                annual_gross = Decimal(str(emp_data.get("annual_gross_salary", 0)))
                annual_net = Decimal(str(emp_data.get("annual_net_salary", 0)))
                annual_basic = Decimal(str(emp_data.get("annual_basic", 0)))
                annual_hra = Decimal(str(emp_data.get("annual_hra", 0)))
                annual_pf = Decimal(str(emp_data.get("annual_pf", 0)))
                annual_esi = Decimal(str(emp_data.get("annual_esi", 0)))
                annual_tds = Decimal(str(emp_data.get("annual_tds", 0)))
                
                # Calculate other allowances and deductions
                annual_special_allowance = annual_gross - annual_basic - annual_hra
                annual_other_allowances = Decimal('0')  # Can be calculated from detailed records
                annual_professional_tax = Decimal(str(annual_gross * Decimal('0.002')))  # Estimate 0.2%
                annual_other_deductions = Decimal('0')
                annual_total_deductions = annual_pf + annual_esi + annual_professional_tax + annual_tds + annual_other_deductions
                
                # Recalculate net if needed
                if annual_net == 0:
                    annual_net = annual_gross - annual_total_deductions
                
                months_worked = emp_data.get("months_worked", 12)
                avg_monthly_gross = annual_gross / 12 if annual_gross > 0 else Decimal('0')
                avg_monthly_net = annual_net / 12 if annual_net > 0 else Decimal('0')
                
                # Employee details
                employee = AnnualSalarySummaryEmployee(
                    employee_id=emp_data["employee_id"],
                    employee_code=emp_data["employee_code"],
                    employee_name=emp_data["employee_name"],
                    designation=emp_data["designation"],
                    department=emp_data["department"],
                    location=emp_data["location"],
                    cost_center=emp_data.get("cost_center"),
                    grade=emp_data.get("grade"),
                    date_of_joining=emp_data.get("date_of_joining"),
                    annual_basic=annual_basic,
                    annual_hra=annual_hra,
                    annual_special_allowance=annual_special_allowance,
                    annual_other_allowances=annual_other_allowances,
                    annual_gross_salary=annual_gross,
                    annual_pf=annual_pf,
                    annual_esi=annual_esi,
                    annual_professional_tax=annual_professional_tax,
                    annual_tds=annual_tds,
                    annual_other_deductions=annual_other_deductions,
                    annual_total_deductions=annual_total_deductions,
                    annual_net_salary=annual_net,
                    months_worked=months_worked,
                    average_monthly_gross=avg_monthly_gross,
                    average_monthly_net=avg_monthly_net
                )
                
                employees.append(employee)
                
                # Update totals
                total_annual_gross += annual_gross
                total_annual_net += annual_net
                total_annual_deductions += annual_total_deductions
                total_annual_basic += annual_basic
                total_annual_hra += annual_hra
                total_annual_pf += annual_pf
                total_annual_esi += annual_esi
                total_annual_tds += annual_tds
                
                # Department totals
                dept = emp_data["department"]
                department_totals[dept]['count'] += 1
                department_totals[dept]['gross'] += annual_gross
                department_totals[dept]['net'] += annual_net
                department_totals[dept]['deductions'] += annual_total_deductions
                
                # Location totals
                loc = emp_data["location"]
                location_totals[loc]['count'] += 1
                location_totals[loc]['gross'] += annual_gross
                location_totals[loc]['net'] += annual_net
                location_totals[loc]['deductions'] += annual_total_deductions
                
                # Grade totals
                grade = emp_data.get("grade", "Unspecified")
                grade_totals[grade]['count'] += 1
                grade_totals[grade]['gross'] += annual_gross
                grade_totals[grade]['net'] += annual_net
                grade_totals[grade]['deductions'] += annual_total_deductions
            
            # Create department summaries
            department_summary = []
            for dept_name, totals in department_totals.items():
                count = totals['count']
                dept_summary = AnnualSalarySummaryDepartment(
                    department_name=dept_name,
                    employee_count=count,
                    total_annual_gross=totals['gross'],
                    total_annual_net=totals['net'],
                    total_annual_deductions=totals['deductions'],
                    average_annual_gross=totals['gross'] / count if count > 0 else Decimal('0'),
                    average_annual_net=totals['net'] / count if count > 0 else Decimal('0')
                )
                department_summary.append(dept_summary)
            
            # Create location summaries
            location_summary = []
            for loc_name, totals in location_totals.items():
                count = totals['count']
                loc_summary = AnnualSalarySummaryLocation(
                    location_name=loc_name,
                    employee_count=count,
                    total_annual_gross=totals['gross'],
                    total_annual_net=totals['net'],
                    total_annual_deductions=totals['deductions'],
                    average_annual_gross=totals['gross'] / count if count > 0 else Decimal('0'),
                    average_annual_net=totals['net'] / count if count > 0 else Decimal('0')
                )
                location_summary.append(loc_summary)
            
            # Create grade summaries
            grade_summary = []
            for grade_name, totals in grade_totals.items():
                count = totals['count']
                grade_sum = AnnualSalarySummaryGrade(
                    grade_name=grade_name,
                    employee_count=count,
                    total_annual_gross=totals['gross'],
                    total_annual_net=totals['net'],
                    total_annual_deductions=totals['deductions'],
                    average_annual_gross=totals['gross'] / count if count > 0 else Decimal('0'),
                    average_annual_net=totals['net'] / count if count > 0 else Decimal('0')
                )
                grade_summary.append(grade_sum)
            
            # Overall summary
            overall_summary = AnnualSalarySummaryOverall(
                total_employees=total_employees,
                total_annual_gross=total_annual_gross,
                total_annual_net=total_annual_net,
                total_annual_deductions=total_annual_deductions,
                average_annual_gross=total_annual_gross / total_employees if total_employees > 0 else Decimal('0'),
                average_annual_net=total_annual_net / total_employees if total_employees > 0 else Decimal('0'),
                total_annual_basic=total_annual_basic,
                total_annual_hra=total_annual_hra,
                total_annual_allowances=total_annual_gross - total_annual_basic - total_annual_hra,
                total_annual_pf=total_annual_pf,
                total_annual_esi=total_annual_esi,
                total_annual_tds=total_annual_tds
            )
            
            # Summary
            summary = {
                "financial_year": filters.financial_year,
                "total_employees": total_employees,
                "total_departments": len(department_summary),
                "total_locations": len(location_summary),
                "total_grades": len(grade_summary),
                "total_annual_cost": float(total_annual_gross),
                "average_annual_salary": float(total_annual_gross / total_employees) if total_employees > 0 else 0,
                "filters_summary": {
                    "financial_year": filters.financial_year,
                    "location": filters.location or "All Locations",
                    "department": filters.department or "All Departments",
                    "cost_center": filters.cost_center or "All Cost Centers",
                    "employee_grade": filters.employee_grade or "All Grades"
                }
            }
            
            return AnnualSalarySummaryResponse(
                financial_year=filters.financial_year,
                employees=employees,
                department_summary=department_summary,
                location_summary=location_summary,
                grade_summary=grade_summary,
                overall_summary=overall_summary,
                filters_applied=filters,
                summary=summary
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Annual Salary Summary report: {e}")
            
            return AnnualSalarySummaryResponse(
                financial_year=filters.financial_year,
                employees=[],
                department_summary=[],
                location_summary=[],
                grade_summary=[],
                overall_summary=AnnualSalarySummaryOverall(
                    total_employees=0,
                    total_annual_gross=Decimal('0'),
                    total_annual_net=Decimal('0'),
                    total_annual_deductions=Decimal('0'),
                    average_annual_gross=Decimal('0'),
                    average_annual_net=Decimal('0'),
                    total_annual_basic=Decimal('0'),
                    total_annual_hra=Decimal('0'),
                    total_annual_allowances=Decimal('0'),
                    total_annual_pf=Decimal('0'),
                    total_annual_esi=Decimal('0'),
                    total_annual_tds=Decimal('0')
                ),
                filters_applied=filters,
                summary={"error": f"Error generating Annual Salary Summary report: {str(e)}"}
            )

    def get_annual_salary_statement_report(self, filters: 'AnnualSalaryStatementFilters') -> 'AnnualSalaryStatementResponse':
        """Get Annual Salary Statement report data for a specific employee"""
        from app.schemas.reports import (
            AnnualSalaryStatementResponse, AnnualSalaryStatementEmployee, 
            AnnualSalaryStatementSalaryDetail
        )
        from decimal import Decimal
        
        try:
            # Validate business_id is provided
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for Annual Salary Statement report")
            
            # Get Annual Salary Statement data from repository
            statement_data = self.repository.get_annual_salary_statement_data(
                periods=filters.periods,
                filters=filters.dict()
            )
            
            if not statement_data.get("employee"):
                return AnnualSalaryStatementResponse(
                    periods=filters.periods,
                    employee=None,
                    filters_applied=filters,
                    summary={"message": statement_data.get("message", "No employee found")},
                    message=statement_data.get("message", "No employee found")
                )
            
            employee_info = statement_data["employee"]
            salary_by_period = statement_data.get("salary_by_period", {})
            
            # Build salary details structure
            salary_details = []
            
            # Track totals across all periods
            total_earnings_all_periods = Decimal('0')
            total_deductions_all_periods = Decimal('0')
            total_net_all_periods = Decimal('0')
            
            # Earnings components
            earnings_components = [
                "Basic Salary",
                "HRA", 
                "Special Allowance",
                "Transport Allowance",
                "Medical Allowance",
                "Other Allowances"
            ]
            
            # Deductions components
            deductions_components = [
                "PF",
                "ESI", 
                "Professional Tax",
                "TDS",
                "Other Deductions"
            ]
            
            # Process earnings
            for component in earnings_components:
                period_values = {}
                component_total = Decimal('0')
                
                for period in filters.periods:
                    period_data = salary_by_period.get(period, {})
                    
                    if component == "Basic Salary":
                        amount = period_data.get('basic_salary', Decimal('0'))
                    else:
                        allowances = period_data.get('allowances', {})
                        amount = Decimal(str(allowances.get(component, 0)))
                    
                    period_values[period.lower()] = f"{amount:,.2f}"
                    component_total += amount
                
                salary_details.append(AnnualSalaryStatementSalaryDetail(
                    type="normal",
                    label=component,
                    period_values=period_values,
                    total=f"{component_total:,.2f}"
                ))
            
            # Total Earnings row
            total_earnings_by_period = {}
            for period in filters.periods:
                period_data = salary_by_period.get(period, {})
                gross = period_data.get('gross_salary', Decimal('0'))
                total_earnings_by_period[period.lower()] = f"{gross:,.2f}"
                total_earnings_all_periods += gross
            
            salary_details.append(AnnualSalaryStatementSalaryDetail(
                type="highlight",
                label="Total Earnings",
                period_values=total_earnings_by_period,
                total=f"{total_earnings_all_periods:,.2f}"
            ))
            
            # Process deductions
            for component in deductions_components:
                period_values = {}
                component_total = Decimal('0')
                
                for period in filters.periods:
                    period_data = salary_by_period.get(period, {})
                    deductions = period_data.get('deductions', {})
                    amount = Decimal(str(deductions.get(component, 0)))
                    
                    period_values[period.lower()] = f"{amount:,.2f}"
                    component_total += amount
                
                salary_details.append(AnnualSalaryStatementSalaryDetail(
                    type="normal",
                    label=component,
                    period_values=period_values,
                    total=f"{component_total:,.2f}"
                ))
            
            # Total Deductions row
            total_deductions_by_period = {}
            for period in filters.periods:
                period_data = salary_by_period.get(period, {})
                deductions = period_data.get('total_deductions', Decimal('0'))
                total_deductions_by_period[period.lower()] = f"{deductions:,.2f}"
                total_deductions_all_periods += deductions
            
            salary_details.append(AnnualSalaryStatementSalaryDetail(
                type="highlight",
                label="Total Deductions",
                period_values=total_deductions_by_period,
                total=f"{total_deductions_all_periods:,.2f}"
            ))
            
            # Net Earnings row
            net_earnings_by_period = {}
            for period in filters.periods:
                period_data = salary_by_period.get(period, {})
                net = period_data.get('net_salary', Decimal('0'))
                net_earnings_by_period[period.lower()] = f"{net:,.2f}"
                total_net_all_periods += net
            
            salary_details.append(AnnualSalaryStatementSalaryDetail(
                type="highlight",
                label="Net Earnings",
                period_values=net_earnings_by_period,
                total=f"{total_net_all_periods:,.2f}"
            ))
            
            # Create employee object
            employee = AnnualSalaryStatementEmployee(
                employee_id=employee_info["id"],
                employee_name=employee_info["name"],
                employee_code=employee_info["code"],
                date_of_joining=employee_info["date_of_joining"],
                designation=employee_info["designation"],
                department=employee_info["department"],
                location=employee_info["location"],
                cost_center=employee_info["cost_center"],
                salary_details=salary_details,
                total_earnings_across_periods=total_earnings_all_periods,
                total_deductions_across_periods=total_deductions_all_periods,
                net_earnings_across_periods=total_net_all_periods
            )
            
            # Create summary
            summary = {
                "employee_name": employee_info["name"],
                "employee_code": employee_info["code"],
                "periods_count": len(filters.periods),
                "total_earnings": float(total_earnings_all_periods),
                "total_deductions": float(total_deductions_all_periods),
                "net_earnings": float(total_net_all_periods),
                "average_monthly_earnings": float(total_earnings_all_periods / len(filters.periods)) if filters.periods else 0,
                "average_monthly_net": float(total_net_all_periods / len(filters.periods)) if filters.periods else 0
            }
            
            return AnnualSalaryStatementResponse(
                periods=filters.periods,
                employee=employee,
                filters_applied=filters,
                summary=summary,
                message="Annual salary statement generated successfully"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Annual Salary Statement report: {e}")
            
            return AnnualSalaryStatementResponse(
                periods=filters.periods,
                employee=None,
                filters_applied=filters,
                summary={"error": f"Error generating Annual Salary Statement report: {str(e)}"},
                message=f"Error: {str(e)}"
            )

    def get_annual_attendance_report(self, filters: 'AnnualAttendanceFilters') -> 'AnnualAttendanceResponse':
        """Get Annual Attendance report data for employees across multiple periods"""
        from app.schemas.reports import (
            AnnualAttendanceResponse, AnnualAttendanceEmployeeData
        )
        
        try:
            # Validate business_id is provided
            business_id = filters.business_id
            if not business_id:
                raise ValueError("business_id is required for Annual Attendance report")
            
            # Get Annual Attendance data from repository
            attendance_data = self.repository.get_annual_attendance_data(
                periods=filters.periods,
                filters=filters.dict()
            )
            
            if not attendance_data.get("employees"):
                return AnnualAttendanceResponse(
                    employees=[],
                    periods=filters.periods,
                    total_employees=0,
                    filters_applied=filters,
                    summary={"message": attendance_data.get("message", "No employees found")},
                    date_range=attendance_data.get("date_range", {"from_date": "", "to_date": ""}),
                    message=attendance_data.get("message", "No employees found")
                )
            
            employees_data = attendance_data["employees"]
            
            # Process employees data
            employees_list = []
            total_presents = 0
            total_absents = 0
            total_paid_days = 0
            total_ot_days = 0
            
            for employee_id, emp_data in employees_data.items():
                employee = emp_data['employee']
                metrics = emp_data['metrics']
                
                # Create employee attendance data
                employee_attendance = AnnualAttendanceEmployeeData(
                    employee_id=employee.id,
                    employee_name=f"{employee.first_name} {employee.last_name}".strip(),
                    employee_code=employee.employee_code or f"EMP{employee.id:03d}",
                    location=emp_data['location'],
                    department=emp_data['department'],
                    cost_center=emp_data['cost_center'],
                    designation=emp_data['designation'],
                    presents=metrics['presents'],
                    absents=metrics['absents'],
                    week_offs=metrics['week_offs'],
                    holidays=metrics['holidays'],
                    paid_leaves=metrics['paid_leaves'],
                    unpaid_leaves=metrics['unpaid_leaves'],
                    paid_days=metrics['paid_days'],
                    total_days=metrics['total_days'],
                    extra_days=metrics['extra_days'],
                    ot_days=metrics['ot_days'],
                    total_hours=metrics['total_hours'],
                    overtime_hours=metrics['overtime_hours']
                )
                
                employees_list.append(employee_attendance)
                
                # Accumulate totals for summary
                total_presents += metrics['presents']
                total_absents += metrics['absents']
                total_paid_days += metrics['paid_days']
                total_ot_days += metrics['ot_days']
            
            # Sort employees by name
            employees_list.sort(key=lambda x: x.employee_name)
            
            # Create summary
            total_employees = len(employees_list)
            summary = {
                "total_employees": total_employees,
                "periods_count": len(filters.periods),
                "date_range": attendance_data.get("date_range", {}),
                "totals": {
                    "total_presents": total_presents,
                    "total_absents": total_absents,
                    "total_paid_days": total_paid_days,
                    "total_ot_days": total_ot_days,
                    "average_presents_per_employee": round(total_presents / total_employees, 2) if total_employees > 0 else 0,
                    "average_paid_days_per_employee": round(total_paid_days / total_employees, 2) if total_employees > 0 else 0
                }
            }
            
            return AnnualAttendanceResponse(
                employees=employees_list,
                periods=filters.periods,
                total_employees=total_employees,
                filters_applied=filters,
                summary=summary,
                date_range=attendance_data.get("date_range", {"from_date": "", "to_date": ""}),
                message="Annual attendance report generated successfully"
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Annual Attendance report: {e}")
            
            return AnnualAttendanceResponse(
                employees=[],
                periods=filters.periods,
                total_employees=0,
                filters_applied=filters,
                summary={"error": f"Error generating Annual Attendance report: {str(e)}"},
                date_range={"from_date": "", "to_date": ""},
                message=f"Error: {str(e)}"
            )