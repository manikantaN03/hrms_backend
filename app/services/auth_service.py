"""
Authentication Service
Handles user login and token generation with session management
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
import logging

from app.models.user import User
from app.schemas.user import AdminResponse
from app.schemas.token import LoginRequest, TokenResponse
from app.schemas.enums import UserStatus
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.core.session import session_manager

logger = logging.getLogger(__name__)


class AuthService:
    """Manages user authentication and session creation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Verify user credentials.
        
        Args:
            email: User's email address
            password: Plain text password
        
        Returns:
            User object if credentials valid, None otherwise
        """
        logger.info(f"Authentication attempt for: {email}")
        
        user = self.user_repo.get_by_email(email)
        if not user:
            logger.warning(f"User not found: {email}")
            return None
        
        if not user.hashed_password:
            logger.warning(f"User has no password (pending OTP verification): {email}")
            return None
        
        if not user.is_email_verified:
            logger.warning(f"Email not verified: {email}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for: {email}")
            return None
        
        logger.info(f"Authentication successful: {email}")
        return user
    
    def login(self, login_data: LoginRequest) -> TokenResponse:
        """
        Process user login and generate access token with session.
        
        Args:
            login_data: Email and password credentials
        
        Returns:
            JWT token and user information
        
        Raises:
            HTTPException: If credentials invalid or account restricted
        """
        # Authenticate user
        user = self.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in."
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}. Please contact administrator."
            )
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value}
        )
        
        # Create session in Redis
        user_data = {
            'email': user.email,
            'role': user.role.value,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        
        session_created = session_manager.create_session(
            user_id=user.id,
            token=access_token,
            user_data=user_data
        )
        
        if session_created:
            logger.info(f"Session created for user {user.id}")
        else:
            logger.warning(f"Session creation failed for user {user.id} (Redis unavailable)")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=AdminResponse.from_user(user)
        )
    
    def logout(self, user_id: int, token: str) -> dict:
        """
        Logout user and invalidate session.
        
        Args:
            user_id: User ID
            token: Current access token
        
        Returns:
            Logout confirmation message
        """
        # Delete session
        session_manager.delete_session(token)
        
        # Blacklist token
        session_manager.blacklist_token(token)
        
        logger.info(f"User {user_id} logged out")
        
        return {
            "message": "Successfully logged out",
            "user_id": user_id
        }
    
    def logout_all_devices(self, user_id: int) -> dict:
        """
        Logout user from all devices.
        
        Args:
            user_id: User ID
        
        Returns:
            Logout confirmation with session count
        """
        # Get active sessions count
        sessions = session_manager.get_user_sessions(user_id)
        session_count = len(sessions)
        
        # Delete all user sessions
        session_manager.delete_all_user_sessions(user_id)
        
        # Blacklist all tokens
        for token in sessions:
            session_manager.blacklist_token(token)
        
        logger.info(f"User {user_id} logged out from {session_count} devices")
        
        return {
            "message": f"Logged out from {session_count} device(s)",
            "user_id": user_id,
            "sessions_terminated": session_count
        }