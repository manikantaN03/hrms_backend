from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, get_user_business_id
from app.models.user import User
from app.schemas.attendance_settings import AttendanceSettingsUpdate, AttendanceSettingsResponse
from app.services.attendance_settings import AttendanceSettingsService

router = APIRouter()


@router.get("/", summary="API root for Attendance Settings")
def root():
    """
    API root endpoint for Attendance Settings
    
    Returns basic API information and documentation link
    """
    return {
        "message": "Attendance Settings API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


@router.get(
    "/list", 
    response_model=list[AttendanceSettingsResponse],
    summary="Get all attendance settings",
    description="Retrieve all attendance settings for user's business"
)
def get_all_settings(
    business_id: Optional[int] = Query(None, description="Business ID (ignored - uses user's business)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return (1-1000)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get all attendance settings for user's business.
    
    **Security**: Business isolation enforced
    - Always uses user's business_id from get_user_business_id()
    - Returns only settings for user's business
    """
    from app.models.attendance_settings import AttendanceSettings
    
    # Get user's business ID (works for owners and employees)
    # This may raise HTTPException(403) if user has no business access
    user_business_id = get_user_business_id(current_admin, db)
    
    try:
        # Always filter by user's business
        query = db.query(AttendanceSettings).filter(
            AttendanceSettings.business_id == user_business_id
        )
        
        settings = query.order_by(AttendanceSettings.created_at.desc()).offset(skip).limit(limit).all()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching settings list: {str(e)}")


@router.get(
    "/{business_id}", 
    response_model=AttendanceSettingsResponse,
    summary="Get attendance settings",
    description="Retrieve attendance settings for user's business"
)
def get_settings(
    business_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get attendance settings for user's business.
    
    **Security**: Business isolation enforced
    - Validates that business_id matches user's business
    - Returns 403 if trying to access different business
    - Auto-creates default settings if none exist
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    
    # Get user's business ID and validate access
    # This may raise HTTPException(403) if user has no business access
    user_business_id = get_user_business_id(current_admin, db)
    
    # Verify user is accessing their own business
    if business_id != user_business_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have access to this business"
        )
    
    try:
        return AttendanceSettingsService.get_settings(user_business_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching settings: {str(e)}")


@router.put(
    "/{business_id}", 
    response_model=AttendanceSettingsResponse,
    summary="Update attendance settings",
    description="Update attendance settings for user's business"
)
def update_settings(
    business_id: int,
    data: AttendanceSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update attendance settings for user's business.
    
    **Security**: Business isolation enforced
    - Validates that business_id matches user's business
    - Returns 403 if trying to update different business
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    
    # Get user's business ID and validate access
    # This may raise HTTPException(403) if user has no business access
    user_business_id = get_user_business_id(current_admin, db)
    
    # Verify user is updating their own business
    if business_id != user_business_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have access to this business"
        )
    
    try:
        return AttendanceSettingsService.update_settings(user_business_id, data, db)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Database integrity error. Please check your input data."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")


@router.post(
    "/{business_id}/reset", 
    response_model=AttendanceSettingsResponse,
    summary="Reset attendance settings",
    description="Reset attendance settings to default values for user's business"
)
def reset_settings(
    business_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Reset attendance settings to defaults for user's business.
    
    **Security**: Business isolation enforced
    - Validates that business_id matches user's business
    - Returns 403 if trying to reset different business
    """
    if business_id <= 0:
        raise HTTPException(status_code=400, detail="Business ID must be positive")
    
    try:
        # Get user's business ID and validate access
        user_business_id = get_user_business_id(current_admin, db)
        
        # Verify user is resetting their own business
        if business_id != user_business_id:
            raise HTTPException(
                status_code=403, 
                detail="You don't have access to this business"
            )
        
        return AttendanceSettingsService.reset_settings(user_business_id, db)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting settings: {str(e)}")
