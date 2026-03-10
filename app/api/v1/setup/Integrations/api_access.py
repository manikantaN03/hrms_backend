from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.setup.Integrations.api_access import (
    APIAccessCreate,
    APIAccessUpdate,
    APIAccessResponse,
)
from app.services.setup.Integrations import api_access as svc
from app.core.config import settings
from app.api.v1.deps import get_current_admin
from app.models.user import User

router = APIRouter(prefix="/integrations/api-access")


# ✅ List API Access (ADMIN / SUPERADMIN)
@router.get("/{business_id}", response_model=list[APIAccessResponse])
def list_api_access(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all API Access configurations for a business.
    GET /api/v1/integrations/api-access/{business_id}
    """
    return svc.list_api_access_service(db, business_id)


# ✅ Create API Access (ADMIN / SUPERADMIN)
@router.post("", response_model=APIAccessResponse, status_code=status.HTTP_201_CREATED)
def create_api_access(
    payload: APIAccessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create new API Access configuration.
    POST /api/v1/integrations/api-access
    """
    return svc.create_api_access_service(db, payload)


# ✅ Update API Access (ADMIN / SUPERADMIN)
@router.put("/{business_id}/{access_id}", response_model=APIAccessResponse)
def update_api_access(
    business_id: int,
    access_id: int,
    payload: APIAccessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an API access configuration.
    PUT /api/v1/integrations/api-access/{business_id}/{access_id}
    """
    return svc.update_api_access_service(db, access_id, payload)


# ✅ Delete API Access (ADMIN / SUPERADMIN)
@router.delete("/{business_id}/{access_id}", status_code=status.HTTP_200_OK)
def delete_api_access(
    business_id: int,
    access_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete an API access configuration.
    DELETE /api/v1/integrations/api-access/{business_id}/{access_id}
    """
    svc.delete_api_access_service(db, access_id)
    return {"message": "API Access deleted"}


# ✅ Debug Endpoint (ADMIN / SUPERADMIN + DEBUG MODE)
@router.get("/{business_id}/debug", response_model=List[Dict])
def list_api_access_debug(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Dev-only debug endpoint: return raw rows from DB for this business.

    Enabled only when `DEBUG` is true in settings.
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Debug endpoint disabled")

    rows = svc._raw_list(db, business_id) if hasattr(svc, "_raw_list") else None
    if rows is None:
        from app.repositories.setup.Integrations import api_access as repo
        rows = repo.list_api_access(db, business_id)

    return [
        {
            "id": r.id,
            "businessId": r.business_id,
            "apiKey": r.api_key,
            "apiEnabled": r.is_enabled,
        }
        for r in rows
    ]
