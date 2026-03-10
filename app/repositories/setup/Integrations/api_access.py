from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.setup.Integrations.api_access import APIAccess
from app.models.business import Business
from app.schemas.setup.Integrations.api_access import APIAccessCreate, APIAccessUpdate
import secrets
import logging

logger = logging.getLogger(__name__)


def list_api_access(db: Session, business_id: int | None = None) -> list[APIAccess]:
    """List all API access configurations, optionally filtered by business_id."""
    query = db.query(APIAccess)
    
    if business_id is not None:
        query = query.filter(APIAccess.business_id == business_id)
    
    return query.all()


def create_api_access(db: Session, data: APIAccessCreate) -> APIAccess:
    """Create a new API access configuration."""
    # Validate business exists
    business = db.query(Business).filter(Business.id == data.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {data.business_id} not found"
        )
    
    # Check if API access already exists for this business
    existing = db.query(APIAccess).filter(APIAccess.business_id == data.business_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API Access already exists for business ID {data.business_id}"
        )
    
    # Generate API key if enabled
    api_key = "API-" + secrets.token_urlsafe(16) if data.api_enabled else None
    
    db_obj = APIAccess(
        business_id=data.business_id,
        is_enabled=data.api_enabled,
        api_key=api_key,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info("Created APIAccess id=%s business_id=%s api_key=%s", db_obj.id, db_obj.business_id, db_obj.api_key)
    return db_obj


def update_api_access(db: Session, access_id: int, data: APIAccessUpdate) -> APIAccess | None:
    """Update an existing API access configuration by ID."""
    db_obj = db.query(APIAccess).filter(APIAccess.id == access_id).first()
    
    if db_obj is None:
        return None
    
    if data.api_enabled is not None:
        db_obj.is_enabled = data.api_enabled
        # Generate new key if enabling, clear if disabling
        if data.api_enabled:
            db_obj.api_key = "API-" + secrets.token_urlsafe(16)
        else:
            db_obj.api_key = None
    
    # Allow custom API key if provided
    if data.api_key is not None:
        db_obj.api_key = data.api_key
    
    db.commit()
    db.refresh(db_obj)
    logger.info("Updated APIAccess id=%s is_enabled=%s", db_obj.id, db_obj.is_enabled)
    return db_obj


def delete_api_access(db: Session, access_id: int) -> bool:
    """Delete an API access configuration by ID. Returns True if successful."""
    db_obj = db.query(APIAccess).filter(APIAccess.id == access_id).first()
    
    if db_obj is None:
        return False
    
    db.delete(db_obj)
    db.commit()
    logger.info("Deleted APIAccess id=%s", access_id)
    return True
