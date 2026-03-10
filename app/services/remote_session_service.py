"""
Remote Session Service
Business logic for remote sessions
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.repositories.remote_session_repository import (
    create_remote_session,
    get_remote_sessions,
    get_remote_session_by_id,
    update_remote_session,
    delete_remote_session,
    assign_support_agent,
    start_session,
    complete_session,
    rate_session
)
from app.schemas.remote_session import (
    RemoteSessionCreate,
    RemoteSessionUpdate,
    RemoteSessionResponse,
    RemoteSessionRating
)
from app.models.remote_session import RemoteSession


def create_session_service(
    db: Session,
    session_data: RemoteSessionCreate,
    business_id: int,
    employee_id: int
) -> RemoteSession:
    """Create a new remote session"""
    try:
        return create_remote_session(db, session_data, business_id, employee_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create remote session: {str(e)}"
        )


def get_sessions_service(
    db: Session,
    business_id: int,
    employee_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[RemoteSession]:
    """Get remote sessions with filters"""
    return get_remote_sessions(db, business_id, employee_id, status_filter, skip, limit)


def get_session_service(db: Session, session_id: int, business_id: int) -> RemoteSession:
    """Get a remote session by ID"""
    session = get_remote_session_by_id(db, session_id, business_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found"
        )
    return session


def update_session_service(
    db: Session,
    session_id: int,
    business_id: int,
    update_data: RemoteSessionUpdate
) -> RemoteSession:
    """Update a remote session"""
    session = update_remote_session(db, session_id, business_id, update_data)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found"
        )
    return session


def delete_session_service(db: Session, session_id: int, business_id: int) -> bool:
    """Delete a remote session"""
    deleted = delete_remote_session(db, session_id, business_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found"
        )
    return True


def assign_agent_service(db: Session, session_id: int, business_id: int, agent_id: int) -> RemoteSession:
    """Assign a support agent to a session"""
    session = assign_support_agent(db, session_id, business_id, agent_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found"
        )
    return session


def start_session_service(db: Session, session_id: int, business_id: int) -> RemoteSession:
    """Start a remote session"""
    session = start_session(db, session_id, business_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found"
        )
    return session


def complete_session_service(
    db: Session,
    session_id: int,
    business_id: int,
    resolution_notes: Optional[str] = None
) -> RemoteSession:
    """Complete a remote session"""
    session = complete_session(db, session_id, business_id, resolution_notes)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found"
        )
    return session


def rate_session_service(
    db: Session,
    session_id: int,
    business_id: int,
    rating_data: RemoteSessionRating
) -> RemoteSession:
    """Rate a completed remote session"""
    session = rate_session(db, session_id, business_id, rating_data.rating, rating_data.feedback)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remote session not found or not completed"
        )
    return session
