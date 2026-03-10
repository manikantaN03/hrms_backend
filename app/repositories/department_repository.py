from sqlalchemy.orm import Session
from app.models.department import Department


class DepartmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, business_id: int):
        return self.db.query(Department).filter(
            Department.business_id == business_id
        ).all()

    def get(self, department_id: int):
        return self.db.query(Department).filter(
            Department.id == department_id
        ).first()

    def find_by_business_and_name(self, business_id: int, name: str):
        return self.db.query(Department).filter(
            Department.business_id == business_id,
            Department.name == name,
        ).first()

    def unset_default(self, business_id: int):
        self.db.query(Department).filter(
            Department.business_id == business_id,
            Department.is_default == True,
        ).update({"is_default": False})
        self.db.commit()

    def create(self, data: dict):
        obj = Department(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, department_id: int, data: dict):
        self.db.query(Department).filter(
            Department.id == department_id
        ).update(data)
        self.db.commit()
        return self.get(department_id)

    def delete(self, department_id: int, hard: bool = False):
        obj = self.get(department_id)

        if hard:
            self.db.delete(obj)

        self.db.commit()
        return obj
