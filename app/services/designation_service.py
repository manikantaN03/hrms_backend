from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.designation_repository import DesignationRepository
from app.schemas.designation import (
    DesignationCreate,
    DesignationUpdate,
    DesignationOut,
)


class DesignationService:
    def __init__(self, db: Session):
        self.repo = DesignationRepository(db)
        self.db = db

    def _count_employees(self, designation_id: int) -> int:
        """
        Count employees assigned to this designation.
        
        TODO: Uncomment the implementation below when Employee model is created.
        For now, returns 0 until employee onboarding is implemented.
        
        When ready to implement:
        1. Uncomment the code below
        2. Ensure Employee model is imported: from app.models.employee import Employee
        3. Test with actual employee data
        """
        # from app.models.employee import Employee
        # return self.db.query(Employee).filter(
        #     Employee.designation_id == designation_id,
        #     Employee.is_active == True
        # ).count()
        return 0

    def list_designations(self, business_id: Optional[int] = None) -> List[DesignationOut]:
        """
        List designations. If business_id provided, return only designations for that business.
        """
        if business_id is not None:
            designations = self.repo.list_by_business(business_id)
        else:
            designations = self.repo.list()

        result: List[DesignationOut] = []
        for d in designations:
            employees = self._count_employees(d.id)
            out = DesignationOut.from_orm(d)
            # set dynamic employees field
            object.__setattr__(out, "employees", employees)
            result.append(out)
        return result

    def get_designation(self, designation_id: int, business_id: Optional[int] = None) -> DesignationOut:
        designation = self.repo.get(designation_id)
        if not designation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Designation not found",
            )
        # If business_id provided, ensure designation belongs to that business
        if business_id is not None and getattr(designation, "business_id", None) != business_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Designation not found for this business",
            )
        employees = self._count_employees(designation.id)
        out = DesignationOut.from_orm(designation)
        object.__setattr__(out, "employees", employees)
        return out

    def create_designation(self, data: DesignationCreate, created_by: int = None) -> DesignationOut:
        # Ensure business_id present on create (if your schema requires it)
        business_id = getattr(data, "business_id", None)
        if business_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="business_id is required when creating a designation",
            )

        name = data.name.strip()

        # uniqueness check scoped to business
        existing = self.repo.get_by_name_and_business(name, business_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Designation with this name already exists for this business",
            )

        # If this one is default, clear the old default(s) for that business
        if data.default:
            self.repo.clear_default(business_id=business_id)

        designation_dict = data.model_dump()
        if created_by:
            designation_dict['created_by'] = created_by
            designation_dict['updated_by'] = created_by
        designation = self.repo.create(designation_dict)
        employees = self._count_employees(designation.id)
        out = DesignationOut.from_orm(designation)
        object.__setattr__(out, "employees", employees)
        return out

    def update_designation(self, designation_id: int, data: DesignationUpdate, updated_by: int = None) -> DesignationOut:
        designation = self.repo.get(designation_id)
        if not designation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Designation not found",
            )

        # Determine target business for uniqueness check:
        target_business_id = getattr(data, "business_id", None) if getattr(data, "business_id", None) is not None else designation.business_id

        # Determine new name
        new_name = data.name.strip() if getattr(data, "name", None) else designation.name

        # uniqueness scoped to target business
        if new_name:
            other = self.repo.get_by_name_and_business(new_name, target_business_id)
            if other and other.id != designation.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Another designation with this name already exists for the target business",
                )

        # If making this the default, clear the existing default for that business
        if getattr(data, "default", False):
            self.repo.clear_default(business_id=target_business_id, exclude_id=designation_id)

        update_data = data.model_dump(exclude_unset=True)
        if updated_by:
            update_data['updated_by'] = updated_by
        designation = self.repo.update(designation, update_data)
        employees = self._count_employees(designation.id)
        out = DesignationOut.from_orm(designation)
        object.__setattr__(out, "employees", employees)
        return out

    def delete_designation(self, designation_id: int) -> None:
        designation = self.repo.get(designation_id)
        if not designation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Designation not found",
            )

        # Optional: block delete if employees exist
        # if self._count_employees(designation.id) > 0:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Cannot delete designation with linked employees",
        #     )

        self.repo.delete(designation)
