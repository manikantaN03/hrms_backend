from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.business_unit_repository import BusinessUnitRepository
from app.models.business import Business
from app.schemas.business_unit import (
	BusinessUnitCreate,
	BusinessUnitUpdate,
)


def list_business_units(db: Session, business_id: int):
	# ensure business exists
	business = db.query(Business).filter(Business.id == business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	repo = BusinessUnitRepository(db)
	return repo.list_by_business(business_id=business_id)


def create_business_unit(db: Session, payload: BusinessUnitCreate, created_by: int = None):
	business = db.query(Business).filter(Business.id == payload.business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	repo = BusinessUnitRepository(db)

	data = payload.model_dump()

	# If default → unset previous default
	if data.get("is_default"):
		repo.unset_default(business_id=data["business_id"])

	if created_by:
		data['created_by'] = created_by
		data['updated_by'] = created_by

	unit = repo.create(data)
	return unit


def get_business_unit(db: Session, unit_id: int, business_id: int | None = None):
	repo = BusinessUnitRepository(db)
	unit = repo.get(unit_id)
	if not unit:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business unit not found")

	# ensure parent business exists
	if business_id is not None:
		if unit.business_id != business_id:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business unit not found for this business")

	business = db.query(Business).filter(Business.id == unit.business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	return unit


def update_business_unit(db: Session, unit_id: int, payload: BusinessUnitUpdate, updated_by: int = None):
	repo = BusinessUnitRepository(db)
	unit = repo.get(unit_id)
	if not unit:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business unit not found")

	# ensure parent business exists
	business = db.query(Business).filter(Business.id == unit.business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	update_data = payload.model_dump(exclude_unset=True)

	# Handle default switch
	if update_data.get("is_default"):
		repo.unset_default(business_id=unit.business_id, exclude_id=unit_id)

	if updated_by:
		update_data['updated_by'] = updated_by

	updated = repo.update(unit, update_data)
	return updated


def delete_business_unit(db: Session, unit_id: int, hard: bool = True):
	repo = BusinessUnitRepository(db)
	unit = repo.get(unit_id)
	if not unit:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business unit not found")

	# ensure parent business exists
	business = db.query(Business).filter(Business.id == unit.business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	# perform hard delete via repo if supported, otherwise fallback
	try:
		# BusinessUnitRepository inherits BaseRepository.delete which performs hard delete
		repo.delete(unit_id)
	except Exception:
		# fallback: try to remove object directly
		obj = repo.get(unit_id)
		if obj:
			db.delete(obj)
			db.commit()

	return unit

