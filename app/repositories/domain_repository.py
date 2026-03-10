"""
Domain Repository
Database operations for domain management
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from app.models.domain import DomainRequest, DomainConfiguration, DomainUsageLog
from app.models.business import Business
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class DomainRequestRepository(BaseRepository[DomainRequest]):
    """Repository for domain request operations."""
    
    def __init__(self, db: Session):
        super().__init__(DomainRequest, db)
    
    def get_with_business_info(self, domain_id: int) -> Optional[DomainRequest]:
        """Get domain request with business and user information"""
        return (
            self.db.query(DomainRequest)
            .options(
                joinedload(DomainRequest.business),
                joinedload(DomainRequest.requester),
                joinedload(DomainRequest.approver)
            )
            .filter(DomainRequest.id == domain_id)
            .first()
        )
    
    def get_all_with_business_info(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        plan_filter: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[DomainRequest]:
        """Get all domain requests with business information and filters"""
        query = (
            self.db.query(DomainRequest)
            .options(
                joinedload(DomainRequest.business),
                joinedload(DomainRequest.requester)
            )
            .order_by(desc(DomainRequest.created_at))
        )
        
        # Apply filters
        if status_filter:
            query = query.filter(DomainRequest.status == status_filter)
        
        if plan_filter:
            if plan_filter in ["Monthly", "Yearly"]:
                query = query.filter(DomainRequest.plan_type == plan_filter)
            else:
                query = query.filter(DomainRequest.plan_name == plan_filter)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.join(Business).filter(
                or_(
                    Business.business_name.ilike(search_pattern),
                    DomainRequest.requested_domain.ilike(search_pattern)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_domain(self, domain: str) -> Optional[DomainRequest]:
        """Get domain request by domain name"""
        return (
            self.db.query(DomainRequest)
            .filter(DomainRequest.requested_domain == domain)
            .first()
        )
    
    def get_by_business_id(self, business_id: int) -> List[DomainRequest]:
        """Get all domain requests for a business"""
        return (
            self.db.query(DomainRequest)
            .filter(DomainRequest.business_id == business_id)
            .order_by(desc(DomainRequest.created_at))
            .all()
        )
    
    def get_pending_requests(self) -> List[DomainRequest]:
        """Get all pending domain requests"""
        return (
            self.db.query(DomainRequest)
            .options(joinedload(DomainRequest.business))
            .filter(DomainRequest.status == "Pending")
            .order_by(asc(DomainRequest.created_at))
            .all()
        )
    
    def get_expiring_domains(self, days: int = 30) -> List[DomainRequest]:
        """Get domains expiring within specified days"""
        expiry_threshold = datetime.utcnow() + timedelta(days=days)
        
        return (
            self.db.query(DomainRequest)
            .options(joinedload(DomainRequest.business))
            .filter(
                and_(
                    DomainRequest.status == "Approved",
                    DomainRequest.is_active == True,
                    DomainRequest.expiry_date <= expiry_threshold,
                    DomainRequest.expiry_date > datetime.utcnow()
                )
            )
            .order_by(asc(DomainRequest.expiry_date))
            .all()
        )
    
    def get_domain_stats(self) -> Dict[str, int]:
        """Get domain statistics"""
        total_requests = self.db.query(DomainRequest).count()
        pending_requests = self.db.query(DomainRequest).filter(DomainRequest.status == "Pending").count()
        approved_requests = self.db.query(DomainRequest).filter(DomainRequest.status == "Approved").count()
        rejected_requests = self.db.query(DomainRequest).filter(DomainRequest.status == "Rejected").count()
        active_domains = self.db.query(DomainRequest).filter(
            and_(DomainRequest.status == "Approved", DomainRequest.is_active == True)
        ).count()
        
        # Expiring soon (within 30 days)
        expiry_threshold = datetime.utcnow() + timedelta(days=30)
        expiring_soon = self.db.query(DomainRequest).filter(
            and_(
                DomainRequest.status == "Approved",
                DomainRequest.is_active == True,
                DomainRequest.expiry_date <= expiry_threshold,
                DomainRequest.expiry_date > datetime.utcnow()
            )
        ).count()
        
        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "active_domains": active_domains,
            "expiring_soon": expiring_soon
        }
    
    def get_domains_by_plan(self) -> List[Tuple[str, str, int]]:
        """Get domain count by plan name and type"""
        return (
            self.db.query(
                DomainRequest.plan_name,
                DomainRequest.plan_type,
                func.count(DomainRequest.id).label('count')
            )
            .filter(DomainRequest.status == "Approved")
            .group_by(DomainRequest.plan_name, DomainRequest.plan_type)
            .all()
        )
    
    def domain_exists(self, domain: str, exclude_id: Optional[int] = None) -> bool:
        """Check if domain already exists"""
        query = self.db.query(DomainRequest).filter(DomainRequest.requested_domain == domain)
        
        if exclude_id:
            query = query.filter(DomainRequest.id != exclude_id)
        
        return query.first() is not None
    
    def approve_domain(self, domain_id: int, approver_id: int, start_date: datetime, expiry_date: datetime) -> bool:
        """Approve a domain request"""
        domain = self.get(domain_id)
        if not domain or domain.status != "Pending":
            return False
        
        domain.status = "Approved"
        domain.approved_by = approver_id
        domain.approved_at = datetime.utcnow()
        domain.start_date = start_date
        domain.expiry_date = expiry_date
        domain.is_active = True
        
        # Update business URL
        if domain.business:
            domain.business.business_url = domain.requested_domain
        
        self.db.commit()
        return True
    
    def reject_domain(self, domain_id: int, approver_id: int, rejection_reason: str) -> bool:
        """Reject a domain request"""
        domain = self.get(domain_id)
        if not domain or domain.status != "Pending":
            return False
        
        domain.status = "Rejected"
        domain.approved_by = approver_id
        domain.approved_at = datetime.utcnow()
        domain.rejection_reason = rejection_reason
        
        self.db.commit()
        return True


class DomainConfigurationRepository(BaseRepository[DomainConfiguration]):
    """Repository for domain configuration operations."""
    
    def __init__(self, db: Session):
        super().__init__(DomainConfiguration, db)
    
    def get_by_domain_request_id(self, domain_request_id: int) -> Optional[DomainConfiguration]:
        """Get configuration by domain request ID"""
        return (
            self.db.query(DomainConfiguration)
            .filter(DomainConfiguration.domain_request_id == domain_request_id)
            .first()
        )
    
    def get_unconfigured_domains(self) -> List[DomainConfiguration]:
        """Get domains that need configuration"""
        return (
            self.db.query(DomainConfiguration)
            .options(joinedload(DomainConfiguration.domain_request))
            .filter(DomainConfiguration.is_configured == False)
            .all()
        )
    
    def update_ssl_status(self, config_id: int, ssl_status: str, ssl_expiry: Optional[datetime] = None) -> bool:
        """Update SSL status for a domain configuration"""
        config = self.get(config_id)
        if not config:
            return False
        
        config.ssl_status = ssl_status
        if ssl_expiry:
            config.ssl_expiry = ssl_expiry
        
        self.db.commit()
        return True
    
    def update_health_status(self, config_id: int, health_status: str, uptime_percentage: Optional[float] = None) -> bool:
        """Update health status for a domain configuration"""
        config = self.get(config_id)
        if not config:
            return False
        
        config.health_status = health_status
        config.last_health_check = datetime.utcnow()
        if uptime_percentage is not None:
            config.uptime_percentage = uptime_percentage
        
        self.db.commit()
        return True


class DomainUsageLogRepository(BaseRepository[DomainUsageLog]):
    """Repository for domain usage log operations."""
    
    def __init__(self, db: Session):
        super().__init__(DomainUsageLog, db)
    
    def get_by_domain_request_id(self, domain_request_id: int, limit: int = 30) -> List[DomainUsageLog]:
        """Get usage logs for a domain request"""
        return (
            self.db.query(DomainUsageLog)
            .filter(DomainUsageLog.domain_request_id == domain_request_id)
            .order_by(desc(DomainUsageLog.log_date))
            .limit(limit)
            .all()
        )
    
    def get_usage_summary(self, domain_request_id: int, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a domain over specified days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = (
            self.db.query(
                func.sum(DomainUsageLog.page_views).label('total_page_views'),
                func.sum(DomainUsageLog.unique_visitors).label('total_unique_visitors'),
                func.sum(DomainUsageLog.bandwidth_mb).label('total_bandwidth_mb'),
                func.avg(DomainUsageLog.avg_response_time).label('avg_response_time'),
                func.sum(DomainUsageLog.error_count).label('total_errors'),
                func.avg(DomainUsageLog.uptime_minutes).label('avg_uptime_minutes')
            )
            .filter(
                and_(
                    DomainUsageLog.domain_request_id == domain_request_id,
                    DomainUsageLog.log_date >= start_date
                )
            )
            .first()
        )
        
        return {
            "total_page_views": result.total_page_views or 0,
            "total_unique_visitors": result.total_unique_visitors or 0,
            "total_bandwidth_gb": float(result.total_bandwidth_mb or 0) / 1024,
            "avg_response_time": float(result.avg_response_time or 0),
            "total_errors": result.total_errors or 0,
            "uptime_percentage": (float(result.avg_uptime_minutes or 0) / (24 * 60)) * 100
        }
    
    def create_daily_log(self, domain_request_id: int, log_data: Dict[str, Any]) -> DomainUsageLog:
        """Create or update daily usage log"""
        log_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if log already exists for today
        existing_log = (
            self.db.query(DomainUsageLog)
            .filter(
                and_(
                    DomainUsageLog.domain_request_id == domain_request_id,
                    DomainUsageLog.log_date == log_date
                )
            )
            .first()
        )
        
        if existing_log:
            # Update existing log
            for key, value in log_data.items():
                if hasattr(existing_log, key):
                    setattr(existing_log, key, value)
            self.db.commit()
            return existing_log
        else:
            # Create new log
            log_data['domain_request_id'] = domain_request_id
            log_data['log_date'] = log_date
            return self.create(log_data)