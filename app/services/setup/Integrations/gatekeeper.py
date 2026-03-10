# app/services/setup/Integrations/gatekeeper.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets

from app.schemas.setup.Integrations.gatekeeper import (
    GatekeeperDeviceCreate,
    GatekeeperDeviceUpdate,
    GatekeeperDeviceOut,
)
from app.repositories.setup.Integrations import gatekeeper as repo
from app.models.setup.Integrations.gatekeeper import GatekeeperDevice
from app.models.business import Business


# helper to generate a 6-char code like front-end
def _generate_code() -> str:
    # similar style: random 6-char uppercase
    return secrets.token_hex(3).upper()


# ---------- CREATE ----------

def create_device_service(
    db: Session,
    payload: GatekeeperDeviceCreate,
) -> GatekeeperDeviceOut:
    # ✅ Validate that the business exists before creating device
    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {payload.business_id} does not exist"
        )
    
    code = _generate_code()

    device = repo.create_device(
        db,
        business_id=payload.business_id,
        name=payload.name,
        device_model=payload.device_model,
        tenant_id=payload.tenant_id,
        device_code=code,
    )

    return GatekeeperDeviceOut.model_validate(device)


# ---------- LIST ----------

def list_devices_service(db: Session, business_id: int | None = None) -> list[GatekeeperDeviceOut]:
    devices = repo.list_devices(db, business_id=business_id)
    return [GatekeeperDeviceOut.model_validate(d) for d in devices]


# ---------- UPDATE ----------

def update_device_service(
    db: Session,
    device_id: int,
    payload: GatekeeperDeviceUpdate,
) -> GatekeeperDeviceOut:
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

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
        business_id=payload.business_id,
        name=payload.name,
        device_model=payload.device_model,
    )
    return GatekeeperDeviceOut.model_validate(device)


# ---------- DELETE ----------

def delete_device_service(db: Session, device_id: int) -> None:
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    repo.delete_device(db, device)


# ---------- RESET ----------

def reset_device_service(db: Session, device_id: int) -> GatekeeperDeviceOut:
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    new_code = _generate_code()
    device = repo.reset_device(db, device, new_code)
    return GatekeeperDeviceOut.model_validate(device)


# (optional) show only the code
def get_device_code_service(db: Session, device_id: int) -> dict:
    device = repo.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"code": device.device_code}
