"""
Domain Models
Manages custom domain/subdomain requests and approvals for businesses
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class DomainRequest(BaseModel):
    """
    Domain/subdomain requests from businesses with approval workflow.
    """
    
    __tablename__ = "domain_requests"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Requester
    
    # ========================================================================
    # Domain Details
    # ========================================================================
    requested_domain = Column(String(255), nullable=False, unique=True, index=True)
    domain_type = Column(String(50), nullable=False, default="subdomain")  # subdomain, custom_domain
    
    # ========================================================================
    # Plan and Pricing
    # ========================================================================
    plan_name = Column(String(100), nullable=False)  # Basic, Advanced, Pro
    plan_type = Column(String(50), nullable=False)   # Monthly, Yearly
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    
    # ========================================================================
    # Approval Workflow
    # ========================================================================
    status = Column(String(50), nullable=False, default="Pending")  # Pending, Approved, Rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # ========================================================================
    # Domain Lifecycle
    # ========================================================================
    start_date = Column(DateTime(timezone=True), nullable=True)  # When approved
    expiry_date = Column(DateTime(timezone=True), nullable=True)  # When expires
    auto_renew = Column(Boolean, default=True, nullable=False)
    
    # ========================================================================
    # Technical Details
    # ========================================================================
    ssl_enabled = Column(Boolean, default=True, nullable=False)
    dns_configured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)  # Active only when approved and configured
    
    # ========================================================================
    # Additional Information
    # ========================================================================
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)  # Internal notes for superadmin
    
    # ========================================================================
    # Relationships
    # ========================================================================
    business = relationship("Business", backref="domain_requests")
    requester = relationship("User", foreign_keys=[user_id], backref="domain_requests")
    approver = relationship("User", foreign_keys=[approved_by], backref="approved_domains")
    
    def __repr__(self):
        return f"<DomainRequest(domain='{self.requested_domain}', status='{self.status}')>"


class DomainConfiguration(BaseModel):
    """
    Technical configuration for approved domains.
    """
    
    __tablename__ = "domain_configurations"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    domain_request_id = Column(Integer, ForeignKey("domain_requests.id"), nullable=False, unique=True, index=True)
    
    # ========================================================================
    # DNS Configuration
    # ========================================================================
    cname_record = Column(String(255), nullable=True)  # CNAME target
    a_record = Column(String(45), nullable=True)  # IP address for A record
    txt_record = Column(String(500), nullable=True)  # TXT record for verification
    
    # ========================================================================
    # SSL Configuration
    # ========================================================================
    ssl_certificate_id = Column(String(255), nullable=True)
    ssl_status = Column(String(50), nullable=False, default="pending")  # pending, active, expired, failed
    ssl_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================================================
    # Load Balancer Configuration
    # ========================================================================
    load_balancer_id = Column(String(255), nullable=True)
    backend_servers = Column(Text, nullable=True)  # JSON array of backend servers
    
    # ========================================================================
    # Monitoring
    # ========================================================================
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), nullable=False, default="unknown")  # healthy, unhealthy, unknown
    uptime_percentage = Column(Numeric(5, 2), nullable=True)  # 99.99%
    
    # ========================================================================
    # Configuration Status
    # ========================================================================
    is_configured = Column(Boolean, default=False, nullable=False)
    configuration_notes = Column(Text, nullable=True)
    
    # ========================================================================
    # Relationships
    # ========================================================================
    domain_request = relationship("DomainRequest", backref="configuration")
    
    def __repr__(self):
        return f"<DomainConfiguration(domain_request_id={self.domain_request_id}, ssl_status='{self.ssl_status}')>"


class DomainUsageLog(BaseModel):
    """
    Usage and analytics logs for domains.
    """
    
    __tablename__ = "domain_usage_logs"
    
    # ========================================================================
    # Relationships
    # ========================================================================
    domain_request_id = Column(Integer, ForeignKey("domain_requests.id"), nullable=False, index=True)
    
    # ========================================================================
    # Usage Metrics
    # ========================================================================
    log_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    page_views = Column(Integer, nullable=False, default=0)
    unique_visitors = Column(Integer, nullable=False, default=0)
    bandwidth_mb = Column(Numeric(10, 2), nullable=False, default=0.0)
    
    # ========================================================================
    # Performance Metrics
    # ========================================================================
    avg_response_time = Column(Numeric(8, 3), nullable=True)  # milliseconds
    error_count = Column(Integer, nullable=False, default=0)
    uptime_minutes = Column(Integer, nullable=False, default=0)
    
    # ========================================================================
    # Geographic Data
    # ========================================================================
    top_countries = Column(Text, nullable=True)  # JSON array of country stats
    top_cities = Column(Text, nullable=True)  # JSON array of city stats
    
    # ========================================================================
    # Relationships
    # ========================================================================
    domain_request = relationship("DomainRequest", backref="usage_logs")
    
    def __repr__(self):
        return f"<DomainUsageLog(domain_request_id={self.domain_request_id}, date={self.log_date})>"