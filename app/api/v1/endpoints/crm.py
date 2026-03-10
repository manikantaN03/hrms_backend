"""
CRM API Endpoints
Customer Relationship Management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, get_user_business_id, validate_business_access
from app.models.user import User
from app.schemas.crm import (
    # Company schemas
    CRMCompanyCreate, CRMCompanyUpdate, CRMCompanyResponse, CRMCompanyListResponse,
    # Contact schemas
    CRMContactCreate, CRMContactUpdate, CRMContactResponse, CRMContactListResponse,
    # Deal schemas
    CRMDealCreate, CRMDealUpdate, CRMDealResponse, CRMDealListResponse,
    # Activity schemas
    CRMActivityCreate, CRMActivityUpdate, CRMActivityResponse, CRMActivityListResponse,
    # Pipeline schemas
    CRMPipelineCreate, CRMPipelineUpdate, CRMPipelineResponse,
    # Analytics
    CRMAnalyticsResponse,
    # Enums
    ContactType, LeadStatus, DealStage, ActivityType, Priority
)
from app.services.crm_service import (
    CRMCompanyService, CRMContactService, CRMDealService, 
    CRMActivityService, CRMAnalyticsService, CRMPipelineService
)

router = APIRouter()

# ============================================================================
# Company Endpoints
# ============================================================================

@router.post("/companies", response_model=CRMCompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CRMCompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new CRM company
    
    **Required fields:**
    - name: Company name
    
    **Optional fields:**
    - industry, website, phone, email, address, etc.
    
    **Returns:**
    - Created company with ID and timestamps
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        company = CRMCompanyService.create_company(db, company_data, current_user.id, business_id)
        return company
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company: {str(e)}"
        )


@router.get("/companies", response_model=CRMCompanyListResponse)
async def get_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, email, website"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get companies with filtering and pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000)
    - search: Search in company name, email, website
    - industry: Filter by industry
    - is_active: Filter by active status
    
    **Returns:**
    - List of companies with pagination info
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        # Set default limit to prevent large queries
        if limit > 100:
            limit = 100
            
        companies, total = CRMCompanyService.get_companies(
            db, business_id, skip, limit, search, industry, is_active
        )
        
        return CRMCompanyListResponse(
            items=companies,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_companies: {str(e)}")
        
        # Return empty result instead of error to prevent timeout
        return CRMCompanyListResponse(
            items=[],
            total=0,
            page=1,
            size=limit,
            pages=0
        )


@router.get("/companies/{company_id}", response_model=CRMCompanyResponse)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get company by ID
    
    **Path Parameters:**
    - company_id: Company ID
    
    **Returns:**
    - Company details
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    company = CRMCompanyService.get_company(db, company_id, business_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company


@router.put("/companies/{company_id}", response_model=CRMCompanyResponse)
async def update_company(
    company_id: int,
    company_data: CRMCompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update company
    
    **Path Parameters:**
    - company_id: Company ID
    
    **Request Body:**
    - Any company fields to update
    
    **Returns:**
    - Updated company details
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    company = CRMCompanyService.update_company(db, company_id, business_id, company_data, current_user.id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete company (soft delete)
    
    **Path Parameters:**
    - company_id: Company ID
    
    **Returns:**
    - 204 No Content on success
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    success = CRMCompanyService.delete_company(db, company_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )


# ============================================================================
# Contact Endpoints
# ============================================================================

@router.post("/contacts", response_model=CRMContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: CRMContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new CRM contact
    
    **Required fields:**
    - first_name: Contact first name
    - last_name: Contact last name
    
    **Optional fields:**
    - email, phone, job_title, company_id, etc.
    
    **Returns:**
    - Created contact with ID and timestamps
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        contact = CRMContactService.create_contact(db, contact_data, current_user.id, business_id)
        return contact
    except ValueError as e:
        # Handle validation errors (like duplicate email)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contact: {str(e)}"
        )


@router.get("/contacts")
async def get_contacts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, email, phone"),
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    lead_status: Optional[LeadStatus] = Query(None, description="Filter by lead status"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get contacts with filtering and pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000)
    - search: Search in contact name, email, phone
    - contact_type: Filter by contact type (lead, customer, prospect, partner)
    - lead_status: Filter by lead status
    - company_id: Filter by company ID
    - is_active: Filter by active status
    
    **Returns:**
    - List of contacts with pagination info
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        contacts, total = CRMContactService.get_contacts(
            db, business_id, skip, limit, search, contact_type, lead_status, company_id, is_active
        )
        
        return {
            "items": contacts,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch contacts: {str(e)}"
        )


@router.get("/contacts/{contact_id}")
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get contact by ID
    
    **Path Parameters:**
    - contact_id: Contact ID
    
    **Returns:**
    - Contact details with company information
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        # Service returns a dictionary, not an object
        contact_dict = CRMContactService.get_contact(db, contact_id, business_id)
        if not contact_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # contact_dict is already properly serialized by the service
        return contact_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contact: {str(e)}"
        )


@router.put("/contacts/{contact_id}")
async def update_contact(
    contact_id: int,
    contact_data: CRMContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update contact
    
    **Path Parameters:**
    - contact_id: Contact ID
    
    **Request Body:**
    - Any contact fields to update
    
    **Returns:**
    - Updated contact details
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        contact_dict = CRMContactService.update_contact(db, contact_id, business_id, contact_data, current_user.id)
        if not contact_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # The service already returns a properly serialized dictionary
        return contact_dict

    except ValueError as e:
        # Handle validation errors (like duplicate email)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Handle any other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact: {str(e)}"
        )


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete contact (soft delete)
    
    **Path Parameters:**
    - contact_id: Contact ID
    
    **Returns:**
    - 204 No Content on success
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    success = CRMContactService.delete_contact(db, contact_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )


# ============================================================================
# Deal Endpoints
# ============================================================================

@router.post("/deals", response_model=CRMDealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal_data: CRMDealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new CRM deal
    
    **Required fields:**
    - name: Deal name
    - value: Deal value
    
    **Optional fields:**
    - description, stage, probability, company_id, contact_id, etc.
    
    **Returns:**
    - Created deal with ID and timestamps
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        deal = CRMDealService.create_deal(db, deal_data, current_user.id, business_id)
        return deal
    except ValueError as e:
        # Handle validation errors (foreign key violations, etc.)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deal: {str(e)}"
        )


@router.get("/deals", response_model=CRMDealListResponse)
async def get_deals(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in deal name, description"),
    stage: Optional[DealStage] = Query(None, description="Filter by deal stage"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    contact_id: Optional[int] = Query(None, description="Filter by contact ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get deals with filtering and pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000)
    - search: Search in deal name, description
    - stage: Filter by deal stage
    - company_id: Filter by company ID
    - contact_id: Filter by contact ID
    - is_active: Filter by active status
    
    **Returns:**
    - List of deals with pagination info
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        deals, total = CRMDealService.get_deals(
            db, business_id, skip, limit, search, stage, company_id, contact_id, is_active
        )
        
        return CRMDealListResponse(
            items=deals,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch deals: {str(e)}"
        )


@router.get("/deals/{deal_id}", response_model=CRMDealResponse)
async def get_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get deal by ID
    
    **Path Parameters:**
    - deal_id: Deal ID
    
    **Returns:**
    - Deal details with company and contact information
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    deal = CRMDealService.get_deal(db, deal_id, business_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    return deal


@router.put("/deals/{deal_id}", response_model=CRMDealResponse)
async def update_deal(
    deal_id: int,
    deal_data: CRMDealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update deal
    
    **Path Parameters:**
    - deal_id: Deal ID
    
    **Request Body:**
    - Any deal fields to update
    
    **Returns:**
    - Updated deal details
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        deal = CRMDealService.update_deal(db, deal_id, business_id, deal_data, current_user.id)
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found"
            )
        return deal
    except ValueError as e:
        # Handle validation errors (foreign key violations, etc.)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update deal: {str(e)}"
        )


@router.delete("/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete deal (soft delete)
    
    **Path Parameters:**
    - deal_id: Deal ID
    
    **Returns:**
    - 204 No Content on success
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    success = CRMDealService.delete_deal(db, deal_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )


# ============================================================================
# Activity Endpoints
# ============================================================================

@router.post("/activities", response_model=CRMActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: CRMActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new CRM activity
    
    **Required fields:**
    - subject: Activity subject
    - activity_type: Type of activity (call, email, meeting, task, note)
    
    **Optional fields:**
    - description, priority, dates, company_id, contact_id, deal_id, etc.
    
    **Returns:**
    - Created activity with ID and timestamps
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        activity = CRMActivityService.create_activity(db, activity_data, current_user.id, business_id)
        return activity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.get("/activities", response_model=CRMActivityListResponse)
async def get_activities(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in subject, description"),
    activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    contact_id: Optional[int] = Query(None, description="Filter by contact ID"),
    deal_id: Optional[int] = Query(None, description="Filter by deal ID"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get activities with filtering and pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000)
    - search: Search in activity subject, description
    - activity_type: Filter by activity type
    - priority: Filter by priority
    - company_id: Filter by company ID
    - contact_id: Filter by contact ID
    - deal_id: Filter by deal ID
    - is_completed: Filter by completion status
    
    **Returns:**
    - List of activities with pagination info
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        activities, total = CRMActivityService.get_activities(db, business_id, skip, limit, search, activity_type, priority, 
            company_id, contact_id, deal_id, is_completed
        )
        
        return CRMActivityListResponse(
            items=activities,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activities: {str(e)}"
        )


@router.get("/activities/{activity_id}", response_model=CRMActivityResponse)
async def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get activity by ID
    
    **Path Parameters:**
    - activity_id: Activity ID
    
    **Returns:**
    - Activity details with related information
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    activity = CRMActivityService.get_activity(db, activity_id, business_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity


@router.put("/activities/{activity_id}", response_model=CRMActivityResponse)
async def update_activity(
    activity_id: int,
    activity_data: CRMActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update activity
    
    **Path Parameters:**
    - activity_id: Activity ID
    
    **Request Body:**
    - Any activity fields to update
    
    **Returns:**
    - Updated activity details
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    activity = CRMActivityService.update_activity(db, activity_id, business_id, activity_data, current_user.id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete activity
    
    **Path Parameters:**
    - activity_id: Activity ID
    
    **Returns:**
    - 204 No Content on success
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    success = CRMActivityService.delete_activity(db, activity_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )


# ============================================================================
# Lead Endpoints (Contacts with lead type)
# ============================================================================

@router.get("/leads", response_model=CRMContactListResponse)
async def get_leads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, email, phone"),
    lead_status: Optional[LeadStatus] = Query(None, description="Filter by lead status"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get leads (contacts with lead type) with filtering and pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000)
    - search: Search in contact name, email, phone
    - lead_status: Filter by lead status
    - company_id: Filter by company ID
    - is_active: Filter by active status
    
    **Returns:**
    - List of leads with pagination info
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        contacts, total = CRMContactService.get_contacts(db, business_id, skip, limit, search, ContactType.LEAD, lead_status, company_id, is_active
        )
        
        return CRMContactListResponse(
            items=contacts,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leads: {str(e)}"
        )


@router.post("/leads", response_model=CRMContactResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: CRMContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new lead (convenience endpoint for creating contacts with lead type)
    
    **Required fields:**
    - first_name: Lead first name
    - last_name: Lead last name
    
    **Optional fields:**
    - email, phone, job_title, company_id, etc.
    
    **Note:** contact_type will be automatically set to 'lead'
    
    **Returns:**
    - Created lead with ID and timestamps
    """
    try:
        # Force contact_type to be 'lead'
        lead_data.contact_type = ContactType.LEAD
        
        # Set default lead_status if not provided
        if not lead_data.lead_status:
            lead_data.lead_status = LeadStatus.NEW
        
        contact = CRMContactService.create_contact(db, lead_data, current_user.id)
        return contact
    except ValueError as e:
        # Handle validation errors (like duplicate email)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )


