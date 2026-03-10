"""
Contact Inquiry Repository
Database operations for contact inquiries
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta
from app.models.contact_inquiry import ContactInquiry, InquiryStatus, InquirySource
from app.schemas.contact_inquiry import ContactInquiryCreate, ContactInquiryUpdate


class ContactInquiryRepository:
    """Repository for contact inquiry operations"""

    @staticmethod
    def create(db: Session, inquiry_data: ContactInquiryCreate) -> ContactInquiry:
        """Create a new contact inquiry"""
        inquiry = ContactInquiry(**inquiry_data.dict())
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        return inquiry

    @staticmethod
    def get_by_id(db: Session, inquiry_id: int) -> Optional[ContactInquiry]:
        """Get inquiry by ID"""
        return db.query(ContactInquiry).filter(ContactInquiry.id == inquiry_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> List[ContactInquiry]:
        """Get all inquiries by email"""
        return db.query(ContactInquiry).filter(ContactInquiry.email == email).order_by(ContactInquiry.created_at.desc()).all()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[InquiryStatus] = None,
        source: Optional[InquirySource] = None,
        is_spam: Optional[bool] = None,
        is_priority: Optional[bool] = None,
        search: Optional[str] = None,
        assigned_to_id: Optional[int] = None
    ) -> List[ContactInquiry]:
        """Get all inquiries with filters"""
        query = db.query(ContactInquiry)

        if status:
            query = query.filter(ContactInquiry.status == status)
        
        if source:
            query = query.filter(ContactInquiry.source == source)
        
        if is_spam is not None:
            query = query.filter(ContactInquiry.is_spam == is_spam)
        
        if is_priority is not None:
            query = query.filter(ContactInquiry.is_priority == is_priority)
        
        if assigned_to_id:
            query = query.filter(ContactInquiry.assigned_to_id == assigned_to_id)
        
        if search:
            search_filter = or_(
                ContactInquiry.full_name.ilike(f"%{search}%"),
                ContactInquiry.email.ilike(f"%{search}%"),
                ContactInquiry.company_name.ilike(f"%{search}%"),
                ContactInquiry.message.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        return query.order_by(ContactInquiry.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def count(
        db: Session,
        status: Optional[InquiryStatus] = None,
        source: Optional[InquirySource] = None,
        is_spam: Optional[bool] = None,
        is_priority: Optional[bool] = None,
        search: Optional[str] = None,
        assigned_to_id: Optional[int] = None
    ) -> int:
        """Count inquiries with filters"""
        query = db.query(func.count(ContactInquiry.id))

        if status:
            query = query.filter(ContactInquiry.status == status)
        
        if source:
            query = query.filter(ContactInquiry.source == source)
        
        if is_spam is not None:
            query = query.filter(ContactInquiry.is_spam == is_spam)
        
        if is_priority is not None:
            query = query.filter(ContactInquiry.is_priority == is_priority)
        
        if assigned_to_id:
            query = query.filter(ContactInquiry.assigned_to_id == assigned_to_id)
        
        if search:
            search_filter = or_(
                ContactInquiry.full_name.ilike(f"%{search}%"),
                ContactInquiry.email.ilike(f"%{search}%"),
                ContactInquiry.company_name.ilike(f"%{search}%"),
                ContactInquiry.message.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        return query.scalar()

    @staticmethod
    def update(db: Session, inquiry_id: int, inquiry_data: ContactInquiryUpdate) -> Optional[ContactInquiry]:
        """Update an inquiry"""
        inquiry = ContactInquiryRepository.get_by_id(db, inquiry_id)
        if not inquiry:
            return None

        update_data = inquiry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inquiry, field, value)

        db.commit()
        db.refresh(inquiry)
        return inquiry

    @staticmethod
    def delete(db: Session, inquiry_id: int) -> bool:
        """Delete an inquiry"""
        inquiry = ContactInquiryRepository.get_by_id(db, inquiry_id)
        if not inquiry:
            return False

        db.delete(inquiry)
        db.commit()
        return True

    @staticmethod
    def mark_as_spam(db: Session, inquiry_id: int) -> Optional[ContactInquiry]:
        """Mark inquiry as spam"""
        inquiry = ContactInquiryRepository.get_by_id(db, inquiry_id)
        if not inquiry:
            return None

        inquiry.is_spam = True
        inquiry.status = InquiryStatus.SPAM
        db.commit()
        db.refresh(inquiry)
        return inquiry

    @staticmethod
    def mark_as_contacted(db: Session, inquiry_id: int) -> Optional[ContactInquiry]:
        """Mark inquiry as contacted"""
        inquiry = ContactInquiryRepository.get_by_id(db, inquiry_id)
        if not inquiry:
            return None

        inquiry.status = InquiryStatus.CONTACTED
        inquiry.contacted_at = datetime.utcnow()
        db.commit()
        db.refresh(inquiry)
        return inquiry

    @staticmethod
    def get_statistics(db: Session) -> dict:
        """Get inquiry statistics"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return {
            "total_inquiries": db.query(func.count(ContactInquiry.id)).scalar(),
            "new_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.status == InquiryStatus.NEW).scalar(),
            "contacted_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.status == InquiryStatus.CONTACTED).scalar(),
            "qualified_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.status == InquiryStatus.QUALIFIED).scalar(),
            "converted_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.status == InquiryStatus.CONVERTED).scalar(),
            "spam_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.is_spam == True).scalar(),
            "priority_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.is_priority == True).scalar(),
            "today_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.created_at >= today_start).scalar(),
            "this_week_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.created_at >= week_start).scalar(),
            "this_month_inquiries": db.query(func.count(ContactInquiry.id)).filter(ContactInquiry.created_at >= month_start).scalar(),
        }

    @staticmethod
    def check_duplicate(db: Session, email: str, hours: int = 24) -> bool:
        """Check if email submitted inquiry in last X hours"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        count = db.query(func.count(ContactInquiry.id)).filter(
            and_(
                ContactInquiry.email == email,
                ContactInquiry.created_at >= time_threshold,
                ContactInquiry.is_spam == False
            )
        ).scalar()
        return count > 0
