from sqlalchemy.orm import Session
from app.models.setup.Integrations.sap_mapping import SAPMapping
from app.schemas.setup.Integrations.sap_mapping import SAPMappingCreate
import logging

logger = logging.getLogger(__name__)


def list_mappings(db: Session, business_id: int | None = None) -> list[SAPMapping]:
    """List all SAP mappings, optionally filtered by business_id."""
    logger.info(f"[SAP MAPPING] Listing mappings for business_id={business_id}")
    query = db.query(SAPMapping)
    
    if business_id is not None:
        query = query.filter(SAPMapping.business_id == business_id)
    
    results = query.all()
    logger.info(f"[SAP MAPPING] Found {len(results)} mappings")
    return results


def create_mapping(db: Session, data: SAPMappingCreate) -> SAPMapping:
    """Create a new SAP mapping."""
    logger.info(f"[SAP MAPPING] Creating mapping for business_id={data.business_id}")
    db_obj = SAPMapping(**data.dict(exclude_unset=True))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info(f"[SAP MAPPING] Created mapping with id={db_obj.id}")
    return db_obj


def update_mapping(db: Session, mapping_id: int, data, business_id: int) -> SAPMapping | None:
    """Update an existing SAP mapping by ID. Validates business ownership."""
    logger.info(f"[SAP MAPPING] Updating mapping_id={mapping_id} for business_id={business_id}")
    db_obj = db.query(SAPMapping).filter(
        SAPMapping.id == mapping_id,
        SAPMapping.business_id == business_id  # CRITICAL: Business isolation
    ).first()
    
    if db_obj is None:
        logger.warning(f"[SAP MAPPING] Mapping not found: mapping_id={mapping_id}, business_id={business_id}")
        return None
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    
    db.commit()
    db.refresh(db_obj)
    logger.info(f"[SAP MAPPING] Updated mapping_id={mapping_id}")
    return db_obj


def delete_mapping(db: Session, mapping_id: int, business_id: int) -> bool:
    """Delete a SAP mapping by ID. Validates business ownership. Returns True if successful."""
    logger.info(f"[SAP MAPPING] Deleting mapping_id={mapping_id} for business_id={business_id}")
    db_obj = db.query(SAPMapping).filter(
        SAPMapping.id == mapping_id,
        SAPMapping.business_id == business_id  # CRITICAL: Business isolation
    ).first()
    
    if db_obj is None:
        logger.warning(f"[SAP MAPPING] Mapping not found: mapping_id={mapping_id}, business_id={business_id}")
        return False
    
    db.delete(db_obj)
    db.commit()
    logger.info(f"[SAP MAPPING] Deleted mapping_id={mapping_id}")
    return True
