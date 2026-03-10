"""
Attendance Models
Attendance and time tracking data models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, ForeignKey, Time, Text, Enum
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum
from datetime import datetime, time


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    LATE = "LATE"
    ON_LEAVE = "ON_LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"
    COMP_OFF = "COMP_OFF"
    LEAVE_WITHOUT_PAY = "LEAVE_WITHOUT_PAY"


class PunchType(str, enum.Enum):
    IN = "in"
    OUT = "out"
    BREAK_OUT = "break_out"
    BREAK_IN = "break_in"


class AttendanceRecord(Base):
    """Daily attendance records"""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Date and timing
    attendance_date = Column(Date, nullable=False, index=True)
    punch_in_time = Column(DateTime)
    punch_out_time = Column(DateTime)
    
    # Calculated fields
    total_hours = Column(Numeric(5, 2))  # Total working hours
    break_hours = Column(Numeric(5, 2))  # Total break hours
    overtime_hours = Column(Numeric(5, 2))  # Overtime hours
    
    # Status and flags
    attendance_status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    is_late = Column(Boolean, default=False)
    is_early_out = Column(Boolean, default=False)
    is_overtime = Column(Boolean, default=False)
    
    # Shift information
    shift_id = Column(Integer, ForeignKey("work_shifts.id"))
    expected_in_time = Column(Time)
    expected_out_time = Column(Time)
    
    # Location tracking
    punch_in_location = Column(String(255))
    punch_out_location = Column(String(255))
    punch_in_ip = Column(String(45))
    punch_out_ip = Column(String(45))
    
    # Manual entry fields
    is_manual_entry = Column(Boolean, default=False)
    manual_entry_reason = Column(Text)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")
    business = relationship("Business")
    shift = relationship("WorkShift")
    punches = relationship("AttendancePunch", back_populates="attendance_record")
    corrections = relationship("AttendanceCorrection", back_populates="attendance_record")


class AttendancePunch(Base):
    """Individual punch records (in/out/break)"""
    __tablename__ = "attendance_punches"

    id = Column(Integer, primary_key=True, index=True)
    attendance_record_id = Column(Integer, ForeignKey("attendance_records.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Punch details
    punch_time = Column(DateTime, nullable=False)
    punch_type = Column(Enum(PunchType), nullable=False)
    
    # Location and device info
    location = Column(String(255))
    ip_address = Column(String(45))
    device_info = Column(Text)
    
    # Remote punch fields
    is_remote = Column(Boolean, default=False)
    latitude = Column(Numeric(10, 8))  # GPS latitude
    longitude = Column(Numeric(11, 8))  # GPS longitude
    location_accuracy = Column(Numeric(8, 2))  # GPS accuracy in meters
    
    # Biometric/manual flags
    is_biometric = Column(Boolean, default=False)
    is_manual = Column(Boolean, default=False)
    manual_reason = Column(Text)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    attendance_record = relationship("AttendanceRecord", back_populates="punches")
    employee = relationship("Employee")


class AttendanceCorrection(Base):
    """Attendance corrections and leave applications"""
    __tablename__ = "attendance_corrections"

    id = Column(Integer, primary_key=True, index=True)
    attendance_record_id = Column(Integer, ForeignKey("attendance_records.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Correction details
    correction_type = Column(String(50), nullable=False)  # late_entry, early_exit, leave, etc.
    original_punch_in = Column(DateTime)
    original_punch_out = Column(DateTime)
    corrected_punch_in = Column(DateTime)
    corrected_punch_out = Column(DateTime)
    
    # Leave details
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"))
    is_half_day = Column(Boolean, default=False)
    
    # Request details
    reason = Column(Text, nullable=False)
    supporting_documents = Column(Text)  # JSON array of file paths
    
    # Approval workflow
    status = Column(String(20), default="pending")  # pending, approved, rejected
    requested_at = Column(DateTime, server_default=func.now())
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attendance_record = relationship("AttendanceRecord", back_populates="corrections")
    employee = relationship("Employee")
    leave_type = relationship("LeaveType")
    approver = relationship("User", foreign_keys=[approved_by])


class ShiftRoster(Base):
    """Employee shift assignments"""
    __tablename__ = "shift_rosters"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Roster details
    roster_date = Column(Date, nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey("work_shifts.id"), nullable=False)
    
    # Override timings (if different from shift default)
    custom_start_time = Column(Time)
    custom_end_time = Column(Time)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_holiday = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    employee = relationship("Employee")
    business = relationship("Business")
    shift = relationship("WorkShift")


class AttendancePolicy(Base):
    """Attendance policies and rules"""
    __tablename__ = "attendance_policies"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Policy details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Timing rules
    grace_period_minutes = Column(Integer, default=0)  # Grace period for late arrival
    half_day_hours = Column(Numeric(4, 2), default=4.0)  # Minimum hours for half day
    full_day_hours = Column(Numeric(4, 2), default=8.0)  # Minimum hours for full day
    
    # Overtime rules
    overtime_start_after_hours = Column(Numeric(4, 2), default=8.0)
    max_overtime_hours_per_day = Column(Numeric(4, 2), default=4.0)
    
    # Break rules
    max_break_hours = Column(Numeric(4, 2), default=1.0)
    auto_deduct_break = Column(Boolean, default=True)
    
    # Punch rules
    allow_multiple_punches = Column(Boolean, default=True)
    require_punch_out = Column(Boolean, default=True)
    auto_punch_out_after_hours = Column(Integer, default=12)
    
    # Location restrictions
    restrict_punch_location = Column(Boolean, default=False)
    allowed_ip_addresses = Column(Text)  # JSON array
    
    # System fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    business = relationship("Business")


class AttendanceSummary(Base):
    """Monthly attendance summary for employees"""
    __tablename__ = "attendance_summaries"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Attendance counts
    total_working_days = Column(Integer, default=0)
    present_days = Column(Integer, default=0)
    absent_days = Column(Integer, default=0)
    half_days = Column(Integer, default=0)
    late_days = Column(Integer, default=0)
    leave_days = Column(Integer, default=0)
    holiday_days = Column(Integer, default=0)
    weekend_days = Column(Integer, default=0)
    
    # Hours summary
    total_hours_worked = Column(Numeric(8, 2), default=0)
    regular_hours = Column(Numeric(8, 2), default=0)
    overtime_hours = Column(Numeric(8, 2), default=0)
    break_hours = Column(Numeric(8, 2), default=0)
    
    # Calculated fields
    attendance_percentage = Column(Numeric(5, 2), default=0)
    punctuality_percentage = Column(Numeric(5, 2), default=0)
    
    # System fields
    calculated_at = Column(DateTime, server_default=func.now())
    is_final = Column(Boolean, default=False)

    # Relationships
    employee = relationship("Employee")
    business = relationship("Business")

    # Unique constraint
    __table_args__ = (
        {"schema": None},
    )