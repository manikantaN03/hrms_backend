# app/services/setup/Integrations/biometricsync.py

import random
import string
from typing import List, Optional
from datetime import date

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.setup.Integrations.biometricsync import (
    BiometricDeviceCreate,
    BiometricDeviceUpdate,
    BiometricDeviceOut,
    BiometricSyncLogOut,
)
from app.repositories.setup.Integrations import biometricsync as repo
from app.models.setup.Integrations.biometricsync import (
    BiometricDevice,
)
from app.models.business import Business


def _generate_device_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ---------- DEVICE ----------

def list_devices_service(
    db: Session,
    business_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> List[BiometricDeviceOut]:
    """
    Return all biometric devices, optionally filtered by business / tenant.
    Used by: GET /integrations/biometric-sync/devices?businessId=&tenantId=
    """
    devices = repo.list_devices(
        db,
        business_id=business_id,
        tenant_id=tenant_id,
    )
    return [BiometricDeviceOut.model_validate(d) for d in devices]


def create_device_service(db: Session, payload: BiometricDeviceCreate) -> BiometricDeviceOut:
    """
    Create new biometric device.

    payload has:
      - business_id (alias: businessId)
      - name (alias: deviceName)
      - host_url (alias: hostURL)
      - app_version (alias: appVersion)
      - tenant_id (optional)
    """
    # ✅ Validate that the business exists before creating device
    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {payload.business_id} does not exist"
        )
    
    device_code = _generate_device_code()

    device = repo.create_device(
        db,
        business_id=payload.business_id,
        tenant_id=payload.tenant_id,
        name=payload.name,
        host_url=payload.host_url,
        app_version=payload.app_version or "1.0",
        device_code=device_code,
    )
    return BiometricDeviceOut.model_validate(device)


def _get_device_or_404(db: Session, device_id: int) -> BiometricDevice:
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


def update_device_service(
    db: Session, device_id: int, payload: BiometricDeviceUpdate
) -> BiometricDeviceOut:
    device = _get_device_or_404(db, device_id)

    # ✅ Validate that the new business exists (if business_id is being updated)
    if payload.business_id is not None:
        business = db.query(Business).filter(Business.id == payload.business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business with ID {payload.business_id} does not exist"
            )

    device = repo.update_device(
        db,
        device,
        business_id=payload.business_id,  # can be None (no change) or int (move to another business)
        name=payload.name,
        host_url=payload.host_url,
        app_version=payload.app_version,
    )
    return BiometricDeviceOut.model_validate(device)


def delete_device_service(db: Session, device_id: int) -> None:
    device = _get_device_or_404(db, device_id)
    repo.delete_device(db, device)


def toggle_activation_service(db: Session, device_id: int) -> BiometricDeviceOut:
    device = _get_device_or_404(db, device_id)
    device = repo.toggle_activation(db, device)
    return BiometricDeviceOut.model_validate(device)


def reset_registration_service(db: Session, device_id: int) -> BiometricDeviceOut:
    device = _get_device_or_404(db, device_id)
    new_code = _generate_device_code()
    device = repo.reset_registration(db, device, new_code)
    return BiometricDeviceOut.model_validate(device)


# ---------- LOGS ----------

def list_logs_service(
    db: Session,
    device_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
) -> List[BiometricSyncLogOut]:
    _get_device_or_404(db, device_id)  # ensure exists
    logs = repo.list_logs_for_device(db, device_id, start_date, end_date)
    return [BiometricSyncLogOut.model_validate(l) for l in logs]
