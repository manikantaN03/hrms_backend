# server/app/core/tokens.py

"""
Token generation and verification utilities
"""

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from typing import Optional
import secrets
import logging
from datetime import datetime, timedelta, timezone 

from .config import settings

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages secure token generation and verification for email verification
    """
    
    def __init__(self):
        """Initialize token serializer"""
        self.serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        self.salt = "email-verification"
    
    def generate_verification_token(self, email: str) -> str:
        """
        Generate a secure verification token for email verification.
        
        Args:
            email: User's email address
            
        Returns:
            str: Signed verification token
        """
        # Add random string for extra security
        token_data = {
            "email": email,
            "random": secrets.token_urlsafe(16),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        token = self.serializer.dumps(token_data, salt=self.salt)
        logger.info(f"Generated verification token for {email}")
        return token
    
    def verify_token(self, token: str, max_age: Optional[int] = None) -> Optional[str]:
        """
        Verify and decode a verification token.
        
        Args:
            token: Token to verify
            max_age: Maximum age in seconds (defaults to settings)
            
        Returns:
            Optional[str]: Email address if valid, None if invalid/expired
        """
        if max_age is None:
            max_age = settings.VERIFICATION_TOKEN_EXPIRE_HOURS * 3600
        
        try:
            token_data = self.serializer.loads(
                token,
                salt=self.salt,
                max_age=max_age
            )
            email = token_data.get("email")
            logger.info(f"✓ Token verified for {email}")
            return email
            
        except SignatureExpired:
            logger.warning("✗ Token expired")
            return None
            
        except BadSignature:
            logger.warning("✗ Invalid token signature")
            return None
            
        except Exception as e:
            logger.error(f"✗ Token verification error: {str(e)}")
            return None
    
    def get_token_expiry_time(self) -> datetime:
        """
        Get the expiry datetime for a new token.
        
        Returns:
            datetime: Expiry time
        """
        return datetime.now(timezone.utc) + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)


# Singleton instance
token_manager = TokenManager()