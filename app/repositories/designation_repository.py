from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError

from app.models.designations import Designation
from app.schemas.designation import (
    DesignationCreate,
    DesignationUpdate,
)


class DesignationRepository:
    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------------------
    # Get single designation by ID
    # ----------------------------------------------------------------------
    def get(self, designation_id: int) -> Optional[Designation]:
        return self.db.get(Designation, designation_id)

    # ----------------------------------------------------------------------
    # Find by name (global)
    # ----------------------------------------------------------------------
    def get_by_name(self, name: str) -> Optional[Designation]:
        stmt = select(Designation).where(Designation.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    # ----------------------------------------------------------------------
    # Find by name scoped to a business
    # ----------------------------------------------------------------------
    def get_by_name_and_business(self, name: str, business_id: int) -> Optional[Designation]:
        stmt = select(Designation).where(
            and_(Designation.name == name, Designation.business_id == business_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # ----------------------------------------------------------------------
    # List all designations (global)
    # ----------------------------------------------------------------------
    def list(self) -> List[Designation]:
        stmt = select(Designation).order_by(Designation.name.asc())
        return self.db.execute(stmt).scalars().all()

    # ----------------------------------------------------------------------
    # List designations for a specific business
    # ----------------------------------------------------------------------
    def list_by_business(self, business_id: int) -> List[Designation]:
        stmt = select(Designation).where(Designation.business_id == business_id).order_by(Designation.name.asc())
        return self.db.execute(stmt).scalars().all()

    # ----------------------------------------------------------------------
    # Set default=False for designations.
    # If business_id provided, only target that business.
    # Optionally exclude a specific id (useful when switching default)
    # ----------------------------------------------------------------------
    def clear_default(self, business_id: Optional[int] = None, exclude_id: Optional[int] = None) -> None:
        q = update(Designation).values(default=False)
        if business_id is not None:
            q = q.where(Designation.business_id == business_id)
        if exclude_id is not None:
            q = q.where(Designation.id != exclude_id)
        self.db.execute(q)
        self.db.commit()

    # ----------------------------------------------------------------------
    # Create a new designation
    # ----------------------------------------------------------------------
    def create(self, data) -> Designation:
        """
        Expects DesignationCreate schema or dict with:
        - name: str
        - default: bool
        - business_id: int  (required if your API expects business-scoped designations)
        """
        payload: Dict[str, Any] = {}

        # Handle both dict and schema object
        if isinstance(data, dict):
            payload["name"] = data.get("name", "").strip()
            payload["default"] = bool(data.get("default", False))
            business_id = data.get("business_id")
            created_by = data.get("created_by")
            updated_by = data.get("updated_by")
        else:
            payload["name"] = data.name.strip()
            payload["default"] = bool(getattr(data, "default", False))
            business_id = getattr(data, "business_id", None)
            created_by = getattr(data, "created_by", None)
            updated_by = getattr(data, "updated_by", None)

        # business_id may be present (if designations are business-scoped)
        if business_id is not None:
            payload["business_id"] = business_id

        # Add audit fields
        if created_by is not None:
            payload["created_by"] = created_by
        if updated_by is not None:
            payload["updated_by"] = updated_by

        # employees should be derived from Employee table; initialize 0
        payload["employees"] = 0

        designation = Designation(**payload)
        self.db.add(designation)
        try:
            self.db.commit()
        except IntegrityError:
            # Unique constraint violation — try to return the existing record instead
            self.db.rollback()
            existing = None
            if business_id is not None:
                existing = self.get_by_name_and_business(payload["name"], business_id)
            else:
                existing = self.get_by_name(payload["name"])

            if existing is not None:
                return existing

            # If we couldn't find an existing row, re-raise the integrity error
            raise

        self.db.refresh(designation)
        return designation

    # ----------------------------------------------------------------------
    # Update an existing designation
    # ----------------------------------------------------------------------
    def update(self, designation: Designation, data: DesignationUpdate) -> Designation:
        if getattr(data, "name", None) is not None:
            designation.name = data.name.strip()

        if getattr(data, "default", None) is not None:
            designation.default = bool(data.default)

        # allow moving designation between businesses if provided
        if getattr(data, "business_id", None) is not None:
            designation.business_id = data.business_id

        self.db.add(designation)
        self.db.commit()
        self.db.refresh(designation)
        return designation

    # ----------------------------------------------------------------------
    # Delete designation
    # ----------------------------------------------------------------------
    def delete(self, designation: Designation) -> None:
        self.db.delete(designation)
        self.db.commit()
