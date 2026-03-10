from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.work_shift_repository import WorkShiftRepository
from app.schemas.work_shift import (
    WorkShiftCreate,
    WorkShiftUpdate,
    WorkShiftOut,
)


class WorkShiftService:
    def __init__(self, db: Session):
        self.repo = WorkShiftRepository(db)
        self.db = db

    def _count_employees(self, shift_id: int) -> int:
        """
        Count employees assigned to this work shift.
        
        TODO: Uncomment the implementation below when Employee model is created.
        For now, returns 0 until employee onboarding is implemented.
        
        When ready to implement:
        1. Uncomment the code below
        2. Ensure Employee model is imported: from app.models.employee import Employee
        3. Test with actual employee data
        """
        # from app.models.employee import Employee
        # return self.db.query(Employee).filter(
        #     Employee.work_shift_id == shift_id,
        #     Employee.is_active == True
        # ).count()
        return 0

    def list_shifts(self, business_id: Optional[int] = None) -> List[WorkShiftOut]:
        # allow optional business scoping when listing shifts
        if business_id is not None:
            shifts = self.repo.list_by_business(business_id)
        else:
            shifts = self.repo.list()
        result: List[WorkShiftOut] = []
        for s in shifts:
            employees = self._count_employees(s.id)
            out = WorkShiftOut.from_orm(s)
            object.__setattr__(out, "employees", employees)
            result.append(out)
        return result

    def get_shift(self, shift_id: int, business_id: Optional[int] = None) -> WorkShiftOut:
        shift = self.repo.get(shift_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work shift not found",
            )
        # If business_id provided, ensure the shift belongs to that business
        if business_id is not None and getattr(shift, "business_id", None) != business_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work shift not found for this business",
            )
        employees = self._count_employees(shift.id)
        out = WorkShiftOut.from_orm(shift)
        object.__setattr__(out, "employees", employees)
        return out

    def create_shift(self, data: WorkShiftCreate, created_by: int = None) -> WorkShiftOut:
        code = data.code.strip()
        # respect business scoping if provided
        business_id = getattr(data, "business_id", None)
        if business_id is not None:
            existing = self.repo.get_by_code_and_business(code, business_id)
        else:
            existing = self.repo.get_by_code(code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Work shift with this code already exists",
            )

        # If this is default, clear previous default(s)
        if data.default:
            # clear defaults scoped to business if business_id provided
            self.repo.clear_default(business_id=business_id)

        shift_dict = data.model_dump()
        if created_by:
            shift_dict['created_by'] = created_by
            shift_dict['updated_by'] = created_by
        shift = self.repo.create(shift_dict)
        employees = self._count_employees(shift.id)
        out = WorkShiftOut.from_orm(shift)
        object.__setattr__(out, "employees", employees)
        return out

    def update_shift(self, shift_id: int, data: WorkShiftUpdate, updated_by: int = None) -> WorkShiftOut:
        shift = self.repo.get(shift_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work shift not found",
            )

        # unique code check on update
        if data.code:
            other = self.repo.get_by_code(data.code.strip())
            if other and other.id != shift.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Another work shift with this code already exists",
                )

        # If making this default, clear all others
        if getattr(data, "default", False):
            # clear defaults within the same business if present
            business_id = getattr(data, "business_id", None)
            self.repo.clear_default(business_id=business_id, exclude_id=shift_id)

        update_data = data.model_dump(exclude_unset=True)
        if updated_by:
            update_data['updated_by'] = updated_by
        shift = self.repo.update(shift, update_data)
        employees = self._count_employees(shift.id)
        out = WorkShiftOut.from_orm(shift)
        object.__setattr__(out, "employees", employees)
        return out

    def delete_shift(self, shift_id: int) -> None:
        shift = self.repo.get(shift_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work shift not found",
            )

        

        self.repo.delete(shift)
