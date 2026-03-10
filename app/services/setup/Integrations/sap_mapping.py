from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.setup.Integrations.sap_mapping import (
    SAPMappingCreate,
    SAPMappingResponse,
)
from app.repositories.setup.Integrations import sap_mapping as repo


def list_sap_mappings_service(db: Session, business_id: int | None) -> list[SAPMappingResponse]:
    """
    List all SAP mappings, optionally filtered by business_id.
    """
    results = repo.list_mappings(db, business_id)
    return [SAPMappingResponse.model_validate(obj, from_attributes=True) for obj in results]


def create_sap_mapping_service(db: Session, payload: SAPMappingCreate) -> SAPMappingResponse:
    """
    Create a new SAP mapping.
    """
    obj = repo.create_mapping(db, payload)
    return SAPMappingResponse.model_validate(obj, from_attributes=True)


def update_sap_mapping_service(db: Session, mapping_id: int, payload, business_id: int) -> SAPMappingResponse:
    """
    Update an existing SAP mapping by ID.
    """
    obj = repo.update_mapping(db, mapping_id, payload, business_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAP Mapping not found"
        )
    return SAPMappingResponse.model_validate(obj, from_attributes=True)


def delete_sap_mapping_service(db: Session, mapping_id: int, business_id: int):
    """
    Delete a SAP mapping by ID.
    """
    success = repo.delete_mapping(db, mapping_id, business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAP Mapping not found"
        )
