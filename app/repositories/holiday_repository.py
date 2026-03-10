from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.holiday import Holiday, Setting
from app.models.location import Location


class HolidayRepository:

    @staticmethod
    def get_by_id(db: Session, holiday_id: int):
        return db.query(Holiday).filter(Holiday.id == holiday_id).first()

    @staticmethod
    def get_filtered(db: Session, location: str = None, year: int = None):
        # Use join with Location to allow filtering by location name (string),
        # or accept a numeric location id (as string/int).
        stmt = select(Holiday).order_by(Holiday.date)

        if location:
            # if location looks like an integer id, filter by id
            try:
                loc_id = int(location)
            except Exception:
                loc_id = None

            if loc_id is not None:
                stmt = stmt.where(Holiday.location_id == loc_id)
            else:
                # join Location and filter by name
                stmt = stmt.join(Location).where(Location.name == location)

        if year:
            stmt = stmt.where(Holiday.date.between(f"{year}-01-01", f"{year}-12-31"))

        result = db.execute(stmt).scalars().all()
        return result
