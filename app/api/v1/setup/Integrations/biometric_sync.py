# app/api/v1/setup/Integrations/biometric_sync.py

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.Integrations.biometric_sync import (
    BiometricDeviceCreate,
    BiometricDeviceUpdate,
    BiometricDeviceOut,
    DeviceListResponse,
    DeviceCodeResponse,
    SyncLogsResponse,
)

from app.services.setup.Integrations import biometric_sync as svc


router = APIRouter(
    prefix="/integrations/biometric-sync",
    tags=["Integrations - Biometric Sync"],
)


# =====================================================
# DEVICE ENDPOINTS
# =====================================================

@router.get(
    "/{business_id}/devices",
    response_model=DeviceListResponse,
)
def list_devices(
    business_id: int,
    tenant_id: Optional[int] = Query(default=None, alias="tenantId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """List all biometric devices"""
    return svc.list_devices_service(
        db,
        business_id=business_id,
        tenant_id=tenant_id,
    )


@router.post(
    "/device",
    response_model=BiometricDeviceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    payload: BiometricDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Create a new biometric device"""
    return svc.create_device_service(db, payload)


@router.get(
    "/{business_id}/device/{device_id}",
    response_model=BiometricDeviceOut,
)
def get_device(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Get a single device"""
    return svc.get_device_service(db, device_id)


@router.put(
    "/{business_id}/device/{device_id}",
    response_model=BiometricDeviceOut,
)
def update_device(
    business_id: int,
    device_id: int,
    payload: BiometricDeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Update a device"""
    return svc.update_device_service(db, device_id, payload)


@router.delete(
    "/{business_id}/device/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_device(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Delete a device"""
    svc.delete_device_service(db, device_id)
    return None


@router.patch(
    "/{business_id}/device/{device_id}/toggle-activation",
    response_model=BiometricDeviceOut,
)
def toggle_activation(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Toggle device activation status"""
    return svc.toggle_activation_service(db, device_id)


@router.post(
    "/{business_id}/device/{device_id}/reset-registration",
    response_model=BiometricDeviceOut,
)
def reset_registration(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Reset device registration"""
    return svc.reset_registration_service(db, device_id)


@router.get(
    "/{business_id}/device/{device_id}/code",
    response_model=DeviceCodeResponse,
)
def get_device_code(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Get device code"""
    return svc.get_device_code_service(db, device_id)


# =====================================================
# SYNC LOG ENDPOINTS
# =====================================================

@router.get(
    "/{business_id}/device/{device_id}/logs",
    response_model=SyncLogsResponse,
)
def get_sync_logs(
    business_id: int,
    device_id: int,
    start_date: Optional[datetime] = Query(default=None, alias="startDate"),
    end_date: Optional[datetime] = Query(default=None, alias="endDate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Get sync logs for a device"""
    return svc.get_sync_logs_service(
        db,
        device_id=device_id,
        start_date=start_date,
        end_date=end_date,
    )
