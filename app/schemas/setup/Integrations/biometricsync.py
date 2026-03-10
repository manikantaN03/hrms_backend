# app/schemas/biometricsync.py
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class CamelModel(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True


# ---------------------------------------------------------
# CREATE DEVICE
# ---------------------------------------------------------

class BiometricDeviceCreate(CamelModel):
    """
    Frontend will send:
    {
        "businessId": 3,
        "deviceName": "Biometric Gate",
        "hostURL": "https://in2.runtimehrms.com",
        "appVersion": "1.0"
    }
    """
    business_id: int = Field(alias="businessId")
    name: str = Field(alias="deviceName")
    host_url: Optional[str] = Field(alias="hostURL", default="https://in2.runtimehrms.com")
    app_version: Optional[str] = Field(alias="appVersion", default="1.0")
    tenant_id: Optional[int] = None


# ---------------------------------------------------------
# UPDATE DEVICE
# ---------------------------------------------------------

class BiometricDeviceUpdate(CamelModel):
    business_id: Optional[int] = Field(alias="businessId", default=None)
    name: Optional[str] = Field(alias="deviceName", default=None)
    host_url: Optional[str] = Field(alias="hostURL", default=None)
    app_version: Optional[str] = Field(alias="appVersion", default=None)


# ---------------------------------------------------------
# OUTPUT (TABLE + MODALS)
# ---------------------------------------------------------

class BiometricDeviceOut(CamelModel):
    id: int

    # Return businessId so frontend knows which business owns this device
    business_id: Optional[int] = Field(default=None, alias="businessId")

    name: str = Field(alias="deviceName")
    device_code: str = Field(alias="code")
    host_url: str = Field(alias="hostURL")
    last_seen: Optional[datetime] = Field(alias="lastSeen")
    activated: bool
    app_version: str = Field(alias="appVersion")

    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


# ---------------------------------------------------------
# LOGS
# ---------------------------------------------------------

class BiometricSyncLogOut(CamelModel):
    id: int
    device_id: int
    synced_at: datetime = Field(alias="syncedAt")
    status: str
    message: Optional[str] = None
