from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.holiday import *
from app.services.holiday_service import HolidayService, holiday_to_response, SettingService
from app.models.holiday import Holiday, Setting
from app.models.location import Location
from app.api.v1.deps import get_current_admin
from app.models.user import User

router = APIRouter()


@router.post("", response_model=HolidayResponse, status_code=201)
def create_holiday(data: HolidayCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    # determine business_id: prefer payload, otherwise use first admin business
    biz_id = getattr(data, "business_id", None)
    if not biz_id:
        if not current_admin.businesses:
            raise HTTPException(status_code=400, detail="No businesses found for this admin")
        biz_id = current_admin.businesses[0].id

    # verify ownership
    if not any(b.id == biz_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")

    return HolidayService.create_holiday(db, data, biz_id)


@router.get("", response_model=list[HolidayResponse])
def get_holidays(
    location: str = Query(None),
    year: int = Query(None),
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    # validate admin access to business
    if not current_admin.businesses or not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    filtered = HolidayService.get_filtered(db, location, year) or []
    filtered = [h for h in filtered if getattr(h, "business_id", None) == business_id]
    return [holiday_to_response(h) for h in filtered]


@router.put("/{holiday_id}", response_model=HolidayResponse)
def update_holiday(
    holiday_id: int,
    data: HolidayUpdate,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    record = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Holiday not found")
    if not current_admin.businesses or not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    if getattr(record, "business_id", None) != business_id:
        raise HTTPException(status_code=403, detail="Holiday does not belong to the given business")
    return HolidayService.update_holiday(db, holiday_id, data)


@router.delete("/{holiday_id}")
def delete_holiday(
    holiday_id: int,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    record = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Holiday not found")
    if not current_admin.businesses or not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    if getattr(record, "business_id", None) != business_id:
        raise HTTPException(status_code=403, detail="Holiday does not belong to the given business")
    return HolidayService.delete_holiday(db, holiday_id)


# Settings endpoints
@router.post("/settings/", response_model=SettingResponse)
def create_setting(
    data: SettingCreate,
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="No access to this business")

    return SettingService.create_setting(db, business_id, data)


@router.get("/settings/", response_model=list[SettingResponse])
def get_all_settings(
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="No access to this business")

    return SettingService.get_all_settings(db, business_id)


@router.get("/settings/{setting_id}", response_model=SettingResponse)
def get_setting(
    setting_id: int,
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    prefix = f"{business_id}:"
    if not setting.key.startswith(prefix):
        raise HTTPException(status_code=403, detail="Setting does not belong to the given business")

    return {"id": setting.id, "key": setting.key[len(prefix):], "value": setting.value}


@router.put("/settings/{setting_id}", response_model=SettingResponse)
def update_setting(
    setting_id: int,
    data: SettingUpdate,
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    prefix = f"{business_id}:"
    if not setting.key.startswith(prefix):
        raise HTTPException(status_code=403, detail="Setting does not belong to the given business")

    setting.value = data.value
    db.commit()
    db.refresh(setting)
    return {"id": setting.id, "key": setting.key[len(prefix):], "value": setting.value}

@router.delete("/settings/{setting_id}")
def delete_setting(
    setting_id: int,
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    prefix = f"{business_id}:"
    if not setting.key.startswith(prefix):
        raise HTTPException(status_code=403, detail="Setting does not belong to the given business")

    db.delete(setting)
    db.commit()
    return {"message": "Setting deleted"}


# Location endpoints
@router.get("/locations", response_model=list[LocationResponse])
def get_locations(
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not current_admin.businesses or not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    
    locations = db.query(Location).filter(Location.business_id == business_id).all()
    return locations


# Copy holidays endpoint
@router.post("/copy", status_code=200)
def copy_holidays(
    data: CopyHolidaysRequest,
    business_id: int = Query(..., description="business_id is required"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not current_admin.businesses or not any(b.id == business_id for b in current_admin.businesses):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    
    return HolidayService.copy_holidays(db, data, business_id)
