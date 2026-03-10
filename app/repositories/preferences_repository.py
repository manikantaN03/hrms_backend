"""
User Preferences Repository
Database operations for user preferences
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.user_preferences import UserPreferences


class PreferencesRepository:
    """Repository for user preferences database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> Optional[UserPreferences]:
        """Get user preferences by user ID"""
        return self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
    
    def create(self, user_id: int, preferences_data: Dict[str, Any]) -> UserPreferences:
        """Create new user preferences"""
        preferences = UserPreferences(
            user_id=user_id,
            **preferences_data
        )
        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
    
    def update(self, preferences: UserPreferences, update_data: Dict[str, Any]) -> UserPreferences:
        """Update existing user preferences"""
        for key, value in update_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
    
    def create_or_update(self, user_id: int, preferences_data: Dict[str, Any]) -> UserPreferences:
        """Create or update user preferences"""
        preferences = self.get_by_user_id(user_id)
        
        if preferences:
            return self.update(preferences, preferences_data)
        else:
            return self.create(user_id, preferences_data)
    
    def delete(self, user_id: int) -> bool:
        """Delete user preferences"""
        preferences = self.get_by_user_id(user_id)
        if preferences:
            self.db.delete(preferences)
            self.db.commit()
            return True
        return False
