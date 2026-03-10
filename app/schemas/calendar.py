"""
Calendar Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


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


class AttendeeStatus(str, Enum):
    """Attendee response status"""
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


# Base schemas
class CalendarEventBase(BaseModel):
    """Base calendar event schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    event_type: EventType = EventType.COMPANY_EVENT
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: bool = False
    priority: EventPriority = EventPriority.MEDIUM
    status: EventStatus = EventStatus.SCHEDULED
    location: Optional[str] = None
    location_id: Optional[int] = None
    employee_id: Optional[int] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_public: bool = True
    reminder_minutes: Optional[int] = None


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating calendar events"""
    business_id: Optional[int] = None
    attendee_ids: Optional[List[int]] = []


class CalendarEventUpdate(BaseModel):
    """Schema for updating calendar events"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    priority: Optional[EventPriority] = None
    status: Optional[EventStatus] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    employee_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_public: Optional[bool] = None
    reminder_minutes: Optional[int] = None
    attendee_ids: Optional[List[int]] = None


class CalendarEventAttendeeResponse(BaseModel):
    """Schema for event attendee response"""
    id: int
    employee_id: int
    employee_name: str
    employee_code: Optional[str] = None
    status: AttendeeStatus
    response_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CalendarEventResponse(BaseModel):
    """Schema for calendar event response"""
    id: int
    business_id: int
    title: str
    description: Optional[str] = None
    event_type: EventType
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: bool
    priority: EventPriority
    status: EventStatus
    location: Optional[str] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    organizer_id: Optional[int] = None
    organizer_name: Optional[str] = None
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    color: str
    is_public: bool
    reminder_minutes: Optional[int] = None
    attendees: List[CalendarEventAttendeeResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Calendar view schemas
class CalendarViewBase(BaseModel):
    """Base calendar view schema"""
    default_view: str = Field("month", pattern=r'^(month|week|day|agenda)$')
    start_day_of_week: int = Field(1, ge=0, le=6)
    time_format: str = Field("12h", pattern=r'^(12h|24h)$')
    show_holidays: bool = True
    show_birthdays: bool = True
    show_work_anniversaries: bool = True
    show_leaves: bool = True
    show_meetings: bool = True
    show_company_events: bool = True


class CalendarViewCreate(CalendarViewBase):
    """Schema for creating calendar view preferences"""
    business_id: Optional[int] = None


class CalendarViewUpdate(BaseModel):
    """Schema for updating calendar view preferences"""
    default_view: Optional[str] = Field(None, pattern=r'^(month|week|day|agenda)$')
    start_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    time_format: Optional[str] = Field(None, pattern=r'^(12h|24h)$')
    show_holidays: Optional[bool] = None
    show_birthdays: Optional[bool] = None
    show_work_anniversaries: Optional[bool] = None
    show_leaves: Optional[bool] = None
    show_meetings: Optional[bool] = None
    show_company_events: Optional[bool] = None


class CalendarViewResponse(CalendarViewBase):
    """Schema for calendar view response"""
    id: int
    user_id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Calendar data schemas
class CalendarDayEvent(BaseModel):
    """Schema for events in a calendar day"""
    id: int
    title: str
    event_type: EventType
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_all_day: bool
    color: str
    priority: EventPriority
    status: EventStatus
    location: Optional[str] = None
    employee_name: Optional[str] = None


class CalendarDay(BaseModel):
    """Schema for a calendar day"""
    date: date
    day_of_week: int
    is_today: bool = False
    is_weekend: bool = False
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    events: List[CalendarDayEvent] = []
    event_count: int = 0


class CalendarWeek(BaseModel):
    """Schema for a calendar week"""
    week_number: int
    start_date: date
    end_date: date
    days: List[CalendarDay]


class CalendarMonth(BaseModel):
    """Schema for a calendar month"""
    year: int
    month: int
    month_name: str
    weeks: List[CalendarWeek]
    total_events: int
    holidays: List[Dict[str, Any]] = []
    birthdays: List[Dict[str, Any]] = []
    work_anniversaries: List[Dict[str, Any]] = []


class CalendarFilters(BaseModel):
    """Schema for calendar filters"""
    year: Optional[int] = None
    month: Optional[int] = None
    week: Optional[int] = None
    date: Optional[date] = None
    event_types: Optional[List[EventType]] = None
    location_ids: Optional[List[int]] = None
    employee_ids: Optional[List[int]] = None
    show_holidays: bool = True
    show_birthdays: bool = True
    show_work_anniversaries: bool = True
    show_leaves: bool = True
    show_meetings: bool = True
    show_company_events: bool = True


class CalendarResponse(BaseModel):
    """Schema for calendar response"""
    view_type: str
    current_date: date
    calendar_data: CalendarMonth
    filters_applied: CalendarFilters
    summary: Dict[str, Any]


# Attendee management schemas
class AttendeeUpdateRequest(BaseModel):
    """Schema for updating attendee status"""
    status: AttendeeStatus


class BulkEventCreate(BaseModel):
    """Schema for creating multiple events"""
    events: List[CalendarEventCreate]


class EventSearchRequest(BaseModel):
    """Schema for searching events"""
    query: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    event_types: Optional[List[EventType]] = None
    location_ids: Optional[List[int]] = None
    employee_ids: Optional[List[int]] = None


class EventSearchResponse(BaseModel):
    """Schema for event search results"""
    total_events: int
    events: List[CalendarEventResponse]
    search_filters: EventSearchRequest