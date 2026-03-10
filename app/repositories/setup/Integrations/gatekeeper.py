# app/repositories/gatekeeper.py
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.setup.Integrations.gatekeeper import GatekeeperDevice


# ---------- LIST / GET ----------

def list_devices(db: Session, business_id: Optional[int] = None) -> List[GatekeeperDevice]:
    q = db.query(GatekeeperDevice)
    
    if business_id is not None:
        q = q.filter(GatekeeperDevice.business_id == business_id)
    
    return q.order_by(GatekeeperDevice.created_at.desc()).all()


def get_device(db: Session, device_id: int) -> Optional[GatekeeperDevice]:
    return db.get(GatekeeperDevice, device_id)


# ---------- CREATE ----------

def create_device(
    db: Session,
    *,
    business_id: int,
    name: str,
    device_model: Optional[str],
    tenant_id: Optional[int],
    device_code: str,
) -> GatekeeperDevice:
    device = GatekeeperDevice(
        business_id=business_id,
        name=name,
        device_model=device_model,
        tenant_id=tenant_id,
        device_code=device_code,
        app_version="Not Activated",
        activated=False,
        last_seen=None,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# ---------- UPDATE ----------

def update_device(
    db: Session,
    device: GatekeeperDevice,
    *,
    business_id: Optional[int] = None,
    name: Optional[str] = None,
    device_model: Optional[str] = None,
) -> GatekeeperDevice:
    if business_id is not None:
        device.business_id = business_id
    if name is not None:
        device.name = name
    if device_model is not None:
        device.device_model = device_model

    db.commit()
    db.refresh(device)
    return device


# ---------- DELETE ----------

def delete_device(db: Session, device: GatekeeperDevice) -> None:
    db.delete(device)
    db.commit()


# ---------- RESET ACTIVATION ----------

def reset_device(db: Session, device: GatekeeperDevice, new_code: str) -> GatekeeperDevice:
    device.device_code = new_code
    device.app_version = "Not Activated"
    device.activated = False
    device.last_seen = None
    device.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device
