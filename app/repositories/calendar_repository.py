"""
Calendar Repository
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, extract, func, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from app.models.calendar import CalendarEvent, CalendarEventAttendee, CalendarView
from app.models.holiday import Holiday
from app.models.employee import Employee, EmployeeProfile
from app.models.requests import LeaveRequest
from app.schemas.calendar import CalendarEventCreate, CalendarEventUpdate, CalendarFilters


class CalendarRepository:
    """Repository for calendar operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event_data: CalendarEventCreate, business_id: int, created_by: int) -> CalendarEvent:
        """Create a new calendar event"""
        event = CalendarEvent(
            business_id=business_id,
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            is_all_day=event_data.is_all_day,
            priority=event_data.priority,
            status=event_data.status,
            location=event_data.location,
            location_id=event_data.location_id,
            employee_id=event_data.employee_id,
            is_recurring=event_data.is_recurring,
            recurrence_pattern=event_data.recurrence_pattern,
            recurrence_end_date=event_data.recurrence_end_date,
            color=event_data.color or "#3788d8",
            is_public=event_data.is_public,
            reminder_minutes=event_data.reminder_minutes,
            organizer_id=created_by,
            created_by=created_by
        )
        
        self.db.add(event)
        self.db.flush()  # Get the ID
        
        # Add attendees if provided
        if event_data.attendee_ids:
            for employee_id in event_data.attendee_ids:
                attendee = CalendarEventAttendee(
                    event_id=event.id,
                    employee_id=employee_id,
                    status="invited"
                )
                self.db.add(attendee)
        
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_event_by_id(self, event_id: int, business_id: int) -> Optional[CalendarEvent]:
        """Get event by ID"""
        return self.db.query(CalendarEvent).options(
            joinedload(CalendarEvent.attendees).joinedload(CalendarEventAttendee.employee),
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.employee),
            joinedload(CalendarEvent.location_rel)
        ).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.business_id == business_id
        ).first()

    def get_events_by_date_range(self, business_id: int, start_date: date, end_date: date, filters: Optional[CalendarFilters] = None) -> List[CalendarEvent]:
        """Get events within date range"""
        query = self.db.query(CalendarEvent).options(
            joinedload(CalendarEvent.attendees).joinedload(CalendarEventAttendee.employee),
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.employee),
            joinedload(CalendarEvent.location_rel)
        ).filter(
            CalendarEvent.business_id == business_id,
            or_(
                and_(CalendarEvent.start_date >= start_date, CalendarEvent.start_date <= end_date),
                and_(CalendarEvent.end_date >= start_date, CalendarEvent.end_date <= end_date),
                and_(CalendarEvent.start_date <= start_date, CalendarEvent.end_date >= end_date)
            )
        )

        # Apply filters
        if filters:
            if filters.event_types:
                query = query.filter(CalendarEvent.event_type.in_(filters.event_types))
            
            if filters.location_ids:
                query = query.filter(CalendarEvent.location_id.in_(filters.location_ids))
            
            if filters.employee_ids:
                query = query.filter(CalendarEvent.employee_id.in_(filters.employee_ids))

        return query.order_by(CalendarEvent.start_date, CalendarEvent.start_time).all()

    def update_event(self, event_id: int, business_id: int, event_data: CalendarEventUpdate, updated_by: int) -> Optional[CalendarEvent]:
        """Update calendar event"""
        event = self.get_event_by_id(event_id, business_id)
        if not event:
            return None

        # Update fields
        update_data = event_data.dict(exclude_unset=True)
        attendee_ids = update_data.pop('attendee_ids', None)
        
        for field, value in update_data.items():
            setattr(event, field, value)
        
        event.updated_by = updated_by
        event.updated_at = datetime.utcnow()

        # Update attendees if provided
        if attendee_ids is not None:
            # Remove existing attendees
            self.db.query(CalendarEventAttendee).filter(
                CalendarEventAttendee.event_id == event_id
            ).delete()
            
            # Add new attendees
            for employee_id in attendee_ids:
                attendee = CalendarEventAttendee(
                    event_id=event_id,
                    employee_id=employee_id,
                    status="invited"
                )
                self.db.add(attendee)

        self.db.commit()
        self.db.refresh(event)
        return event

    def delete_event(self, event_id: int, business_id: int) -> bool:
        """Delete calendar event"""
        event = self.get_event_by_id(event_id, business_id)
        if not event:
            return False

        # Delete attendees first
        self.db.query(CalendarEventAttendee).filter(
            CalendarEventAttendee.event_id == event_id
        ).delete()

        # Delete event
        self.db.delete(event)
        self.db.commit()
        return True

    def get_holidays_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[Holiday]:
        """Get holidays within date range"""
        return self.db.query(Holiday).filter(
            Holiday.business_id == business_id,
            Holiday.date >= start_date,
            Holiday.date <= end_date
        ).order_by(Holiday.date).all()

    def get_employee_birthdays_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[Employee]:
        """Get employee birthdays within date range"""
        # Extract month and day from date range
        start_month = start_date.month
        start_day = start_date.day
        end_month = end_date.month
        end_day = end_date.day

        query = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.is_active == True,
            Employee.date_of_birth.isnot(None)
        )

        # Handle year boundary
        if start_month <= end_month:
            query = query.filter(
                or_(
                    and_(
                        extract('month', Employee.date_of_birth) == start_month,
                        extract('day', Employee.date_of_birth) >= start_day
                    ),
                    and_(
                        extract('month', Employee.date_of_birth) > start_month,
                        extract('month', Employee.date_of_birth) < end_month
                    ),
                    and_(
                        extract('month', Employee.date_of_birth) == end_month,
                        extract('day', Employee.date_of_birth) <= end_day
                    )
                )
            )
        else:  # Year boundary crossing
            query = query.filter(
                or_(
                    and_(
                        extract('month', Employee.date_of_birth) == start_month,
                        extract('day', Employee.date_of_birth) >= start_day
                    ),
                    extract('month', Employee.date_of_birth) > start_month,
                    extract('month', Employee.date_of_birth) < end_month,
                    and_(
                        extract('month', Employee.date_of_birth) == end_month,
                        extract('day', Employee.date_of_birth) <= end_day
                    )
                )
            )

        return query.order_by(
            extract('month', Employee.date_of_birth),
            extract('day', Employee.date_of_birth)
        ).all()

    def get_employee_work_anniversaries_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[Employee]:
        """Get employee work anniversaries within date range"""
        # Similar logic to birthdays but for date_of_joining
        start_month = start_date.month
        start_day = start_date.day
        end_month = end_date.month
        end_day = end_date.day

        query = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.is_active == True,
            Employee.date_of_joining.isnot(None)
        )

        # Handle year boundary
        if start_month <= end_month:
            query = query.filter(
                or_(
                    and_(
                        extract('month', Employee.date_of_joining) == start_month,
                        extract('day', Employee.date_of_joining) >= start_day
                    ),
                    and_(
                        extract('month', Employee.date_of_joining) > start_month,
                        extract('month', Employee.date_of_joining) < end_month
                    ),
                    and_(
                        extract('month', Employee.date_of_joining) == end_month,
                        extract('day', Employee.date_of_joining) <= end_day
                    )
                )
            )
        else:  # Year boundary crossing
            query = query.filter(
                or_(
                    and_(
                        extract('month', Employee.date_of_joining) == start_month,
                        extract('day', Employee.date_of_joining) >= start_day
                    ),
                    extract('month', Employee.date_of_joining) > start_month,
                    extract('month', Employee.date_of_joining) < end_month,
                    and_(
                        extract('month', Employee.date_of_joining) == end_month,
                        extract('day', Employee.date_of_joining) <= end_day
                    )
                )
            )

        return query.order_by(
            extract('month', Employee.date_of_joining),
            extract('day', Employee.date_of_joining)
        ).all()

    def get_leave_requests_by_date_range(self, business_id: int, start_date: date, end_date: date) -> List[LeaveRequest]:
        """Get approved leave requests within date range"""
        return self.db.query(LeaveRequest).options(
            joinedload(LeaveRequest.employee)
        ).filter(
            LeaveRequest.business_id == business_id,
            LeaveRequest.status == "approved",
            or_(
                and_(LeaveRequest.start_date >= start_date, LeaveRequest.start_date <= end_date),
                and_(LeaveRequest.end_date >= start_date, LeaveRequest.end_date <= end_date),
                and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= end_date)
            )
        ).order_by(LeaveRequest.start_date).all()

    def search_events(self, business_id: int, query: str, filters: Optional[Dict[str, Any]] = None) -> List[CalendarEvent]:
        """Search events by title, description, or location"""
        search_query = self.db.query(CalendarEvent).options(
            joinedload(CalendarEvent.attendees).joinedload(CalendarEventAttendee.employee),
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.employee),
            joinedload(CalendarEvent.location_rel)
        ).filter(
            CalendarEvent.business_id == business_id
        )

        if query:
            search_term = f"%{query}%"
            search_query = search_query.filter(
                or_(
                    CalendarEvent.title.ilike(search_term),
                    CalendarEvent.description.ilike(search_term),
                    CalendarEvent.location.ilike(search_term)
                )
            )

        if filters:
            if filters.get('start_date'):
                search_query = search_query.filter(CalendarEvent.start_date >= filters['start_date'])
            
            if filters.get('end_date'):
                search_query = search_query.filter(CalendarEvent.start_date <= filters['end_date'])
            
            if filters.get('event_types'):
                search_query = search_query.filter(CalendarEvent.event_type.in_(filters['event_types']))

        return search_query.order_by(desc(CalendarEvent.start_date)).limit(50).all()

    def update_attendee_status(self, event_id: int, employee_id: int, status: str) -> bool:
        """Update attendee status"""
        attendee = self.db.query(CalendarEventAttendee).filter(
            CalendarEventAttendee.event_id == event_id,
            CalendarEventAttendee.employee_id == employee_id
        ).first()

        if not attendee:
            return False

        attendee.status = status
        attendee.response_date = datetime.utcnow()
        attendee.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def get_calendar_view(self, user_id: int, business_id: int) -> Optional[CalendarView]:
        """Get user calendar view preferences"""
        return self.db.query(CalendarView).filter(
            CalendarView.user_id == user_id,
            CalendarView.business_id == business_id
        ).first()

    def create_or_update_calendar_view(self, user_id: int, business_id: int, view_data: Dict[str, Any]) -> CalendarView:
        """Create or update calendar view preferences"""
        view = self.get_calendar_view(user_id, business_id)
        
        if view:
            # Update existing
            for field, value in view_data.items():
                setattr(view, field, value)
            view.updated_at = datetime.utcnow()
        else:
            # Create new - exclude business_id from view_data since it's passed as parameter
            view_data_copy = {k: v for k, v in view_data.items() if k not in ['business_id', 'user_id']}
            view = CalendarView(
                user_id=user_id,
                business_id=business_id,
                **view_data_copy
            )
            self.db.add(view)

        self.db.commit()
        self.db.refresh(view)
        return view