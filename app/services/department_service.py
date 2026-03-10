from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.department_repository import DepartmentRepository
from app.models.business import Business
from app.schemas.department_schema import (
	DepartmentCreate,
	DepartmentUpdate,
)


def list_departments(db: Session, business_id: int):
	business = db.query(Business).filter(Business.id == business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	repo = DepartmentRepository(db)
	return repo.get_all(business_id)


def create_department(db: Session, payload: DepartmentCreate):
	business = db.query(Business).filter(Business.id == payload.business_id).first()
	if not business:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

	repo = DepartmentRepository(db)

	# duplicate name check
	existing = repo.find_by_business_and_name(payload.business_id, payload.name)
	if existing:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department with this name already exists")

	if payload.isDefault:
		repo.unset_default(business_id=payload.business_id)

	data = {
		"business_id": payload.business_id,
		"name": payload.name,
		"head": payload.head,
		"deputy_head": payload.deputyHead,
		"is_default": payload.isDefault,
	}

	obj = repo.create(data)
	return obj


def get_department(db: Session, department_id: int, business_id: int | None = None):
	repo = DepartmentRepository(db)
	obj = repo.get(department_id)
	if not obj:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

	if business_id is not None and getattr(obj, "business_id", None) != business_id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found for this business")

	return obj


def update_department(db: Session, department_id: int, payload: DepartmentUpdate):
	repo = DepartmentRepository(db)
	obj = repo.get(department_id)
	if not obj:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

	update_data = {}
	if payload.name is not None:
		update_data["name"] = payload.name
	if payload.head is not None:
		update_data["head"] = payload.head
	if payload.deputyHead is not None:
		update_data["deputy_head"] = payload.deputyHead
	if payload.employees is not None:
		update_data["employees"] = payload.employees
	if payload.isDefault is not None:
		if payload.isDefault:
			repo.unset_default(business_id=obj.business_id)
		update_data["is_default"] = payload.isDefault

	updated = repo.update(department_id, update_data)
	return updated


def delete_department(db: Session, department_id: int, hard: bool = True):
	repo = DepartmentRepository(db)
	obj = repo.get(department_id)
	if not obj:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

	deleted = repo.delete(department_id, hard=hard)
	return deleted

