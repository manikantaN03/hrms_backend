"""
Domain Service
Business logic for domain management
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.domain import DomainRequest, DomainConfiguration, DomainUsageLog
from app.models.business import Business
from app.repositories.domain_repository import (
    DomainRequestRepository, 
    DomainConfigurationRepository, 
    DomainUsageLogRepository
)
from app.schemas.domain import (
    DomainRequestCreate,
    DomainRequestUpdate,
    DomainApprovalUpdate,
    DomainListResponse
)

logger = logging.getLogger(__name__)


class DomainService:
    """Service for domain request management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.domain_repo = DomainRequestRepository(db)
        self.config_repo = DomainConfigurationRepository(db)
        self.usage_repo = DomainUsageLogRepository(db)
    
    def get_all_domains_for_frontend(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        plan_filter: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[DomainListResponse]:
        """Get all domains formatted for frontend"""
        domains = self.domain_repo.get_all_with_business_info(
            skip=skip, 
            limit=limit,
            status_filter=status_filter,
            plan_filter=plan_filter,
            search_term=search_term
        )
        
        result = []
        for domain in domains:
            # Format for frontend compatibility
            domain_response = DomainListResponse(
                id=domain.id,
                name=domain.business.business_name if domain.business else "Unknown Business",
                url=domain.requested_domain,
                plan=f"{domain.plan_name} ({domain.plan_type})",
                createdDate=domain.created_at.strftime("%d %b %Y") if domain.created_at else "",
                expiringOn=domain.expiry_date.strftime("%d %b %Y") if domain.expiry_date else "",
                status=domain.status,
                price=str(domain.price),
                logo=f"/assets/img/icons/{domain.plan_name.lower()}-icon.svg"  # Default logo based on plan
            )
            result.append(domain_response)
        
        return result
    
    def get_domain_by_id(self, domain_id: int) -> Optional[DomainRequest]:
        """Get domain request by ID with business info"""
        return self.domain_repo.get_with_business_info(domain_id)
    
    def create_domain_request(self, domain_data: DomainRequestCreate, user_id: int) -> DomainRequest:
        """Create a new domain request"""
        # Check if domain already exists
        if self.domain_repo.domain_exists(domain_data.requested_domain):
            raise ValueError(f"Domain '{domain_data.requested_domain}' is already requested or in use")
        
        # Create domain request
        domain_dict = domain_data.model_dump()
        domain_dict["user_id"] = user_id
        domain_dict["status"] = "Pending"
        domain_dict["created_at"] = datetime.utcnow()
        
        # Calculate expiry date based on plan type
        if domain_data.plan_type.lower() == "yearly":
            expiry_months = 12
        else:
            expiry_months = 1
        
        # Set tentative expiry date (will be updated on approval)
        domain_dict["expiry_date"] = datetime.utcnow() + timedelta(days=expiry_months * 30)
        
        domain = self.domain_repo.create(domain_dict)
        
        logger.info(f"Domain request created: {domain.requested_domain} by user {user_id}")
        return domain
    
    def update_domain_request(self, domain_id: int, update_data: DomainRequestUpdate) -> Optional[DomainRequest]:
        """Update a domain request"""
        domain = self.domain_repo.get(domain_id)
        if not domain:
            return None
        
        # Only allow updates for pending requests
        if domain.status != "Pending":
            raise ValueError("Cannot update non-pending domain requests")
        
        # Check domain uniqueness if domain is being changed
        if update_data.requested_domain and update_data.requested_domain != domain.requested_domain:
            if self.domain_repo.domain_exists(update_data.requested_domain, exclude_id=domain_id):
                raise ValueError(f"Domain '{update_data.requested_domain}' is already requested or in use")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()
        
        return self.domain_repo.update(domain, update_dict)
    
    def approve_domain_request(self, domain_id: int, approval_data: DomainApprovalUpdate, approver_id: int) -> Optional[DomainRequest]:
        """Approve or reject a domain request"""
        domain = self.domain_repo.get(domain_id)
        if not domain:
            return None
        
        if domain.status != "Pending":
            raise ValueError("Domain request is not pending approval")
        
        if approval_data.status == "Approved":
            # Calculate dates
            start_date = approval_data.start_date or datetime.utcnow()
            
            if approval_data.expiry_date:
                expiry_date = approval_data.expiry_date
            else:
                # Calculate expiry based on plan type
                if domain.plan_type.lower() == "yearly":
                    expiry_date = start_date + timedelta(days=365)
                else:
                    expiry_date = start_date + timedelta(days=30)
            
            success = self.domain_repo.approve_domain(domain_id, approver_id, start_date, expiry_date)
            if success:
                # Create domain configuration record
                config_data = {
                    "domain_request_id": domain_id,
                    "ssl_status": "pending",
                    "health_status": "unknown",
                    "is_configured": False
                }
                self.config_repo.create(config_data)
                
                logger.info(f"Domain approved: {domain.requested_domain} by user {approver_id}")
        
        elif approval_data.status == "Rejected":
            rejection_reason = approval_data.rejection_reason or "No reason provided"
            success = self.domain_repo.reject_domain(domain_id, approver_id, rejection_reason)
            if success:
                logger.info(f"Domain rejected: {domain.requested_domain} by user {approver_id}")
        
        # Update admin notes if provided
        if approval_data.admin_notes:
            domain.admin_notes = approval_data.admin_notes
            self.db.commit()
        
        return self.domain_repo.get(domain_id)
    
    def delete_domain_request(self, domain_id: int) -> bool:
        """Delete a domain request"""
        domain = self.domain_repo.get(domain_id)
        if not domain:
            return False
        
        # Only allow deletion of pending or rejected requests
        if domain.status == "Approved" and domain.is_active:
            raise ValueError("Cannot delete active approved domains")
        
        # Delete associated configuration if exists
        config = self.config_repo.get_by_domain_request_id(domain_id)
        if config:
            self.config_repo.delete(config.id)
        
        # Delete usage logs
        usage_logs = self.usage_repo.get_by_domain_request_id(domain_id)
        for log in usage_logs:
            self.usage_repo.delete(log.id)
        
        # Delete domain request
        self.domain_repo.delete(domain_id)
        
        logger.info(f"Domain request deleted: {domain.requested_domain}")
        return True
    
    def get_domain_stats(self) -> Dict[str, Any]:
        """Get domain statistics for dashboard"""
        return self.domain_repo.get_domain_stats()
    
    def get_pending_requests(self) -> List[DomainRequest]:
        """Get all pending domain requests"""
        return self.domain_repo.get_pending_requests()
    
    def get_expiring_domains(self, days: int = 30) -> List[DomainRequest]:
        """Get domains expiring within specified days"""
        return self.domain_repo.get_expiring_domains(days)
    
    def get_domains_by_plan(self) -> List[Dict[str, Any]]:
        """Get domain analytics by plan"""
        plan_data = self.domain_repo.get_domains_by_plan()
        
        analytics = []
        for plan_name, plan_type, count in plan_data:
            analytics.append({
                "plan": f"{plan_name} ({plan_type})",
                "domains": count,
                "plan_name": plan_name,
                "plan_type": plan_type
            })
        
        return analytics
    
    def search_domains(self, search_term: str, skip: int = 0, limit: int = 100) -> List[DomainListResponse]:
        """Search domains by business name or domain"""
        return self.get_all_domains_for_frontend(
            skip=skip,
            limit=limit,
            search_term=search_term
        )
    
    def renew_domain(self, domain_id: int, renewal_months: int = 12) -> Optional[DomainRequest]:
        """Renew a domain for specified months"""
        domain = self.domain_repo.get(domain_id)
        if not domain or domain.status != "Approved":
            return None
        
        # Extend expiry date
        if domain.expiry_date:
            new_expiry = domain.expiry_date + timedelta(days=renewal_months * 30)
        else:
            new_expiry = datetime.utcnow() + timedelta(days=renewal_months * 30)
        
        domain.expiry_date = new_expiry
        domain.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Domain renewed: {domain.requested_domain} until {new_expiry}")
        return domain
    
    def deactivate_expired_domains(self) -> int:
        """Deactivate expired domains"""
        expired_domains = (
            self.db.query(DomainRequest)
            .filter(
                DomainRequest.status == "Approved",
                DomainRequest.is_active == True,
                DomainRequest.expiry_date < datetime.utcnow()
            )
            .all()
        )
        
        count = 0
        for domain in expired_domains:
            domain.is_active = False
            domain.updated_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            self.db.commit()
            logger.info(f"Deactivated {count} expired domains")
        
        return count


class DomainConfigurationService:
    """Service for domain configuration management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_repo = DomainConfigurationRepository(db)
    
    def get_configuration(self, domain_request_id: int) -> Optional[DomainConfiguration]:
        """Get domain configuration"""
        return self.config_repo.get_by_domain_request_id(domain_request_id)
    
    def update_configuration(self, domain_request_id: int, config_data: Dict[str, Any]) -> Optional[DomainConfiguration]:
        """Update domain configuration"""
        config = self.config_repo.get_by_domain_request_id(domain_request_id)
        if not config:
            return None
        
        config_data["updated_at"] = datetime.utcnow()
        return self.config_repo.update(config, config_data)
    
    def mark_as_configured(self, domain_request_id: int) -> bool:
        """Mark domain as fully configured"""
        config = self.config_repo.get_by_domain_request_id(domain_request_id)
        if not config:
            return False
        
        config.is_configured = True
        config.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True


class DomainUsageService:
    """Service for domain usage analytics."""
    
    def __init__(self, db: Session):
        self.db = db
        self.usage_repo = DomainUsageLogRepository(db)
    
    def get_usage_summary(self, domain_request_id: int, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a domain"""
        return self.usage_repo.get_usage_summary(domain_request_id, days)
    
    def log_daily_usage(self, domain_request_id: int, usage_data: Dict[str, Any]) -> DomainUsageLog:
        """Log daily usage data"""
        return self.usage_repo.create_daily_log(domain_request_id, usage_data)
    
    def get_usage_history(self, domain_request_id: int, limit: int = 30) -> List[DomainUsageLog]:
        """Get usage history for a domain"""
        return self.usage_repo.get_by_domain_request_id(domain_request_id, limit)