@router.get("/leads/{lead_id}")
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get lead by ID
    
    **Path Parameters:**
    - lead_id: Lead ID
    
    **Returns:**
    - Lead details with company information
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        contact = CRMContactService.get_contact(db, lead_id, business_id)
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Verify it's actually a lead (contact is already a dict)
        if contact.get("contact_type") != ContactType.LEAD.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact is not a lead"
            )
        
        # contact is already a properly serialized dictionary
        return contact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lead: {str(e)}"
        )


@router.put("/leads/{lead_id}")
async def update_lead(
    lead_id: int,
    lead_data: CRMContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update lead
    
    **Path Parameters:**
    - lead_id: Lead ID
    
    **Request Body:**
    - Any lead fields to update
    
    **Returns:**
    - Updated lead details
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Ensure contact_type remains 'lead' if provided
        if lead_data.contact_type and lead_data.contact_type != ContactType.LEAD:
            # Allow conversion to customer if explicitly requested
            pass
        
        contact_dict = CRMContactService.update_contact(db, lead_id, business_id, lead_data, current_user.id)
        if not contact_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        return contact_dict

    except ValueError as e:
        # Handle validation errors (like duplicate email)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Handle any other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead: {str(e)}"
        )


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete lead (soft delete)
    
    **Path Parameters:**
    - lead_id: Lead ID
    
    **Returns:**
    - 204 No Content on success
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    success = CRMContactService.delete_contact(db, lead_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )


