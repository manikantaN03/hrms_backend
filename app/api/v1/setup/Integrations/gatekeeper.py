# app/api/v1/setup/Integrations/gatekeeper.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.Integrations.gatekeeper import (
    GatekeeperDeviceCreate,
    GatekeeperDeviceUpdate,
    GatekeeperDeviceOut,
)
from app.services.setup.Integrations import gatekeeper as svc


router = APIRouter(
    prefix="/integrations/gatekeeper-devices",
)


# ---------------------------------------------------------
# LIST DEVICES  (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.get(
    "/{business_id}",
    response_model=list[GatekeeperDeviceOut],
)
def list_devices(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    GET /api/v1/integrations/gatekeeper-devices/{business_id}
    """
    return svc.list_devices_service(db, business_id)


# ---------------------------------------------------------
# CREATE DEVICE (businessId from payload)
# ---------------------------------------------------------
@router.post(
    "",
    response_model=GatekeeperDeviceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    payload: GatekeeperDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    POST /api/v1/integrations/gatekeeper-devices
    """
    return svc.create_device_service(db, payload)


# ---------------------------------------------------------
# UPDATE DEVICE (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.put(
    "/{business_id}/{device_id}",
    response_model=GatekeeperDeviceOut,
)
def update_device(
    business_id: int,
    device_id: int,
    payload: GatekeeperDeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    PUT /api/v1/integrations/gatekeeper-devices/{business_id}/{device_id}
    """
    return svc.update_device_service(db, device_id, payload)


# ---------------------------------------------------------
# RESET DEVICE (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.post(
    "/{business_id}/{device_id}/reset",
    response_model=GatekeeperDeviceOut,
)
def reset_device(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    POST /api/v1/integrations/gatekeeper-devices/{business_id}/{device_id}/reset
    """
    return svc.reset_device_service(db, device_id)


# ---------------------------------------------------------
# DELETE DEVICE (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.delete(
    "/{business_id}/{device_id}",
    status_code=status.HTTP_200_OK,
)
def delete_device(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    DELETE /api/v1/integrations/gatekeeper-devices/{business_id}/{device_id}
    """
    svc.delete_device_service(db, device_id)
    return {"message": "Device deleted"}


# ---------------------------------------------------------
# GET DEVICE CODE (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.get(
    "/{business_id}/{device_id}/code",
    response_model=dict,
)
def get_device_code(
    business_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    GET /api/v1/integrations/gatekeeper-devices/{business_id}/{device_id}/code
    """
    return svc.get_device_code_service(db, device_id)
