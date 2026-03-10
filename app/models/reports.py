"""
Reports Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Numeric, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class AIReportQuery(Base):
    """AI Report Query Model"""
    __tablename__ = "ai_report_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_data = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="ai_queries")


class ReportTemplate(Base):
    """Report Template Model"""
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # salary, attendance, employee, statutory, annual, other
    description = Column(Text, nullable=True)
    template_config = Column(JSON, nullable=False)  # Report configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedReport(Base):
    """Generated Report Model"""
    __tablename__ = "generated_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=True)  # Report parameters used
    file_path = Column(String(500), nullable=True)  # Path to generated file
    status = Column(String(50), default="generating")  # generating, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="generated_reports")
    template = relationship("ReportTemplate")


class SalaryReport(Base):
    """Salary Report Data Model"""
    __tablename__ = "salary_reports"
    __table_args__ = (
        # Unique constraint to prevent duplicate salary reports for same employee and period
        UniqueConstraint('employee_id', 'report_period', name='uq_salary_report_employee_period'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    report_period = Column(String(20), nullable=False)  # YYYY-MM format
    basic_salary = Column(Numeric(15, 2), default=0)
    gross_salary = Column(Numeric(15, 2), default=0)
    net_salary = Column(Numeric(15, 2), default=0)
    total_deductions = Column(Numeric(15, 2), default=0)
    overtime_amount = Column(Numeric(15, 2), default=0)
    bonus_amount = Column(Numeric(15, 2), default=0)
    allowances = Column(JSON, nullable=True)  # Various allowances
    deductions = Column(JSON, nullable=True)  # Various deductions
    
    # NCP (Non-Contributing Period) Days - for PF calculation
    ncp_days = Column(Integer, default=0, nullable=False)  # Days absent/LOP
    working_days = Column(Integer, default=30, nullable=False)  # Total working days in month
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee")


class AttendanceReport(Base):
    """Attendance Report Data Model"""
    __tablename__ = "attendance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    report_date = Column(Date, nullable=False)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    total_hours = Column(Numeric(5, 2), default=0)
    overtime_hours = Column(Numeric(5, 2), default=0)
    status = Column(String(50), default="present")  # present, absent, half_day, leave
    location = Column(String(200), nullable=True)
    is_remote = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee")


class EmployeeReport(Base):
    """Employee Report Data Model"""
    __tablename__ = "employee_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    report_type = Column(String(100), nullable=False)  # joining, exit, promotion, increment, etc.
    report_data = Column(JSON, nullable=False)  # Flexible data storage
    effective_date = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee")


class StatutoryReport(Base):
    """Statutory Report Data Model"""
    __tablename__ = "statutory_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    report_period = Column(String(20), nullable=False)  # YYYY-MM format
    report_type = Column(String(100), nullable=False)  # esi, pf, tds, lwf, etc.
    employee_contribution = Column(Numeric(15, 2), default=0)
    employer_contribution = Column(Numeric(15, 2), default=0)
    total_contribution = Column(Numeric(15, 2), default=0)
    statutory_data = Column(JSON, nullable=True)  # Additional statutory data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee")


class AnnualReport(Base):
    """Annual Report Data Model"""
    __tablename__ = "annual_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    report_year = Column(Integer, nullable=False)
    report_type = Column(String(100), nullable=False)  # salary, attendance, leaves
    annual_data = Column(JSON, nullable=False)  # Annual summary data
    total_amount = Column(Numeric(15, 2), default=0)  # For salary reports
    total_days = Column(Integer, default=0)  # For attendance/leave reports
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee")


class ActivityLog(Base):
    """Activity Log Model for Other Reports"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(200), nullable=False)
    module = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="activity_logs")


class UserFeedback(Base):
    """User Feedback Model"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(100), nullable=False)  # suggestion, bug, feature_request
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="feedback")


class SystemAlert(Base):
    """System Alert Model"""
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False)  # info, warning, error, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship
    resolver = relationship("User")