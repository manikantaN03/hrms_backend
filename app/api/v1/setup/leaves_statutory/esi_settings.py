"""
ESI Settings Endpoints
API routes for ESI configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.schemas.esi_settings import (
    ESISettingsResponse,
    ESISettingsUpdate,
    ESIComponentMappingCreate,
    ESIComponentMappingUpdate,
    ESIComponentMappingResponse,
    ESIComponentBulkUpdate,
    ESIRateChangeCreate,
    ESIRateChangeUpdate,
    ESIRateChangeResponse,
)
from app.services.esi_settings_service import ESISettingsService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=ESISettingsResponse,
    summary="Get ESI Settings"
)
def get_esi_settings(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get ESI settings for a business.
    Creates default settings if none exist.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    settings = service.get_or_create_settings(business_id)
    
    logger.info(f"ESI settings retrieved for business {business_id} by {current_user.email}")
    return settings


@router.put(
    "/{settings_id}",
    response_model=ESISettingsResponse,
    summary="Update ESI Settings"
)
def update_esi_settings(
    settings_id: int,
    data: ESISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update ESI settings (enable/disable, calculation base).
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
    try:
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        settings = service.update_settings(settings_id, update_dict)
        
        logger.info(f"ESI settings {settings_id} updated by {current_user.email}")
        return settings
    except Exception as e:
        logger.error(f"Error updating ESI settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Component Mapping Endpoints
# ============================================================================

@router.post(
    "/{settings_id}/components",
    response_model=ESIComponentMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Component Mapping"
)
def add_component_mapping(
    settings_id: int,
    data: ESIComponentMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Add a new salary component to ESI calculation.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
    try:
        component = service.add_component_mapping(settings_id, data.model_dump())
        logger.info(f"Component added to ESI settings {settings_id} by {current_user.email}")
        return component
    except Exception as e:
        logger.error(f"Error adding component: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/components/{component_id}",
    response_model=ESIComponentMappingResponse,
    summary="Update Component Mapping"
)
def update_component_mapping(
    component_id: int,
    data: ESIComponentMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update component selection status.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
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
    data: ESIComponentBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Bulk update component selection status.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
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
    response_model=ESIRateChangeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add ESI Rate"
)
def add_esi_rate(
    settings_id: int,
    data: ESIRateChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Add a new ESI rate configuration.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
    try:
        rate = service.add_rate_change(settings_id, data.model_dump())
        logger.info(f"ESI rate added to settings {settings_id} by {current_user.email}")
        return rate
    except Exception as e:
        logger.error(f"Error adding ESI rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/rates/{rate_id}",
    response_model=ESIRateChangeResponse,
    summary="Update ESI Rate"
)
def update_esi_rate(
    rate_id: int,
    data: ESIRateChangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update an existing ESI rate.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
    try:
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        rate = service.update_rate_change(rate_id, update_dict)
        
        logger.info(f"ESI rate {rate_id} updated by {current_user.email}")
        return rate
    except Exception as e:
        logger.error(f"Error updating ESI rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/rates/{rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ESI Rate"
)
def delete_esi_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete an ESI rate configuration.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = ESISettingsService(db)
    
    try:
        service.delete_rate_change(rate_id)
        logger.info(f"ESI rate {rate_id} deleted by {current_user.email}")
    except Exception as e:
        logger.error(f"Error deleting ESI rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
