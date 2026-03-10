from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.grades import Grade
from app.schemas.grade import GradeCreate, GradeUpdate


class GradeRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # Get single grade by ID
    # -------------------------
    def get(self, grade_id: int) -> Optional[Grade]:
        return self.db.get(Grade, grade_id)

    # -------------------------
    # Find by name (exact match)
    # -------------------------
    def get_by_name(self, name: str) -> Optional[Grade]:
        normalized = name.strip()
        stmt = select(Grade).where(Grade.name == normalized)
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------
    # (Optional) Case-insensitive name lookup
    # Useful to prevent "Associate" vs "associate" duplicates
    # -------------------------
    def get_by_name_case_insensitive(self, name: str) -> Optional[Grade]:
        normalized = name.strip()
        stmt = select(Grade).where(func.lower(Grade.name) == func.lower(normalized))
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------
    # List all grades ordered by name
    # -------------------------
    def list(self, business_id: Optional[int] = None) -> List[Grade]:
        """List grades, optionally filtered by `business_id`."""
        stmt = select(Grade)
        if business_id is not None:
            stmt = stmt.where(Grade.business_id == business_id)
        stmt = stmt.order_by(Grade.name.asc())
        return self.db.execute(stmt).scalars().all()

    # -------------------------
    # Create a new grade
    # -------------------------
    def create(self, data) -> Grade:
        """
        Create a Grade. Accepts either GradeCreate schema or dict.
        We intentionally initialize employees to 0 here;
        the service layer computes the live employee count if needed.
        """
        # Handle both dict and schema object
        if isinstance(data, dict):
            name = data.get("name", "").strip()
            business_id = data.get("business_id")
            created_by = data.get("created_by")
            updated_by = data.get("updated_by")
        else:
            name = data.name.strip()
            business_id = getattr(data, "business_id", None)
            created_by = getattr(data, "created_by", None)
            updated_by = getattr(data, "updated_by", None)
        
        grade = Grade(
            name=name,
            employees=0,
            business_id=business_id,
            created_by=created_by,
            updated_by=updated_by,
        )
        self.db.add(grade)
        self.db.commit()
        self.db.refresh(grade)
        return grade

    # -------------------------
    # Update an existing grade
    # -------------------------
    def update(self, grade: Grade, data) -> Grade:
        """
        Update an existing grade.

        Accepts either a mapping/dict (e.g. service.model_dump() result)
        or a schema-like object with attributes (e.g. `GradeUpdate`).
        """
        # dict-like input
        if isinstance(data, dict):
            name = data.get("name")
            if name is not None:
                grade.name = name.strip()

            if "employees" in data and data.get("employees") is not None:
                grade.employees = data.get("employees")

        else:
            if getattr(data, "name", None) is not None:
                grade.name = data.name.strip()

            # If you keep a denormalized employees column and want the API to set it:
            if getattr(data, "employees", None) is not None:
                grade.employees = data.employees

        self.db.add(grade)
        self.db.commit()
        self.db.refresh(grade)
        return grade

    # -------------------------
    # Delete a grade
    # -------------------------
    def delete(self, grade: Grade) -> None:
        self.db.delete(grade)
        self.db.commit()
