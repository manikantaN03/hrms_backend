"""
Domain Endpoints
API endpoints for domain management (SuperAdmin Domain module)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.api.v1.deps import get_current_superadmin, get_current_user
from app.models.user import User
from app.schemas.domain import (
    DomainRequestCreate,
    DomainRequestUpdate,
    DomainApprovalUpdate,
    DomainRequestResponse,
    DomainListResponse,
    DomainSummary,
    DomainAnalytics,
    DomainConfigurationResponse
)
from app.schemas.domain_additional import DomainConfigurationUpdateRequest
from app.services.domain_service import DomainService, DomainConfigurationService, DomainUsageService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SUPERADMIN DOMAIN MANAGEMENT
# ============================================================================

@router.get("/", response_model=List[DomainListResponse])
def get_all_domains(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records"),
    status: Optional[str] = Query(None, description="Filter by status"),
    plan: Optional[str] = Query(None, description="Filter by plan"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get all domain requests for superadmin dashboard.
    
    Returns domains in the format expected by frontend:
    - id, name, url, plan, createdDate, expiringOn, status, price, logo
    """
    try:
        service = DomainService(db)
        
        domains = service.get_all_domains_for_frontend(
            skip=skip,
            limit=limit,
            status_filter=status,
            plan_filter=plan,
            search_term=search
        )
        
        logger.info(f"Superadmin {superadmin.email} retrieved {len(domains)} domains")
        return domains
        
    except Exception as e:
        logger.error(f"Error fetching domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching domains: {str(e)}"
        )


