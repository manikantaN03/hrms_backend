# app/schemas/gatekeeper.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CamelModel(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True


# ----------------------------------------------------
# CREATE / UPDATE SCHEMAS
# ----------------------------------------------------

class GatekeeperDeviceCreate(CamelModel):
    """
    Schema for creating a new gatekeeper device
    Frontend will send:
    {
        "businessId": 3,
        "deviceName": "Main Gate",
        "deviceModel": "GK-101"
    }
    """
    business_id: int = Field(
        alias="businessId",
        gt=0,
        description="Business ID to which this device belongs"
    )
    name: str = Field(
        alias="deviceName",
        min_length=1,
        max_length=200,
        description="Device name (e.g., 'Main Gate Scanner')"
    )
    device_model: Optional[str] = Field(
        alias="deviceModel",
        default=None,
        max_length=100,
        description="Device model (e.g., 'GK-101')"
    )
    tenant_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Optional tenant ID for multi-tenant setup"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name is not empty or whitespace"""
        if not v or not v.strip():
            raise ValueError("Device name cannot be empty or whitespace")
        return v.strip()
    
    @field_validator("device_model")
    @classmethod
    def validate_device_model(cls, v: Optional[str]) -> Optional[str]:
        """Validate device model is not empty if provided"""
        if v is not None and v.strip():
            return v.strip()
        return None


class GatekeeperDeviceUpdate(CamelModel):
    """
    Schema for updating an existing gatekeeper device
    Frontend allows editing device name/model
    """
    business_id: Optional[int] = Field(
        alias="businessId",
        default=None,
        gt=0,
        description="Business ID (optional for update)"
    )
    name: Optional[str] = Field(
        alias="deviceName",
        default=None,
        min_length=1,
        max_length=200,
        description="Device name"
    )
    device_model: Optional[str] = Field(
        alias="deviceModel",
        default=None,
        max_length=100,
        description="Device model"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate device name is not empty or whitespace"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Device name cannot be empty or whitespace")
        return v.strip() if v else None
    
    @field_validator("device_model")
    @classmethod
    def validate_device_model(cls, v: Optional[str]) -> Optional[str]:
        """Validate device model is not empty if provided"""
        if v is not None and v.strip():
            return v.strip()
        return None


# ----------------------------------------------------
# OUTPUT SCHEMA (TABLE + MODALS)
# ----------------------------------------------------

class GatekeeperDeviceOut(CamelModel):
    """Schema for gatekeeper device output"""
    id: int = Field(description="Device ID")

    # Return businessId so frontend knows where device belongs
    business_id: Optional[int] = Field(
        default=None,
        serialization_alias="businessId",
        description="Business ID"
    )

    name: str = Field(description="Device name")

    device_model: Optional[str] = Field(
        default=None,
        serialization_alias="deviceModel",
        description="Device model"
    )

    last_seen: Optional[datetime] = Field(
        default=None,
        serialization_alias="lastSeen",
        description="Last seen timestamp"
    )

    # "Not Activated" until activation
    app_version: str = Field(
        serialization_alias="appVersion",
        description="Application version or activation status"
    )

    device_code: str = Field(
        serialization_alias="code",
        description="Unique device code"
    )

    created_at: datetime = Field(
        serialization_alias="createdAt",
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        serialization_alias="updatedAt",
        description="Last update timestamp"
    )
