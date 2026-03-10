from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.setup.Integrations.api_access import (
    APIAccessCreate,
    APIAccessUpdate,
    APIAccessResponse,
)
from app.repositories.setup.Integrations import api_access as repo


def list_api_access_service(db: Session, business_id: int | None) -> list[APIAccessResponse]:
    """
    List all API access configurations, optionally filtered by business_id.
    """
    results = repo.list_api_access(db, business_id)
    return [APIAccessResponse.model_validate(obj) for obj in results]


def create_api_access_service(db: Session, payload: APIAccessCreate) -> APIAccessResponse:
    """
    Create a new API access configuration.
    """
    obj = repo.create_api_access(db, payload)
    # Return the object directly - Pydantic will read from ORM attributes
    return APIAccessResponse.model_validate(obj, from_attributes=True)


def update_api_access_service(db: Session, access_id: int, payload: APIAccessUpdate) -> APIAccessResponse:
    """
    Update an existing API access configuration by ID.
    """
    obj = repo.update_api_access(db, access_id, payload)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Access configuration not found"
        )
    return APIAccessResponse.model_validate(obj, from_attributes=True)


def delete_api_access_service(db: Session, access_id: int):
    """
    Delete an API access configuration by ID.
    """
    success = repo.delete_api_access(db, access_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Access configuration not found"
        )
