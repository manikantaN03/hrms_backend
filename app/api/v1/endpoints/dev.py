"""
Developer Endpoints
Development and testing utilities (REMOVE IN PRODUCTION)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.get("/get-otp/{email}", response_model=dict, tags=["Developer"])
def get_user_otp(email: str, db: Session = Depends(get_db)):
    """[DEV ONLY] Retrieve the current OTP for a user."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {email}"
        )
    
    if not user.email_otp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active OTP found."
        )

    return {
        "email": user.email,
        "otp": user.email_otp,
        "created_at": user.otp_created_at.isoformat() if user.otp_created_at else None,
        "attempts": user.otp_attempts,
        "is_verified": user.is_email_verified,
        "has_password": bool(user.hashed_password),
        "status": user.status.value,
        "role": user.role.value
    }