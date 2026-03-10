"""
Contact Inquiry API Endpoints
Public and admin endpoints for contact/demo requests
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.api.v1.deps import get_db, get_current_user
from app.services.contact_inquiry_service import ContactInquiryService
from app.schemas.contact_inquiry import (
    ContactInquiryCreate,
    ContactInquiryUpdate,
    ContactInquiryResponse,
    ContactInquiryList,
    ContactInquiryStats
)
from app.models.contact_inquiry import InquiryStatus, InquirySource
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ============================================================================

@router.post("/public/submit", response_model=ContactInquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_contact_inquiry(
    inquiry: ContactInquiryCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit a contact/demo request from landing page (PUBLIC - No Auth Required)
    
    This endpoint is publicly accessible for landing page form submissions.
    """
    try:
        # Capture request metadata
        inquiry.ip_address = request.client.host if request.client else None
        inquiry.user_agent = request.headers.get("user-agent")
        inquiry.referrer_url = request.headers.get("referer")
        
        # Create inquiry
        result = ContactInquiryService.create_inquiry(db, inquiry)
        
        logger.info(f"Public inquiry submitted: {inquiry.email} from {inquiry.company_name}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in public inquiry submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit inquiry. Please try again later."
        )


# ============================================================================
# ADMIN ENDPOINTS (Authentication Required)
# ============================================================================

@router.get("/", response_model=ContactInquiryList)
def get_all_inquiries(
    skip: int = 0,
    limit: int = 100,
    status: Optional[InquiryStatus] = None,
    source: Optional[InquirySource] = None,
    is_spam: Optional[bool] = None,
    is_priority: Optional[bool] = None,
    search: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all contact inquiries with filters (ADMIN)
    
    Filters:
    - status: Filter by inquiry status
    - source: Filter by inquiry source
    - is_spam: Filter spam inquiries
    - is_priority: Filter priority inquiries
    - search: Search in name, email, company, message
    - assigned_to_id: Filter by assigned user
    """
    return ContactInquiryService.get_inquiries(
        db, skip, limit, status, source, is_spam, is_priority, search, assigned_to_id
    )


@router.get("/statistics", response_model=ContactInquiryStats)
def get_inquiry_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get contact inquiry statistics (ADMIN)
    
    Returns counts for:
    - Total inquiries
    - New, contacted, qualified, converted inquiries
    - Spam and priority inquiries
    - Today, this week, this month inquiries
    """
    return ContactInquiryService.get_statistics(db)


@router.get("/{inquiry_id}", response_model=ContactInquiryResponse)
def get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific inquiry by ID (ADMIN)
    """
    return ContactInquiryService.get_inquiry(db, inquiry_id)


@router.put("/{inquiry_id}", response_model=ContactInquiryResponse)
def update_inquiry(
    inquiry_id: int,
    inquiry_data: ContactInquiryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an inquiry (ADMIN)
    
    Can update:
    - status
    - assigned_to_id
    - contacted_at
    - follow_up_date
    - notes
    - is_spam
    - is_priority
    """
    return ContactInquiryService.update_inquiry(db, inquiry_id, inquiry_data)


@router.delete("/{inquiry_id}")
def delete_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an inquiry (ADMIN)
    """
    return ContactInquiryService.delete_inquiry(db, inquiry_id)


@router.post("/{inquiry_id}/mark-spam", response_model=ContactInquiryResponse)
def mark_inquiry_as_spam(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an inquiry as spam (ADMIN)
    """
    return ContactInquiryService.mark_as_spam(db, inquiry_id)


@router.post("/{inquiry_id}/mark-contacted", response_model=ContactInquiryResponse)
def mark_inquiry_as_contacted(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an inquiry as contacted (ADMIN)
    """
    return ContactInquiryService.mark_as_contacted(db, inquiry_id)


@router.get("/email/{email}", response_model=list[ContactInquiryResponse])
def get_inquiries_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all inquiries by email address (ADMIN)
    """
    return ContactInquiryService.get_inquiries_by_email(db, email)
