"""
Support API Endpoints
Remote sessions and support management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin, get_user_business_id
from app.models.user import User
from app.schemas.remote_session import (
    RemoteSessionCreate,
    RemoteSessionUpdate,
    RemoteSessionResponse,
    RemoteSessionRating
)
from app.services.remote_session_service import (
    create_session_service,
    get_sessions_service,
    get_session_service,
    update_session_service,
    delete_session_service,
    assign_agent_service,
    start_session_service,
    complete_session_service,
    rate_session_service
)

router = APIRouter()


# ============================================================================
# Remote Sessions Endpoints
# ============================================================================

@router.get("/remote-sessions", response_model=List[RemoteSessionResponse])
async def get_remote_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all remote sessions with pagination and filtering
    
    **Filters:**
    - status: Filter by session status (pending, scheduled, in_progress, completed, cancelled)
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    
    **Returns:**
    - List of remote sessions with employee and agent details
    """
    try:
        # Get business_id for current user
        business_id = get_user_business_id(current_user, db)
        
        # Get employee_id for filtering (regular users see only their sessions)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Admins and superadmins can see all sessions
        if current_user.role in ["superadmin", "admin"]:
            employee_id = None
        
        # Calculate pagination
        skip = (page - 1) * size
        
        # Get sessions
        sessions = get_sessions_service(db, business_id, employee_id, status_filter, skip, size)
        
        # Build response
        response_list = []
        for session in sessions:
            session_data = RemoteSessionResponse(
                id=session.id,
                business_id=session.business_id,
                employee_id=session.employee_id,
                support_agent_id=session.support_agent_id,
                session_type=session.session_type,
                title=session.title,
                description=session.description,
                status=session.status,
                requested_date=session.requested_date,
                scheduled_date=session.scheduled_date,
                started_at=session.started_at,
                completed_at=session.completed_at,
                computer_name=session.computer_name,
                ip_address=session.ip_address,
                operating_system=session.operating_system,
                issue_category=session.issue_category,
                agent_notes=session.agent_notes,
                resolution_notes=session.resolution_notes,
                rating=session.rating,
                feedback=session.feedback,
                created_at=session.created_at,
                updated_at=session.updated_at,
                employee_name=f"{session.employee.first_name} {session.employee.last_name}" if session.employee else None,
                employee_code=session.employee.employee_code if session.employee else None,
                support_agent_name=f"{session.support_agent.first_name} {session.support_agent.last_name}" if session.support_agent else None
            )
            response_list.append(session_data)
        
        return response_list
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch remote sessions: {str(e)}"
        )


