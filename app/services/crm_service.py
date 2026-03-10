"""
CRM Service
Business logic for CRM operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import random

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
from app.repositories.crm_repository import (
    CRMCompanyRepository, CRMContactRepository, CRMDealRepository,
    CRMActivityRepository, CRMAnalyticsRepository, CRMPipelineRepository
)


class CRMSerializationHelper:
    """Helper class for CRM object serialization"""
    
    @staticmethod
    def serialize_company(company) -> Dict:
        """Serialize company object to dictionary - optimized for performance"""
        if not company:
            return {}
            
        company_dict = {
            "id": company.id,
            "name": company.name,
            "email": company.email,
            "phone": company.phone,
            "phone2": company.phone2,
            "fax": company.fax,
            "website": company.website,
            "ratings": float(company.ratings) if company.ratings else 0.0,
            "owner_id": company.owner_id,
            "tags": company.tags,
            "deals_info": company.deals_info,
            "industry": company.industry,
            "source": company.source,
            "currency": company.currency or "USD",
            "language": company.language or "English",
            "about": company.about,
            "contact_person": company.contact_person,
            "logo_url": company.logo_url,
            "address": company.address,
            "country": company.country,
            "state": company.state,
            "city": company.city,
            "postal_code": company.postal_code,
            "facebook_url": company.facebook_url,
            "twitter_url": company.twitter_url,
            "linkedin_url": company.linkedin_url,
            "skype_handle": company.skype_handle,
            "whatsapp": company.whatsapp,
            "instagram_url": company.instagram_url,
            "visibility": company.visibility or "private",
            "status": company.status or "Active",
            "annual_revenue": float(company.annual_revenue) if company.annual_revenue else None,
            "employee_count": company.employee_count,
            "description": company.description,
            "is_active": company.is_active if company.is_active is not None else True,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "created_by": company.created_by,
            "updated_by": company.updated_by,
            "owner": None
        }
        
        # Add owner info if exists (lazy loading to avoid N+1 queries)
        try:
            if hasattr(company, 'owner') and company.owner:
                company_dict["owner"] = {
                    "id": company.owner.id,
                    "name": getattr(company.owner, 'name', 'Unknown'),
                    "email": getattr(company.owner, 'email', 'Unknown')
                }
        except Exception:
            # Skip owner info if there's an issue to prevent errors
            pass
        
        return company_dict
    
    @staticmethod
    def serialize_contact(contact) -> Dict:
        """Serialize contact object to dictionary"""
        contact_dict = {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "full_name": contact.full_name,
            "email": contact.email,
            "phone": contact.phone,
            "mobile": contact.mobile,
            "job_title": contact.job_title,
            "department": contact.department,
            "contact_type": contact.contact_type,
            "is_primary": contact.is_primary,
            "is_active": contact.is_active,
            "company_id": contact.company_id,
            "lead_source": contact.lead_source,
            "lead_status": contact.lead_status,
            "rating": contact.rating,
            "owner_id": contact.owner_id,
            "tags": contact.tags,
            "profile_image_url": contact.profile_image_url,
            "currency": contact.currency,
            "language": contact.language,
            "date_of_birth": contact.date_of_birth,
            "industry": contact.industry,
            "deals_info": contact.deals_info,
            "visibility": contact.visibility,
            "status": contact.status,
            "value": contact.value,
            "address": contact.address,
            "city": contact.city,
            "state": contact.state,
            "country": contact.country,
            "postal_code": contact.postal_code,
            "location": contact.location,
            "linkedin_url": contact.linkedin_url,
            "twitter_handle": contact.twitter_handle,
            "facebook_url": contact.facebook_url,
            "instagram_url": contact.instagram_url,
            "skype_handle": contact.skype_handle,
            "notes": contact.notes,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "created_by": contact.created_by,
            "updated_by": contact.updated_by,
            "company": None,
            "owner": None
        }
        
        # Add company info if exists
        if hasattr(contact, 'company') and contact.company:
            contact_dict["company"] = CRMSerializationHelper.serialize_company(contact.company)
        
        # Add owner info if exists
        if hasattr(contact, 'owner') and contact.owner:
            contact_dict["owner"] = {
                "id": contact.owner.id,
                "name": contact.owner.name,
                "email": contact.owner.email
            }
        
        return contact_dict
    
    @staticmethod
    def serialize_pipeline(pipeline) -> Dict:
        """Serialize pipeline object to dictionary"""
        if not pipeline:
            return {}
        
        # Format date for frontend
        date_str = pipeline.created_at.strftime("%d %b %Y") if pipeline.created_at else ""
        
        # Format value for frontend
        value_str = f"${pipeline.total_deal_value:,.0f}" if pipeline.total_deal_value else "$0"
        
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "description": pipeline.description,
            "is_default": pipeline.is_default,
            "is_active": pipeline.is_active,
            "stages_config": pipeline.stages_config,
            "total_deal_value": float(pipeline.total_deal_value) if pipeline.total_deal_value else 0.0,
            "deal_count": pipeline.deal_count or 0,
            "current_stage": pipeline.current_stage,
            "stage_color": pipeline.stage_color or "primary",
            "status": pipeline.status or "Active",
            "created_at": pipeline.created_at,
            "updated_at": pipeline.updated_at,
            "created_by": pipeline.created_by,
            "updated_by": pipeline.updated_by,
            
            # Frontend compatibility fields
            "value": value_str,
            "deals": pipeline.deal_count or 0,
            "stage": pipeline.current_stage,
            "stageColor": pipeline.stage_color or "primary",
            "date": date_str
        }


class CRMCompanyService:
    """Service for CRM Company operations"""
    
    @staticmethod
    def create_company(db: Session, company_data: CRMCompanyCreate, user_id: int, business_id: int) -> Dict:
        """Create a new company"""
        company = CRMCompanyRepository.create(db, company_data, user_id, business_id)
        return CRMSerializationHelper.serialize_company(company)
    
    @staticmethod
    def get_company(db: Session, company_id: int, business_id: int) -> Optional[Dict]:
        """Get company by ID"""
        company = CRMCompanyRepository.get_by_id(db, company_id, business_id)
        if not company:
            return None
        return CRMSerializationHelper.serialize_company(company)
    
    @staticmethod
    def get_companies(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple:
        """Get companies with filtering and pagination"""
        companies, total = CRMCompanyRepository.get_all(db, business_id, skip, limit, search, industry, is_active)
        
        # Serialize companies
        serialized_companies = [
            CRMSerializationHelper.serialize_company(company) 
            for company in companies
        ]
        
        return serialized_companies, total
    
    @staticmethod
    def update_company(
        db: Session,
        company_id: int,
        business_id: int,
        company_data: CRMCompanyUpdate,
        user_id: int
    ) -> Optional[Dict]:
        """Update company"""
        company = CRMCompanyRepository.update(db, company_id, business_id, company_data, user_id)
        if not company:
            return None
        return CRMSerializationHelper.serialize_company(company)
    
    @staticmethod
    def delete_company(db: Session, company_id: int, business_id: int) -> bool:
        """Delete company (soft delete)"""
        return CRMCompanyRepository.delete(db, company_id, business_id)


class CRMContactService:
    """Service for CRM Contact operations"""
    
    @staticmethod
    def create_contact(db: Session, contact_data: CRMContactCreate, user_id: int, business_id: int) -> Dict:
        """Create a new contact"""
        contact = CRMContactRepository.create(db, contact_data, user_id, business_id)
        return CRMSerializationHelper.serialize_contact(contact)
    
    @staticmethod
    def get_contact(db: Session, contact_id: int, business_id: int) -> Optional[Dict]:
        """Get contact by ID"""
        contact = CRMContactRepository.get_by_id(db, contact_id, business_id)
        if not contact:
            return None
        return CRMSerializationHelper.serialize_contact(contact)
    
    @staticmethod
    def get_contacts(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        contact_type: Optional[ContactType] = None,
        lead_status: Optional[LeadStatus] = None,
        company_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> tuple:
        """Get contacts with filtering and pagination"""
        contacts, total = CRMContactRepository.get_all(
            db, business_id, skip, limit, search, contact_type, lead_status, company_id, is_active
        )
        
        # Serialize contacts
        serialized_contacts = [
            CRMSerializationHelper.serialize_contact(contact) 
            for contact in contacts
        ]
        
        return serialized_contacts, total
    
    @staticmethod
    def update_contact(
        db: Session,
        contact_id: int,
        business_id: int,
        contact_data: CRMContactUpdate,
        user_id: int
    ) -> Optional[Dict]:
        """Update contact"""
        contact = CRMContactRepository.update(db, contact_id, business_id, contact_data, user_id)
        if not contact:
            return None
        return CRMSerializationHelper.serialize_contact(contact)
    
    @staticmethod
    def delete_contact(db: Session, contact_id: int, business_id: int) -> bool:
        """Delete contact (soft delete)"""
        return CRMContactRepository.delete(db, contact_id, business_id)


class CRMDealService:
    """Service for CRM Deal operations"""
    
    @staticmethod
    def create_deal(db: Session, deal_data: CRMDealCreate, user_id: int, business_id: int) -> Dict:
        """Create a new deal"""
        try:
            # Validate foreign key references before creating
            if deal_data.contact_id:
                contact = db.query(CRMContact).filter(CRMContact.id == deal_data.contact_id).first()
                if not contact:
                    raise ValueError(f"Contact with ID {deal_data.contact_id} does not exist")
            
            if deal_data.company_id:
                company = db.query(CRMCompany).filter(CRMCompany.id == deal_data.company_id).first()
                if not company:
                    raise ValueError(f"Company with ID {deal_data.company_id} does not exist")
            
            deal = CRMDealRepository.create(db, deal_data, user_id, business_id)
            return CRMDealService._serialize_deal(deal)
        except ValueError as ve:
            # Re-raise validation errors
            raise ve
        except Exception as e:
            # Handle database constraint violations and other errors
            error_msg = str(e).lower()
            if "foreign key constraint" in error_msg or "violates foreign key constraint" in error_msg:
                if "contact_id" in error_msg:
                    raise ValueError("Invalid contact ID - contact does not exist")
                elif "company_id" in error_msg:
                    raise ValueError("Invalid company ID - company does not exist")
                else:
                    raise ValueError("Invalid reference - related record does not exist")
            else:
                # Re-raise other exceptions
                raise e
    
    @staticmethod
    def get_deal(db: Session, deal_id: int, business_id: int) -> Optional[Dict]:
        """Get deal by ID"""
        deal = CRMDealRepository.get_by_id(db, deal_id, business_id)
        if not deal:
            return None
        return CRMDealService._serialize_deal(deal)
    
    @staticmethod
    def get_deals(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        stage: Optional[DealStage] = None,
        company_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> tuple:
        """Get deals with filtering and pagination"""
        deals, total = CRMDealRepository.get_all(
            db, business_id, skip, limit, search, stage, company_id, contact_id, is_active
        )
        
        # Serialize deals
        serialized_deals = [CRMDealService._serialize_deal(deal) for deal in deals]
        return serialized_deals, total
    
    @staticmethod
    def update_deal(
        db: Session,
        deal_id: int,
        business_id: int,
        deal_data: CRMDealUpdate,
        user_id: int
    ) -> Optional[Dict]:
        """Update deal"""
        try:
            # Validate foreign key references before updating
            if hasattr(deal_data, 'contact_id') and deal_data.contact_id:
                contact = db.query(CRMContact).filter(CRMContact.id == deal_data.contact_id).first()
                if not contact:
                    raise ValueError(f"Contact with ID {deal_data.contact_id} does not exist")
            
            if hasattr(deal_data, 'company_id') and deal_data.company_id:
                company = db.query(CRMCompany).filter(CRMCompany.id == deal_data.company_id).first()
                if not company:
                    raise ValueError(f"Company with ID {deal_data.company_id} does not exist")
            
            deal = CRMDealRepository.update(db, deal_id, business_id, deal_data, user_id)
            if not deal:
                return None
            return CRMDealService._serialize_deal(deal)
        except ValueError as ve:
            # Re-raise validation errors
            raise ve
        except Exception as e:
            # Handle database constraint violations and other errors
            error_msg = str(e).lower()
            if "foreign key constraint" in error_msg or "violates foreign key constraint" in error_msg:
                if "contact_id" in error_msg:
                    raise ValueError("Invalid contact ID - contact does not exist")
                elif "company_id" in error_msg:
                    raise ValueError("Invalid company ID - company does not exist")
                else:
                    raise ValueError("Invalid reference - related record does not exist")
            else:
                # Re-raise other exceptions
                raise e
    
    @staticmethod
    def delete_deal(db: Session, deal_id: int, business_id: int) -> bool:
        """Delete deal (soft delete)"""
        return CRMDealRepository.delete(db, deal_id, business_id)
    
    @staticmethod
    def _serialize_deal(deal) -> Dict:
        """Serialize deal object to dictionary"""
        deal_dict = {
            "id": deal.id,
            "name": deal.name,
            "description": deal.description,
            "value": deal.value,
            "currency": deal.currency,
            "stage": deal.stage,
            "probability": deal.probability,
            "pipeline": deal.pipeline,
            "status": deal.status,
            "period": deal.period,
            "period_value": deal.period_value,
            "project": deal.project,
            "assignee": deal.assignee,
            "tags": deal.tags,
            "lead_source": deal.lead_source,
            "priority": deal.priority,
            "company_id": deal.company_id,
            "contact_id": deal.contact_id,
            "due_date": deal.due_date,
            "expected_close_date": deal.expected_close_date,
            "actual_close_date": deal.actual_close_date,
            "followup_date": deal.followup_date,
            "is_won": deal.is_won,
            "is_lost": deal.is_lost,
            "lost_reason": deal.lost_reason,
            "is_active": deal.is_active,
            "created_at": deal.created_at,
            "updated_at": deal.updated_at,
            "created_by": deal.created_by,
            "updated_by": deal.updated_by,
            # Frontend display fields
            "initials": deal.initials,
            "title": deal.title,
            "amount": deal.amount,
            "email": deal.email,
            "phone": deal.phone,
            "location": deal.location,
            "owner": deal.owner,
            "owner_img": deal.owner_img,
            "progress": deal.progress,
            "date": deal.date,
            "competitor": deal.competitor,
            "next_step": deal.next_step,
            # Relationships
            "company": None,
            "contact": None
        }
        
        # Add company info if exists
        if hasattr(deal, 'company') and deal.company:
            deal_dict["company"] = CRMSerializationHelper.serialize_company(deal.company)
        
        # Add contact info if exists
        if hasattr(deal, 'contact') and deal.contact:
            deal_dict["contact"] = CRMSerializationHelper.serialize_contact(deal.contact)
        
        return deal_dict


class CRMActivityService:
    """Service for CRM Activity operations"""
    
    @staticmethod
    def create_activity(db: Session, activity_data: CRMActivityCreate, user_id: int, business_id: int) -> CRMActivity:
        """Create a new activity"""
        return CRMActivityRepository.create(db, activity_data, user_id, business_id)
    
    @staticmethod
    def get_activity(db: Session, activity_id: int, business_id: int) -> Optional[CRMActivity]:
        """Get activity by ID"""
        return CRMActivityRepository.get_by_id(db, activity_id, business_id)
    
    @staticmethod
    def get_activities(
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
    ) -> tuple:
        """Get activities with filtering and pagination"""
        return CRMActivityRepository.get_all(
            db, business_id, skip, limit, search, activity_type, priority,
            company_id, contact_id, deal_id, is_completed
        )
    
    @staticmethod
    def update_activity(
        db: Session,
        activity_id: int,
        business_id: int,
        activity_data: CRMActivityUpdate,
        user_id: int
    ) -> Optional[CRMActivity]:
        """Update activity"""
        return CRMActivityRepository.update(db, activity_id, business_id, activity_data, user_id)
    
    @staticmethod
    def delete_activity(db: Session, activity_id: int, business_id: int) -> bool:
        """Delete activity"""
        return CRMActivityRepository.delete(db, activity_id, business_id)


class CRMAnalyticsService:
    """Service for CRM Analytics"""
    
    @staticmethod
    def get_analytics(db: Session, business_id: int) -> Dict[str, Any]:
        """Get CRM analytics data matching frontend structure"""
        # Get real data from database
        contacts_data = CRMAnalyticsRepository.get_contacts_for_analytics(db, business_id)
        deals_data = CRMAnalyticsRepository.get_deals_for_analytics(db, business_id)
        leads_data = CRMAnalyticsRepository.get_leads_for_analytics(db, business_id)
        companies_data = CRMAnalyticsRepository.get_companies_for_analytics(db, business_id)
        
        # Get chart data
        deals_by_stage_chart = CRMAnalyticsRepository.get_deals_by_stage_chart(db, business_id)
        leads_by_source_chart = CRMAnalyticsRepository.get_leads_by_source_chart(db, business_id)
        
        return {
            "contacts": contacts_data,
            "deals": deals_data,
            "leads": leads_data,
            "companies": companies_data,
            "deals_by_stage_chart": deals_by_stage_chart,
            "leads_by_source_chart": leads_by_source_chart
        }


class CRMPipelineService:
    """Service for CRM Pipeline operations"""
    
    @staticmethod
    def create_pipeline(db: Session, pipeline_data: CRMPipelineCreate, user_id: int, business_id: int) -> Dict:
        """Create a new pipeline"""
        pipeline = CRMPipelineRepository.create(db, pipeline_data, user_id, business_id)
        return CRMSerializationHelper.serialize_pipeline(pipeline)
    
    @staticmethod
    def get_pipeline(db: Session, pipeline_id: int, business_id: int) -> Optional[Dict]:
        """Get pipeline by ID"""
        pipeline = CRMPipelineRepository.get_by_id(db, pipeline_id, business_id)
        if not pipeline:
            return None
        return CRMSerializationHelper.serialize_pipeline(pipeline)
    
    @staticmethod
    def get_pipelines(
        db: Session,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple:
        """Get pipelines with filtering and pagination"""
        pipelines, total = CRMPipelineRepository.get_all(db, business_id, skip, limit, search, status, is_active)
        
        # Serialize pipelines
        serialized_pipelines = [
            CRMSerializationHelper.serialize_pipeline(pipeline) 
            for pipeline in pipelines
        ]
        
        return serialized_pipelines, total
    
    @staticmethod
    def update_pipeline(
        db: Session,
        pipeline_id: int,
        business_id: int,
        pipeline_data: CRMPipelineUpdate,
        user_id: int
    ) -> Optional[Dict]:
        """Update pipeline"""
        pipeline = CRMPipelineRepository.update(db, pipeline_id, business_id, pipeline_data, user_id)
        if not pipeline:
            return None
        return CRMSerializationHelper.serialize_pipeline(pipeline)
    
    @staticmethod
    def delete_pipeline(db: Session, pipeline_id: int, business_id: int) -> bool:
        """Delete pipeline (soft delete)"""
        return CRMPipelineRepository.delete(db, pipeline_id, business_id)
    
    @staticmethod
    def update_pipeline_stats(db: Session, pipeline_id: int, business_id: int) -> Optional[Dict]:
        """Update pipeline statistics"""
        pipeline = CRMPipelineRepository.update_pipeline_stats(db, pipeline_id, business_id)
        if not pipeline:
            return None
        return CRMSerializationHelper.serialize_pipeline(pipeline)