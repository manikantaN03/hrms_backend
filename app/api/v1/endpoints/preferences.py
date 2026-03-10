"""
User Preferences Endpoints
API endpoints for managing user notification and communication preferences
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.preferences_service import PreferencesService
from app.schemas.preferences import (
    UserPreferencesUpdate,
    UserPreferencesResponse
)

router = APIRouter()


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's preferences.
    
    Returns user notification and communication preferences.
    If preferences don't exist, creates default preferences.
    """
    try:
        service = PreferencesService(db)
        return service.get_user_preferences(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's preferences.
    
    Allows updating:
    - Communication preferences (email, SMS, browser push)
    - Alert preferences (attendance, onboarding, confirmations, flight risk)
    
    Only provided fields will be updated.
    """
    try:
        service = PreferencesService(db)
        return service.update_user_preferences(current_user.id, preferences_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.post("/preferences/reset", response_model=UserPreferencesResponse)
async def reset_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset current user's preferences to defaults.
    
    Default preferences:
    - Email alerts: Enabled
    - SMS alerts: Disabled
    - Browser push: Disabled
    - Daily attendance summary: Enabled
    - Onboarding updates: Enabled
    - Employee confirmations: Enabled
    - Flight risk changes: Disabled
    """
    try:
        service = PreferencesService(db)
        return service.reset_user_preferences(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset preferences: {str(e)}"
        )