@router.get("/summary", response_model=DomainSummary)
def get_domain_summary(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get domain statistics summary for dashboard.
    """
    try:
        service = DomainService(db)
        stats = service.get_domain_stats()
        
        summary = DomainSummary(
            total_requests=stats["total_requests"],
            pending_requests=stats["pending_requests"],
            approved_requests=stats["approved_requests"],
            rejected_requests=stats["rejected_requests"],
            active_domains=stats["active_domains"],
            expiring_soon=stats["expiring_soon"]
        )
        
        logger.info(f"Domain summary retrieved by {superadmin.email}")
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching domain summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching domain summary: {str(e)}"
        )


@router.get("/{domain_id}", response_model=DomainRequestResponse)
def get_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get domain details by ID.
    """
    try:
        service = DomainService(db)
        domain = service.get_domain_by_id(domain_id)
        
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        # Format response for frontend
        response = DomainRequestResponse.model_validate(domain)
        if domain.business:
            response.name = domain.business.business_name
            response.logo = f"/assets/img/icons/{domain.plan_name.lower()}-icon.svg"
        
        response.url = domain.requested_domain
        response.plan = f"{domain.plan_name} ({domain.plan_type})"
        response.createdDate = domain.created_at.strftime("%d %b %Y") if domain.created_at else ""
        response.expiringOn = domain.expiry_date.strftime("%d %b %Y") if domain.expiry_date else ""
        
        logger.info(f"Domain {domain_id} retrieved by {superadmin.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching domain {domain_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching domain: {str(e)}"
        )


@router.post("/", response_model=DomainRequestResponse, status_code=status.HTTP_201_CREATED)
def create_domain_request(
    domain_data: DomainRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new domain request.
    """
    try:
        service = DomainService(db)
        domain = service.create_domain_request(domain_data, current_user.id)
        
        logger.info(f"Domain request created by {current_user.email}: {domain.requested_domain}")
        return DomainRequestResponse.model_validate(domain)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating domain request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating domain request: {str(e)}"
        )


@router.put("/{domain_id}", response_model=DomainRequestResponse)
def update_domain_request(
    domain_id: int,
    update_data: DomainRequestUpdate,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Update a domain request.
    """
    try:
        service = DomainService(db)
        domain = service.update_domain_request(domain_id, update_data)
        
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        logger.info(f"Domain {domain_id} updated by {superadmin.email}")
        return DomainRequestResponse.model_validate(domain)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating domain {domain_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating domain: {str(e)}"
        )


@router.patch("/{domain_id}/approval", response_model=DomainRequestResponse)
def approve_or_reject_domain(
    domain_id: int,
    approval_data: DomainApprovalUpdate,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Approve or reject a domain request.
    """
    try:
        service = DomainService(db)
        domain = service.approve_domain_request(domain_id, approval_data, superadmin.id)
        
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        action = "approved" if approval_data.status == "Approved" else "rejected"
        logger.info(f"Domain {domain_id} {action} by {superadmin.email}")
        return DomainRequestResponse.model_validate(domain)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing domain approval {domain_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing domain approval: {str(e)}"
        )


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain_request(
    domain_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Delete a domain request.
    """
    try:
        service = DomainService(db)
        success = service.delete_domain_request(domain_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        logger.info(f"Domain {domain_id} deleted by {superadmin.email}")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting domain {domain_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting domain: {str(e)}"
        )


# ============================================================================
# DOMAIN ANALYTICS
# ============================================================================

@router.get("/analytics/by-plan", response_model=List[Dict[str, Any]])
def get_domain_analytics_by_plan(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get domain analytics by plan.
    """
    try:
        service = DomainService(db)
        analytics = service.get_domains_by_plan()
        
        logger.info(f"Domain analytics by plan retrieved by {superadmin.email}")
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching domain analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching domain analytics: {str(e)}"
        )


@router.get("/analytics/expiring", response_model=List[DomainRequestResponse])
def get_expiring_domains(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get domains expiring within specified days.
    """
    try:
        service = DomainService(db)
        expiring_domains = service.get_expiring_domains(days)
        
        result = []
        for domain in expiring_domains:
            response = DomainRequestResponse.model_validate(domain)
            if domain.business:
                response.name = domain.business.business_name
            result.append(response)
        
        logger.info(f"Expiring domains retrieved by {superadmin.email}: {len(result)} found")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching expiring domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching expiring domains: {str(e)}"
        )


@router.get("/analytics/usage/{domain_id}", response_model=Dict[str, Any])
def get_domain_usage_analytics(
    domain_id: int,
    days: int = Query(30, ge=1, le=365, description="Days of usage data"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get usage analytics for a specific domain.
    """
    try:
        usage_service = DomainUsageService(db)
        usage_summary = usage_service.get_usage_summary(domain_id, days)
        
        logger.info(f"Usage analytics for domain {domain_id} retrieved by {superadmin.email}")
        return usage_summary
        
    except Exception as e:
        logger.error(f"Error fetching domain usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching domain usage analytics: {str(e)}"
        )


# ============================================================================
# DOMAIN CONFIGURATION MANAGEMENT
# ============================================================================

@router.get("/{domain_id}/configuration", response_model=DomainConfigurationResponse)
def get_domain_configuration(
    domain_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get domain configuration details.
    """
    try:
        config_service = DomainConfigurationService(db)
        config = config_service.get_configuration(domain_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain configuration not found"
            )
        
        logger.info(f"Domain configuration {domain_id} retrieved by {superadmin.email}")
        return DomainConfigurationResponse.model_validate(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching domain configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching domain configuration: {str(e)}"
        )


@router.patch("/{domain_id}/configuration", response_model=DomainConfigurationResponse)
def update_domain_configuration(
    domain_id: int,
    config_data: DomainConfigurationUpdateRequest,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Update domain configuration.
    
    **Request body:**
    - cname_record: CNAME target record
    - a_record: IP address for A record
    - txt_record: TXT record for verification
    - ssl_certificate_id: SSL certificate ID
    - ssl_status: SSL status (pending, active, expired, failed)
    - ssl_expiry: SSL certificate expiry date
    - load_balancer_id: Load balancer ID
    - backend_servers: JSON array of backend servers
    - health_status: Health status (healthy, unhealthy, unknown)
    - uptime_percentage: Uptime percentage
    - is_configured: Whether domain is fully configured
    - configuration_notes: Configuration notes
    """
    try:
        config_service = DomainConfigurationService(db)
        # Convert Pydantic model to dict, excluding None values
        config_dict = config_data.model_dump(exclude_none=True)
        config = config_service.update_configuration(domain_id, config_dict)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain configuration not found"
            )
        
        logger.info(f"Domain configuration {domain_id} updated by {superadmin.email}")
        return DomainConfigurationResponse.model_validate(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating domain configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating domain configuration: {str(e)}"
        )


# ============================================================================
# MAINTENANCE OPERATIONS
# ============================================================================

@router.post("/maintenance/deactivate-expired", response_model=Dict[str, Any])
def deactivate_expired_domains(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Deactivate expired domains.
    """
    try:
        service = DomainService(db)
        count = service.deactivate_expired_domains()
        
        logger.info(f"Expired domains deactivated by {superadmin.email}: {count} domains")
        return {
            "message": f"Deactivated {count} expired domains",
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Error deactivating expired domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deactivating expired domains: {str(e)}"
        )


@router.post("/{domain_id}/renew", response_model=DomainRequestResponse)
def renew_domain(
    domain_id: int,
    renewal_months: int = Query(12, ge=1, le=60, description="Renewal period in months"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Renew a domain for specified months.
    """
    try:
        service = DomainService(db)
        domain = service.renew_domain(domain_id, renewal_months)
        
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found or not eligible for renewal"
            )
        
        logger.info(f"Domain {domain_id} renewed by {superadmin.email} for {renewal_months} months")
        return DomainRequestResponse.model_validate(domain)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renewing domain {domain_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error renewing domain: {str(e)}"
        )