"""
User Repository
Data access layer for user operations
"""

from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.user import User
from ..schemas.enums import UserRole, UserStatus
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.
        
        Args:
            email: User's email
        
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_mobile(self, mobile: str) -> Optional[User]:
        """
        Find user by mobile number.
        
        Args:
            mobile: User's mobile number
        
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.mobile == mobile).first()
    
    def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            role: User role to filter by
            skip: Number of records to skip (pagination)
            limit: Maximum records to return
        
        Returns:
            List of users with the specified role
        """
        return (
            self.db.query(User)
            .filter(User.role == role)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.
        
        Args:
            skip: Pagination offset
            limit: Maximum records
        
        Returns:
            List of active users
        """
        return (
            self.db.query(User)
            .filter(User.status == UserStatus.ACTIVE)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if email is already registered.
        
        Args:
            email: Email to check
            exclude_id: User ID to exclude from check (for updates)
        
        Returns:
            True if email exists, False otherwise
        """
        query = self.db.query(User).filter(User.email == email)
        
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        
        return query.first() is not None
    
    def mobile_exists(self, mobile: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if mobile number is already registered.
        
        Args:
            mobile: Mobile number to check
            exclude_id: User ID to exclude from check (for updates)
        
        Returns:
            True if mobile exists, False otherwise
        """
        query = self.db.query(User).filter(User.mobile == mobile)
        
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        
        return query.first() is not None