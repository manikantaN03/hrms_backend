"""
Profile API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.profile_service import ProfileService
from app.schemas.profile import (
    ProfileBasicInfoUpdate, ProfileAddressUpdate, ProfilePasswordChange,
    ProfileResponse, LoginSessionsResponse, LogoutSessionRequest,
    ProfileUpdateResponse, PasswordChangeResponse
)
import os
import uuid
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    service = ProfileService(db)
    profile = service.get_user_profile(current_user.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.put("/basic-info", response_model=ProfileUpdateResponse)
async def update_basic_info(
    update_data: ProfileBasicInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update basic profile information"""
    service = ProfileService(db)
    result = service.update_basic_info(current_user.id, update_data)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@router.put("/address", response_model=ProfileUpdateResponse)
async def update_address_info(
    update_data: ProfileAddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update address information"""
    service = ProfileService(db)
    result = service.update_address_info(current_user.id, update_data)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_data: ProfilePasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    service = ProfileService(db)
    result = service.change_password(current_user.id, password_data)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@router.get("/sessions", response_model=LoginSessionsResponse)
async def get_login_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user login sessions"""
    service = ProfileService(db)
    return service.get_login_sessions(current_user.id)


@router.post("/logout-session")
async def logout_session(
    logout_data: LogoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout a specific session"""
    service = ProfileService(db)
    result = service.logout_session(current_user.id, logout_data.session_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/upload-image", response_model=ProfileUpdateResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile image"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, JPG, and GIF are allowed."
        )
    
    # Validate file size (4MB limit)
    max_size = 4 * 1024 * 1024  # 4MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum size is 4MB."
        )
    
    try:
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"profile_{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        
        # Ensure upload directory exists
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Update user profile with image path
        service = ProfileService(db)
        relative_path = f"{settings.UPLOAD_DIR}/{unique_filename}"
        result = service.update_profile_image(current_user.id, relative_path)
        
        if not result.success:
            # Clean up uploaded file if database update fails
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading image: {str(e)}"
        )


@router.delete("/image", response_model=ProfileUpdateResponse)
async def remove_profile_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove profile image"""
    service = ProfileService(db)
    
    # Get current profile to find image path
    profile = service.get_user_profile(current_user.id)
    if profile and profile.profile_image:
        # Remove file from filesystem
        try:
            file_path = os.path.join(os.getcwd(), profile.profile_image)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass  # Continue even if file removal fails
    
    # Update database
    result = service.update_profile_image(current_user.id, None)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@router.get("/countries")
async def get_countries():
    """Get list of countries for address dropdown"""
    countries = [
        {"code": "IN", "name": "India"},
        {"code": "US", "name": "USA"},
        {"code": "CA", "name": "Canada"},
        {"code": "DE", "name": "Germany"},
        {"code": "GB", "name": "United Kingdom"},
        {"code": "AU", "name": "Australia"},
        {"code": "FR", "name": "France"},
        {"code": "JP", "name": "Japan"},
        {"code": "SG", "name": "Singapore"},
        {"code": "AE", "name": "United Arab Emirates"}
    ]
    return {"countries": countries}


@router.get("/states")
async def get_states(country_code: str = "IN"):
    """Get list of states for selected country"""
    # Mock data for Indian states
    if country_code == "IN":
        states = [
            {"code": "AP", "name": "Andhra Pradesh"},
            {"code": "AR", "name": "Arunachal Pradesh"},
            {"code": "AS", "name": "Assam"},
            {"code": "BR", "name": "Bihar"},
            {"code": "CG", "name": "Chhattisgarh"},
            {"code": "GA", "name": "Goa"},
            {"code": "GJ", "name": "Gujarat"},
            {"code": "HR", "name": "Haryana"},
            {"code": "HP", "name": "Himachal Pradesh"},
            {"code": "JK", "name": "Jammu and Kashmir"},
            {"code": "JH", "name": "Jharkhand"},
            {"code": "KA", "name": "Karnataka"},
            {"code": "KL", "name": "Kerala"},
            {"code": "MP", "name": "Madhya Pradesh"},
            {"code": "MH", "name": "Maharashtra"},
            {"code": "MN", "name": "Manipur"},
            {"code": "ML", "name": "Meghalaya"},
            {"code": "MZ", "name": "Mizoram"},
            {"code": "NL", "name": "Nagaland"},
            {"code": "OR", "name": "Odisha"},
            {"code": "PB", "name": "Punjab"},
            {"code": "RJ", "name": "Rajasthan"},
            {"code": "SK", "name": "Sikkim"},
            {"code": "TN", "name": "Tamil Nadu"},
            {"code": "TS", "name": "Telangana"},
            {"code": "TR", "name": "Tripura"},
            {"code": "UP", "name": "Uttar Pradesh"},
            {"code": "UK", "name": "Uttarakhand"},
            {"code": "WB", "name": "West Bengal"},
            {"code": "DL", "name": "Delhi"}
        ]
    else:
        # Mock data for other countries
        states = [
            {"code": "ST1", "name": "State 1"},
            {"code": "ST2", "name": "State 2"},
            {"code": "ST3", "name": "State 3"}
        ]
    
    return {"states": states}


@router.get("/cities")
async def get_cities(state_code: str = "TS"):
    """Get list of cities for selected state"""
    # Mock data for Telangana cities
    if state_code == "TS":
        cities = [
            {"code": "HYD", "name": "Hyderabad"},
            {"code": "WGL", "name": "Warangal"},
            {"code": "NZB", "name": "Nizamabad"},
            {"code": "KMM", "name": "Khammam"},
            {"code": "MDK", "name": "Medak"},
            {"code": "RNG", "name": "Rangareddy"},
            {"code": "NLG", "name": "Nalgonda"},
            {"code": "ADL", "name": "Adilabad"},
            {"code": "MBN", "name": "Mahbubnagar"},
            {"code": "KRN", "name": "Karimnagar"}
        ]
    else:
        # Mock data for other states
        cities = [
            {"code": "CT1", "name": "City 1"},
            {"code": "CT2", "name": "City 2"},
            {"code": "CT3", "name": "City 3"}
        ]
    
    return {"cities": cities}