from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_

from app.models.work_shifts import WorkShift
from app.schemas.work_shift import (
    WorkShiftCreate,
    WorkShiftUpdate,
)


class WorkShiftRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # Get single shift by ID
    # -------------------------
    def get(self, shift_id: int) -> Optional[WorkShift]:
        return self.db.get(WorkShift, shift_id)

    # -------------------------
    # Find by code (global)
    # -------------------------
    def get_by_code(self, code: str) -> Optional[WorkShift]:
        code_norm = code.strip()
        stmt = select(WorkShift).where(WorkShift.code == code_norm)
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------
    # Find by code scoped to a business (optional)
    # -------------------------
    def get_by_code_and_business(self, code: str, business_id: int) -> Optional[WorkShift]:
        code_norm = code.strip()
        stmt = select(WorkShift).where(and_(WorkShift.code == code_norm, WorkShift.business_id == business_id))
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------
    # List all shifts ordered by name
    # -------------------------
    def list(self) -> List[WorkShift]:
        stmt = select(WorkShift).order_by(WorkShift.name.asc())
        return self.db.execute(stmt).scalars().all()

    # -------------------------
    # List shifts for a specific business (optional)
    # -------------------------
    def list_by_business(self, business_id: int) -> List[WorkShift]:
        stmt = select(WorkShift).where(WorkShift.business_id == business_id).order_by(WorkShift.name.asc())
        return self.db.execute(stmt).scalars().all()

    # -------------------------
    # Unset default flag for shifts.
    # - If business_id provided, only affects that business.
    # - If exclude_id provided, that id will be left as-is.
    # -------------------------
    def clear_default(self, business_id: Optional[int] = None, exclude_id: Optional[int] = None) -> None:
        q = update(WorkShift).values(default=False)
        if business_id is not None:
            q = q.where(WorkShift.business_id == business_id)
        if exclude_id is not None:
            q = q.where(WorkShift.id != exclude_id)
        self.db.execute(q)
        self.db.commit()

    # -------------------------
    # Create a new work shift
    # -------------------------
    def create(self, data) -> WorkShift:
        # Handle both dict and schema object
        if isinstance(data, dict):
            payload: Dict[str, Any] = {
                "code": data.get("code", "").strip(),
                "name": data.get("name", "").strip(),
                "payable_hrs": data.get("payable_hrs"),
                "rules": int(data.get("rules", 0) or 0),
                "default": bool(data.get("default", False)),
                "timing": data.get("timing"),
                "start_buffer_hours": int(data.get("start_buffer_hours", 0) or 0),
                "end_buffer_hours": int(data.get("end_buffer_hours", 0) or 0),
                "business_id": data.get("business_id"),
                "created_by": data.get("created_by"),
                "updated_by": data.get("updated_by"),
            }
        else:
            payload: Dict[str, Any] = {
                "code": data.code.strip(),
                "name": data.name.strip(),
                "payable_hrs": data.payable_hrs,
                "rules": int(getattr(data, "rules", 0) or 0),
                "default": bool(getattr(data, "default", False)),
                "timing": getattr(data, "timing", None),
                "start_buffer_hours": int(getattr(data, "start_buffer_hours", 0) or 0),
                "end_buffer_hours": int(getattr(data, "end_buffer_hours", 0) or 0),
                "business_id": getattr(data, "business_id", None),
                "created_by": getattr(data, "created_by", None),
                "updated_by": getattr(data, "updated_by", None),
            }

        # optional business_id if your model/schema supports it
        if getattr(data, "business_id", None) is not None:
            payload["business_id"] = data.business_id

        shift = WorkShift(**payload)
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    # -------------------------
    # Update an existing work shift
    # -------------------------
    def update(self, shift: WorkShift, data: WorkShiftUpdate) -> WorkShift:
        if getattr(data, "code", None) is not None:
            shift.code = data.code.strip()
        if getattr(data, "name", None) is not None:
            shift.name = data.name.strip()
        if getattr(data, "payable_hrs", None) is not None:
            shift.payable_hrs = data.payable_hrs
        if getattr(data, "rules", None) is not None:
            shift.rules = int(data.rules)
        if getattr(data, "default", None) is not None:
            shift.default = bool(data.default)
        if getattr(data, "timing", None) is not None:
            shift.timing = data.timing
        if getattr(data, "start_buffer_hours", None) is not None:
            shift.start_buffer_hours = int(data.start_buffer_hours)
        if getattr(data, "end_buffer_hours", None) is not None:
            shift.end_buffer_hours = int(data.end_buffer_hours)

        # optional business update
        if getattr(data, "business_id", None) is not None:
            shift.business_id = data.business_id

        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    # -------------------------
    # Delete a work shift
    # -------------------------
    def delete(self, shift: WorkShift) -> None:
        self.db.delete(shift)
        self.db.commit()
