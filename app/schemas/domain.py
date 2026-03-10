"""
Domain Schemas
Pydantic models for domain request/response validation
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import re


# ============================================================================
# Domain Request Schemas
# ============================================================================

class DomainRequestBase(BaseModel):
    """Base domain request schema"""
    
    business_id: int = Field(..., description="Business ID")
    requested_domain: str = Field(..., min_length=3, max_length=255, description="Requested domain/subdomain")
    domain_type: str = Field(default="subdomain", description="Domain type (subdomain/custom_domain)")
    plan_name: str = Field(..., min_length=1, max_length=100, description="Plan name")
    plan_type: str = Field(..., min_length=1, max_length=50, description="Plan type (Monthly/Yearly)")
    price: Decimal = Field(..., gt=0, description="Domain price")
    currency: str = Field(default="USD", max_length=10, description="Currency code")
    auto_renew: bool = Field(default=True, description="Auto-renewal enabled")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @validator('requested_domain')
    def validate_domain(cls, v):
        """Validate domain format"""
        # Basic domain validation - allow simple domain patterns
        if not v or len(v) < 3:
            raise ValueError('Domain must be at least 3 characters')
        return v.lower()


class DomainRequestCreate(DomainRequestBase):
    """Schema for creating a new domain request"""
    pass


class DomainRequestUpdate(BaseModel):
    """Schema for updating a domain request"""
    
    requested_domain: Optional[str] = Field(None, min_length=3, max_length=255)
    domain_type: Optional[str] = Field(None, max_length=50)
    plan_name: Optional[str] = Field(None, min_length=1, max_length=100)
    plan_type: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    auto_renew: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)


class DomainApprovalUpdate(BaseModel):
    """Schema for approving/rejecting domain requests"""
    
    status: str = Field(..., pattern="^(Approved|Rejected)$", description="Approval status")
    rejection_reason: Optional[str] = Field(None, max_length=1000, description="Reason for rejection")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Internal admin notes")
    start_date: Optional[datetime] = Field(None, description="Domain start date (for approved domains)")
    expiry_date: Optional[datetime] = Field(None, description="Domain expiry date")


class DomainRequestResponse(DomainRequestBase):
    """Schema for domain request responses"""
    
    id: int
    user_id: int
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    start_date: Optional[datetime]
    expiry_date: Optional[datetime]
    ssl_enabled: bool
    dns_configured: bool
    is_active: bool
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields for frontend compatibility
    name: Optional[str] = None  # Business name
    url: Optional[str] = None  # Domain URL
    plan: Optional[str] = None  # Combined plan info
    createdDate: Optional[str] = None  # Formatted created date
    expiringOn: Optional[str] = None  # Formatted expiring date
    logo: Optional[str] = None  # Business logo
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Domain Configuration Schemas
# ============================================================================

class DomainConfigurationBase(BaseModel):
    """Base domain configuration schema"""
    
    cname_record: Optional[str] = Field(None, max_length=255, description="CNAME record")
    a_record: Optional[str] = Field(None, max_length=45, description="A record IP address")
    txt_record: Optional[str] = Field(None, max_length=500, description="TXT record for verification")
    ssl_certificate_id: Optional[str] = Field(None, max_length=255, description="SSL certificate ID")
    ssl_status: str = Field(default="pending", description="SSL status")
    load_balancer_id: Optional[str] = Field(None, max_length=255, description="Load balancer ID")
    backend_servers: Optional[str] = Field(None, description="Backend servers JSON")
    health_status: str = Field(default="unknown", description="Health check status")
    uptime_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Uptime percentage")
    configuration_notes: Optional[str] = Field(None, max_length=1000, description="Configuration notes")


class DomainConfigurationCreate(DomainConfigurationBase):
    """Schema for creating domain configuration"""
    
    domain_request_id: int = Field(..., description="Domain request ID")


class DomainConfigurationUpdate(DomainConfigurationBase):
    """Schema for updating domain configuration"""
    
    is_configured: Optional[bool] = None


class DomainConfigurationResponse(DomainConfigurationBase):
    """Schema for domain configuration responses"""
    
    id: int
    domain_request_id: int
    ssl_expiry: Optional[datetime]
    last_health_check: Optional[datetime]
    is_configured: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Domain Usage Log Schemas
# ============================================================================

class DomainUsageLogBase(BaseModel):
    """Base domain usage log schema"""
    
    page_views: int = Field(default=0, ge=0, description="Page views count")
    unique_visitors: int = Field(default=0, ge=0, description="Unique visitors count")
    bandwidth_mb: Decimal = Field(default=0.0, ge=0, description="Bandwidth usage in MB")
    avg_response_time: Optional[Decimal] = Field(None, ge=0, description="Average response time in ms")
    error_count: int = Field(default=0, ge=0, description="Error count")
    uptime_minutes: int = Field(default=0, ge=0, description="Uptime in minutes")
    top_countries: Optional[str] = Field(None, description="Top countries JSON")
    top_cities: Optional[str] = Field(None, description="Top cities JSON")


class DomainUsageLogCreate(DomainUsageLogBase):
    """Schema for creating domain usage log"""
    
    domain_request_id: int = Field(..., description="Domain request ID")
    log_date: Optional[datetime] = Field(None, description="Log date")


class DomainUsageLogResponse(DomainUsageLogBase):
    """Schema for domain usage log responses"""
    
    id: int
    domain_request_id: int
    log_date: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Dashboard and Summary Schemas
# ============================================================================

class DomainSummary(BaseModel):
    """Domain summary for dashboard"""
    
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    active_domains: int
    expiring_soon: int


class DomainListResponse(BaseModel):
    """Response for domain list with frontend compatibility"""
    
    id: int
    name: str  # Business name
    url: str  # Domain URL
    plan: str  # Plan with type
    createdDate: str  # Formatted created date
    expiringOn: str  # Formatted expiring date
    status: str  # Status
    price: str  # Price as string
    logo: str  # Logo URL
    
    model_config = ConfigDict(from_attributes=True)


class DomainAnalytics(BaseModel):
    """Domain analytics data"""
    
    domain_id: int
    domain_url: str
    total_page_views: int
    total_unique_visitors: int
    total_bandwidth_gb: Decimal
    avg_response_time: Optional[Decimal]
    uptime_percentage: Optional[Decimal]
    error_rate: Optional[Decimal]
    
    model_config = ConfigDict(from_attributes=True)