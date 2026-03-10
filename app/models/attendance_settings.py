from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class AttendanceSettings(Base):
    __tablename__ = "attendance_settings"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, unique=True, index=True)
    business = relationship("Business", back_populates="attendance_settings")
    
    # Default Attendance Settings
    default_attendance = Column(String, default="PRESENT")
    mark_out_on_punch = Column(Boolean, default=False)  # every2ndPunch in frontend
    punch_count = Column(Integer, default=2)
    enable_manual_attendance = Column(Boolean, default=False)  # manualAttendance in frontend

    # Holiday Sandwich Rules (individual boolean flags to match frontend)
    no_holiday_if_absent = Column(Boolean, default=False)
    apply_holiday_one_side = Column(Boolean, default=False)
    apply_holiday_either = Column(Boolean, default=False)

    # Week Off Sandwich Rules (individual boolean flags to match frontend)
    no_week_off_if_absent = Column(Boolean, default=False)
    apply_week_off_one_side = Column(Boolean, default=False)
    apply_week_off_either = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   
