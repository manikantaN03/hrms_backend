"""
User Registration Endpoints
Handles admin signup with OTP email verification
"""

from collections import defaultdict
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.user import (
    UnifiedRegistrationRequest,
    UserRegistrationResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    ResendOTPRequest,
    SetPasswordRequest,
    SetPasswordResponse,
)
from app.services.registration_service import RegistrationService

router = APIRouter()

# Rate limiting storage (in-memory)
registration_attempts = defaultdict(list)


def check_rate_limit(request: Request, max_attempts: int = 5, window_minutes: int = 15):
    """
    Prevent registration spam.
    
    Automatically disabled in DEBUG mode.
    
    Args:
        request: FastAPI request object
        max_attempts: Maximum registration attempts allowed
        window_minutes: Time window in minutes
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Skip rate limiting in debug mode
    if settings.DEBUG:
        return
    
    client_ip = request.client.host
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Clean old attempts
    registration_attempts[client_ip] = [
        timestamp for timestamp in registration_attempts[client_ip]
        if now - timestamp < datetime.timedelta(minutes=window_minutes)
    ]
    
    # Check limit
    if len(registration_attempts[client_ip]) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Try again in {window_minutes} minutes."
        )
    
    # Record this attempt
    registration_attempts[client_ip].append(now)


# ============================================================================
# Developer Endpoints (Rate Limit Management)
# ============================================================================

@router.get("/check-rate-limit", tags=["Developer"])
def check_rate_limit_status(request: Request):
    """
    [DEV ONLY] Check current rate limit status.
    
    Shows registration attempts from your IP.
    """
    client_ip = request.client.host
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Clean old attempts
    if client_ip in registration_attempts:
        registration_attempts[client_ip] = [
            timestamp for timestamp in registration_attempts[client_ip]
            if now - timestamp < datetime.timedelta(minutes=15)
        ]
    
    attempts = len(registration_attempts.get(client_ip, []))
    max_attempts = 5
    remaining = max(0, max_attempts - attempts)
    
    return {
        "ip": client_ip,
        "attempts": attempts,
        "max_attempts": max_attempts,
        "remaining_attempts": remaining,
        "is_rate_limited": attempts >= max_attempts,
        "rate_limiting_active": not settings.DEBUG,
        "message": "Rate limited - wait 15 minutes" if attempts >= max_attempts else "OK"
    }


@router.delete("/clear-rate-limit", tags=["Developer"])
def clear_rate_limit(request: Request):
    """
    [DEV ONLY] Clear rate limiting for current IP.
    
    Use this if you get rate limited during development.
    """
    client_ip = request.client.host
    
    cleared = False
    if client_ip in registration_attempts:
        del registration_attempts[client_ip]
        cleared = True
    
    return {
        "message": f"Rate limit cleared for IP: {client_ip}" if cleared else f"No rate limit found for IP: {client_ip}",
        "ip": client_ip,
        "can_register": True
    }


# ============================================================================
# Registration Endpoints
# ============================================================================

@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new admin account"
)
async def register(
    registration_data: UnifiedRegistrationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new admin account.
    
    **Registration Fields:**
    - First Name (required)
    - Last Name (required)
    - Email (required, unique)
    - Mobile (required, unique, 10 digits)
    
    **Registration Flow:**
    1. Submit registration with basic info
    2. Receive 6-digit OTP via email
    3. Verify OTP
    4. Create password
    5. Login
    
    **Example Request:**
    ```json
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "mobile": "9876543210"
    }
    ```
    
    **Rate Limiting:**
    - Disabled in DEBUG mode
    - Production: 5 attempts per 15 minutes per IP
    
    Returns:
        Registration confirmation with OTP sent message
    """
    check_rate_limit(request)
    
    registration_service = RegistrationService(db)
    return await registration_service.register_unified(registration_data)


@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_otp(
    verify_data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code.
    
    **OTP Rules:**
    - Valid for 10 minutes
    - Maximum 5 attempts
    - Must be exactly 6 digits
    
    **Example Request:**
    ```json
    {
        "email": "john@example.com",
        "otp": "123456"
    }
    ```
    
    Returns:
        Verification success message with redirect instruction
    """
    registration_service = RegistrationService(db)
    return registration_service.verify_otp(verify_data)


@router.post("/send-otp", operation_id="send_otp_initial")
async def send_otp(
    otp_data: ResendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Send OTP to user's email (frontend compatible endpoint).
    
    **Rate Limit:** 60-second cooldown between requests.
    
    **Use Cases:**
    - Initial OTP request
    - OTP expired
    - Email not received
    
    Returns:
        Confirmation that OTP was sent
    """
    registration_service = RegistrationService(db)
    return await registration_service.resend_otp(otp_data)


@router.post("/resend-otp")
async def resend_otp(
    resend_data: ResendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Resend OTP to user's email.
    
    **Rate Limit:** 60-second cooldown between requests.
    
    **Use Cases:**
    - OTP expired
    - Email not received
    - Too many failed attempts
    
    Returns:
        Confirmation that new OTP was sent
    """
    registration_service = RegistrationService(db)
    return await registration_service.resend_otp(resend_data)


@router.post("/send-otp-frontend", operation_id="send_otp_frontend_compatible")
async def send_otp_frontend_compatible(
    resend_data: ResendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Send OTP to user's email (frontend compatible endpoint).
    
    This is an alias for /resend-otp to maintain frontend compatibility.
    
    **Rate Limit:** 60-second cooldown between requests.
    
    Returns:
        Confirmation that OTP was sent
    """
    registration_service = RegistrationService(db)
    return await registration_service.resend_otp(resend_data)

#there is a blank line above this line


@router.post("/set-password", response_model=SetPasswordResponse)
def set_password(
    password_data: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Create password after OTP verification.
    
    **Prerequisites:**
    - Email verified with OTP
    - Password not yet set
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    
    After successful password creation, user can login immediately.
    
    Returns:
        Success message with login confirmation
    """
    registration_service = RegistrationService(db)
    return registration_service.set_password(password_data)