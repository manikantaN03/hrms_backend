"""
Admin Service
Business logic for user management in unified table
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
import logging

from app.models.user import User
from app.schemas.user import AdminCreateRequest, AdminUpdateRequest
from app.schemas.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class AdminService:
    """
    Manages user lifecycle in unified table.
    
    Key Principle: All users (superadmins, admins, regular users) are
    stored in the same table and appear in the same lists.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def create_admin(self, admin_data: AdminCreateRequest, created_by_id: int) -> User:
        """
        Create a new admin account.
        
        Created admin will:
        - Be stored in unified users table with role=ADMIN
        - Appear in all user lists (/admins and /users)
        - Have email auto-verified (since created by superadmin)
        
        Args:
            admin_data: Admin registration details
            created_by_id: ID of superadmin creating this account
        
        Returns:
            Created admin user
        """
        # Check for duplicate email
        if self.user_repo.email_exists(admin_data.email):
            logger.warning(f"Admin creation failed - email exists: {admin_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Build admin data
        admin_dict = admin_data.model_dump(exclude={'password', 'confirm_password'})
        admin_dict['hashed_password'] = get_password_hash(admin_data.password)
        admin_dict['role'] = UserRole.ADMIN
        admin_dict['is_email_verified'] = True  # Auto-verified for admin-created accounts
        admin_dict['created_by'] = created_by_id
        
        # Create in unified users table
        new_admin = self.user_repo.create(admin_dict)
        
        logger.info(
            f"Admin created in unified table: {new_admin.email} "
            f"(ID: {new_admin.id}, Role: {new_admin.role.value}, "
            f"Created by: {created_by_id})"
        )
        
        return new_admin
    
    def get_all_admins(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get ALL registered users from unified table.
        
        Important: Despite the method name, this returns ALL users
        (not just admins) because all registered users should appear
        in the same list.
        
        Returns:
            Complete list of all users (all roles)
        """
        all_users = self.user_repo.get_all(skip, limit)
        
        logger.info(
            f"Retrieved {len(all_users)} total users from unified table "
            f"(includes all roles: SUPERADMIN, ADMIN, USER)"
        )
        
        return all_users
    
    def get_admin_by_id(self, user_id: int) -> User:
        """
        Get specific user by ID.
        
        Works for any user type (admin, superadmin, or regular user).
        
        Args:
            user_id: User ID
        
        Returns:
            User object
        
        Raises:
            HTTPException: If user not found
        """
        user = self.user_repo.get(user_id)
        
        if not user:
            logger.warning(f"User not found: ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.debug(f"Retrieved user: {user.email} (Role: {user.role.value})")
        return user
    
    def update_admin(self, user_id: int, admin_data: AdminUpdateRequest) -> User:
        """
        Update user account in unified table.
        
        Can update any user type (admin, superadmin, or regular user).
        
        Args:
            user_id: User ID to update
            admin_data: Updated user details
        
        Returns:
            Updated user object
        
        Raises:
            HTTPException: If user not found or email already taken
        """
        user = self.get_admin_by_id(user_id)
        
        # Check if email changed and is available
        if admin_data.email != user.email:
            if self.user_repo.email_exists(admin_data.email, exclude_id=user_id):
                logger.warning(
                    f"Update failed - email already exists: {admin_data.email}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Build update dictionary
        update_dict = admin_data.model_dump(exclude={'password'})
        
        # Update password only if provided
        if admin_data.password:
            update_dict['hashed_password'] = get_password_hash(admin_data.password)
        
        # Update user
        updated_user = self.user_repo.update(user, update_dict)
        
        logger.info(
            f"User updated in unified table: {updated_user.email} "
            f"(ID: {updated_user.id}, Role: {updated_user.role.value})"
        )
        
        return updated_user
    
    def delete_admin(self, user_id: int) -> None:
        """
        Delete user from unified table.
        
        Args:
            user_id: User ID to delete
        
        Raises:
            HTTPException: If user not found
        """
        user = self.get_admin_by_id(user_id)
        self.user_repo.delete(user_id)
        
        logger.info(
            f"User deleted from unified table: {user.email} "
            f"(ID: {user.id}, Role: {user.role.value})"
        )