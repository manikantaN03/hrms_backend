from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.helpdesk_category_repository import (
    create_category,
    get_all_categories,
    get_category_by_id,
    update_category,
    delete_category,
)
from app.schemas.helpdesk_category import CategoryCreate, CategoryUpdate

def create_category_service(db: Session, payload: CategoryCreate):
    return create_category(db, payload)

def get_categories_service(db: Session,business_id: int):
    return get_all_categories(db, business_id)

def get_category_service(db: Session, category_id: int, business_id: int):
    category = get_category_by_id(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

def update_category_service(db: Session, category_id: int, business_id: int, payload: CategoryUpdate):
    updated = update_category(db, category_id, business_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated

def delete_category_service(db: Session, category_id: int, business_id: int):
    deleted = delete_category(db, category_id, business_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}