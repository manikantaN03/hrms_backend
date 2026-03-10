"""
User Preferences Service
Business logic for user preferences management
"""

from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status

from app.repositories.preferences_repository import PreferencesRepository
from app.schemas.preferences import (
    UserPreferencesCreate,
    UserPreferencesUpdate,
    UserPreferencesResponse
)
from app.models.user import User


class PreferencesService:
    """Service for user preferences business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = PreferencesRepository(db)
    
    def get_user_preferences(self, user_id: int) -> UserPreferencesResponse:
        """
        Get user preferences by user ID.
        If preferences don't exist, create default preferences.
        """
        preferences = self.repository.get_by_user_id(user_id)
        
        if not preferences:
            # Create default preferences
            default_data = UserPreferencesCreate().model_dump()
            preferences = self.repository.create(user_id, default_data)
        
        return UserPreferencesResponse.model_validate(preferences)
    
    def update_user_preferences(
        self,
        user_id: int,
        preferences_data: UserPreferencesUpdate
    ) -> UserPreferencesResponse:
        """Update user preferences"""
        
        # Get or create preferences
        preferences = self.repository.get_by_user_id(user_id)
        
        if not preferences:
            # Create new preferences with provided data
            create_data = UserPreferencesCreate().model_dump()
            update_dict = preferences_data.model_dump(exclude_unset=True)
            create_data.update(update_dict)
            preferences = self.repository.create(user_id, create_data)
        else:
            # Update existing preferences
            update_dict = preferences_data.model_dump(exclude_unset=True)
            if update_dict:
                preferences = self.repository.update(preferences, update_dict)
        
        return UserPreferencesResponse.model_validate(preferences)
    
    def reset_user_preferences(self, user_id: int) -> UserPreferencesResponse:
        """Reset user preferences to defaults"""
        
        default_data = UserPreferencesCreate().model_dump()
        preferences = self.repository.create_or_update(user_id, default_data)
        
        return UserPreferencesResponse.model_validate(preferences)