@router.post("/remote-sessions", response_model=RemoteSessionResponse)
async def create_remote_session(
    session_data: RemoteSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new remote session request
    
    **Request Body:**
    - session_type: Type of session (technical_support, software_installation, etc.)
    - title: Session title (5-255 characters)
    - description: Detailed description (min 10 characters)
    - requested_date: Requested date and time
    - computer_name: Optional computer name
    - ip_address: Optional IP address
    - operating_system: Optional OS information
    - issue_category: Optional issue category
    
    **Returns:**
    - Created remote session with ID and status
    """
    try:
        # Get business_id for current user
        business_id = get_user_business_id(current_user, db)
        
        # Get employee_id from current user
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If user doesn't have employee_id, try to find their employee record
        if not employee_id:
            from app.models.employee import Employee
            
            # Try to find employee by email matching user email
            employee = db.query(Employee).filter(
                Employee.business_id == business_id,
                Employee.email == current_user.email,
                Employee.employee_status.in_(["active", "ACTIVE"])
            ).first()
            
            if employee:
                employee_id = employee.id
            else:
                # If still no employee found, get the first active employee for this business
                # This allows business owners to create sessions on behalf of their business
                employee = db.query(Employee).filter(
                    Employee.business_id == business_id,
                    Employee.employee_status.in_(["active", "ACTIVE"])
                ).first()
                
                if employee:
                    employee_id = employee.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No active employee found for this business. Please add an employee first."
                    )
        
        # Create session
        new_session = create_session_service(db, session_data, business_id, employee_id)
        
        # Build response
        return RemoteSessionResponse(
            id=new_session.id,
            business_id=new_session.business_id,
            employee_id=new_session.employee_id,
            support_agent_id=new_session.support_agent_id,
            session_type=new_session.session_type,
            title=new_session.title,
            description=new_session.description,
            status=new_session.status,
            requested_date=new_session.requested_date,
            scheduled_date=new_session.scheduled_date,
            started_at=new_session.started_at,
            completed_at=new_session.completed_at,
            computer_name=new_session.computer_name,
            ip_address=new_session.ip_address,
            operating_system=new_session.operating_system,
            issue_category=new_session.issue_category,
            agent_notes=new_session.agent_notes,
            resolution_notes=new_session.resolution_notes,
            rating=new_session.rating,
            feedback=new_session.feedback,
            created_at=new_session.created_at,
            updated_at=new_session.updated_at
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create remote session: {str(e)}"
        )


@router.get("/remote-sessions/{session_id}", response_model=RemoteSessionResponse)
async def get_remote_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a remote session by ID
    
    **Returns:**
    - Complete remote session details with employee and agent information
    """
    try:
        # Get business_id for current user
        business_id = get_user_business_id(current_user, db)
        
        # Get session
        session = get_session_service(db, session_id, business_id)
        
        # Build response
        return RemoteSessionResponse(
            id=session.id,
            business_id=session.business_id,
            employee_id=session.employee_id,
            support_agent_id=session.support_agent_id,
            session_type=session.session_type,
            title=session.title,
            description=session.description,
            status=session.status,
            requested_date=session.requested_date,
            scheduled_date=session.scheduled_date,
            started_at=session.started_at,
            completed_at=session.completed_at,
            computer_name=session.computer_name,
            ip_address=session.ip_address,
            operating_system=session.operating_system,
            issue_category=session.issue_category,
            agent_notes=session.agent_notes,
            resolution_notes=session.resolution_notes,
            rating=session.rating,
            feedback=session.feedback,
            created_at=session.created_at,
            updated_at=session.updated_at,
            employee_name=f"{session.employee.first_name} {session.employee.last_name}" if session.employee else None,
            employee_code=session.employee.employee_code if session.employee else None,
            support_agent_name=f"{session.support_agent.first_name} {session.support_agent.last_name}" if session.support_agent else None
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch remote session: {str(e)}"
        )


@router.delete("/remote-sessions/{session_id}")
async def delete_remote_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a remote session
    
    **Requires:** Admin or Superadmin role
    
    **Returns:**
    - Success message
    """
    try:
        # Get business_id for current user
        business_id = get_user_business_id(current_user, db)
        
        # Delete session
        delete_session_service(db, session_id, business_id)
        
        return {"message": "Remote session deleted successfully"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete remote session: {str(e)}"
        )


@router.put("/remote-sessions/{session_id}/rate", response_model=RemoteSessionResponse)
async def rate_remote_session(
    session_id: int,
    rating_data: RemoteSessionRating,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rate a completed remote session
    
    **Request Body:**
    - rating: Rating from 1 to 5 stars
    - feedback: Optional feedback text
    
    **Returns:**
    - Updated remote session with rating
    """
    try:
        # Get business_id for current user
        business_id = get_user_business_id(current_user, db)
        
        # Rate session
        session = rate_session_service(db, session_id, business_id, rating_data)
        
        # Build response
        return RemoteSessionResponse(
            id=session.id,
            business_id=session.business_id,
            employee_id=session.employee_id,
            support_agent_id=session.support_agent_id,
            session_type=session.session_type,
            title=session.title,
            description=session.description,
            status=session.status,
            requested_date=session.requested_date,
            scheduled_date=session.scheduled_date,
            started_at=session.started_at,
            completed_at=session.completed_at,
            computer_name=session.computer_name,
            ip_address=session.ip_address,
            operating_system=session.operating_system,
            issue_category=session.issue_category,
            agent_notes=session.agent_notes,
            resolution_notes=session.resolution_notes,
            rating=session.rating,
            feedback=session.feedback,
            created_at=session.created_at,
            updated_at=session.updated_at,
            employee_name=f"{session.employee.first_name} {session.employee.last_name}" if session.employee else None,
            employee_code=session.employee.employee_code if session.employee else None,
            support_agent_name=f"{session.support_agent.first_name} {session.support_agent.last_name}" if session.support_agent else None
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rate remote session: {str(e)}"
        )
