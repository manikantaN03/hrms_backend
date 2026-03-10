from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from app.repositories.shift_policy_repository import ShiftPolicyRepository
from app.repositories.work_shift_repository import WorkShiftRepository
from app.schemas.shift_policy import ShiftPolicyCreate, ShiftPolicyUpdate, ShiftPolicyDetailResponse
from app.schemas.work_shift import WorkShiftOut

class ShiftPolicyService:

    @staticmethod
    def create_policy(db: Session, payload: ShiftPolicyCreate) -> ShiftPolicyDetailResponse:
        # Validate default shift
        if payload.default_shift_id:
            ws_repo = WorkShiftRepository(db)
            shift = ws_repo.get(payload.default_shift_id)
            if not shift or getattr(shift, "business_id", None) != payload.business_id:
                raise HTTPException(status_code=404, detail=f"Default shift {payload.default_shift_id} not found")
        # Validate weekly shifts
        if payload.weekly_shifts:
            ws_repo = WorkShiftRepository(db)
            for day, shift_id in payload.weekly_shifts.items():
                if shift_id:
                    s = ws_repo.get(shift_id)
                    if not s or getattr(s, "business_id", None) != payload.business_id:
                        raise HTTPException(status_code=404, detail=f"Shift {shift_id} for {day} not found")
        # Unset other defaults if needed
        if payload.is_default:
            ShiftPolicyRepository.set_as_default(db, 0, payload.business_id)  # use 0 for new policy
        policy = ShiftPolicyRepository.create(db, payload)
        return ShiftPolicyService.get_policy_by_id(db, policy.id, payload.business_id)

    @staticmethod
    def get_all_policies(db: Session, business_id: int) -> List[ShiftPolicyDetailResponse]:
        policies = ShiftPolicyRepository.get_all(db, business_id)
        result = []
        for policy in policies:
            weekly_detail = {}
            ws_repo = WorkShiftRepository(db)
            for day, shift_id in policy.weekly_shifts.items():
                if shift_id:
                    shift = ws_repo.get(shift_id)
                    weekly_detail[day] = WorkShiftOut.model_validate(shift) if shift and getattr(shift, "business_id", None) == business_id else None
                else:
                    weekly_detail[day] = None
            result.append(ShiftPolicyDetailResponse(
                id=policy.id,
                business_id=policy.business_id,
                title=policy.title,
                description=policy.description,
                is_default=policy.is_default,
                default_shift=WorkShiftOut.model_validate(policy.default_shift) if policy.default_shift else None,
                weekly_shifts_detail=weekly_detail,
                created_at=policy.created_at,
                updated_at=policy.updated_at
            ))
        return result

    @staticmethod
    def get_policy_by_id(db: Session, policy_id: int, business_id: int) -> ShiftPolicyDetailResponse:
        policy = ShiftPolicyRepository.get_by_id(db, policy_id, business_id)
        if not policy:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        weekly_detail = {}
        ws_repo = WorkShiftRepository(db)
        for day, shift_id in policy.weekly_shifts.items():
            if shift_id:
                shift = ws_repo.get(shift_id)
                weekly_detail[day] = WorkShiftOut.model_validate(shift) if shift and getattr(shift, "business_id", None) == business_id else None
            else:
                weekly_detail[day] = None
        return ShiftPolicyDetailResponse(
            id=policy.id,
            business_id=policy.business_id,
            title=policy.title,
            description=policy.description,
            is_default=policy.is_default,
            default_shift=WorkShiftOut.model_validate(policy.default_shift) if policy.default_shift else None,
            weekly_shifts_detail=weekly_detail,
            created_at=policy.created_at,
            updated_at=policy.updated_at
        )

    @staticmethod
    def get_default_policy(db: Session, business_id: int) -> ShiftPolicyDetailResponse:
        policy = ShiftPolicyRepository.get_default_policy(db, business_id)
        if not policy:
            raise HTTPException(status_code=404, detail=f"Default policy for business {business_id} not found")

        weekly_detail = {}
        ws_repo = WorkShiftRepository(db)
        for day, shift_id in policy.weekly_shifts.items():
            if shift_id:
                shift = ws_repo.get(shift_id)
                weekly_detail[day] = WorkShiftOut.model_validate(shift) if shift and getattr(shift, "business_id", None) == business_id else None
            else:
                weekly_detail[day] = None

        return ShiftPolicyDetailResponse(
            id=policy.id,
            business_id=policy.business_id,
            title=policy.title,
            description=policy.description,
            is_default=policy.is_default,
            default_shift=WorkShiftOut.model_validate(policy.default_shift) if policy.default_shift else None,
            weekly_shifts_detail=weekly_detail,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )

    @staticmethod
    def update_policy(db: Session, policy_id: int, business_id: int, payload: ShiftPolicyUpdate) -> ShiftPolicyDetailResponse:
        # validate default_shift and weekly shifts if present
        ws_repo = WorkShiftRepository(db)
        if getattr(payload, "default_shift_id", None) is not None:
            s = ws_repo.get(payload.default_shift_id)
            if not s or getattr(s, "business_id", None) != business_id:
                raise HTTPException(status_code=404, detail=f"Default shift {payload.default_shift_id} not found")

        if getattr(payload, "weekly_shifts", None):
            for day, shift_id in payload.weekly_shifts.items():
                if shift_id:
                    s = ws_repo.get(shift_id)
                    if not s or getattr(s, "business_id", None) != business_id:
                        raise HTTPException(status_code=404, detail=f"Shift {shift_id} for {day} not found")

        updated = ShiftPolicyRepository.update(db, policy_id, business_id, payload)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

        # if marking as default, ensure it's the only default
        if getattr(payload, "is_default", False):
            ShiftPolicyRepository.set_as_default(db, policy_id, business_id)

        return ShiftPolicyService.get_policy_by_id(db, policy_id, business_id)

    @staticmethod
    def delete_policy(db: Session, policy_id: int, business_id: int) -> None:
        ok = ShiftPolicyRepository.delete(db, policy_id, business_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    # update_policy, delete_policy, get_default_policy can be similarly implemented
