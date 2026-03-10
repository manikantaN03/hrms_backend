# app/api/routes/setup/Integrations/sap_mapping.py

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business

from app.schemas.setup.Integrations.sap_mapping import (
    SAPMappingCreate,
    SAPMappingUpdate,
    SAPMappingResponse,
)
from app.services.setup.Integrations import sap_mapping as svc

router = APIRouter(prefix="/integrations/sap-mapping")


# ---------------------------------------------------------
# LIST SAP MAPPINGS (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.get(
    "/{business_id}",
    response_model=list[SAPMappingResponse],
    response_model_exclude_none=True,
)
def list_sap_mappings(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    GET /api/v1/integrations/sap-mapping/{business_id}
    """
    # CRITICAL: Validate user owns this business
    from app.api.v1.endpoints.master_setup import get_user_business_id
    user_business_id = get_user_business_id(current_user, db)
    
    if business_id != user_business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAP Mapping not found"
        )
    
    return svc.list_sap_mappings_service(db, business_id)


# ---------------------------------------------------------
# CREATE SAP MAPPING (businessId from payload)
# ---------------------------------------------------------
@router.post(
    "",
    response_model=SAPMappingResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def create_sap_mapping(
    payload: SAPMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    POST /api/v1/integrations/sap-mapping
    """
    # CRITICAL: Inject user's business_id into payload
    from app.api.v1.endpoints.master_setup import get_user_business_id
    user_business_id = get_user_business_id(current_user, db)
    payload.business_id = user_business_id
    
    return svc.create_sap_mapping_service(db, payload)


# ---------------------------------------------------------
# UPDATE SAP MAPPING (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.put(
    "/{business_id}/{mapping_id}",
    response_model=SAPMappingResponse,
    response_model_exclude_none=True,
)
def update_sap_mapping(
    business_id: int,
    mapping_id: int,
    payload: SAPMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    PUT /api/v1/integrations/sap-mapping/{business_id}/{mapping_id}
    """
    # CRITICAL: Validate user owns this business
    from app.api.v1.endpoints.master_setup import get_user_business_id
    user_business_id = get_user_business_id(current_user, db)
    
    if business_id != user_business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAP Mapping not found"
        )
    
    # Validate the mapping belongs to this business
    return svc.update_sap_mapping_service(db, mapping_id, payload, business_id)


# ---------------------------------------------------------
# DELETE SAP MAPPING (BUSINESS-SCOPED)
# ---------------------------------------------------------
@router.delete(
    "/{business_id}/{mapping_id}",
    status_code=status.HTTP_200_OK,
)
def delete_sap_mapping(
    business_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    DELETE /api/v1/integrations/sap-mapping/{business_id}/{mapping_id}
    """
    # CRITICAL: Validate user owns this business
    from app.api.v1.endpoints.master_setup import get_user_business_id
    user_business_id = get_user_business_id(current_user, db)
    
    if business_id != user_business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAP Mapping not found"
        )
    
    # Validate the mapping belongs to this business
    svc.delete_sap_mapping_service(db, mapping_id, business_id)
    return {"message": "SAP Mapping deleted"}
