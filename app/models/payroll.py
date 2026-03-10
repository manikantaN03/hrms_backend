"""
Payroll Management Models
Models for handling payroll processing, periods, and calculations
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Date, DECIMAL, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum as PyEnum
from .base import BaseModel


class PayrollPeriodStatus(PyEnum):
    """Payroll period status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PROCESSING = "processing"


class PayrollRunStatus(PyEnum):
    """Payroll run status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PayrollPeriod(BaseModel):
    """Payroll period model"""
    __tablename__ = "payroll_periods"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Period Details
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default=PayrollPeriodStatus.OPEN.value, nullable=False)
    
    # Configuration
    custom_days_enabled = Column(Boolean, default=False)
    custom_days = Column(Integer, nullable=True)
    different_month = Column(Boolean, default=False)
    calendar_month = Column(String(20), nullable=True)
    calendar_year = Column(Integer, nullable=True)
    
    # Reporting
    reporting_enabled = Column(Boolean, default=False)
    
    # Relationships
    business = relationship("Business")
    payroll_runs = relationship("PayrollRun", back_populates="period")


class PayrollRun(BaseModel):
    """Payroll run model"""
    __tablename__ = "payroll_runs"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Run Details
    run_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(20), default=PayrollRunStatus.PENDING.value, nullable=False)
    runtime_seconds = Column(Integer, nullable=True)
    
    # Processing Details
    total_employees = Column(Integer, default=0)
    processed_employees = Column(Integer, default=0)
    failed_employees = Column(Integer, default=0)
    
    # Results
    total_gross_salary = Column(DECIMAL(15, 2), default=0)
    total_deductions = Column(DECIMAL(15, 2), default=0)
    total_net_salary = Column(DECIMAL(15, 2), default=0)
    
    # Logs and Notes
    log_file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    business = relationship("Business")
    period = relationship("PayrollPeriod", back_populates="payroll_runs")
    creator = relationship("Employee", foreign_keys=[created_by])


class LeaveEncashment(BaseModel):
    """Leave encashment model"""
    __tablename__ = "leave_encashments"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Encashment Details
    leave_type = Column(String(100), nullable=False)
    leave_balance = Column(DECIMAL(5, 2), nullable=False)
    encashment_days = Column(DECIMAL(5, 2), nullable=False)
    daily_salary = Column(DECIMAL(10, 2), nullable=False)
    encashment_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Configuration
    payment_period = Column(Date, nullable=False)
    balance_as_on = Column(Date, nullable=False)
    balance_above = Column(DECIMAL(5, 2), default=0)
    
    # Components
    salary_components = Column(JSON, nullable=True)  # List of component IDs
    
    # Status
    is_processed = Column(Boolean, default=False)
    processed_date = Column(DateTime, nullable=True)
    
    # Relationships
    business = relationship("Business")
    period = relationship("PayrollPeriod")
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("User", foreign_keys=[created_by])


class PayrollRecalculation(BaseModel):
    """Payroll recalculation model"""
    __tablename__ = "payroll_recalculations"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Recalculation Details
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    all_employees = Column(Boolean, default=True)
    selected_employees = Column(JSON, nullable=True)  # List of employee IDs
    
    # Status
    status = Column(String(20), default="pending", nullable=False)
    progress_percentage = Column(Integer, default=0)
    
    # Results
    total_employees = Column(Integer, default=0)
    processed_employees = Column(Integer, default=0)
    failed_employees = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Messages
    success_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    business = relationship("Business")
    period = relationship("PayrollPeriod")
    creator = relationship("Employee", foreign_keys=[created_by])


class StatutoryBonus(BaseModel):
    """Statutory bonus model"""
    __tablename__ = "statutory_bonuses"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Bonus Configuration
    bonus_rate = Column(DECIMAL(5, 2), default=8.33)
    eligibility_cutoff = Column(DECIMAL(10, 2), default=21000)
    min_wages = Column(DECIMAL(10, 2), default=7000)
    min_bonus = Column(DECIMAL(10, 2), default=100)
    max_bonus = Column(DECIMAL(10, 2), default=0)
    
    # Employee Details
    base_salary = Column(DECIMAL(10, 2), nullable=False)
    bonus_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Components
    salary_components = Column(JSON, nullable=True)  # List of component IDs
    
    # Status
    is_processed = Column(Boolean, default=False)
    processed_date = Column(DateTime, nullable=True)
    
    # Relationships
    business = relationship("Business")
    period = relationship("PayrollPeriod")
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("Employee", foreign_keys=[created_by])


class Gratuity(BaseModel):
    """Gratuity model"""
    __tablename__ = "gratuities"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Gratuity Configuration
    min_years = Column(Integer, default=5)
    payable_days = Column(Integer, default=15)
    month_days = Column(Integer, default=26)
    exit_only = Column(Boolean, default=False)
    year_rounding = Column(String(20), default="round_down")  # round_up, round_down
    
    # Employee Details
    years_of_service = Column(DECIMAL(5, 2), nullable=False)
    base_salary = Column(DECIMAL(10, 2), nullable=False)
    gratuity_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Components
    salary_components = Column(JSON, nullable=True)  # List of component IDs
    
    # Status
    is_processed = Column(Boolean, default=False)
    processed_date = Column(DateTime, nullable=True)
    
    # Relationships
    business = relationship("Business")
    period = relationship("PayrollPeriod")
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("Employee", foreign_keys=[created_by])


class HoldSalary(BaseModel):
    """Hold salary model"""
    __tablename__ = "hold_salaries"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Hold Details
    hold_start_date = Column(Date, nullable=False)
    hold_end_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("Employee", foreign_keys=[created_by])


class PayrollRecord(BaseModel):
    """Individual employee payroll record"""
    __tablename__ = "payroll_records"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    
    # Salary Details
    gross_salary = Column(DECIMAL(15, 2), default=0)
    total_deductions = Column(DECIMAL(15, 2), default=0)
    net_salary = Column(DECIMAL(15, 2), default=0)
    
    # Status
    is_processed = Column(Boolean, default=False)
    processed_date = Column(DateTime, nullable=True)
    
    # Relationships
    business = relationship("Business")
    employee = relationship("Employee", back_populates="payroll_records")
    period = relationship("PayrollPeriod")


class PayrollStatistics(BaseModel):
    """Payroll statistics model"""
    __tablename__ = "payroll_statistics"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    
    # Statistics
    total_employees = Column(Integer, default=0)
    active_employees = Column(Integer, default=0)
    on_hold_employees = Column(Integer, default=0)
    
    # Salary Statistics
    total_gross_salary = Column(DECIMAL(15, 2), default=0)
    total_deductions = Column(DECIMAL(15, 2), default=0)
    total_net_salary = Column(DECIMAL(15, 2), default=0)
    average_salary = Column(DECIMAL(10, 2), default=0)
    
    # Processing Statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # Last Updated
    last_calculated = Column(DateTime, default=datetime.now)
    
    # Relationships
    business = relationship("Business")
    period = relationship("PayrollPeriod")