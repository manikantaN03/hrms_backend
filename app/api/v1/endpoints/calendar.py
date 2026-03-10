"""
Calendar API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.api.v1.endpoints.master_setup import get_user_business_id
from app.models.user import User
from app.services.calendar_service import CalendarService
from app.schemas.calendar import (
    CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse,
    CalendarViewCreate, CalendarViewUpdate, CalendarViewResponse,
    CalendarResponse, CalendarFilters, EventSearchRequest, EventSearchResponse,
    AttendeeUpdateRequest, BulkEventCreate
)

router = APIRouter()


@router.get("/", response_model=CalendarResponse)
async def get_calendar(
    year: Optional[int] = Query(None, ge=2020, le=2030),
    month: Optional[int] = Query(None, ge=1, le=12),
    view: Optional[str] = Query("month", pattern=r'^(month|week|day|agenda)$'),
    show_holidays: bool = Query(True),
    show_birthdays: bool = Query(True),
    show_work_anniversaries: bool = Query(True),
    show_leaves: bool = Query(True),
    show_meetings: bool = Query(True),
    show_company_events: bool = Query(True),
    location_ids: Optional[List[int]] = Query(None),
    employee_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get calendar data for specified month/year with events
    
    **Returns:**
    - Calendar grid with events for the specified period
    - Includes holidays, birthdays, work anniversaries, leaves, meetings
    - Supports filtering by location, employee, event types
    - Compatible with frontend calendar components
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Default to current month/year if not provided
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        # Create filters
        filters = CalendarFilters(
            year=year,
            month=month,
            location_ids=location_ids,
            employee_ids=employee_ids,
            show_holidays=show_holidays,
            show_birthdays=show_birthdays,
            show_work_anniversaries=show_work_anniversaries,
            show_leaves=show_leaves,
            show_meetings=show_meetings,
            show_company_events=show_company_events
        )
        
        service = CalendarService(db)
        calendar_data = service.get_calendar_data(business_id, view, filters)
        
        return calendar_data
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendar data: {str(e)}"
        )


@router.get("/events", response_model=List[CalendarEventResponse])
async def get_events(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    location_ids: Optional[List[int]] = Query(None),
    employee_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get calendar events within date range
    
    **Query Parameters:**
    - start_date: Start date for event range
    - end_date: End date for event range
    - event_types: Filter by event types
    - location_ids: Filter by location IDs
    - employee_ids: Filter by employee IDs
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Default to current month if no dates provided
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        
        if not end_date:
            if start_date.month == 12:
                end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
        
        # Create filters
        filters = CalendarFilters(
            event_types=event_types,
            location_ids=location_ids,
            employee_ids=employee_ids
        )
        
        service = CalendarService(db)
        events = service.get_events_by_date_range(business_id, start_date, end_date, filters)
        
        return events
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.post("/events", response_model=CalendarEventResponse)
async def create_event(
    event_data: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new calendar event
    
    **Any authenticated user can create events**
    """
    try:
        business_id = get_user_business_id(current_user, db)
        event_data.business_id = business_id
        
        service = CalendarService(db)
        event = service.create_event(event_data, current_user.id)
        
        return event
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get calendar event by ID"""
    try:
        business_id = get_user_business_id(current_user, db)
        
        service = CalendarService(db)
        event = service.get_event_by_id(event_id, business_id)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return event
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event: {str(e)}"
        )


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: int,
    event_data: CalendarEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update calendar event
    
    **Any authenticated user can update events**
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        service = CalendarService(db)
        event = service.update_event(event_id, business_id, event_data, current_user.id)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return event
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}"
        )


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete calendar event
    
    **Any authenticated user can delete events**
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        service = CalendarService(db)
        success = service.delete_event(event_id, business_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return {"message": "Event deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )


@router.post("/events/bulk", response_model=List[CalendarEventResponse])
async def create_bulk_events(
    bulk_data: BulkEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple calendar events
    
    **Any authenticated user can create bulk events**
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Set business_id for all events
        for event_data in bulk_data.events:
            event_data.business_id = business_id
        
        service = CalendarService(db)
        events = service.create_bulk_events(bulk_data.events, current_user.id)
        
        return events
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk events: {str(e)}"
        )


@router.post("/events/search", response_model=EventSearchResponse)
async def search_events(
    search_request: EventSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search calendar events
    
    **Search Parameters:**
    - query: Text search in title, description, location
    - start_date: Filter by start date
    - end_date: Filter by end date
    - event_types: Filter by event types
    - location_ids: Filter by location IDs
    - employee_ids: Filter by employee IDs
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        service = CalendarService(db)
        results = service.search_events(business_id, search_request)
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search events: {str(e)}"
        )


@router.put("/events/{event_id}/attendees/{employee_id}")
async def update_attendee_status(
    event_id: int,
    employee_id: int,
    status_update: AttendeeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update attendee response status for an event
    
    **Status Options:**
    - invited: Initial invitation status
    - accepted: Attendee accepted the invitation
    - declined: Attendee declined the invitation
    - tentative: Attendee marked as tentative
    """
    try:
        service = CalendarService(db)
        success = service.update_attendee_status(event_id, employee_id, status_update.status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event or attendee not found"
            )
        
        return {"message": "Attendee status updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update attendee status: {str(e)}"
        )


