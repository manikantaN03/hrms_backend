"""
Password Reset Endpoints
Handles forgot password flow with OTP verification
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ResendResetOTPRequest
)
from app.services.password_reset_service import PasswordResetService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset"
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset - sends OTP to email.
    
    **Flow:**
    1. User provides email
    2. System generates 6-digit OTP
    3. OTP sent to email
    4. User verifies OTP
    5. User sets new password
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    **Security:**
    - Returns success even if email doesn't exist (prevents email enumeration)
    - OTP expires in 10 minutes
    - Maximum 5 verification attempts
    - 60-second cooldown between requests
    
    Returns:
        Success message with email
    """
    try:
        password_reset_service = PasswordResetService(db)
        result = await password_reset_service.request_password_reset(request.email)
        return ForgotPasswordResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post(
    "/verify-reset-otp",
    response_model=VerifyResetOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify password reset OTP"
)
def verify_reset_otp(
    request: VerifyResetOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP for password reset.
    
    **OTP Rules:**
    - Valid for 10 minutes
    - Maximum 5 attempts
    - Must be exactly 6 digits
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "otp": "123456"
    }
    ```
    
    Returns:
        Verification success message
    """
    try:
        password_reset_service = PasswordResetService(db)
        result = password_reset_service.verify_reset_otp(request.email, request.otp)
        return VerifyResetOTPResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify reset OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password"
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password after OTP verification.
    
    **Prerequisites:**
    - OTP must be verified
    - Password must meet requirements
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "otp": "123456",
        "new_password": "NewPass@123",
        "confirm_password": "NewPass@123"
    }
    ```
    
    After successful reset, user can login with new password.
    
    Returns:
        Success message with reset timestamp
    """
    try:
        password_reset_service = PasswordResetService(db)
        result = password_reset_service.reset_password(
            email=request.email,
            otp=request.otp,
            new_password=request.new_password
        )
        return ResetPasswordResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post(
    "/resend-reset-otp",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend password reset OTP"
)
async def resend_reset_otp(
    request: ResendResetOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Resend password reset OTP.
    
    **Rate Limit:** 60-second cooldown between requests.
    
    **Use Cases:**
    - OTP expired
    - Email not received
    - Too many failed attempts
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    Returns:
        Confirmation that new OTP was sent
    """
    try:
        password_reset_service = PasswordResetService(db)
        result = await password_reset_service.request_password_reset(request.email)
        return ForgotPasswordResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend reset OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP"
        )
