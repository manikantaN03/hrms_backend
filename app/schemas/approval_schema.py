from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class ApprovalSettingsCreateUpdate(BaseModel):
    business_id: int = Field(..., alias="businessId", gt=0, description="Business ID")

    leave_request: Literal["manager", "both", "managerThenHR"] = Field(
        ..., 
        alias="leaveRequest",
        description="Leave request approval workflow"
    )
    missed_punch: str = Field(
        ..., 
        alias="missedPunch",
        min_length=1,
        max_length=50,
        description="Missed punch approval authority"
    )
    missed_punch_days: int = Field(
        ..., 
        alias="missedPunchDays",
        ge=1,
        le=31,
        description="Days allowed for missed punch requests"
    )

    comp_off: str = Field(
        ..., 
        alias="compOff",
        min_length=1,
        max_length=50,
        description="Comp off approval authority"
    )
    comp_off_lapse_days: int = Field(
        ..., 
        alias="compOffLapseDays",
        ge=0,
        le=90,
        description="Days after which comp offs lapse"
    )
    lapse_monthly: bool = Field(
        ..., 
        alias="lapseMonthly",
        description="Lapse all comp offs at month end"
    )

    remote_punch: bool = Field(
        ..., 
        alias="remotePunch",
        description="Enable remote punch"
    )
    remote_location: bool = Field(
        ..., 
        alias="remoteLocation",
        description="Restrict remote punch to employee location"
    )

    selfie_punch: bool = Field(
        ..., 
        alias="selfiePunch",
        description="Enable selfie punch"
    )
    selfie_location: bool = Field(
        ..., 
        alias="selfieLocation",
        description="Restrict selfie punch to employee location"
    )

    time_relaxation: str = Field(
        ..., 
        alias="timeRelaxation",
        min_length=1,
        max_length=50,
        description="Time relaxation approval authority"
    )
    time_requests: int = Field(
        ..., 
        alias="timeRequests",
        ge=0,
        le=31,
        description="Monthly time relaxation requests limit per person"
    )
    time_hours: int = Field(
        ..., 
        alias="timeHours",
        ge=0,
        le=100,
        description="Monthly time relaxation hours limit per person"
    )

    travel_calc: Literal["calculated", "approved"] = Field(
        ..., 
        alias="travelCalc",
        description="Travel reimbursement calculation method"
    )

    shift_change_level1: str = Field(
        default="", 
        alias="shiftChangeLevel1",
        max_length=50,
        description="Shift change request level 1 approver"
    )
    shift_change_level2: str = Field(
        default="", 
        alias="shiftChangeLevel2",
        max_length=50,
        description="Shift change request level 2 approver"
    )
    shift_change_level3: str = Field(
        default="", 
        alias="shiftChangeLevel3",
        max_length=50,
        description="Shift change request level 3 approver"
    )
    shift_change_approvals_required: int = Field(
        default=0, 
        alias="shiftChangeApprovalsRequired",
        ge=0,
        le=3,
        description="Number of approvals required for shift change"
    )

    weekoff_change_level1: str = Field(
        default="", 
        alias="weekoffChangeLevel1",
        max_length=50,
        description="Week off change request level 1 approver"
    )
    weekoff_change_level2: str = Field(
        default="", 
        alias="weekoffChangeLevel2",
        max_length=50,
        description="Week off change request level 2 approver"
    )
    weekoff_change_level3: str = Field(
        default="", 
        alias="weekoffChangeLevel3",
        max_length=50,
        description="Week off change request level 3 approver"
    )
    weekoff_change_approvals_required: int = Field(
        default=0, 
        alias="weekoffChangeApprovalsRequired",
        ge=0,
        le=3,
        description="Number of approvals required for week off change"
    )

    @field_validator('leave_request')
    @classmethod
    def validate_leave_request(cls, v: str) -> str:
        if v not in ["manager", "both", "managerThenHR"]:
            raise ValueError("leave_request must be one of: manager, both, managerThenHR")
        return v

    @field_validator('travel_calc')
    @classmethod
    def validate_travel_calc(cls, v: str) -> str:
        if v not in ["calculated", "approved"]:
            raise ValueError("travel_calc must be one of: calculated, approved")
        return v

    model_config = ConfigDict(populate_by_name=True)


class ApprovalSettingsResponse(BaseModel):
    id: int
    business_id: int = Field(..., alias="businessId")
    
    leave_request: str = Field(..., alias="leaveRequest")
    missed_punch: str = Field(..., alias="missedPunch")
    missed_punch_days: int = Field(..., alias="missedPunchDays")

    comp_off: str = Field(..., alias="compOff")
    comp_off_lapse_days: int = Field(..., alias="compOffLapseDays")
    lapse_monthly: bool = Field(..., alias="lapseMonthly")

    remote_punch: bool = Field(..., alias="remotePunch")
    remote_location: bool = Field(..., alias="remoteLocation")

    selfie_punch: bool = Field(..., alias="selfiePunch")
    selfie_location: bool = Field(..., alias="selfieLocation")

    time_relaxation: str = Field(..., alias="timeRelaxation")
    time_requests: int = Field(..., alias="timeRequests")
    time_hours: int = Field(..., alias="timeHours")

    travel_calc: str = Field(..., alias="travelCalc")
    
    shift_change_level1: str = Field(..., alias="shiftChangeLevel1")
    shift_change_level2: str = Field(..., alias="shiftChangeLevel2")
    shift_change_level3: str = Field(..., alias="shiftChangeLevel3")
    shift_change_approvals_required: int = Field(..., alias="shiftChangeApprovalsRequired")

    weekoff_change_level1: str = Field(..., alias="weekoffChangeLevel1")
    weekoff_change_level2: str = Field(..., alias="weekoffChangeLevel2")
    weekoff_change_level3: str = Field(..., alias="weekoffChangeLevel3")
    weekoff_change_approvals_required: int = Field(..., alias="weekoffChangeApprovalsRequired")
    
    is_active: bool = Field(..., alias="isActive")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
