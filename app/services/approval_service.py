from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.approval_repository import ApprovalRepository


class ApprovalService:
    def __init__(self, db: Session):
        self.repo = ApprovalRepository(db)

    def get_by_business(self, business_id: int):
        """Get approval settings by business ID"""
        return self.repo.get_by_business(business_id)

    def create_or_update(self, data: dict) -> dict:
        """Create or update approval settings"""
        business_id = data.get("business_id")
        existing = self.repo.get_by_business(business_id)
        
        if existing:
            return self.repo.update(existing.id, data)
        else:
            return self.repo.create(data)


def get_approval_service(db: Session) -> ApprovalService:
    return ApprovalService(db)