"""
Remote Session Schemas
Pydantic schemas for remote session validation
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class RemoteSessionStatus(str, Enum):
    """Remote session status enumeration"""
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RemoteSessionType(str, Enum):
    """Remote session type enumeration"""
    TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT"
    SOFTWARE_INSTALLATION = "SOFTWARE_INSTALLATION"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    TRAINING = "TRAINING"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    OTHER = "OTHER"


class RemoteSessionBase(BaseModel):
    """Base remote session schema"""
    session_type: RemoteSessionType = Field(..., description="Type of remote session")
    title: str = Field(..., min_length=5, max_length=255, description="Session title")
    description: str = Field(..., min_length=10, description="Detailed description")
    requested_date: datetime = Field(..., description="Requested date and time")
    computer_name: Optional[str] = Field(None, max_length=100, description="Computer name")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP address")
    operating_system: Optional[str] = Field(None, max_length=100, description="Operating system")
    issue_category: Optional[str] = Field(None, max_length=100, description="Issue category")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty or whitespace only')
        return v.strip()


class RemoteSessionCreate(RemoteSessionBase):
    """Schema for creating a remote session"""
    employee_id: Optional[int] = Field(None, description="Employee ID (optional for superadmin)")


class RemoteSessionUpdate(BaseModel):
    """Schema for updating a remote session"""
    session_type: Optional[RemoteSessionType] = None
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[RemoteSessionStatus] = None
    support_agent_id: Optional[int] = None
    computer_name: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = Field(None, max_length=50)
    operating_system: Optional[str] = Field(None, max_length=100)
    issue_category: Optional[str] = Field(None, max_length=100)
    agent_notes: Optional[str] = None
    resolution_notes: Optional[str] = None


class RemoteSessionResponse(RemoteSessionBase):
    """Schema for remote session response"""
    id: int
    business_id: int
    employee_id: int
    support_agent_id: Optional[int] = None
    status: RemoteSessionStatus
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields from joins
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    support_agent_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RemoteSessionRating(BaseModel):
    """Schema for rating a remote session"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    feedback: Optional[str] = Field(None, max_length=1000, description="Optional feedback")
    
    @validator('feedback')
    def validate_feedback(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v
