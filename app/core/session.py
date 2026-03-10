"""
Session Management with Redis
Handles user sessions, token blacklisting, and active session tracking
"""

from datetime import timedelta
from typing import Optional, List, Dict
import json
import logging

from .redis_client import get_redis
from .config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions using Redis"""
    
    def __init__(self):
        self.redis = get_redis()
        self.session_prefix = "session:"
        self.blacklist_prefix = "blacklist:"
        self.user_sessions_prefix = "user_sessions:"
    
    def _is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis is not None
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    def create_session(
        self, 
        user_id: int, 
        token: str, 
        user_data: dict,
        expires_in_minutes: Optional[int] = None
    ) -> bool:
        """
        Create a new user session.
        
        Args:
            user_id: User ID
            token: JWT access token
            user_data: User information (email, role, etc.)
            expires_in_minutes: Session expiration time
        
        Returns:
            True if session created successfully
        """
        if not self._is_available():
            logger.warning("Redis not available, skipping session creation")
            return False
        
        try:
            expires = expires_in_minutes or settings.SESSION_EXPIRE_MINUTES
            
            # Session data
            session_data = {
                'user_id': user_id,
                'token': token,
                'email': user_data.get('email'),
                'role': user_data.get('role'),
                'created_at': user_data.get('created_at'),
            }
            
            # Store session with token as key
            session_key = f"{self.session_prefix}{token}"
            self.redis.setex(
                session_key,
                timedelta(minutes=expires),
                json.dumps(session_data)
            )
            
            # Track active sessions for user
            self._add_user_session(user_id, token, expires)
            
            logger.info(f"Session created for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    def get_session(self, token: str) -> Optional[Dict]:
        """
        Get session data by token.
        
        Args:
            token: JWT access token
        
        Returns:
            Session data dictionary or None
        """
        if not self._is_available():
            return None
        
        try:
            session_key = f"{self.session_prefix}{token}"
            session_data = self.redis.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def delete_session(self, token: str) -> bool:
        """
        Delete a session.
        
        Args:
            token: JWT access token
        
        Returns:
            True if session deleted
        """
        if not self._is_available():
            return False
        
        try:
            # Get session to find user_id
            session = self.get_session(token)
            
            # Delete session
            session_key = f"{self.session_prefix}{token}"
            self.redis.delete(session_key)
            
            # Remove from user's active sessions
            if session:
                user_id = session.get('user_id')
                if user_id:
                    self._remove_user_session(user_id, token)
            
            logger.info(f"Session deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def refresh_session(self, token: str, expires_in_minutes: Optional[int] = None) -> bool:
        """
        Refresh session expiration time.
        
        Args:
            token: JWT access token
            expires_in_minutes: New expiration time
        
        Returns:
            True if refreshed successfully
        """
        if not self._is_available():
            return False
        
        try:
            session_key = f"{self.session_prefix}{token}"
            expires = expires_in_minutes or settings.SESSION_EXPIRE_MINUTES
            
            # Refresh expiration
            self.redis.expire(session_key, timedelta(minutes=expires))
            
            logger.info(f"Session refreshed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh session: {e}")
            return False
    
    # ========================================================================
    # User Active Sessions Tracking
    # ========================================================================
    
    def _add_user_session(self, user_id: int, token: str, expires_in_minutes: int):
        """Add token to user's active sessions list"""
        try:
            sessions_key = f"{self.user_sessions_prefix}{user_id}"
            
            # Add token to set
            self.redis.sadd(sessions_key, token)
            
            # Set expiration on the set itself
            self.redis.expire(sessions_key, timedelta(minutes=expires_in_minutes))
            
        except Exception as e:
            logger.error(f"Failed to track user session: {e}")
    
    def _remove_user_session(self, user_id: int, token: str):
        """Remove token from user's active sessions"""
        try:
            sessions_key = f"{self.user_sessions_prefix}{user_id}"
            self.redis.srem(sessions_key, token)
            
        except Exception as e:
            logger.error(f"Failed to remove user session: {e}")
    
    def get_user_sessions(self, user_id: int) -> List[str]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of active tokens
        """
        if not self._is_available():
            return []
        
        try:
            sessions_key = f"{self.user_sessions_prefix}{user_id}"
            tokens = self.redis.smembers(sessions_key)
            return list(tokens) if tokens else []
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def delete_all_user_sessions(self, user_id: int) -> bool:
        """
        Delete all sessions for a user (force logout from all devices).
        
        Args:
            user_id: User ID
        
        Returns:
            True if all sessions deleted
        """
        if not self._is_available():
            return False
        
        try:
            # Get all user's tokens
            tokens = self.get_user_sessions(user_id)
            
            # Delete each session
            for token in tokens:
                session_key = f"{self.session_prefix}{token}"
                self.redis.delete(session_key)
            
            # Delete user sessions set
            sessions_key = f"{self.user_sessions_prefix}{user_id}"
            self.redis.delete(sessions_key)
            
            logger.info(f"Deleted {len(tokens)} sessions for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user sessions: {e}")
            return False
    
    # ========================================================================
    # Token Blacklisting (for immediate invalidation)
    # ========================================================================
    
    def blacklist_token(self, token: str, expires_in_minutes: Optional[int] = None) -> bool:
        """
        Add token to blacklist (for logout/revocation).
        
        Args:
            token: JWT access token
            expires_in_minutes: How long to keep in blacklist
        
        Returns:
            True if blacklisted successfully
        """
        if not self._is_available():
            return False
        
        try:
            expires = expires_in_minutes or settings.SESSION_EXPIRE_MINUTES
            blacklist_key = f"{self.blacklist_prefix}{token}"
            
            self.redis.setex(
                blacklist_key,
                timedelta(minutes=expires),
                "1"
            )
            
            logger.info("Token blacklisted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            token: JWT access token
        
        Returns:
            True if token is blacklisted
        """
        if not self._is_available():
            return False
        
        try:
            blacklist_key = f"{self.blacklist_prefix}{token}"
            return self.redis.exists(blacklist_key) > 0
            
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            return False
    
    # ========================================================================
    # Session Statistics
    # ========================================================================
    
    def get_active_sessions_count(self) -> int:
        """Get total number of active sessions"""
        if not self._is_available():
            return 0
        
        try:
            pattern = f"{self.session_prefix}*"
            keys = self.redis.keys(pattern)
            return len(keys)
            
        except Exception as e:
            logger.error(f"Failed to count sessions: {e}")
            return 0
    
    def get_session_info(self, user_id: int) -> Dict:
        """
        Get session information for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with session info
        """
        if not self._is_available():
            return {
                'active_sessions': 0,
                'sessions': [],
                'redis_available': False
            }
        
        try:
            tokens = self.get_user_sessions(user_id)
            sessions = []
            
            for token in tokens:
                session = self.get_session(token)
                if session:
                    sessions.append({
                        'token_preview': token[:20] + '...',
                        'email': session.get('email'),
                        'role': session.get('role'),
                        'created_at': session.get('created_at')
                    })
            
            return {
                'active_sessions': len(sessions),
                'sessions': sessions,
                'redis_available': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {
                'active_sessions': 0,
                'sessions': [],
                'redis_available': False,
                'error': str(e)
            }


# Global session manager instance
session_manager = SessionManager()