from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class LeavePolicyBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    leave_type: str = Field(..., alias="leaveType", min_length=1, max_length=100)
    policy_name: str = Field(..., alias="policyName", min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)

    # Grant Settings
    grant_enabled: bool = Field(True, alias="grantLeaves")
    grant_condition: int = Field(0, alias="condition", ge=0)
    monthly_grant_leaves: List[float] = Field(..., alias="monthlyLeaves")
    reset_negative_balance: bool = Field(False, alias="resetNegative")

    # Lapse Settings
    lapse_enabled: bool = Field(False, alias="lapseLeaves")
    monthly_lapse_limits: List[float] = Field(default_factory=lambda: [0] * 12, alias="lapseMonthly")

    # Other Options
    do_not_apply_during_probation: bool = Field(False, alias="doNotApplyDuring")
    do_not_apply_after_probation: bool = Field(False, alias="doNotApplyAfter")
    auto_apply: bool = Field(False, alias="autoApply")

    @field_validator("monthly_grant_leaves", "monthly_lapse_limits")
    @classmethod
    def validate_monthly_array(cls, v):
        if len(v) != 12:
            raise ValueError("Monthly values must be exactly 12 elements (one per month)")
        if any(val < 0 for val in v):
            raise ValueError("Monthly values cannot be negative")
        return v

    @field_validator("leave_type")
    @classmethod
    def validate_leave_type(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Leave type cannot be empty")
        return v.strip()


class LeavePolicyCreate(LeavePolicyBase):
    business_id: Optional[int] = None


class LeavePolicyUpdate(LeavePolicyBase):
    business_id: Optional[int] = None


class LeavePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    business_id: int
    name: str
    type: str
    grant: str
    lapse: str
    monthly: List[float]

    # Full details for edit
    leaveType: str
    policyName: str
    description: Optional[str]
    grantLeaves: bool
    condition: int
    monthlyLeaves: List[float]
    resetNegative: bool
    lapseLeaves: bool
    lapseMonthly: List[float]
    doNotApplyDuring: bool
    doNotApplyAfter: bool
    autoApply: bool

    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle ORM objects"""
        if hasattr(obj, '__dict__'):
            return cls(
                id=obj.id,
                business_id=obj.business_id,
                name=obj.policy_name,
                type=obj.leave_type,
                grant="Yes" if obj.grant_enabled else "No",
                lapse="Yes" if obj.lapse_enabled else "No",
                monthly=obj.monthly_grant_leaves or [0] * 12,

                # Full details
                leaveType=obj.leave_type,
                policyName=obj.policy_name,
                description=obj.description,
                grantLeaves=obj.grant_enabled,
                condition=obj.grant_condition,
                monthlyLeaves=obj.monthly_grant_leaves or [0] * 12,
                resetNegative=obj.reset_negative_balance,
                lapseLeaves=obj.lapse_enabled,
                lapseMonthly=obj.monthly_lapse_limits or [0] * 12,
                doNotApplyDuring=obj.do_not_apply_during_probation,
                doNotApplyAfter=obj.do_not_apply_after_probation,
                autoApply=obj.auto_apply,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        return obj


class PolicySummary(BaseModel):
    """Simplified response for list view"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    grant: str
    lapse: str