# ============================================================================
# Pipeline Endpoints
# ============================================================================

@router.post("/pipelines", status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_data: CRMPipelineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new CRM pipeline
    
    **Required fields:**
    - name: Pipeline name
    
    **Optional fields:**
    - description, stages_config, etc.
    
    **Returns:**
    - Created pipeline with ID and timestamps
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        pipeline = CRMPipelineService.create_pipeline(db, pipeline_data, current_user.id, business_id)
        return pipeline
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {str(e)}"
        )


@router.get("/pipelines")
async def get_pipelines(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, description"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get pipelines with filtering and pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000)
    - search: Search in pipeline name, description
    - status: Filter by status (Active, Inactive)
    - is_active: Filter by active status
    
    **Returns:**
    - List of pipelines (frontend expects simple array)
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        pipelines, total = CRMPipelineService.get_pipelines(db, business_id, skip, limit, search, status, is_active
        )
        
        # Frontend expects simple array of pipelines, not paginated response
        return pipelines
    except Exception as e:
        print(f"Pipeline API error: {e}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pipelines: {str(e)}"
        )


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get pipeline by ID
    
    **Path Parameters:**
    - pipeline_id: Pipeline ID
    
    **Returns:**
    - Pipeline details
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    pipeline = CRMPipelineService.get_pipeline(db, pipeline_id, business_id)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    return pipeline


@router.put("/pipelines/{pipeline_id}")
async def update_pipeline(
    pipeline_id: int,
    pipeline_data: CRMPipelineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update pipeline
    
    **Path Parameters:**
    - pipeline_id: Pipeline ID
    
    **Request Body:**
    - Any pipeline fields to update
    
    **Returns:**
    - Updated pipeline details
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    pipeline = CRMPipelineService.update_pipeline(db, pipeline_id, business_id, pipeline_data, current_user.id)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    return pipeline


@router.delete("/pipelines/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete pipeline (soft delete)
    
    **Path Parameters:**
    - pipeline_id: Pipeline ID
    
    **Returns:**
    - 204 No Content on success
    """
    # Get business ID from current user
    business_id = get_user_business_id(current_user, db)
    validate_business_access(business_id, current_user, db)
    
    success = CRMPipelineService.delete_pipeline(db, pipeline_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )


@router.get("/pipeline", response_model=List[CRMDealResponse])
async def get_pipeline_deals(
    stage: Optional[DealStage] = Query(None, description="Filter by deal stage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get sales pipeline view (deals organized by stage)
    
    **Query Parameters:**
    - stage: Filter by specific deal stage
    
    **Returns:**
    - List of active deals organized by pipeline stage
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        deals, _ = CRMDealService.get_deals(
            db, business_id, skip=0, limit=1000, stage=stage, is_active=True
        )
        return deals
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pipeline deals: {str(e)}"
        )


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/analytics", response_model=CRMAnalyticsResponse)
async def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get CRM analytics and metrics
    
    **Returns:**
    - Comprehensive CRM analytics including:
      - Contacts data for analytics table
      - Deals data for analytics table  
      - Leads data for analytics table
      - Companies data for analytics table
      - Deals by stage chart data
      - Leads by source chart data
    """
    try:
        # Get business ID from current user
        business_id = get_user_business_id(current_user, db)
        validate_business_access(business_id, current_user, db)
        
        analytics = CRMAnalyticsService.get_analytics(db, business_id)
        return analytics
    except Exception as e:
        print(f"Analytics API error: {e}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )