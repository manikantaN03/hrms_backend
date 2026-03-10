from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.leave_type_repository import LeaveTypeRepository

repo = LeaveTypeRepository()

class LeaveTypeService:

    def create_leave_type(self, db: Session, data, business_id: int):
        # Validation is now handled by Pydantic schema validators
        if repo.get_by_alias(db, data.alias, business_id):
            raise HTTPException(
                status_code=400,
                detail=f"Leave type with alias '{data.alias}' already exists for this business"
            )

        # Convert to dict with by_alias=False to get snake_case field names
        leave_data = data.model_dump(by_alias=False)
        leave_data["business_id"] = business_id
        return repo.create(db, leave_data)

    def get_all(self, db: Session, business_id: int = None):
        return repo.get_all(db, business_id)

    def get_one(self, db: Session, leave_type_id: int, business_id: int = None):
        leave = repo.get_by_id(db, leave_type_id, business_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave type not found")
        return leave

    def update(self, db: Session, leave_type_id: int, data, business_id: int = None):
        leave = repo.get_by_id(db, leave_type_id, business_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave type not found")

        # Check alias uniqueness if alias is being updated
        if hasattr(data, 'alias') and data.alias and data.alias != leave.alias:
            if repo.get_by_alias(db, data.alias, business_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Alias '{data.alias}' already exists for this business"
                )

        # Convert to dict with by_alias=False to get snake_case field names
        update_data = data.model_dump(exclude_unset=True, by_alias=False)
        return repo.update(db, leave, update_data)

    def delete(self, db: Session, leave_type_id: int, business_id: int = None):
        leave = repo.get_by_id(db, leave_type_id, business_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave type not found")

        repo.delete(db, leave)
        return True

leave_type_service = LeaveTypeService()
