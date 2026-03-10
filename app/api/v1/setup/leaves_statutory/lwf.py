from fastapi import APIRouter, Depends, status

from sqlalchemy.orm import Session
 
from app.api.v1.deps import get_db, get_current_admin

from app.models.user import User
 
from app.services.lwf_service import LWFService

from app.schemas.lwf_schemas import (
    LWFRateCreate,
    LWFRateOut,
    LWFComponentToggle,
    LWFSettingsResponse,
    LWFSettingsUpdate,
)

 
router = APIRouter()

service = LWFService()
 
 
# -------------------------------------------------
# GET LWF SETTINGS
# -------------------------------------------------

@router.get(
    "",
    response_model=LWFSettingsResponse,
    summary="Get LWF settings"
)
def get_lwf_settings(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return service.get_or_create_settings(db, business_id)


# -------------------------------------------------
# UPDATE LWF SETTINGS
# -------------------------------------------------

@router.put(
    "",
    response_model=LWFSettingsResponse,
    summary="Update LWF settings"
)
def update_lwf_settings(
    business_id: int,
    data: LWFSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return service.update_settings(db, business_id, data)


# -------------------------------------------------

# GET LWF APPLICABLE COMPONENTS

# -------------------------------------------------

@router.get(

    "/components/{business_id}",

    summary="Get LWF applicable salary components"

)

def get_lwf_components(

    business_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin),

):

    return service.get_lwf_components(db, business_id)
 
 
# -------------------------------------------------

# TOGGLE LWF CHECKBOX

# -------------------------------------------------

@router.put(

    "/components/{component_id}",

    summary="Toggle LWF applicability"

)

def toggle_lwf_component(

    component_id: int,

    data: LWFComponentToggle,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin),

):

    # Require business_id in the payload and validate ownership
    service.toggle_lwf_component(
        db,
        component_id,
        data.is_lwf_applicable,
        data.business_id,
    )

    return {"message": "LWF applicability updated"}
 
 
# -------------------------------------------------

# CREATE LWF RATE

# -------------------------------------------------

@router.post(

    "/rates",

    response_model=LWFRateOut,

    status_code=status.HTTP_201_CREATED,

    summary="Create LWF rate"

)

def create_lwf_rate(

    data: LWFRateCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin),

):

    return service.create_rate(db, data)
 
 
# -------------------------------------------------

# LIST LWF RATES

# -------------------------------------------------

@router.get(

    "/rates",

    response_model=list[LWFRateOut],

    summary="List LWF rates"

)

def list_lwf_rates(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin),

):

    return service.list_rates(db)

 