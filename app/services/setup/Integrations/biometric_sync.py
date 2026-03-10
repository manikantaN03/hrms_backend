# app/services/setup/Integrations/biometric_sync.py

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business import Business
from app.repositories.setup.Integrations import biometric_sync as repo
from app.schemas.setup.Integrations.biometric_sync import (
    BiometricDeviceCreate,
    BiometricDeviceUpdate,
    DeviceListResponse,
    SyncLogsRequest,
    SyncLogsResponse,
)


# =========================================================
# DEVICE SERVICES
# =========================================================

def list_devices_service(
    db: Session,
    business_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> DeviceListResponse:
    """List all biometric devices"""
    devices = repo.list_devices(db, business_id=business_id, tenant_id=tenant_id)
    
    # Get license count from business
    license_count = 3  # Default fallback
    if business_id:
        business = db.query(Business).filter(Business.id == business_id).first()
        if business and hasattr(business, 'biometric_license_count'):
            license_count = business.biometric_license_count
    
    return DeviceListResponse(
        devices=devices,
        total=len(devices),
        license_count=license_count,
    )


def get_device_service(db: Session, device_id: int):
    """Get a single device"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    return device


def create_device_service(
    db: Session,
    payload: BiometricDeviceCreate,
):
    """Create a new biometric device"""
    # Verify business exists
    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    # Create device
    device = repo.create_device(
        db,
        device_name=payload.name,
        business_id=payload.business_id,
        tenant_id=payload.tenant_id,
    )
    
    return device


def update_device_service(
    db: Session,
    device_id: int,
    payload: BiometricDeviceUpdate,
):
    """Update a device"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    # Update fields
    update_data = payload.model_dump(exclude_unset=True, by_alias=False)
    device = repo.update_device(db, device, **update_data)
    
    return device


def delete_device_service(db: Session, device_id: int):
    """Delete a device"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    repo.delete_device(db, device)


def toggle_activation_service(db: Session, device_id: int):
    """Toggle device activation"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    device = repo.toggle_activation(db, device)
    return device


def reset_registration_service(db: Session, device_id: int):
    """Reset device registration"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    device = repo.reset_registration(db, device)
    return device


def get_device_code_service(db: Session, device_id: int):
    """Get device code"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    return {"deviceCode": device.device_code}


# =========================================================
# SYNC LOG SERVICES
# =========================================================

def get_sync_logs_service(
    db: Session,
    device_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> SyncLogsResponse:
    """Get sync logs for a device"""
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    
    logs = repo.get_sync_logs(
        db,
        device_id=device_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    return SyncLogsResponse(
        logs=logs,
        total=len(logs),
    )
