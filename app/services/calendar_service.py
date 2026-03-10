"""
Calendar Service
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import calendar
from app.repositories.calendar_repository import CalendarRepository
from app.schemas.calendar import (
    CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse,
    CalendarViewCreate, CalendarViewUpdate, CalendarViewResponse,
    CalendarResponse, CalendarFilters, EventSearchRequest, EventSearchResponse,
    CalendarMonth, CalendarWeek, CalendarDay, CalendarDayEvent
)


class CalendarService:
    """Service for calendar operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = CalendarRepository(db)

    def get_calendar_data(self, business_id: int, view_type: str, filters: CalendarFilters) -> CalendarResponse:
        """Get calendar data for specified view and filters"""
        try:
            # Default to current month/year if not provided
            year = filters.year or datetime.now().year
            month = filters.month or datetime.now().month
            current_date = date(year, month, 1)

            # Get calendar month data
            calendar_month = self._build_calendar_month(business_id, year, month, filters)

            # Create response
            response = CalendarResponse(
                view_type=view_type,
                current_date=current_date,
                calendar_data=calendar_month,
                filters_applied=filters,
                summary={
                    "total_events": calendar_month.total_events,
                    "holidays_count": len(calendar_month.holidays),
                    "birthdays_count": len(calendar_month.birthdays),
                    "work_anniversaries_count": len(calendar_month.work_anniversaries)
                }
            )

            return response

        except Exception as e:
            raise Exception(f"Failed to get calendar data: {str(e)}")

    def _build_calendar_month(self, business_id: int, year: int, month: int, filters: CalendarFilters) -> CalendarMonth:
        """Build calendar month structure with events"""
        try:
            # Get month boundaries
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            # Get all events for the month
            events = self.repository.get_events_by_date_range(business_id, first_day, last_day, filters)
            
            # Get holidays, birthdays, work anniversaries
            holidays = []
            birthdays = []
            work_anniversaries = []
            
            if filters.show_holidays:
                holidays = self.repository.get_holidays_by_date_range(business_id, first_day, last_day)
            
            if filters.show_birthdays:
                birthday_employees = self.repository.get_employee_birthdays_by_date_range(business_id, first_day, last_day)
                birthdays = [
                    {
                        "id": emp.id,
                        "name": f"{emp.first_name} {emp.last_name}",
                        "employee_code": emp.employee_code,
                        "date": date(year, emp.date_of_birth.month, emp.date_of_birth.day),
                        "type": "birthday"
                    }
                    for emp in birthday_employees
                ]
            
            if filters.show_work_anniversaries:
                anniversary_employees = self.repository.get_employee_work_anniversaries_by_date_range(business_id, first_day, last_day)
                work_anniversaries = [
                    {
                        "id": emp.id,
                        "name": f"{emp.first_name} {emp.last_name}",
                        "employee_code": emp.employee_code,
                        "date": date(year, emp.date_of_joining.month, emp.date_of_joining.day),
                        "years": year - emp.date_of_joining.year,
                        "type": "work_anniversary"
                    }
                    for emp in anniversary_employees
                ]

            # Build calendar structure
            cal = calendar.monthcalendar(year, month)
            weeks = []
            total_events = 0

            for week_num, week_days in enumerate(cal):
                days = []
                week_start = None
                week_end = None

                for day_num in week_days:
                    if day_num == 0:
                        # Previous/next month day - skip or handle as needed
                        continue
                    
                    current_date = date(year, month, day_num)
                    if week_start is None:
                        week_start = current_date
                    week_end = current_date

                    # Get events for this day
                    day_events = [event for event in events if self._event_occurs_on_date(event, current_date)]
                    
                    # Convert to calendar day events
                    calendar_day_events = []
                    for event in day_events:
                        calendar_day_events.append(CalendarDayEvent(
                            id=event.id,
                            title=event.title,
                            event_type=event.event_type,
                            start_time=event.start_time.strftime("%H:%M") if event.start_time else None,
                            end_time=event.end_time.strftime("%H:%M") if event.end_time else None,
                            is_all_day=event.is_all_day,
                            color=event.color,
                            priority=event.priority,
                            status=event.status,
                            location=event.location,
                            employee_name=f"{event.employee.first_name} {event.employee.last_name}" if event.employee else None
                        ))

                    # Check if it's a holiday
                    is_holiday = any(h.date == current_date for h in holidays)
                    holiday_name = next((h.name for h in holidays if h.date == current_date), None)

                    # Create calendar day
                    calendar_day = CalendarDay(
                        date=current_date,
                        day_of_week=current_date.weekday(),
                        is_today=current_date == date.today(),
                        is_weekend=current_date.weekday() >= 5,
                        is_holiday=is_holiday,
                        holiday_name=holiday_name,
                        events=calendar_day_events,
                        event_count=len(calendar_day_events)
                    )
                    
                    days.append(calendar_day)
                    total_events += len(calendar_day_events)

                if week_start and week_end:
                    calendar_week = CalendarWeek(
                        week_number=week_num + 1,
                        start_date=week_start,
                        end_date=week_end,
                        days=days
                    )
                    weeks.append(calendar_week)

            # Create calendar month
            calendar_month = CalendarMonth(
                year=year,
                month=month,
                month_name=calendar.month_name[month],
                weeks=weeks,
                total_events=total_events,
                holidays=[
                    {
                        "id": h.id,
                        "name": h.name,
                        "date": h.date,
                        "type": "holiday"
                    }
                    for h in holidays
                ],
                birthdays=birthdays,
                work_anniversaries=work_anniversaries
            )

            return calendar_month

        except Exception as e:
            raise Exception(f"Failed to build calendar month: {str(e)}")

    def _event_occurs_on_date(self, event, target_date: date) -> bool:
        """Check if an event occurs on a specific date"""
        if event.start_date <= target_date:
            if event.end_date:
                return target_date <= event.end_date
            else:
                return target_date == event.start_date
        return False

    def get_events_by_date_range(self, business_id: int, start_date: date, end_date: date, filters: Optional[CalendarFilters] = None) -> List[CalendarEventResponse]:
        """Get events within date range"""
        try:
            events = self.repository.get_events_by_date_range(business_id, start_date, end_date, filters)
            return [self._convert_to_response(event) for event in events]
        except Exception as e:
            raise Exception(f"Failed to get events by date range: {str(e)}")

    def create_event(self, event_data: CalendarEventCreate, created_by: int) -> CalendarEventResponse:
        """Create a new calendar event"""
        try:
            event = self.repository.create_event(event_data, event_data.business_id, created_by)
            return self._convert_to_response(event)
        except Exception as e:
            raise Exception(f"Failed to create event: {str(e)}")

    def get_event_by_id(self, event_id: int, business_id: int) -> Optional[CalendarEventResponse]:
        """Get event by ID"""
        try:
            event = self.repository.get_event_by_id(event_id, business_id)
            return self._convert_to_response(event) if event else None
        except Exception as e:
            raise Exception(f"Failed to get event by ID: {str(e)}")

    def update_event(self, event_id: int, business_id: int, event_data: CalendarEventUpdate, updated_by: int) -> Optional[CalendarEventResponse]:
        """Update calendar event"""
        try:
            event = self.repository.update_event(event_id, business_id, event_data, updated_by)
            return self._convert_to_response(event) if event else None
        except Exception as e:
            raise Exception(f"Failed to update event: {str(e)}")

    def delete_event(self, event_id: int, business_id: int) -> bool:
        """Delete calendar event"""
        try:
            return self.repository.delete_event(event_id, business_id)
        except Exception as e:
            raise Exception(f"Failed to delete event: {str(e)}")

    def create_bulk_events(self, events_data: List[CalendarEventCreate], created_by: int) -> List[CalendarEventResponse]:
        """Create multiple calendar events"""
        try:
            created_events = []
            for event_data in events_data:
                event = self.repository.create_event(event_data, event_data.business_id, created_by)
                created_events.append(self._convert_to_response(event))
            return created_events
        except Exception as e:
            raise Exception(f"Failed to create bulk events: {str(e)}")

    def search_events(self, business_id: int, search_request: EventSearchRequest) -> EventSearchResponse:
        """Search calendar events"""
        try:
            filters = {
                'start_date': search_request.start_date,
                'end_date': search_request.end_date,
                'event_types': search_request.event_types
            }
            
            events = self.repository.search_events(business_id, search_request.query, filters)
            
            return EventSearchResponse(
                total_events=len(events),
                events=[self._convert_to_response(event) for event in events],
                search_filters=search_request
            )
        except Exception as e:
            raise Exception(f"Failed to search events: {str(e)}")

    def update_attendee_status(self, event_id: int, employee_id: int, status: str) -> bool:
        """Update attendee response status"""
        try:
            return self.repository.update_attendee_status(event_id, employee_id, status)
        except Exception as e:
            raise Exception(f"Failed to update attendee status: {str(e)}")

    def get_calendar_view(self, user_id: int, business_id: int) -> Optional[CalendarViewResponse]:
        """Get user calendar view preferences"""
        try:
            view = self.repository.get_calendar_view(user_id, business_id)
            if view:
                return CalendarViewResponse(
                    id=view.id,
                    user_id=view.user_id,
                    business_id=view.business_id,
                    default_view=view.default_view,
                    start_day_of_week=view.start_day_of_week,
                    time_format=view.time_format,
                    show_holidays=view.show_holidays,
                    show_birthdays=view.show_birthdays,
                    show_work_anniversaries=view.show_work_anniversaries,
                    show_leaves=view.show_leaves,
                    show_meetings=view.show_meetings,
                    show_company_events=view.show_company_events,
                    created_at=view.created_at,
                    updated_at=view.updated_at
                )
            return None
        except Exception as e:
            raise Exception(f"Failed to get calendar view: {str(e)}")

    def create_calendar_view(self, user_id: int, view_data: CalendarViewCreate) -> CalendarViewResponse:
        """Create calendar view preferences"""
        try:
            view_dict = view_data.dict(exclude_unset=True)
            view = self.repository.create_or_update_calendar_view(user_id, view_data.business_id, view_dict)
            
            return CalendarViewResponse(
                id=view.id,
                user_id=view.user_id,
                business_id=view.business_id,
                default_view=view.default_view,
                start_day_of_week=view.start_day_of_week,
                time_format=view.time_format,
                show_holidays=view.show_holidays,
                show_birthdays=view.show_birthdays,
                show_work_anniversaries=view.show_work_anniversaries,
                show_leaves=view.show_leaves,
                show_meetings=view.show_meetings,
                show_company_events=view.show_company_events,
                created_at=view.created_at,
                updated_at=view.updated_at
            )
        except Exception as e:
            raise Exception(f"Failed to create calendar view: {str(e)}")

    def update_calendar_view(self, user_id: int, business_id: int, view_data: CalendarViewUpdate) -> CalendarViewResponse:
        """Update calendar view preferences"""
        try:
            view_dict = view_data.dict(exclude_unset=True)
            view = self.repository.create_or_update_calendar_view(user_id, business_id, view_dict)
            
            return CalendarViewResponse(
                id=view.id,
                user_id=view.user_id,
                business_id=view.business_id,
                default_view=view.default_view,
                start_day_of_week=view.start_day_of_week,
                time_format=view.time_format,
                show_holidays=view.show_holidays,
                show_birthdays=view.show_birthdays,
                show_work_anniversaries=view.show_work_anniversaries,
                show_leaves=view.show_leaves,
                show_meetings=view.show_meetings,
                show_company_events=view.show_company_events,
                created_at=view.created_at,
                updated_at=view.updated_at
            )
        except Exception as e:
            raise Exception(f"Failed to update calendar view: {str(e)}")

    def get_holidays_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get holidays for calendar display"""
        try:
            holidays = self.repository.get_holidays_by_date_range(business_id, start_date, end_date)
            return [
                {
                    "id": holiday.id,
                    "name": holiday.name,
                    "date": holiday.date,
                    "type": "holiday",
                    "is_optional": getattr(holiday, 'is_optional', False)
                }
                for holiday in holidays
            ]
        except Exception as e:
            raise Exception(f"Failed to get holidays: {str(e)}")

    def get_employee_birthdays_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get employee birthdays for calendar display"""
        try:
            employees = self.repository.get_employee_birthdays_by_date_range(business_id, start_date, end_date)
            return [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "employee_code": emp.employee_code,
                    "date": date(start_date.year, emp.date_of_birth.month, emp.date_of_birth.day),
                    "type": "birthday",
                    "age": start_date.year - emp.date_of_birth.year
                }
                for emp in employees
            ]
        except Exception as e:
            raise Exception(f"Failed to get employee birthdays: {str(e)}")

    def get_employee_work_anniversaries_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get employee work anniversaries for calendar display"""
        try:
            employees = self.repository.get_employee_work_anniversaries_by_date_range(business_id, start_date, end_date)
            return [
                {
                    "id": emp.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "employee_code": emp.employee_code,
                    "date": date(start_date.year, emp.date_of_joining.month, emp.date_of_joining.day),
                    "type": "work_anniversary",
                    "years": start_date.year - emp.date_of_joining.year
                }
                for emp in employees
            ]
        except Exception as e:
            raise Exception(f"Failed to get employee work anniversaries: {str(e)}")

    def _convert_to_response(self, event) -> CalendarEventResponse:
        """Convert database event to response schema"""
        try:
            # Get attendees
            attendees = []
            if event.attendees:
                from app.schemas.calendar import CalendarEventAttendeeResponse
                for attendee in event.attendees:
                    attendees.append(CalendarEventAttendeeResponse(
                        id=attendee.id,
                        employee_id=attendee.employee_id,
                        employee_name=f"{attendee.employee.first_name} {attendee.employee.last_name}" if attendee.employee else "Unknown",
                        employee_code=attendee.employee.employee_code if attendee.employee else None,
                        status=attendee.status,
                        response_date=attendee.response_date
                    ))

            return CalendarEventResponse(
                id=event.id,
                business_id=event.business_id,
                title=event.title,
                description=event.description,
                event_type=event.event_type,
                start_date=event.start_date,
                end_date=event.end_date,
                start_time=event.start_time,
                end_time=event.end_time,
                is_all_day=event.is_all_day,
                priority=event.priority,
                status=event.status,
                location=event.location,
                location_id=event.location_id,
                location_name=event.location_rel.name if event.location_rel else None,
                organizer_id=event.organizer_id,
                organizer_name=event.organizer.name if event.organizer else None,  # User model uses 'name' field
                employee_id=event.employee_id,
                employee_name=f"{event.employee.first_name} {event.employee.last_name}" if event.employee else None,
                is_recurring=event.is_recurring,
                recurrence_pattern=event.recurrence_pattern,
                recurrence_end_date=event.recurrence_end_date,
                color=event.color,
                is_public=event.is_public,
                reminder_minutes=event.reminder_minutes,
                attendees=attendees,
                created_at=event.created_at,
                updated_at=event.updated_at
            )
        except Exception as e:
            raise Exception(f"Failed to convert event to response: {str(e)}")