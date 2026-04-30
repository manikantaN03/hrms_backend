"""
EPF Settings Endpoints
API routes for EPF configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, validate_business_access
from app.models.user import User
from app.schemas.epf_settings import (
    EPFSettingsResponse,
    EPFSettingsUpdate,
    EPFComponentMappingCreate,
    EPFComponentMappingUpdate,
    EPFComponentMappingResponse,
    EPFComponentBulkUpdate,
    EPFRateChangeCreate,
    EPFRateChangeUpdate,
    EPFRateChangeResponse,
)
from app.services.epf_settings_service import EPFSettingsService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=EPFSettingsResponse,
    summary="Get EPF Settings"
)
def get_epf_settings(
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get EPF settings for a business.
    Creates default settings if none exist.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    settings = service.get_or_create_settings(business_id)
    
    logger.info(f"EPF settings retrieved for business {business_id} by {current_user.email}")
    return settings


@router.put(
    "/{settings_id}",
    response_model=EPFSettingsResponse,
    summary="Update EPF Settings"
)
def update_epf_settings(
    business_id: int = Path(...),
    settings_id: int = Path(...),
    data: EPFSettingsUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update EPF settings (enable/disable, calculation base).
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    # Validate admin access to the business
    validate_business_access(business_id, current_user, db)

    # Ensure the settings belong to the requested business
    settings_obj = service.settings_repo.get(settings_id)
    if not settings_obj or settings_obj.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPF settings not found for this business")

    try:
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        settings = service.update_settings(settings_id, update_dict)

        logger.info(f"EPF settings {settings_id} updated by {current_user.email}")
        return settings
    except Exception as e:
        logger.error(f"Error updating EPF settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Component Mapping Endpoints
# ============================================================================

@router.post(
    "/{settings_id}/components",
    response_model=EPFComponentMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Component Mapping"
)
def add_component_mapping(
    business_id: int = Path(...),
    settings_id: int = Path(...),
    data: EPFComponentMappingCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Add a new salary component to EPF calculation.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    # Validate admin has access to the business
    validate_business_access(business_id, current_user, db)

    # Ensure the settings belong to the requested business
    settings_obj = service.settings_repo.get(settings_id)
    if not settings_obj or settings_obj.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPF settings not found for this business")

    try:
        component = service.add_component_mapping(settings_id, data.model_dump())
        logger.info(f"Component added to EPF settings {settings_id} by {current_user.email}")
        return component
    except Exception as e:
        logger.error(f"Error adding component: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/components/{component_id}",
    response_model=EPFComponentMappingResponse,
    summary="Update Component Mapping"
)
def update_component_mapping(
    business_id: int = Path(...),
    component_id: int = Path(...),
    data: EPFComponentMappingUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update component selection status.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    # Validate admin access to the business
    validate_business_access(business_id, current_user, db)

    # Ensure component belongs to the business
    comp = service.component_repo.get(component_id)
    if not comp or not comp.epf_settings or comp.epf_settings.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found for this business")

    try:
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        component = service.update_component_mapping(component_id, update_dict)

        logger.info(f"Component {component_id} updated by {current_user.email}")
        return component
    except Exception as e:
        logger.error(f"Error updating component: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/components/bulk-update",
    summary="Bulk Update Components"
)
def bulk_update_components(
    business_id: int = Path(...),
    data: EPFComponentBulkUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Bulk update component selection status.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    # Validate admin access
    validate_business_access(business_id, current_user, db)

    # Verify components belong to business
    for cid in data.component_ids:
        comp = service.component_repo.get(cid)
        if not comp or not comp.epf_settings or comp.epf_settings.business_id != business_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Component {cid} not found for this business")

    try:
        count = service.bulk_update_components(data.component_ids, data.is_selected)
        logger.info(f"{count} components updated by {current_user.email}")
        return {"updated_count": count, "message": f"{count} components updated successfully"}
    except Exception as e:
        logger.error(f"Error bulk updating components: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Rate Change Endpoints
# ============================================================================

@router.post(
    "/{settings_id}/rates",
    response_model=EPFRateChangeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add EPF Rate"
)
def add_epf_rate(
    business_id: int = Path(...),
    settings_id: int = Path(...),
    data: EPFRateChangeCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Add a new EPF rate configuration.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    # Validate admin access
    validate_business_access(business_id, current_user, db)

    # Ensure settings belong to business
    settings_obj = service.settings_repo.get(settings_id)
    if not settings_obj or settings_obj.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPF settings not found for this business")

    try:
        rate = service.add_rate_change(settings_id, data.model_dump())
        logger.info(f"EPF rate added to settings {settings_id} by {current_user.email}")
        return rate
    except Exception as e:
        logger.error(f"Error adding EPF rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/rates/{rate_id}",
    response_model=EPFRateChangeResponse,
    summary="Update EPF Rate"
)
def update_epf_rate(
    business_id: int = Path(...),
    rate_id: int = Path(...),
    data: EPFRateChangeUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update an existing EPF rate.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    # Validate access
    validate_business_access(business_id, current_user, db)

    # Ensure rate belongs to a settings record for this business
    rate_obj = service.rate_repo.get(rate_id)
    if not rate_obj or not rate_obj.epf_settings or rate_obj.epf_settings.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPF rate not found for this business")

    try:
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        rate = service.update_rate_change(rate_id, update_dict)

        logger.info(f"EPF rate {rate_id} updated by {current_user.email}")
        return rate
    except Exception as e:
        logger.error(f"Error updating EPF rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/rates/{rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete EPF Rate"
)
def delete_epf_rate(
    business_id: int = Path(...),
    rate_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete an EPF rate configuration.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)

    validate_business_access(business_id, current_user, db)

    rate_obj = service.rate_repo.get(rate_id)
    if not rate_obj or not rate_obj.epf_settings or rate_obj.epf_settings.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPF rate not found for this business")

    try:
        service.delete_rate_change(rate_id)
        logger.info(f"EPF rate {rate_id} deleted by {current_user.email}")
    except Exception as e:
        logger.error(f"Error deleting EPF rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
