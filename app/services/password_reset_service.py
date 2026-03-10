"""
Password Reset Service
Handles forgot password flow with OTP verification
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from datetime import datetime, timezone

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.otp import otp_manager
from app.core.security import get_password_hash
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class PasswordResetService:
    """
    Handles password reset flow with OTP verification.
    
    Flow:
        1. User requests password reset (provides email)
        2. Generate and send OTP via email
        3. User verifies OTP
        4. User sets new password
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def request_password_reset(self, email: str) -> dict:
        """
        Request password reset - sends OTP to email.
        
        Args:
            email: User's email address
        
        Returns:
            Success message
        
        Raises:
            HTTPException: If user not found or email not verified
        """
        # Check if user exists
        user = self.user_repo.get_by_email(email)
        
        if not user:
            # Don't reveal if email exists for security
            logger.warning(f"Password reset requested for non-existent email: {email}")
            # Still return success to prevent email enumeration
            return {
                "message": f"If an account exists with {email}, you will receive a password reset code.",
                "email": email
            }
        
        # Check if email is verified
        if not user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified. Please complete registration first."
            )
        
        # Check if user has a password set
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No password set. Please complete registration first."
            )
        
        # Check resend cooldown
        if user.otp_created_at:
            can_resend, seconds_remaining = otp_manager.can_resend(user.otp_created_at)
            if not can_resend:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {seconds_remaining} seconds before requesting a new code."
                )
        
        try:
            # Generate new OTP
            otp = otp_manager.generate_otp()
            otp_created_at = datetime.now(timezone.utc)
            
            # Update user with new OTP
            user.email_otp = otp
            user.otp_created_at = otp_created_at
            user.otp_attempts = 0
            self.db.commit()
            
            logger.info(f"Password reset OTP generated for: {email}")
            
            # Send OTP email
            try:
                await email_service.send_password_reset_otp_email(
                    user_email=user.email,
                    user_name=user.name,
                    otp=otp
                )
                logger.info(f"Password reset OTP email sent to: {email}")
            except Exception as email_error:
                logger.error(f"Failed to send password reset email to {email}: {str(email_error)}")
                # Don't fail the request if email fails
            
            return {
                "message": f"Password reset code sent to {email}. Please check your inbox.",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"Password reset request failed for {email}: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process password reset request. Please try again."
            )
    
    def verify_reset_otp(self, email: str, otp: str) -> dict:
        """
        Verify OTP for password reset.
        
        Args:
            email: User's email address
            otp: 6-digit OTP code
        
        Returns:
            Success message with reset token
        
        Raises:
            HTTPException: If verification fails
        """
        user = self.user_repo.get_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        # Validate OTP
        is_valid, error_message = otp_manager.validate(
            stored_otp=user.email_otp,
            provided_otp=otp,
            created_at=user.otp_created_at,
            attempts=user.otp_attempts
        )
        
        if not is_valid:
            # Increment attempts
            user.otp_attempts += 1
            self.db.commit()
            
            logger.warning(f"Invalid password reset OTP for {email}: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # OTP is valid - mark as verified for password reset
        # We'll use a flag to indicate OTP was verified for password reset
        user.otp_attempts = 0
        # Don't clear OTP yet - we'll clear it after password is reset
        self.db.commit()
        
        logger.info(f"Password reset OTP verified for: {email}")
        
        return {
            "message": "OTP verified successfully. You can now reset your password.",
            "email": email,
            "verified": True
        }
    
    def reset_password(self, email: str, otp: str, new_password: str) -> dict:
        """
        Reset password after OTP verification.
        
        Args:
            email: User's email address
            otp: Verified OTP code
            new_password: New password
        
        Returns:
            Success message
        
        Raises:
            HTTPException: If reset fails
        """
        user = self.user_repo.get_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        # Verify OTP one more time for security
        is_valid, error_message = otp_manager.validate(
            stored_otp=user.email_otp,
            provided_otp=otp,
            created_at=user.otp_created_at,
            attempts=user.otp_attempts
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP. Please request a new password reset."
            )
        
        # Validate new password
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long."
            )
        
        try:
            # Update password
            user.hashed_password = get_password_hash(new_password)
            
            # Clear OTP data
            user.email_otp = None
            user.otp_created_at = None
            user.otp_attempts = 0
            
            self.db.commit()
            
            logger.info(f"Password reset successful for: {email}")
            
            return {
                "message": "Password reset successful. You can now login with your new password.",
                "email": email,
                "reset_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Password reset failed for {email}: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password. Please try again."
            )
