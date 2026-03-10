"""
Contact Inquiry Service
Business logic for contact inquiries
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status
from app.repositories.contact_inquiry_repository import ContactInquiryRepository
from app.schemas.contact_inquiry import (
    ContactInquiryCreate,
    ContactInquiryUpdate,
    ContactInquiryResponse,
    ContactInquiryList,
    ContactInquiryStats
)
from app.models.contact_inquiry import InquiryStatus, InquirySource
import logging

logger = logging.getLogger(__name__)


class ContactInquiryService:
    """Service for contact inquiry operations"""

    @staticmethod
    def create_inquiry(db: Session, inquiry_data: ContactInquiryCreate) -> ContactInquiryResponse:
        """Create a new contact inquiry"""
        try:
            # Check for duplicate submissions (spam prevention)
            if ContactInquiryRepository.check_duplicate(db, inquiry_data.email, hours=24):
                logger.warning(f"Duplicate inquiry attempt from email: {inquiry_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="You have already submitted an inquiry recently. Please wait 24 hours before submitting again."
                )

            # Create inquiry
            inquiry = ContactInquiryRepository.create(db, inquiry_data)
            logger.info(f"Created new inquiry: ID={inquiry.id}, Email={inquiry.email}, Company={inquiry.company_name}")

            # TODO: Send email notification to sales team
            # TODO: Send confirmation email to customer
            
            return ContactInquiryResponse.from_orm(inquiry)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating inquiry: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit inquiry. Please try again later."
            )

    @staticmethod
    def get_inquiry(db: Session, inquiry_id: int) -> ContactInquiryResponse:
        """Get inquiry by ID"""
        inquiry = ContactInquiryRepository.get_by_id(db, inquiry_id)
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry with ID {inquiry_id} not found"
            )
        return ContactInquiryResponse.from_orm(inquiry)

    @staticmethod
    def get_inquiries(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[InquiryStatus] = None,
        source: Optional[InquirySource] = None,
        is_spam: Optional[bool] = None,
        is_priority: Optional[bool] = None,
        search: Optional[str] = None,
        assigned_to_id: Optional[int] = None
    ) -> ContactInquiryList:
        """Get all inquiries with filters"""
        inquiries = ContactInquiryRepository.get_all(
            db, skip, limit, status, source, is_spam, is_priority, search, assigned_to_id
        )
        total = ContactInquiryRepository.count(
            db, status, source, is_spam, is_priority, search, assigned_to_id
        )
        
        return ContactInquiryList(
            total=total,
            items=[ContactInquiryResponse.from_orm(inquiry) for inquiry in inquiries]
        )

    @staticmethod
    def update_inquiry(db: Session, inquiry_id: int, inquiry_data: ContactInquiryUpdate) -> ContactInquiryResponse:
        """Update an inquiry"""
        inquiry = ContactInquiryRepository.update(db, inquiry_id, inquiry_data)
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry with ID {inquiry_id} not found"
            )
        
        logger.info(f"Updated inquiry: ID={inquiry_id}")
        return ContactInquiryResponse.from_orm(inquiry)

    @staticmethod
    def delete_inquiry(db: Session, inquiry_id: int) -> dict:
        """Delete an inquiry"""
        success = ContactInquiryRepository.delete(db, inquiry_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry with ID {inquiry_id} not found"
            )
        
        logger.info(f"Deleted inquiry: ID={inquiry_id}")
        return {"message": "Inquiry deleted successfully"}

    @staticmethod
    def mark_as_spam(db: Session, inquiry_id: int) -> ContactInquiryResponse:
        """Mark inquiry as spam"""
        inquiry = ContactInquiryRepository.mark_as_spam(db, inquiry_id)
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry with ID {inquiry_id} not found"
            )
        
        logger.info(f"Marked inquiry as spam: ID={inquiry_id}")
        return ContactInquiryResponse.from_orm(inquiry)

    @staticmethod
    def mark_as_contacted(db: Session, inquiry_id: int) -> ContactInquiryResponse:
        """Mark inquiry as contacted"""
        inquiry = ContactInquiryRepository.mark_as_contacted(db, inquiry_id)
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry with ID {inquiry_id} not found"
            )
        
        logger.info(f"Marked inquiry as contacted: ID={inquiry_id}")
        return ContactInquiryResponse.from_orm(inquiry)

    @staticmethod
    def get_statistics(db: Session) -> ContactInquiryStats:
        """Get inquiry statistics"""
        stats = ContactInquiryRepository.get_statistics(db)
        return ContactInquiryStats(**stats)

    @staticmethod
    def get_inquiries_by_email(db: Session, email: str) -> List[ContactInquiryResponse]:
        """Get all inquiries by email"""
        inquiries = ContactInquiryRepository.get_by_email(db, email)
        return [ContactInquiryResponse.from_orm(inquiry) for inquiry in inquiries]
