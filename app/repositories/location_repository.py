from sqlalchemy.orm import Session
from app.models.location import Location


class LocationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, business_id: int):
        return self.db.query(Location).filter(
            Location.business_id == business_id,
            Location.is_active == True
        ).all()

    def get(self, location_id: int):
        return self.db.query(Location).filter(
            Location.id == location_id,
            Location.is_active == True
        ).first()

    def create(self, data: dict):
        location = Location(**data)
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def update(self, location_id: int, data: dict):
        location = self.get(location_id)
        if not location:
            return None

        for key, value in data.items():
            setattr(location, key, value)

        self.db.commit()
        self.db.refresh(location)
        return location

    def delete(self, location_id: int, hard: bool = False):
        """Delete a location.

        By default this performs a soft-delete (sets `is_active=False`).
        If `hard=True`, the row is removed from the database.
        """
        # Lookup without filtering by is_active so hard-delete can remove soft-deleted rows too
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return None

        if hard:
            # Hard delete: remove the row from DB
            self.db.delete(location)
            self.db.commit()
            return True

        # Soft delete
        location.is_active = False
        self.db.commit()
        return location

    def unset_default(self, business_id: int):
        self.db.query(Location).filter(
            Location.business_id == business_id,
            Location.is_default == True
        ).update({Location.is_default: False})
        self.db.commit()
