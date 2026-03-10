# app/repositories/biometricsync.py
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy.orm import Session

from app.models.setup.Integrations.biometricsync import (
    BiometricDevice,
    BiometricSyncLog,
)


# ---------- DEVICES ----------

def list_devices(
    db: Session,
    business_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> List[BiometricDevice]:
    """
    Return devices, optionally filtered by business and/or tenant.
    Used by: list_devices_service(...)
    """
    q = db.query(BiometricDevice)

    if business_id is not None:
        q = q.filter(BiometricDevice.business_id == business_id)

    if tenant_id is not None:
        q = q.filter(BiometricDevice.tenant_id == tenant_id)

    return q.order_by(BiometricDevice.created_at.desc()).all()


def get_device(db: Session, device_id: int) -> Optional[BiometricDevice]:
    return db.get(BiometricDevice, device_id)


def create_device(
    db: Session,
    *,
    business_id: int,
    name: str,
    host_url: str,
    app_version: str,
    tenant_id: Optional[int],
    device_code: str,
) -> BiometricDevice:
    """
    Insert a new BiometricDevice row.
    Now includes business_id for multi-business setup.
    """
    device = BiometricDevice(
        business_id=business_id,
        name=name,
        host_url=host_url,
        app_version=app_version,
        tenant_id=tenant_id,
        device_code=device_code,
        activated=False,
        last_seen=None,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device(
    db: Session,
    device: BiometricDevice,
    *,
    business_id: Optional[int] = None,
    name: Optional[str] = None,
    host_url: Optional[str] = None,
    app_version: Optional[str] = None,
) -> BiometricDevice:
    """
    Update existing device fields (only if provided).
    Can also move device to a different business if business_id is passed.
    """
    if business_id is not None:
        device.business_id = business_id
    if name is not None:
        device.name = name
    if host_url is not None:
        device.host_url = host_url
    if app_version is not None:
        device.app_version = app_version

    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device: BiometricDevice) -> None:
    db.delete(device)
    db.commit()


def toggle_activation(db: Session, device: BiometricDevice) -> BiometricDevice:
    device.activated = not device.activated
    device.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


def reset_registration(
    db: Session,
    device: BiometricDevice,
    new_code: str,
) -> BiometricDevice:
    device.device_code = new_code
    device.activated = False
    device.last_seen = None
    db.commit()
    db.refresh(device)
    return device


# ---------- LOGS ----------

def list_logs_for_device(
    db: Session,
    device_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[BiometricSyncLog]:
    q = db.query(BiometricSyncLog).filter(
        BiometricSyncLog.device_id == device_id
    )

    if start_date:
        q = q.filter(
            BiometricSyncLog.synced_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        q = q.filter(
            BiometricSyncLog.synced_at <= datetime.combine(end_date, datetime.max.time())
        )

    return q.order_by(BiometricSyncLog.synced_at.desc()).all()
