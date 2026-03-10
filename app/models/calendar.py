"""
Calendar Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.models.base import Base


class EventType(str, Enum):
    """Event types for calendar"""
    HOLIDAY = "holiday"
    MEETING = "meeting"
    BIRTHDAY = "birthday"
    WORK_ANNIVERSARY = "work_anniversary"
    WEDDING_ANNIVERSARY = "wedding_anniversary"
    LEAVE = "leave"
    COMPANY_EVENT = "company_event"
    TRAINING = "training"
    DEADLINE = "deadline"
    REMINDER = "reminder"


class EventPriority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EventStatus(str, Enum):
    """Event status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    POSTPONED = "postponed"


class CalendarEvent(Base):
    """Calendar events model"""
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(SQLEnum(EventType, native_enum=False), nullable=False, default=EventType.COMPANY_EVENT)
    
    # Date and time
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_all_day = Column(Boolean, default=False)
    
    # Event properties
    priority = Column(SQLEnum(EventPriority, native_enum=False), nullable=False, default=EventPriority.MEDIUM)
    status = Column(SQLEnum(EventStatus, native_enum=False), nullable=False, default=EventStatus.SCHEDULED)
    
    # Location and attendees
    location = Column(String(255), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    # Organizer and attendees
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # For employee-specific events
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100), nullable=True)  # daily, weekly, monthly, yearly
    recurrence_end_date = Column(Date, nullable=True)
    
    # Metadata
    color = Column(String(7), nullable=True, default="#3788d8")  # Hex color code
    is_public = Column(Boolean, default=True)
    reminder_minutes = Column(Integer, nullable=True)  # Minutes before event to remind
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    business = relationship("Business", back_populates="calendar_events")
    location_rel = relationship("Location")
    organizer = relationship("User", foreign_keys=[organizer_id])
    employee = relationship("Employee")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    attendees = relationship("CalendarEventAttendee", back_populates="event")


class CalendarEventAttendee(Base):
    """Calendar event attendees"""
    __tablename__ = "calendar_event_attendees"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Attendance status
    status = Column(String(20), default="invited")  # invited, accepted, declined, tentative
    response_date = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event = relationship("CalendarEvent", back_populates="attendees")
    employee = relationship("Employee")


class CalendarView(Base):
    """User calendar view preferences"""
    __tablename__ = "calendar_views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # View preferences
    default_view = Column(String(20), default="month")  # month, week, day, agenda
    start_day_of_week = Column(Integer, default=1)  # 0=Sunday, 1=Monday
    time_format = Column(String(10), default="12h")  # 12h, 24h
    
    # Event type visibility
    show_holidays = Column(Boolean, default=True)
    show_birthdays = Column(Boolean, default=True)
    show_work_anniversaries = Column(Boolean, default=True)
    show_leaves = Column(Boolean, default=True)
    show_meetings = Column(Boolean, default=True)
    show_company_events = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    business = relationship("Business")