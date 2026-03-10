# app/repositories/setup/Integrations/biometric_sync.py

import secrets
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.setup.Integrations.biometricsync import (
    BiometricDevice,
    BiometricSyncLog,
)


# =====================================================
# BIOMETRIC DEVICE REPOSITORY
# =====================================================

def get_device(db: Session, device_id: int) -> Optional[BiometricDevice]:
    """Get device by ID"""
    return db.get(BiometricDevice, device_id)


def get_device_by_code(db: Session, device_code: str) -> Optional[BiometricDevice]:
    """Get device by device code"""
    return (
        db.query(BiometricDevice)
        .filter(BiometricDevice.device_code == device_code)
        .first()
    )


def list_devices(
    db: Session,
    business_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> List[BiometricDevice]:
    """List all devices with optional filters"""
    query = db.query(BiometricDevice)
    
    if business_id is not None:
        query = query.filter(BiometricDevice.business_id == business_id)
    
    if tenant_id is not None:
        query = query.filter(BiometricDevice.tenant_id == tenant_id)
    
    return query.order_by(BiometricDevice.created_at.desc()).all()


def generate_device_code() -> str:
    """Generate a unique 6-character device code"""
    return secrets.token_hex(3).upper()


def create_device(
    db: Session,
    *,
    device_name: str,
    business_id: int,
    tenant_id: Optional[int] = None,
) -> BiometricDevice:
    """Create a new biometric device"""
    # Generate unique device code
    device_code = generate_device_code()
    
    # Ensure uniqueness
    while get_device_by_code(db, device_code):
        device_code = generate_device_code()
    
    device = BiometricDevice(
        name=device_name,
        device_code=device_code,
        business_id=business_id,
        tenant_id=tenant_id,
        activated=False,
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device(
    db: Session,
    device: BiometricDevice,
    **kwargs
) -> BiometricDevice:
    """Update device fields"""
    for key, value in kwargs.items():
        if value is not None and hasattr(device, key):
            setattr(device, key, value)
    
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device: BiometricDevice) -> None:
    """Delete a device"""
    db.delete(device)
    db.commit()


def toggle_activation(db: Session, device: BiometricDevice) -> BiometricDevice:
    """Toggle device activation status"""
    device.activated = not device.activated
    device.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


def reset_registration(db: Session, device: BiometricDevice) -> BiometricDevice:
    """Reset device registration"""
    device.activated = False
    device.last_seen = None
    db.commit()
    db.refresh(device)
    return device


def update_last_seen(db: Session, device: BiometricDevice) -> BiometricDevice:
    """Update device last seen timestamp"""
    device.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


# =====================================================
# SYNC LOG REPOSITORY
# =====================================================

def create_sync_log(
    db: Session,
    *,
    device_id: int,
    synced_at: datetime,
    status: str,
    message: Optional[str] = None,
) -> BiometricSyncLog:
    """Create a sync log entry"""
    log = BiometricSyncLog(
        device_id=device_id,
        synced_at=synced_at,
        status=status,
        message=message,
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_sync_logs(
    db: Session,
    device_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[BiometricSyncLog]:
    """Get sync logs for a device with optional date range"""
    query = db.query(BiometricSyncLog).filter(
        BiometricSyncLog.device_id == device_id
    )
    
    if start_date:
        query = query.filter(BiometricSyncLog.synced_at >= start_date)
    
    if end_date:
        query = query.filter(BiometricSyncLog.synced_at <= end_date)
    
    return query.order_by(BiometricSyncLog.synced_at.desc()).all()
