from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.holiday import Holiday, Setting
from app.models.location import Location
from app.schemas.holiday import HolidayCreate, HolidayUpdate, CopyHolidaysRequest
from app.repositories.holiday_repository import HolidayRepository


def get_day_name(date_obj: date) -> str:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][date_obj.weekday()]


def holiday_to_response(h):
    return {
        "id": h.id,
        "business_id": getattr(h, "business_id", None),
        "location_id": h.location_id,
        "date": h.date,
        "name": h.name,
        "day": get_day_name(h.date)
    }


class HolidayService:

    @staticmethod
    def create_holiday(db: Session, data: HolidayCreate, business_id: int = None):
        # Resolve location: accept either location name (string) or location_id
        loc_id = None
        if getattr(data, "location_id", None):
            loc_id = data.location_id
        elif getattr(data, "location", None):
            # find location by name
            loc = db.query(Location).filter(Location.name == data.location).first()
            if not loc:
                raise HTTPException(400, f"Location '{data.location}' does not exist. Create it first.")
            loc_id = loc.id

        if loc_id is None:
            raise HTTPException(400, "Missing location information")

        # Determine business id: explicit param > payload > error
        biz_id = business_id or getattr(data, "business_id", None)
        if not biz_id:
            raise HTTPException(400, "Missing business_id in payload or as parameter")

        existing = db.query(Holiday).filter(
            Holiday.location_id == loc_id,
            Holiday.date == data.date
        ).first()

        if existing:
            raise HTTPException(400, f"Holiday already exists for location id {loc_id} on {data.date}")

        holiday = Holiday(business_id=biz_id, location_id=loc_id, date=data.date, name=data.name)
        db.add(holiday)
        db.commit()
        db.refresh(holiday)
        return holiday_to_response(holiday)

    @staticmethod
    def update_holiday(db: Session, holiday_id: int, data: HolidayUpdate):
        holiday = HolidayRepository.get_by_id(db, holiday_id)
        if not holiday:
            raise HTTPException(404, "Holiday not found")

        update_data = data.dict(exclude_unset=True)

        # Duplicate check
        # resolve new location id (if provided as name or id)
        new_loc = None
        if "location_id" in update_data:
            new_loc = update_data.get("location_id")
        elif "location" in update_data:
            loc = db.query(Location).filter(Location.name == update_data.get("location")).first()
            if not loc:
                raise HTTPException(400, f"Location '{update_data.get('location')}' does not exist")
            new_loc = loc.id

        new_date = update_data.get("date", holiday.date)

        if new_loc is None:
            new_loc = holiday.location_id

        dup = db.query(Holiday).filter(
            Holiday.location_id == new_loc,
            Holiday.date == new_date,
            Holiday.id != holiday_id
        ).first()

        if dup:
            raise HTTPException(400, f"Holiday already exists for {new_loc} on {new_date}")

        for key, value in update_data.items():
            # map incoming 'location' (name) to 'location_id'
            if key == "location":
                # already resolved above; skip
                continue
            setattr(holiday, key, value)

        # ensure location_id updated if needed
        if new_loc is not None:
            holiday.location_id = new_loc

        db.commit()
        db.refresh(holiday)

        return holiday_to_response(holiday)

    @staticmethod
    def get_filtered(db: Session, location: str = None, year: int = None):
        """Return a list of Holiday objects filtered by location and/or year."""
        return HolidayRepository.get_filtered(db, location, year)

    @staticmethod
    def delete_holiday(db: Session, holiday_id: int):
        holiday = HolidayRepository.get_by_id(db, holiday_id)
        if not holiday:
            raise HTTPException(404, "Holiday not found")
        db.delete(holiday)
        db.commit()
        return {"message": "Holiday deleted successfully"}

    @staticmethod
    def copy_holidays(db: Session, data: CopyHolidaysRequest, business_id: int):
        """Copy holidays from one location/year to another location/year"""
        from app.models.location import Location
        
        # Find source location
        from_location = db.query(Location).filter(
            Location.name == data.from_location,
            Location.business_id == business_id
        ).first()
        if not from_location:
            raise HTTPException(400, f"Source location '{data.from_location}' not found")
        
        # Find target location
        to_location = db.query(Location).filter(
            Location.name == data.to_location,
            Location.business_id == business_id
        ).first()
        if not to_location:
            raise HTTPException(400, f"Target location '{data.to_location}' not found")
        
        # Get holidays from source location and year
        source_holidays = db.query(Holiday).filter(
            Holiday.location_id == from_location.id,
            Holiday.business_id == business_id,
            Holiday.date.between(f"{data.from_year}-01-01", f"{data.from_year}-12-31")
        ).all()
        
        if not source_holidays:
            raise HTTPException(400, f"No holidays found for {data.from_location} in {data.from_year}")
        
        copied_count = 0
        for source_holiday in source_holidays:
            # Calculate new date (same month/day, different year)
            try:
                new_date = source_holiday.date.replace(year=data.to_year)
            except ValueError:
                # Handle leap year edge case (Feb 29)
                if source_holiday.date.month == 2 and source_holiday.date.day == 29:
                    new_date = source_holiday.date.replace(year=data.to_year, day=28)
                else:
                    continue
            
            # Check if holiday already exists
            existing = db.query(Holiday).filter(
                Holiday.location_id == to_location.id,
                Holiday.date == new_date
            ).first()
            
            if not existing:
                new_holiday = Holiday(
                    business_id=business_id,
                    location_id=to_location.id,
                    date=new_date,
                    name=source_holiday.name
                )
                db.add(new_holiday)
                copied_count += 1
        
        db.commit()
        return {"message": f"Successfully copied {copied_count} holidays from {data.from_location} ({data.from_year}) to {data.to_location} ({data.to_year})"}


class SettingService:

    @staticmethod
    def create_setting(db, business_id, data):
        """Store settings using a business-prefixed key to avoid schema changes.

        Returns a plain dict with `id`, `key` (unprefixed), and `value`.
        """
        prefix = f"{business_id}:"
        composite_key = f"{prefix}{data.key}"

        existing = db.query(Setting).filter(Setting.key == composite_key).first()

        if existing:
            existing.value = data.value
            db.commit()
            db.refresh(existing)
            return {"id": existing.id, "key": data.key, "value": existing.value}

        setting = Setting(key=composite_key, value=data.value)
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return {"id": setting.id, "key": data.key, "value": setting.value}

    @staticmethod
    def get_all_settings(db, business_id):
        prefix = f"{business_id}:"
        rows = db.query(Setting).filter(Setting.key.like(f"{prefix}%")).all()
        results = []
        for r in rows:
            # strip prefix for API consumers
            key = r.key[len(prefix):] if r.key.startswith(prefix) else r.key
            results.append({"id": r.id, "key": key, "value": r.value})
        return results