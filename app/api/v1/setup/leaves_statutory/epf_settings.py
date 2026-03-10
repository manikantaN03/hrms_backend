"""
EPF Settings Endpoints
API routes for EPF configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
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
    business_id: int,
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
    settings_id: int,
    data: EPFSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update EPF settings (enable/disable, calculation base).
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
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
    settings_id: int,
    data: EPFComponentMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Add a new salary component to EPF calculation.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
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
    component_id: int,
    data: EPFComponentMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update component selection status.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
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
    data: EPFComponentBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Bulk update component selection status.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
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
    settings_id: int,
    data: EPFRateChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Add a new EPF rate configuration.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
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
    rate_id: int,
    data: EPFRateChangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update an existing EPF rate.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
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
    rate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete an EPF rate configuration.
    
    **Access:** ADMIN or SUPERADMIN
    """
    service = EPFSettingsService(db)
    
    try:
        service.delete_rate_change(rate_id)
        logger.info(f"EPF rate {rate_id} deleted by {current_user.email}")
    except Exception as e:
        logger.error(f"Error deleting EPF rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
