"""
Additional Pydantic schemas for Domain endpoints
Replaces Dict[str, Any] and dict with proper typed schemas for Swagger/OpenAPI documentation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class DomainConfigurationUpdateRequest(BaseModel):
    """Schema for updating domain configuration"""
    
    cname_record: Optional[str] = Field(
        default=None,
        max_length=255,
        description="CNAME target record",
        example="app.example.com"
    )
    a_record: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address for A record",
        example="192.168.1.1"
    )
    txt_record: Optional[str] = Field(
        default=None,
        max_length=500,
        description="TXT record for verification",
        example="verification-token-12345"
    )
    ssl_certificate_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="SSL certificate ID",
        example="cert-abc123"
    )
    ssl_status: Optional[str] = Field(
        default=None,
        max_length=50,
        description="SSL status (pending, active, expired, failed)",
        example="active"
    )
    ssl_expiry: Optional[datetime] = Field(
        default=None,
        description="SSL certificate expiry date",
        example="2026-12-31T23:59:59"
    )
    load_balancer_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Load balancer ID",
        example="lb-xyz789"
    )
    backend_servers: Optional[str] = Field(
        default=None,
        description="JSON array of backend servers",
        example='["server1.example.com", "server2.example.com"]'
    )
    health_status: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Health status (healthy, unhealthy, unknown)",
        example="healthy"
    )
    uptime_percentage: Optional[Decimal] = Field(
        default=None,
        description="Uptime percentage (e.g., 99.99)",
        example=99.99
    )
    is_configured: Optional[bool] = Field(
        default=None,
        description="Whether domain is fully configured",
        example=True
    )
    configuration_notes: Optional[str] = Field(
        default=None,
        description="Configuration notes",
        example="Domain configured successfully"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cname_record": "app.example.com",
                "a_record": "192.168.1.1",
                "ssl_status": "active",
                "ssl_expiry": "2026-12-31T23:59:59",
                "health_status": "healthy",
                "uptime_percentage": 99.99,
                "is_configured": True,
                "configuration_notes": "Domain configured successfully"
            }
        }
