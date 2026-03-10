# app/schemas/setup/Integrations/biometric_sync.py

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, HttpUrl


# =========================================================
# BASE CAMEL CASE MODEL
# =========================================================

class CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        },
    )


# =========================================================
# BIOMETRIC DEVICE SCHEMAS
# =========================================================

class BiometricDeviceCreate(CamelModel):
    """Schema for creating a new biometric device"""
    name: str = Field(
        alias="deviceName",
        min_length=1,
        max_length=200,
        description="Device name (e.g., 'Main Gate Biometric')"
    )
    business_id: int = Field(
        alias="businessId",
        gt=0,
        description="Business ID to which this device belongs"
    )
    tenant_id: Optional[int] = Field(
        default=None,
        alias="tenantId",
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


class BiometricDeviceUpdate(CamelModel):
    """Schema for updating an existing biometric device"""
    name: Optional[str] = Field(
        default=None,
        alias="deviceName",
        min_length=1,
        max_length=200,
        description="Device name"
    )
    host_url: Optional[str] = Field(
        default=None,
        alias="hostUrl",
        max_length=255,
        description="Host URL for the device"
    )
    activated: Optional[bool] = Field(
        default=None,
        alias="isActivated",
        description="Device activation status"
    )
    app_version: Optional[str] = Field(
        default=None,
        alias="appVersion",
        max_length=50,
        description="Application version"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate device name is not empty or whitespace"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Device name cannot be empty or whitespace")
        return v.strip() if v else None
    
    @field_validator("host_url")
    @classmethod
    def validate_host_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate host URL format"""
        if v is not None and v.strip():
            if not v.startswith(("http://", "https://")):
                raise ValueError("Host URL must start with http:// or https://")
        return v
    
    @field_validator("app_version")
    @classmethod
    def validate_app_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate app version is not empty"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("App version cannot be empty or whitespace")
        return v.strip() if v else None


class BiometricDeviceOut(CamelModel):
    """Schema for biometric device output"""
    id: int = Field(description="Device ID")
    name: str = Field(alias="deviceName", description="Device name")
    device_code: str = Field(alias="deviceCode", description="Unique device code")
    host_url: str = Field(alias="hostUrl", description="Host URL")
    activated: bool = Field(alias="isActivated", description="Activation status")
    last_seen: Optional[datetime] = Field(
        default=None,
        alias="lastSeen",
        description="Last seen timestamp"
    )
    app_version: Optional[str] = Field(
        default="1.0",
        alias="appVersion",
        description="Application version"
    )
    business_id: int = Field(alias="businessId", description="Business ID")
    tenant_id: Optional[int] = Field(
        default=None,
        alias="tenantId",
        description="Tenant ID"
    )
    created_at: datetime = Field(alias="createdAt", description="Creation timestamp")
    updated_at: datetime = Field(alias="updatedAt", description="Last update timestamp")


# =========================================================
# SYNC LOG SCHEMAS
# =========================================================

class BiometricSyncLogCreate(CamelModel):
    """Schema for creating a sync log entry"""
    device_id: int = Field(
        alias="deviceId",
        gt=0,
        description="Device ID"
    )
    synced_at: datetime = Field(
        alias="syncDate",
        description="Sync timestamp"
    )
    status: Literal["SUCCESS", "FAILED", "PARTIAL"] = Field(
        description="Sync status"
    )
    message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Sync message or error details"
    )


class BiometricSyncLogOut(CamelModel):
    """Schema for sync log output"""
    id: int = Field(description="Log ID")
    device_id: int = Field(alias="deviceId", description="Device ID")
    synced_at: datetime = Field(alias="syncDate", description="Sync timestamp")
    status: str = Field(description="Sync status")
    message: Optional[str] = Field(default=None, description="Sync message")


# =========================================================
# REQUEST/RESPONSE SCHEMAS
# =========================================================

class DeviceListResponse(CamelModel):
    """Response schema for device list"""
    devices: List[BiometricDeviceOut] = Field(description="List of devices")
    total: int = Field(ge=0, description="Total number of devices")
    license_count: int = Field(
        alias="licenseCount",
        ge=0,
        description="Total license count"
    )


class DeviceCodeResponse(CamelModel):
    """Response schema for device code"""
    device_code: str = Field(
        alias="deviceCode",
        min_length=1,
        description="Unique device code"
    )


class ResetRegistrationRequest(CamelModel):
    """Request schema for resetting device registration"""
    device_id: int = Field(
        alias="deviceId",
        gt=0,
        description="Device ID to reset"
    )


class SyncLogsRequest(CamelModel):
    """Request schema for fetching sync logs"""
    device_id: int = Field(
        alias="deviceId",
        gt=0,
        description="Device ID"
    )
    start_date: Optional[datetime] = Field(
        default=None,
        alias="startDate",
        description="Start date for filtering logs"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        alias="endDate",
        description="End date for filtering logs"
    )
    
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate end_date is after start_date"""
        if v is not None and info.data.get("start_date") is not None:
            if v < info.data["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class SyncLogsResponse(CamelModel):
    """Response schema for sync logs"""
    logs: List[BiometricSyncLogOut] = Field(description="List of sync logs")
    total: int = Field(ge=0, description="Total number of logs")
