"""
Remote Session Repository
Database operations for remote sessions
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime

from app.models.remote_session import RemoteSession, RemoteSessionStatus
from app.models.employee import Employee
from app.schemas.remote_session import RemoteSessionCreate, RemoteSessionUpdate


def create_remote_session(db: Session, session_data: RemoteSessionCreate, business_id: int, employee_id: int) -> RemoteSession:
    """Create a new remote session"""
    new_session = RemoteSession(
        business_id=business_id,
        employee_id=employee_id,
        session_type=session_data.session_type.value if hasattr(session_data.session_type, 'value') else session_data.session_type,
        title=session_data.title,
        description=session_data.description,
        requested_date=session_data.requested_date,
        computer_name=session_data.computer_name,
        ip_address=session_data.ip_address,
        operating_system=session_data.operating_system,
        issue_category=session_data.issue_category,
        status=RemoteSessionStatus.PENDING.value
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def get_remote_sessions(
    db: Session,
    business_id: int,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[RemoteSession]:
    """Get remote sessions with filters"""
    query = db.query(RemoteSession).options(
        joinedload(RemoteSession.employee),
        joinedload(RemoteSession.support_agent)
    ).filter(RemoteSession.business_id == business_id)
    
    if employee_id:
        query = query.filter(RemoteSession.employee_id == employee_id)
    
    if status:
        # Convert string to enum
        try:
            status_enum = RemoteSessionStatus(status)
            query = query.filter(RemoteSession.status == status_enum)
        except ValueError:
            # Invalid status, return empty result
            return []
    
    return query.order_by(desc(RemoteSession.created_at)).offset(skip).limit(limit).all()


def get_remote_session_by_id(db: Session, session_id: int, business_id: int) -> Optional[RemoteSession]:
    """Get a remote session by ID"""
    return db.query(RemoteSession).options(
        joinedload(RemoteSession.employee),
        joinedload(RemoteSession.support_agent)
    ).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id
    ).first()


def update_remote_session(
    db: Session,
    session_id: int,
    business_id: int,
    update_data: RemoteSessionUpdate
) -> Optional[RemoteSession]:
    """Update a remote session"""
    session = db.query(RemoteSession).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id
    ).first()
    
    if not session:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(session, field, value)
    
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
    return session


def delete_remote_session(db: Session, session_id: int, business_id: int) -> bool:
    """Delete a remote session"""
    session = db.query(RemoteSession).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id
    ).first()
    
    if not session:
        return False
    
    db.delete(session)
    db.commit()
    return True


def assign_support_agent(db: Session, session_id: int, business_id: int, agent_id: int) -> Optional[RemoteSession]:
    """Assign a support agent to a session"""
    session = db.query(RemoteSession).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id
    ).first()
    
    if not session:
        return None
    
    session.support_agent_id = agent_id
    session.status = RemoteSessionStatus.SCHEDULED.value
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
    return session


def start_session(db: Session, session_id: int, business_id: int) -> Optional[RemoteSession]:
    """Start a remote session"""
    session = db.query(RemoteSession).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id
    ).first()
    
    if not session:
        return None
    
    session.status = RemoteSessionStatus.IN_PROGRESS.value
    session.started_at = datetime.now()
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
    return session


def complete_session(
    db: Session,
    session_id: int,
    business_id: int,
    resolution_notes: Optional[str] = None
) -> Optional[RemoteSession]:
    """Complete a remote session"""
    session = db.query(RemoteSession).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id
    ).first()
    
    if not session:
        return None
    
    session.status = RemoteSessionStatus.COMPLETED.value
    session.completed_at = datetime.now()
    if resolution_notes:
        session.resolution_notes = resolution_notes
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
    return session


def rate_session(db: Session, session_id: int, business_id: int, rating: int, feedback: Optional[str] = None) -> Optional[RemoteSession]:
    """Rate a completed remote session"""
    session = db.query(RemoteSession).filter(
        RemoteSession.id == session_id,
        RemoteSession.business_id == business_id,
        RemoteSession.status == RemoteSessionStatus.COMPLETED.value
    ).first()
    
    if not session:
        return None
    
    session.rating = rating
    session.feedback = feedback
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
    return session
