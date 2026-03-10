from sqlalchemy.orm import Session
from app.models.helpdesk_category import HelpdeskCategory
from app.schemas.helpdesk_category import CategoryCreate, CategoryUpdate


def create_category(db: Session, payload: CategoryCreate):
    # Check if name already exists for this business
    existing = db.query(HelpdeskCategory).filter(
        HelpdeskCategory.name == payload.name,
        HelpdeskCategory.business_id == payload.business_id
    ).first()
    
    if existing:
        raise ValueError(f"Helpdesk category '{payload.name}' already exists")
    
    category = HelpdeskCategory(
        business_id=payload.business_id,          
        name=payload.name,
        primary_approver=payload.primary_approver,  
        backup_approver=payload.backup_approver,   
        is_active=payload.is_active,                
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_all_categories(db: Session, business_id: int):
    return (
        db.query(HelpdeskCategory)
        .filter(HelpdeskCategory.business_id == business_id)  
        .order_by(HelpdeskCategory.id.desc())
        .all()
    )


def get_category_by_id(db: Session, category_id: int, business_id: int):
    return (
        db.query(HelpdeskCategory)
        .filter(
            HelpdeskCategory.id == category_id,
            HelpdeskCategory.business_id == business_id  
        )
        .first()
    )


def update_category(db: Session, category_id: int, business_id: int, payload: CategoryUpdate):
    category = get_category_by_id(db, category_id, business_id)
    if not category:
        return None

    # Check if new name already exists for this business (excluding self)
    existing = db.query(HelpdeskCategory).filter(
        HelpdeskCategory.name == payload.name,
        HelpdeskCategory.business_id == business_id,
        HelpdeskCategory.id != category_id
    ).first()
    
    if existing:
        raise ValueError(f"Helpdesk category '{payload.name}' already exists")

    category.name = payload.name
    category.primary_approver = payload.primary_approver     
    category.backup_approver = payload.backup_approver       
    category.is_active = payload.is_active                   

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int, business_id: int):
    category = get_category_by_id(db, category_id, business_id)
    if not category:
        return False

    db.delete(category)
    db.commit()
    return True
