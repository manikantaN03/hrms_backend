# app/repositories/business_unit_repository.py

from typing import List, Optional

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from app.models.business_unit import BusinessUnit
from sqlalchemy import insert, text
from sqlalchemy.exc import SQLAlchemyError


class BusinessUnitRepository(BaseRepository[BusinessUnit]):
    """
    Repository for BusinessUnit model.
    Includes helpers for managing defaults per business.
    """

    def __init__(self, db: Session):
        super().__init__(BusinessUnit, db)

    def list_by_business(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BusinessUnit]:
        return (
            self.db.query(BusinessUnit)
            .filter(BusinessUnit.business_id == business_id)
            .order_by(BusinessUnit.id.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def unset_default(
        self,
        business_id: int,
        exclude_id: Optional[int] = None,
    ) -> None:
        """
        Set is_default = False for all units of a business.
        Optionally keep one unit unchanged (exclude_id).
        """
        query = self.db.query(BusinessUnit).filter(
            BusinessUnit.business_id == business_id,
            BusinessUnit.is_default == True,  # noqa: E712
        )

        if exclude_id is not None:
            query = query.filter(BusinessUnit.id != exclude_id)

        query.update({BusinessUnit.is_default: False}, synchronize_session=False)
        self.db.commit()

    def create(self, data: dict) -> BusinessUnit:
        """
        Create a business unit using an explicit INSERT that excludes
        the `is_active` column to remain compatible with databases
        that haven't had the column added yet.

        This avoids relying on model-level INSERT behavior which will
        fail if the physical table is missing `is_active`.
        """
        # Allow only known, safe columns in the insert statement
        allowed = [
            "business_id",
            "name",
            "report_title",
            "is_default",
            "header_image_url",
            "footer_image_url",
            "created_by",
            "updated_by",
        ]

        insert_data = {k: v for k, v in data.items() if k in allowed}
        # Ensure is_active is provided to satisfy NOT NULL DB constraint
        if "is_active" not in insert_data:
            insert_data["is_active"] = True

        try:
            # Build raw INSERT using only allowed columns to avoid inserting
            # `is_active` when the physical table may not have that column yet.
            cols = [
                "business_id",
                "name",
                "report_title",
                "is_default",
                "header_image_url",
                "footer_image_url",
                "is_active",
                "created_by",
                "updated_by",
            ]

            provided = [c for c in cols if c in insert_data]
            if not provided:
                raise SQLAlchemyError("No valid columns provided for insert")

            col_list = ", ".join(provided)
            param_list = ", ".join([f":{c}" for c in provided])

            sql = text(
                f"INSERT INTO business_units ({col_list}) VALUES ({param_list}) RETURNING id, created_at, updated_at"
            )

            result = self.db.execute(sql, insert_data)
            new_id_row = result.fetchone()
            self.db.commit()

            if not new_id_row:
                raise SQLAlchemyError("Insert did not return new id")

            new_id = new_id_row[0]
            return self.get(new_id)

        except Exception:
            self.db.rollback()
            raise
