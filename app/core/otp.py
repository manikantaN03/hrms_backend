"""
OTP (One-Time Password) Management
Handles generation, validation, and expiry of email verification codes
"""

import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class OTPManager:
    """Manages OTP lifecycle for email verification."""
    
    # Configuration constants
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 5
    RESEND_COOLDOWN_SECONDS = 60
    
    def generate_otp(self) -> str:
        """
        Generate a secure 6-digit OTP.
        
        Returns:
            6-digit numeric string
        """
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(self.OTP_LENGTH)])
        logger.info(f"OTP generated (first 2 digits): {otp[:2]}****")
        return otp
    
    def get_expiry_time(self) -> datetime:
        """
        Calculate expiry time for a new OTP.
        
        Returns:
            Datetime when OTP will expire
        """
        return datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
    
    def is_expired(self, created_at: datetime) -> bool:
        """
        Check if an OTP has expired.
        
        Args:
            created_at: When the OTP was created
        
        Returns:
            True if expired, False if still valid
        """
        if not created_at:
            return True
        
        expiry_time = created_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        return datetime.now(timezone.utc) > expiry_time
    
    def can_resend(self, last_sent_at: Optional[datetime]) -> Tuple[bool, int]:
        """
        Check if enough time has passed to resend OTP.
        
        Args:
            last_sent_at: When the last OTP was sent
        
        Returns:
            Tuple of (can_resend: bool, seconds_remaining: int)
        """
        if not last_sent_at:
            return True, 0
        
        elapsed = (datetime.now(timezone.utc) - last_sent_at).total_seconds()
        
        if elapsed >= self.RESEND_COOLDOWN_SECONDS:
            return True, 0
        
        remaining = int(self.RESEND_COOLDOWN_SECONDS - elapsed)
        return False, remaining
    
    def validate(
        self,
        stored_otp: str,
        provided_otp: str,
        created_at: datetime,
        attempts: int
    ) -> Tuple[bool, str]:
        """
        Validate an OTP with comprehensive checks.
        
        Args:
            stored_otp: OTP stored in database
            provided_otp: OTP entered by user
            created_at: When OTP was created
            attempts: Number of failed attempts so far
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check 1: OTP exists
        if not stored_otp:
            return False, "No OTP found. Please request a new verification code."
        
        # Check 2: Not too many attempts
        if attempts >= self.MAX_ATTEMPTS:
            return False, "Too many failed attempts. Please request a new OTP."
        
        # Check 3: Not expired
        if self.is_expired(created_at):
            return False, "OTP has expired. Please request a new one."
        
        # Check 4: OTP matches
        if stored_otp != provided_otp:
            remaining = self.MAX_ATTEMPTS - attempts - 1
            return False, f"Invalid OTP. {remaining} attempts remaining."
        
        return True, "OTP verified successfully"


# Singleton instance
otp_manager = OTPManager()