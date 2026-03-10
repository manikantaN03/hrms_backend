from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.grade_repository import GradeRepository
from app.schemas.grade import GradeCreate, GradeUpdate, GradeOut



class GradeService:
    def __init__(self, db: Session):
        self.repo = GradeRepository(db)
        self.db = db

    def _count_employees(self, grade_id: int) -> int:
        """
        Count employees assigned to this grade.
        
        TODO: Uncomment the implementation below when Employee model is created.
        For now, returns 0 until employee onboarding is implemented.
        
        When ready to implement:
        1. Uncomment the code below
        2. Ensure Employee model is imported: from app.models.employee import Employee
        3. Test with actual employee data
        """
        # from app.models.employee import Employee
        # return self.db.query(Employee).filter(
        #     Employee.grade_id == grade_id,
        #     Employee.is_active == True
        # ).count()
        return 0

    def list_grades(self, business_id: Optional[int] = None) -> List[GradeOut]:
        grades = self.repo.list(business_id=business_id)
        result: List[GradeOut] = []
        for g in grades:
            employees = self._count_employees(g.id)
            out = GradeOut.from_orm(g)
            # set computed employees value
            object.__setattr__(out, "employees", employees)
            result.append(out)
        return result

    def get_grade(self, grade_id: int, business_id: Optional[int] = None) -> GradeOut:
        grade = self.repo.get(grade_id)
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found",
            )
        # If business_id provided, ensure the grade belongs to that business
        if business_id is not None and getattr(grade, "business_id", None) != business_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found for this business",
            )
        employees = self._count_employees(grade.id)
        out = GradeOut.from_orm(grade)
        object.__setattr__(out, "employees", employees)
        return out

    def create_grade(self, data: GradeCreate, created_by: int = None) -> GradeOut:
        name = data.name.strip()
        existing = self.repo.get_by_name(name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grade with this name already exists",
            )
        grade_dict = data.model_dump()
        if created_by:
            grade_dict['created_by'] = created_by
            grade_dict['updated_by'] = created_by
        grade = self.repo.create(grade_dict)
        employees = self._count_employees(grade.id)
        out = GradeOut.from_orm(grade)
        object.__setattr__(out, "employees", employees)
        return out

    def update_grade(self, grade_id: int, data: GradeUpdate, updated_by: int = None) -> GradeOut:
        grade = self.repo.get(grade_id)
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found",
            )

        if data.name:
            other = self.repo.get_by_name(data.name.strip())
            if other and other.id != grade.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Another grade with this name already exists",
                )

        update_data = data.model_dump(exclude_unset=True)
        if updated_by:
            update_data['updated_by'] = updated_by
        grade = self.repo.update(grade, update_data)
        employees = self._count_employees(grade.id)
        out = GradeOut.from_orm(grade)
        object.__setattr__(out, "employees", employees)
        return out

    def delete_grade(self, grade_id: int) -> None:
        grade = self.repo.get(grade_id)
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found",
            )

        # Optional: prevent deleting grades that still have employees
        # if self._count_employees(grade.id) > 0:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Cannot delete grade with linked employees",
        #     )

        self.repo.delete(grade)
