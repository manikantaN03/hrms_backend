"""
Approval Settings Endpoints
API routes for Approval configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business
from app.schemas.approval_schema import (
    ApprovalSettingsCreateUpdate,
    ApprovalSettingsResponse,
)
from app.services.approval_service import get_approval_service

router = APIRouter(prefix="/approvals")


# ============================================================================
# Helpers
# ============================================================================

def validate_business_exists(db: Session, business_id: int) -> Business:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    return business


def approval_to_response_dict(approval_obj) -> dict:
    """Convert approval object to response dictionary with camelCase keys"""
    if not approval_obj:
        return {}
    
    return {
        "id": approval_obj.id,
        "businessId": approval_obj.business_id,
        "leaveRequest": approval_obj.leave_request,
        "missedPunch": approval_obj.missed_punch,
        "missedPunchDays": approval_obj.missed_punch_days,
        "compOff": approval_obj.comp_off,
        "compOffLapseDays": approval_obj.comp_off_lapse_days,
        "lapseMonthly": approval_obj.lapse_monthly,
        "remotePunch": approval_obj.remote_punch,
        "remoteLocation": approval_obj.remote_location,
        "selfiePunch": approval_obj.selfie_punch,
        "selfieLocation": approval_obj.selfie_location,
        "timeRelaxation": approval_obj.time_relaxation,
        "timeRequests": approval_obj.time_requests,
        "timeHours": approval_obj.time_hours,
        "travelCalc": approval_obj.travel_calc,
        "shiftChangeLevel1": approval_obj.shift_change_level1,
        "shiftChangeLevel2": approval_obj.shift_change_level2,
        "shiftChangeLevel3": approval_obj.shift_change_level3,
        "shiftChangeApprovalsRequired": approval_obj.shift_change_approvals_required,
        "weekoffChangeLevel1": approval_obj.weekoff_change_level1,
        "weekoffChangeLevel2": approval_obj.weekoff_change_level2,
        "weekoffChangeLevel3": approval_obj.weekoff_change_level3,
        "weekoffChangeApprovalsRequired": approval_obj.weekoff_change_approvals_required,
        "isActive": approval_obj.is_active,
    }


# ============================================================================
# Approval Settings Endpoints
# ============================================================================

@router.get(
    "/{business_id}",
    status_code=status.HTTP_200_OK,
    summary="Get approval settings for a business",
)
def get_approval_settings(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    **Access:** ADMIN or SUPERADMIN
    """
    validate_business_exists(db, business_id)
    service = get_approval_service(db)

    settings = service.get_by_business(business_id)
    if not settings:
        # Return default settings if none exist
        return {
            "businessId": business_id,
            "leaveRequest": "manager",
            "missedPunch": "disabled",
            "missedPunchDays": 7,
            "compOff": "disabled",
            "compOffLapseDays": 0,
            "lapseMonthly": False,
            "remotePunch": False,
            "remoteLocation": False,
            "selfiePunch": False,
            "selfieLocation": False,
            "timeRelaxation": "disabled",
            "timeRequests": 5,
            "timeHours": 10,
            "travelCalc": "calculated",
            "shiftChangeLevel1": "",
            "shiftChangeLevel2": "",
            "shiftChangeLevel3": "",
            "shiftChangeApprovalsRequired": 0,
            "weekoffChangeLevel1": "",
            "weekoffChangeLevel2": "",
            "weekoffChangeLevel3": "",
            "weekoffChangeApprovalsRequired": 0,
            "isActive": True,
        }

    return approval_to_response_dict(settings)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Create or update approval settings",
)
def save_approval_settings(
    data: ApprovalSettingsCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    **Access:** ADMIN or SUPERADMIN

    POST returns **200 OK** with updated settings
    """
    # business_id must be provided in request body
    business_id = getattr(data, "business_id", None)
    if not business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="business_id is required in request body",
        )

    validate_business_exists(db, business_id)
    service = get_approval_service(db)

    # Convert to dict for repository
    payload = data.model_dump(by_alias=False)
    settings = service.create_or_update(payload)

    return approval_to_response_dict(settings)
