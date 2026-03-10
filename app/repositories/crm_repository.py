"""
CRM Repository
Data access layer for CRM operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from app.models.crm import (
    CRMCompany, CRMContact, CRMDeal, CRMActivity, CRMPipeline,
    ContactType, LeadStatus, DealStage, ActivityType, Priority
)
from app.schemas.crm import (
    CRMCompanyCreate, CRMCompanyUpdate,
    CRMContactCreate, CRMContactUpdate,
    CRMDealCreate, CRMDealUpdate,
    CRMActivityCreate, CRMActivityUpdate,
    CRMPipelineCreate, CRMPipelineUpdate
)


class CRMCompanyRepository:
    """Repository for CRM Company operations"""
    
    @staticmethod
    def create(db: Session, company_data: CRMCompanyCreate, user_id: int, business_id: int) -> CRMCompany:
        """Create a new company"""
        company = CRMCompany(
            **company_data.dict(),
            business_id=business_id,
            created_by=user_id
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company
    
    @staticmethod
    def get_by_id(db: Session, company_id: int, business_id: int) -> Optional[CRMCompany]:
        """Get company by ID with relationships"""
        return db.query(CRMCompany).options(
            joinedload(CRMCompany.owner)
        ).filter(
            CRMCompany.id == company_id,
            CRMCompany.business_id == business_id
        ).first()
    
    @staticmethod
    def get_all(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[CRMCompany], int]:
        """Get companies with filtering and pagination - optimized for performance"""
        
        # Limit the maximum number of records to prevent performance issues
        if limit > 100:
            limit = 100
            
        # Base query with minimal joins for performance
        query = db.query(CRMCompany).filter(CRMCompany.business_id == business_id)
        
        # Default to active companies only (exclude soft-deleted ones)
        if is_active is None:
            query = query.filter(CRMCompany.is_active == True)
        else:
            query = query.filter(CRMCompany.is_active == is_active)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    CRMCompany.name.ilike(search_term),
                    CRMCompany.email.ilike(search_term),
                    CRMCompany.website.ilike(search_term)
                )
            )
        
        if industry:
            query = query.filter(CRMCompany.industry == industry)
        
        if is_active is not None:
            query = query.filter(CRMCompany.is_active == is_active)
        
        # Get total count efficiently - use a separate optimized query
        try:
            # Use a more efficient count query
            count_query = db.query(func.count(CRMCompany.id))
            
            # Default to active companies only (exclude soft-deleted ones)
            if is_active is None:
                count_query = count_query.filter(CRMCompany.is_active == True)
            else:
                count_query = count_query.filter(CRMCompany.is_active == is_active)
            
            # Apply same filters to count query
            if search:
                search_term = f"%{search}%"
                count_query = count_query.filter(
                    or_(
                        CRMCompany.name.ilike(search_term),
                        CRMCompany.email.ilike(search_term),
                        CRMCompany.website.ilike(search_term)
                    )
                )
            
            if industry:
                count_query = count_query.filter(CRMCompany.industry == industry)
            
            total = count_query.scalar() or 0
        except Exception as e:
            print(f"Count query error: {e}")
            total = 0
        
        # Get companies with pagination and ordering
        try:
            companies = query.order_by(CRMCompany.name).offset(skip).limit(limit).all()
        except Exception as e:
            print(f"Companies query error: {e}")
            companies = []
        
        return companies, total
    
    @staticmethod
    def update(
        db: Session,
        company_id: int,
        business_id: int,
        company_data: CRMCompanyUpdate,
        user_id: int
    ) -> Optional[CRMCompany]:
        """Update company"""
        company = db.query(CRMCompany).filter(
            CRMCompany.id == company_id,
            CRMCompany.business_id == business_id
        ).first()
        if not company:
            return None
        
        update_data = company_data.dict(exclude_unset=True)
        if update_data:
            update_data['updated_by'] = user_id
            for field, value in update_data.items():
                setattr(company, field, value)
            
            db.commit()
            db.refresh(company)
        
        return company
    
    @staticmethod
    def delete(db: Session, company_id: int, business_id: int) -> bool:
        """Delete company (soft delete)"""
        company = db.query(CRMCompany).filter(
            CRMCompany.id == company_id,
            CRMCompany.business_id == business_id
        ).first()
        if not company:
            return False
        
        company.is_active = False
        db.commit()
        return True


class CRMContactRepository:
    """Repository for CRM Contact operations"""
    
    @staticmethod
    def create(db: Session, contact_data: CRMContactCreate, user_id: int, business_id: int) -> CRMContact:
        """Create a new contact"""
        try:
            # Validate company_id if provided
            if contact_data.company_id:
                from app.models.crm import CRMCompany
                company = db.query(CRMCompany).filter(
                    CRMCompany.id == contact_data.company_id,
                    CRMCompany.business_id == business_id
                ).first()
                if not company:
                    raise ValueError(f"Company with ID {contact_data.company_id} does not exist")
            
            # Validate owner_id if provided
            if contact_data.owner_id:
                from app.models.user import User
                owner = db.query(User).filter(User.id == contact_data.owner_id).first()
                if not owner:
                    raise ValueError(f"User with ID {contact_data.owner_id} does not exist")
            
            contact = CRMContact(
                **contact_data.dict(),
                business_id=business_id,
                created_by=user_id
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)
            return contact
        except IntegrityError as e:
            db.rollback()
            if "duplicate key value" in str(e) and "email" in str(e):
                raise ValueError(f"A contact with email '{contact_data.email}' already exists")
            elif "foreign key constraint" in str(e).lower():
                # Extract which foreign key failed
                if "company_id" in str(e):
                    raise ValueError(f"Invalid company_id: Company does not exist")
                elif "owner_id" in str(e):
                    raise ValueError(f"Invalid owner_id: User does not exist")
                else:
                    raise ValueError(f"Foreign key constraint violation: {str(e)}")
            else:
                raise e
        except ValueError:
            # Re-raise validation errors
            db.rollback()
            raise
    
    @staticmethod
    def get_by_id(db: Session, contact_id: int, business_id: int) -> Optional[CRMContact]:
        """Get contact by ID with relationships"""
        return db.query(CRMContact).options(
            joinedload(CRMContact.company),
            joinedload(CRMContact.owner)
        ).filter(
            CRMContact.id == contact_id,
            CRMContact.business_id == business_id
        ).first()
    
    @staticmethod
    def get_all(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        contact_type: Optional[ContactType] = None,
        lead_status: Optional[LeadStatus] = None,
        company_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[CRMContact], int]:
        """Get contacts with filtering and pagination"""
        query = db.query(CRMContact).options(
            joinedload(CRMContact.company),
            joinedload(CRMContact.owner)
        ).filter(CRMContact.business_id == business_id)
        
        # Default to active contacts only (exclude soft-deleted ones)
        if is_active is None:
            query = query.filter(CRMContact.is_active == True)
        else:
            query = query.filter(CRMContact.is_active == is_active)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    CRMContact.first_name.ilike(f"%{search}%"),
                    CRMContact.last_name.ilike(f"%{search}%"),
                    CRMContact.email.ilike(f"%{search}%"),
                    CRMContact.phone.ilike(f"%{search}%"),
                    CRMContact.mobile.ilike(f"%{search}%")
                )
            )
        
        if contact_type:
            query = query.filter(CRMContact.contact_type == contact_type)
        
        if lead_status:
            query = query.filter(CRMContact.lead_status == lead_status)
        
        if company_id:
            query = query.filter(CRMContact.company_id == company_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        contacts = query.order_by(CRMContact.first_name, CRMContact.last_name).offset(skip).limit(limit).all()
        
        return contacts, total
    
    @staticmethod
    def update(
        db: Session,
        contact_id: int,
        business_id: int,
        contact_data: CRMContactUpdate,
        user_id: int
    ) -> Optional[CRMContact]:
        """Update contact"""
        try:
            contact = db.query(CRMContact).filter(
                CRMContact.id == contact_id,
                CRMContact.business_id == business_id
            ).first()
            if not contact:
                return None
            
            update_data = contact_data.dict(exclude_unset=True)
            
            # Validate company_id if being updated
            if 'company_id' in update_data and update_data['company_id']:
                from app.models.crm import CRMCompany
                company = db.query(CRMCompany).filter(
                    CRMCompany.id == update_data['company_id'],
                    CRMCompany.business_id == business_id
                ).first()
                if not company:
                    raise ValueError(f"Company with ID {update_data['company_id']} does not exist")
            
            # Validate owner_id if being updated
            if 'owner_id' in update_data and update_data['owner_id']:
                from app.models.user import User
                owner = db.query(User).filter(User.id == update_data['owner_id']).first()
                if not owner:
                    raise ValueError(f"User with ID {update_data['owner_id']} does not exist")
            
            if update_data:
                update_data['updated_by'] = user_id
                for field, value in update_data.items():
                    setattr(contact, field, value)
                
                db.commit()
                db.refresh(contact)
            
            return contact
        except IntegrityError as e:
            db.rollback()
            if "duplicate key value" in str(e) and "email" in str(e):
                raise ValueError(f"A contact with email '{contact_data.email}' already exists")
            elif "foreign key constraint" in str(e).lower():
                # Extract which foreign key failed
                if "company_id" in str(e):
                    raise ValueError(f"Invalid company_id: Company does not exist")
                elif "owner_id" in str(e):
                    raise ValueError(f"Invalid owner_id: User does not exist")
                else:
                    raise ValueError(f"Foreign key constraint violation: {str(e)}")
            else:
                raise e
        except ValueError:
            # Re-raise validation errors
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete(db: Session, contact_id: int, business_id: int) -> bool:
        """Delete contact (soft delete)"""
        contact = db.query(CRMContact).filter(
            CRMContact.id == contact_id,
            CRMContact.business_id == business_id
        ).first()
        if not contact:
            return False
        
        contact.is_active = False
        db.commit()
        return True


class CRMDealRepository:
    """Repository for CRM Deal operations"""
    
    @staticmethod
    def create(db: Session, deal_data: CRMDealCreate, user_id: int, business_id: int) -> CRMDeal:
        """Create a new deal"""
        deal = CRMDeal(
            **deal_data.dict(),
            business_id=business_id,
            created_by=user_id
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)
        return deal
    
    @staticmethod
    def get_by_id(db: Session, deal_id: int, business_id: int) -> Optional[CRMDeal]:
        """Get deal by ID with relationships"""
        return db.query(CRMDeal).options(
            joinedload(CRMDeal.company),
            joinedload(CRMDeal.contact)
        ).filter(
            CRMDeal.id == deal_id,
            CRMDeal.business_id == business_id
        ).first()
    
    @staticmethod
    def get_all(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        stage: Optional[DealStage] = None,
        company_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[CRMDeal], int]:
        """Get deals with filtering and pagination"""
        query = db.query(CRMDeal).options(
            joinedload(CRMDeal.company),
            joinedload(CRMDeal.contact)
        ).filter(CRMDeal.business_id == business_id)
        
        # Default to active deals only (exclude soft-deleted ones)
        if is_active is None:
            query = query.filter(CRMDeal.is_active == True)
        else:
            query = query.filter(CRMDeal.is_active == is_active)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    CRMDeal.name.ilike(f"%{search}%"),
                    CRMDeal.description.ilike(f"%{search}%")
                )
            )
        
        if stage:
            query = query.filter(CRMDeal.stage == stage)
        
        if company_id:
            query = query.filter(CRMDeal.company_id == company_id)
        
        if contact_id:
            query = query.filter(CRMDeal.contact_id == contact_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        deals = query.order_by(desc(CRMDeal.value)).offset(skip).limit(limit).all()
        
        return deals, total
    
    @staticmethod
    def update(
        db: Session,
        deal_id: int,
        business_id: int,
        deal_data: CRMDealUpdate,
        user_id: int
    ) -> Optional[CRMDeal]:
        """Update deal"""
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.business_id == business_id
        ).first()
        if not deal:
            return None
        
        update_data = deal_data.dict(exclude_unset=True)
        if update_data:
            update_data['updated_by'] = user_id
            for field, value in update_data.items():
                setattr(deal, field, value)
            
            db.commit()
            db.refresh(deal)
        
        return deal
    
    @staticmethod
    def delete(db: Session, deal_id: int, business_id: int) -> bool:
        """Delete deal (soft delete)"""
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.business_id == business_id
        ).first()
        if not deal:
            return False
        
        deal.is_active = False
        db.commit()
        return True


class CRMActivityRepository:
    """Repository for CRM Activity operations"""
    
    @staticmethod
    def create(db: Session, activity_data: CRMActivityCreate, user_id: int, business_id: int) -> CRMActivity:
        """Create a new activity"""
        # Convert activity data to dict and handle title field
        activity_dict = activity_data.dict()
        
        # If title is provided in the request but not subject, use title as subject
        # This handles frontend compatibility
        if hasattr(activity_data, 'title') and activity_data.title and not activity_dict.get('subject'):
            activity_dict['subject'] = activity_data.title
        
        activity = CRMActivity(
            **activity_dict,
            business_id=business_id,
            created_by=user_id
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    
    @staticmethod
    def get_by_id(db: Session, activity_id: int, business_id: int) -> Optional[CRMActivity]:
        """Get activity by ID with relationships"""
        return db.query(CRMActivity).options(
            joinedload(CRMActivity.company),
            joinedload(CRMActivity.contact),
            joinedload(CRMActivity.deal)
        ).filter(
            CRMActivity.id == activity_id,
            CRMActivity.business_id == business_id
        ).first()
    
    @staticmethod
    def get_all(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        activity_type: Optional[ActivityType] = None,
        priority: Optional[Priority] = None,
        company_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        deal_id: Optional[int] = None,
        is_completed: Optional[bool] = None
    ) -> Tuple[List[CRMActivity], int]:
        """Get activities with filtering and pagination"""
        query = db.query(CRMActivity).options(
            joinedload(CRMActivity.company),
            joinedload(CRMActivity.contact),
            joinedload(CRMActivity.deal)
        ).filter(CRMActivity.business_id == business_id)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    CRMActivity.subject.ilike(f"%{search}%"),
                    CRMActivity.description.ilike(f"%{search}%")
                )
            )
        
        if activity_type:
            query = query.filter(CRMActivity.activity_type == activity_type)
        
        if priority:
            query = query.filter(CRMActivity.priority == priority)
        
        if company_id:
            query = query.filter(CRMActivity.company_id == company_id)
        
        if contact_id:
            query = query.filter(CRMActivity.contact_id == contact_id)
        
        if deal_id:
            query = query.filter(CRMActivity.deal_id == deal_id)
        
        if is_completed is not None:
            query = query.filter(CRMActivity.is_completed == is_completed)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        activities = query.order_by(desc(CRMActivity.start_date)).offset(skip).limit(limit).all()
        
        return activities, total
    
    @staticmethod
    def update(
        db: Session,
        activity_id: int,
        business_id: int,
        activity_data: CRMActivityUpdate,
        user_id: int
    ) -> Optional[CRMActivity]:
        """Update activity"""
        activity = db.query(CRMActivity).filter(
            CRMActivity.id == activity_id,
            CRMActivity.business_id == business_id
        ).first()
        if not activity:
            return None
        
        update_data = activity_data.dict(exclude_unset=True)
        if update_data:
            # Handle title field - if title is provided but not subject, use title as subject
            if hasattr(activity_data, 'title') and activity_data.title and not update_data.get('subject'):
                update_data['subject'] = activity_data.title
            
            update_data['updated_by'] = user_id
            for field, value in update_data.items():
                setattr(activity, field, value)
            
            db.commit()
            db.refresh(activity)
        
        return activity
    
    @staticmethod
    def delete(db: Session, activity_id: int, business_id: int) -> bool:
        """Delete activity"""
        activity = db.query(CRMActivity).filter(
            CRMActivity.id == activity_id,
            CRMActivity.business_id == business_id
        ).first()
        if not activity:
            return False
        
        db.delete(activity)
        db.commit()
        return True


class CRMPipelineRepository:
    """Repository for CRM Pipeline operations"""
    
    @staticmethod
    def create(db: Session, pipeline_data: CRMPipelineCreate, user_id: int, business_id: int) -> CRMPipeline:
        """Create a new pipeline"""
        pipeline = CRMPipeline(
            **pipeline_data.dict(),
            business_id=business_id,
            created_by=user_id
        )
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        return pipeline
    
    @staticmethod
    def get_by_id(db: Session, pipeline_id: int, business_id: int) -> Optional[CRMPipeline]:
        """Get pipeline by ID (only active pipelines)"""
        return db.query(CRMPipeline).filter(
            and_(
                CRMPipeline.id == pipeline_id,
                CRMPipeline.business_id == business_id,
                CRMPipeline.is_active == True
            )
        ).first()
    
    @staticmethod
    def get_all(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[CRMPipeline], int]:
        """Get pipelines with filtering and pagination"""
        query = db.query(CRMPipeline).filter(CRMPipeline.business_id == business_id)
        
        # Default to active pipelines only (exclude soft-deleted ones)
        if is_active is None:
            query = query.filter(CRMPipeline.is_active == True)
        else:
            query = query.filter(CRMPipeline.is_active == is_active)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    CRMPipeline.name.ilike(f"%{search}%"),
                    CRMPipeline.description.ilike(f"%{search}%")
                )
            )
        
        if status:
            query = query.filter(CRMPipeline.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        pipelines = query.order_by(CRMPipeline.name).offset(skip).limit(limit).all()
        
        return pipelines, total
    
    @staticmethod
    def update(
        db: Session,
        pipeline_id: int,
        business_id: int,
        pipeline_data: CRMPipelineUpdate,
        user_id: int
    ) -> Optional[CRMPipeline]:
        """Update pipeline"""
        pipeline = db.query(CRMPipeline).filter(
            CRMPipeline.id == pipeline_id,
            CRMPipeline.business_id == business_id
        ).first()
        if not pipeline:
            return None
        
        update_data = pipeline_data.dict(exclude_unset=True)
        if update_data:
            update_data['updated_by'] = user_id
            for field, value in update_data.items():
                setattr(pipeline, field, value)
            
            db.commit()
            db.refresh(pipeline)
        
        return pipeline
    
    @staticmethod
    def delete(db: Session, pipeline_id: int, business_id: int) -> bool:
        """Delete pipeline (soft delete)"""
        pipeline = db.query(CRMPipeline).filter(
            CRMPipeline.id == pipeline_id,
            CRMPipeline.business_id == business_id
        ).first()
        if not pipeline:
            return False
        
        pipeline.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def update_pipeline_stats(db: Session, pipeline_id: int) -> Optional[CRMPipeline]:
        """Update pipeline statistics (deal count and total value)"""
        pipeline = db.query(CRMPipeline).filter(CRMPipeline.id == pipeline_id).first()
        if not pipeline:
            return None
        
        # Calculate stats from deals that reference this pipeline
        deals = db.query(CRMDeal).filter(
            and_(
                CRMDeal.pipeline == pipeline.name,
                CRMDeal.is_active == True
            )
        ).all()
        
        pipeline.deal_count = len(deals)
        pipeline.total_deal_value = sum(deal.value for deal in deals if deal.value)
        
        db.commit()
        db.refresh(pipeline)
        return pipeline


class CRMAnalyticsRepository:
    """Repository for CRM Analytics operations"""
    
    @staticmethod
    def get_analytics(db: Session, business_id: int) -> dict:
        """Get CRM analytics data"""
        # Total counts
        total_companies = db.query(CRMCompany).filter(
            CRMCompany.is_active == True,
            CRMCompany.business_id == business_id
        ).count()
        total_contacts = db.query(CRMContact).filter(
            CRMContact.is_active == True,
            CRMContact.business_id == business_id
        ).count()
        total_deals = db.query(CRMDeal).filter(
            CRMDeal.is_active == True,
            CRMDeal.business_id == business_id
        ).count()
        total_activities = db.query(CRMActivity).filter(
            CRMActivity.business_id == business_id
        ).count()
        
        # Deals by stage
        deals_by_stage = db.query(
            CRMDeal.stage,
            func.count(CRMDeal.id).label('count'),
            func.sum(CRMDeal.value).label('total_value')
        ).filter(
            CRMDeal.is_active == True,
            CRMDeal.business_id == business_id
        ).group_by(CRMDeal.stage).all()
        
        # Revenue by month (last 12 months)
        revenue_by_month = db.query(
            func.date_trunc('month', CRMDeal.actual_close_date).label('month'),
            func.sum(CRMDeal.value).label('revenue')
        ).filter(
            and_(
                CRMDeal.is_won == True,
                CRMDeal.business_id == business_id,
                CRMDeal.actual_close_date >= datetime.now() - timedelta(days=365)
            )
        ).group_by(func.date_trunc('month', CRMDeal.actual_close_date)).all()
        
        # Lead sources
        lead_sources = db.query(
            CRMContact.lead_source,
            func.count(CRMContact.id).label('count')
        ).filter(
            and_(
                CRMContact.is_active == True,
                CRMContact.business_id == business_id,
                CRMContact.lead_source.isnot(None)
            )
        ).group_by(CRMContact.lead_source).all()
        
        return {
            "total_companies": total_companies,
            "total_contacts": total_contacts,
            "total_deals": total_deals,
            "total_activities": total_activities,
            "deals_by_stage": [
                {
                    "stage": stage,
                    "count": count,
                    "total_value": float(total_value or 0)
                }
                for stage, count, total_value in deals_by_stage
            ],
            "revenue_by_month": [
                {
                    "month": month.strftime("%Y-%m") if month else None,
                    "revenue": float(revenue or 0)
                }
                for month, revenue in revenue_by_month
            ],
            "lead_sources": [
                {
                    "source": source,
                    "count": count
                }
                for source, count in lead_sources
            ]
        }
    
    @staticmethod
    def get_companies_for_analytics(db: Session, business_id: int) -> List[dict]:
        """Get companies data for analytics table"""
        companies = db.query(CRMCompany).options(
            joinedload(CRMCompany.owner)
        ).filter(
            and_(
                CRMCompany.business_id == business_id,
                CRMCompany.is_active == True
            )
        ).all()
        
        return [
            {
                "id": company.id,
                "name": company.name,
                "email": company.email,
                "phone": company.phone,
                "industry": company.industry,
                "annual_revenue": float(company.annual_revenue or 0),
                "employee_count": company.employee_count,
                "created_at": company.created_at.strftime("%Y-%m-%d") if company.created_at else None,
                "owner": {
                    "id": company.owner.id,
                    "name": company.owner.name,
                    "email": company.owner.email
                } if company.owner else None
            }
            for company in companies
        ]
    
    @staticmethod
    def get_contacts_for_analytics(db: Session, business_id: int) -> List[dict]:
        """Get contacts data for analytics table"""
        contacts = db.query(CRMContact).options(
            joinedload(CRMContact.company),
            joinedload(CRMContact.owner)
        ).filter(
            and_(
                CRMContact.business_id == business_id,
                CRMContact.is_active == True
            )
        ).all()
        
        return [
            {
                "id": contact.id,
                "name": f"{contact.first_name} {contact.last_name}",
                "email": contact.email,
                "phone": contact.phone or contact.mobile,
                "contact_type": contact.contact_type.value if contact.contact_type else None,
                "lead_status": contact.lead_status.value if contact.lead_status else None,
                "lead_source": contact.lead_source,
                "created_at": contact.created_at.strftime("%Y-%m-%d") if contact.created_at else None,
                "company": {
                    "id": contact.company.id,
                    "name": contact.company.name
                } if contact.company else None,
                "owner": {
                    "id": contact.owner.id,
                    "name": contact.owner.name,
                    "email": contact.owner.email
                } if contact.owner else None
            }
            for contact in contacts
        ]
    
    @staticmethod
    def get_leads_for_analytics(db: Session, business_id: int) -> List[dict]:
        """Get leads data for analytics table"""
        leads = db.query(CRMContact).options(
            joinedload(CRMContact.company),
            joinedload(CRMContact.owner)
        ).filter(
            and_(
                CRMContact.business_id == business_id,
                CRMContact.contact_type == ContactType.LEAD,
                CRMContact.is_active == True
            )
        ).all()
        
        return [
            {
                "id": lead.id,
                "name": f"{lead.first_name} {lead.last_name}",
                "email": lead.email,
                "phone": lead.phone or lead.mobile,
                "lead_status": lead.lead_status.value if lead.lead_status else None,
                "lead_source": lead.lead_source,
                "value": float(lead.value or 0),
                "created_at": lead.created_at.strftime("%Y-%m-%d") if lead.created_at else None,
                "company": {
                    "id": lead.company.id,
                    "name": lead.company.name
                } if lead.company else None,
                "owner": {
                    "id": lead.owner.id,
                    "name": lead.owner.name,
                    "email": lead.owner.email
                } if lead.owner else None
            }
            for lead in leads
        ]
    
    @staticmethod
    def get_deals_for_analytics(db: Session, business_id: int) -> List[dict]:
        """Get deals data for analytics table"""
        deals = db.query(CRMDeal).options(
            joinedload(CRMDeal.company),
            joinedload(CRMDeal.contact)
        ).filter(
            and_(
                CRMDeal.business_id == business_id,
                CRMDeal.is_active == True
            )
        ).all()
        
        return [
            {
                "id": deal.id,
                "name": deal.name,
                "value": float(deal.value or 0),
                "stage": deal.stage.value if deal.stage else None,
                "probability": deal.probability,
                "pipeline": deal.pipeline,
                "expected_close_date": deal.expected_close_date.strftime("%Y-%m-%d") if deal.expected_close_date else None,
                "created_at": deal.created_at.strftime("%Y-%m-%d") if deal.created_at else None,
                "company": {
                    "id": deal.company.id,
                    "name": deal.company.name
                } if deal.company else None,
                "contact": {
                    "id": deal.contact.id,
                    "name": f"{deal.contact.first_name} {deal.contact.last_name}"
                } if deal.contact else None,
                "owner": {
                    "name": deal.owner
                } if deal.owner else None
            }
            for deal in deals
        ]
    
    @staticmethod
    def get_revenue_chart(db: Session, business_id: int) -> dict:
        """Get revenue data for line chart"""
        # Get monthly revenue for the last 12 months
        revenue_data = db.query(
            func.date_trunc('month', CRMDeal.actual_close_date).label('month'),
            func.sum(CRMDeal.value).label('revenue')
        ).filter(
            and_(
                CRMDeal.business_id == business_id,
                CRMDeal.is_won == True,
                CRMDeal.actual_close_date >= datetime.now() - timedelta(days=365)
            )
        ).group_by(func.date_trunc('month', CRMDeal.actual_close_date)).order_by('month').all()
        
        # Format for ApexCharts line chart
        categories = [month.strftime("%b %Y") for month, revenue in revenue_data]
        series_data = [float(revenue or 0) for month, revenue in revenue_data]
        
        return {
            "series": [
                {
                    "name": "Revenue",
                    "data": series_data
                }
            ],
            "categories": categories
        }
    
    @staticmethod
    def get_deals_by_stage_chart(db: Session, business_id: int) -> dict:
        """Get deals by stage data for donut chart"""
        stage_data = db.query(
            CRMDeal.stage,
            func.count(CRMDeal.id).label('count')
        ).filter(
            and_(
                CRMDeal.business_id == business_id,
                CRMDeal.is_active == True
            )
        ).group_by(CRMDeal.stage).all()
        
        # Format for ApexCharts donut
        labels = [stage.value for stage, count in stage_data]
        series = [count for stage, count in stage_data]
        
        return {
            "series": series,
            "labels": labels
        }
    
    @staticmethod
    def get_leads_by_source_chart(db: Session, business_id: int) -> dict:
        """Get leads by source data for donut chart"""
        lead_sources = db.query(
            CRMContact.lead_source,
            func.count(CRMContact.id).label('count')
        ).filter(
            and_(
                CRMContact.business_id == business_id,
                CRMContact.contact_type == ContactType.LEAD,
                CRMContact.is_active == True,
                CRMContact.lead_source.isnot(None)
            )
        ).group_by(CRMContact.lead_source).order_by(desc('count')).all()
        
        # Format for ApexCharts donut
        labels = [source.lead_source for source in lead_sources[:4]]  # Limit to 4
        series = [source.count for source in lead_sources[:4]]
        
        return {
            "series": series,
            "labels": labels
        }