@router.get("/view", response_model=CalendarViewResponse)
async def get_calendar_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user calendar view preferences"""
    try:
        business_id = get_user_business_id(current_user, db)
        
        service = CalendarService(db)
        view = service.get_calendar_view(current_user.id, business_id)
        
        if not view:
            # Return default view if none exists
            from app.schemas.calendar import CalendarViewBase
            default_view = CalendarViewBase()
            return CalendarViewResponse(
                id=0,
                user_id=current_user.id,
                business_id=business_id,
                **default_view.dict(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        return view
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendar view: {str(e)}"
        )


@router.post("/view", response_model=CalendarViewResponse)
async def create_calendar_view(
    view_data: CalendarViewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create calendar view preferences"""
    try:
        business_id = get_user_business_id(current_user, db)
        view_data.business_id = business_id
        
        service = CalendarService(db)
        view = service.create_calendar_view(current_user.id, view_data)
        
        return view
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create calendar view: {str(e)}"
        )


@router.put("/view", response_model=CalendarViewResponse)
async def update_calendar_view(
    view_data: CalendarViewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update calendar view preferences"""
    try:
        business_id = get_user_business_id(current_user, db)
        
        service = CalendarService(db)
        view = service.update_calendar_view(current_user.id, business_id, view_data)
        
        return view
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update calendar view: {str(e)}"
        )


@router.get("/holidays", response_model=List[Dict[str, Any]])
async def get_holidays(
    year: Optional[int] = Query(None, ge=2020, le=2030),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get holidays for calendar display
    
    **Query Parameters:**
    - year: Year to fetch holidays for (default: current year)
    - month: Month to fetch holidays for (optional, if not provided returns full year)
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        # Calculate date range
        if month:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        
        service = CalendarService(db)
        holidays = service.get_holidays_by_date_range(business_id, start_date, end_date)
        
        return holidays
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch holidays: {str(e)}"
        )


@router.get("/birthdays", response_model=List[Dict[str, Any]])
async def get_birthdays(
    year: Optional[int] = Query(None, ge=2020, le=2030),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get employee birthdays for calendar display
    
    **Query Parameters:**
    - year: Year to fetch birthdays for (default: current year)
    - month: Month to fetch birthdays for (optional, if not provided returns full year)
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        # Calculate date range
        if month:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        
        service = CalendarService(db)
        birthdays = service.get_employee_birthdays_by_date_range(business_id, start_date, end_date)
        
        return birthdays
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch birthdays: {str(e)}"
        )


@router.get("/work-anniversaries", response_model=List[Dict[str, Any]])
async def get_work_anniversaries(
    year: Optional[int] = Query(None, ge=2020, le=2030),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get employee work anniversaries for calendar display
    
    **Query Parameters:**
    - year: Year to fetch anniversaries for (default: current year)
    - month: Month to fetch anniversaries for (optional, if not provided returns full year)
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        # Calculate date range
        if month:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        
        service = CalendarService(db)
        anniversaries = service.get_employee_work_anniversaries_by_date_range(business_id, start_date, end_date)
        
        return anniversaries
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch work anniversaries: {str(e)}"
        )