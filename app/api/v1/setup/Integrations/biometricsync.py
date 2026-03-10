# app/api/v1/setup/Integrations/biometricsync.py

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.setup.Integrations.biometricsync import (
    BiometricDeviceCreate,
    BiometricDeviceUpdate,
    BiometricDeviceOut,
    BiometricSyncLogOut,
)
from app.services.setup.Integrations import biometricsync as svc
from app.api.v1.deps import get_current_admin
from app.models.user import User


router = APIRouter(
    prefix="/integrations/biometric-sync",
)


# ---------- DEVICES ----------

@router.get(
    "/{business_id}/devices",
    response_model=List[BiometricDeviceOut],
)
def list_devices(
    business_id: int,
    tenant_id: Optional[int] = Query(default=None, alias="tenantId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List biometric devices for a given business (and optional tenant).
    """
    return svc.list_devices_service(
        db,
        business_id=business_id,
        tenant_id=tenant_id,
    )


@router.post(
    "/devices",
    response_model=BiometricDeviceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    payload: BiometricDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new biometric device.
    """
    return svc.create_device_service(db, payload)


@router.put(
    "/{business_id}/devices/{device_id}",
    response_model=BiometricDeviceOut,
)
def update_device(
    business_id: int,
    device_id: int,
    payload: BiometricDeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an existing biometric device.
    """
    return svc.update_device_service(db, device_id, payload)


@router.delete(
    "/{business_id}/devices/{device_id}",
    status_code=status.HTTP_200_OK,
)
def delete_device(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a biometric device.
    """
    svc.delete_device_service(db, device_id)
    return {"message": "Device deleted"}


@router.patch(
    "/{business_id}/devices/{device_id}/toggle-activate",
    response_model=BiometricDeviceOut,
)
def toggle_activation(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Toggle activation state of a biometric device.
    """
    return svc.toggle_activation_service(db, device_id)


@router.post(
    "/{business_id}/devices/{device_id}/reset-registration",
    response_model=BiometricDeviceOut,
)
def reset_registration(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Reset registration of a biometric device.
    """
    return svc.reset_registration_service(db, device_id)


@router.get(
    "/{business_id}/devices/{device_id}/logs",
    response_model=List[BiometricSyncLogOut],
)
def list_logs(
    business_id: int,
    device_id: int,
    start_date: Optional[date] = Query(None, alias="startDate"),
    end_date: Optional[date] = Query(None, alias="endDate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List biometric sync logs for a device.
    """
    return svc.list_logs_service(db, device_id, start_date, end_date)
