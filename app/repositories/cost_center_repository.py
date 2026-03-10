from sqlalchemy.orm import Session
from app.models.cost_center import CostCenter


class CostCenterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, business_id: int):
        return self.db.query(CostCenter).filter(
            CostCenter.business_id == business_id,
            CostCenter.is_active == True
        ).all()

    def get_all_global(self):
        """Return all active cost centers across all businesses."""
        return self.db.query(CostCenter).filter(CostCenter.is_active == True).order_by(CostCenter.id.asc()).all()

    def get(self, id: int):
        return self.db.query(CostCenter).filter(CostCenter.id == id).first()

    def find_by_business_and_name(self, business_id: int, name: str):
        return self.db.query(CostCenter).filter(
            CostCenter.business_id == business_id,
            CostCenter.name == name,
            CostCenter.is_active == True
        ).first()

    def unset_default(self, business_id: int):
        self.db.query(CostCenter).filter(
            CostCenter.business_id == business_id,
            CostCenter.is_default == True
        ).update({"is_default": False})

        self.db.commit()

    def create(self, data: dict):
        obj = CostCenter(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, id: int, data: dict):
        obj = self.get(id)
        for key, value in data.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int):
        obj = self.get(id)
        obj.is_active = False
        self.db.commit()
