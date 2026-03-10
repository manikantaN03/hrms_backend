from sqlalchemy.orm import Session
from app.models.approval_settings import ApprovalSettings


class ApprovalRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_business(self, business_id: int):
        return self.db.query(ApprovalSettings).filter(
            ApprovalSettings.business_id == business_id
        ).first()

    def get(self, approval_id: int):
        return self.db.query(ApprovalSettings).filter(
            ApprovalSettings.id == approval_id
        ).first()

    def create(self, data: dict):
        obj = ApprovalSettings(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, approval_id: int, data: dict):
        self.db.query(ApprovalSettings).filter(
            ApprovalSettings.id == approval_id
        ).update(data)
        self.db.commit()
        return self.get(approval_id)
