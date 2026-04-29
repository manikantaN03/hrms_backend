# app/api/v1/setup/Integrations/biometricsync.py

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.setup.Integrations.biometricsync import (
    BiometricDeviceCreate,
    BiometricDeviceUpdate,
    BiometricDeviceOut,
    BiometricSyncLogOut,
)
from app.services.setup.Integrations import biometricsync as svc
from app.api.v1.deps import get_current_admin, validate_business_access
from app.models.user import User


router = APIRouter(
    prefix="/integrations/biometric-sync",
)


# ---------- DEVICES ----------

@router.get(
    "/devices",
    response_model=List[BiometricDeviceOut],
)
def list_devices(
    business_id: int = Path(...),
    tenant_id: Optional[int] = Query(default=None, alias="tenantId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List biometric devices for a given business (and optional tenant).
    """
    validate_business_access(business_id, current_user, db)
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
    # Ensure the admin has access to the business specified in the payload
    validate_business_access(payload.business_id, current_user, db)
    return svc.create_device_service(db, payload)


@router.put(
    "/devices/{device_id}",
    response_model=BiometricDeviceOut,
)
def update_device(
    business_id: int = Path(...),
    device_id: int = Path(...),
    payload: BiometricDeviceUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an existing biometric device.
    """
    validate_business_access(business_id, current_user, db)
    return svc.update_device_service(db, device_id, payload)


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_200_OK,
)
def delete_device(
    business_id: int = Path(...),
    device_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a biometric device.
    """
    validate_business_access(business_id, current_user, db)
    svc.delete_device_service(db, device_id)
    return {"message": "Device deleted"}


@router.patch(
    "/devices/{device_id}/toggle-activate",
    response_model=BiometricDeviceOut,
)
def toggle_activation(
    business_id: int = Path(...),
    device_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Toggle activation state of a biometric device.
    """
    validate_business_access(business_id, current_user, db)
    return svc.toggle_activation_service(db, device_id)


@router.post(
    "/devices/{device_id}/reset-registration",
    response_model=BiometricDeviceOut,
)
def reset_registration(
    business_id: int = Path(...),
    device_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Reset registration of a biometric device.
    """
    validate_business_access(business_id, current_user, db)
    return svc.reset_registration_service(db, device_id)


@router.get(
    "/devices/{device_id}/logs",
    response_model=List[BiometricSyncLogOut],
)
def list_logs(
    business_id: int = Path(...),
    device_id: int = Path(...),
    start_date: Optional[date] = Query(None, alias="startDate"),
    end_date: Optional[date] = Query(None, alias="endDate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List biometric sync logs for a device.
    """
    validate_business_access(business_id, current_user, db)
    return svc.list_logs_service(db, device_id, start_date, end_date)
