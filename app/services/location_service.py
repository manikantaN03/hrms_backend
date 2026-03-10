from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.location_repository import LocationRepository
from app.models.business import Business
from app.schemas.location_schema import (
	LocationCreate,
	LocationUpdate,
)


def list_locations(db: Session, business_id: int):
	business = db.query(Business).filter(Business.id == business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	repo = LocationRepository(db)
	return repo.get_all(business_id)


def create_location(db: Session, payload: LocationCreate):
	business = db.query(Business).filter(Business.id == payload.business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	repo = LocationRepository(db)

	if payload.isDefault:
		repo.unset_default(business_id=payload.business_id)

	data = {
		"business_id": payload.business_id,
		"name": payload.name,
		"state": payload.state,
		"location_head": payload.locationHead,
		"deputy_head": payload.deputyHead,
		"is_default": payload.isDefault,
		"map_url": payload.mapUrl,
	}

	obj = repo.create(data)
	return obj


def get_location(db: Session, location_id: int, business_id: int | None = None):
	repo = LocationRepository(db)
	obj = repo.get(location_id)
	if not obj:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

	if business_id is not None and getattr(obj, "business_id", None) != business_id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found for this business")

	return obj


def update_location(db: Session, location_id: int, payload: LocationUpdate):
	repo = LocationRepository(db)
	obj = repo.get(location_id)
	if not obj:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

	update_data = {}
	if payload.name is not None:
		update_data["name"] = payload.name
	if payload.state is not None:
		update_data["state"] = payload.state
	if payload.locationHead is not None:
		update_data["location_head"] = payload.locationHead
	if payload.deputyHead is not None:
		update_data["deputy_head"] = payload.deputyHead
	if payload.mapUrl is not None:
		update_data["map_url"] = payload.mapUrl
	if payload.isDefault is not None:
		if payload.isDefault:
			repo.unset_default(business_id=obj.business_id)
		update_data["is_default"] = payload.isDefault

	updated = repo.update(location_id, update_data)
	return updated


def delete_location(db: Session, location_id: int, hard: bool = True):
	repo = LocationRepository(db)
	obj = repo.get(location_id)
	if not obj:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

	deleted = repo.delete(location_id, hard=hard)
	return deleted

