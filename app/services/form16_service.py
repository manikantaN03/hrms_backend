from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.repositories.form16_repository import Form16Repository

class Form16Service:
    def __init__(self, db: Session):
        self.repo = Form16Repository(db)

    def create_employer(self, data: Dict, business_id: Optional[int] = None):
        if business_id is not None:
            data["business_id"] = business_id
        return self.repo.create_employer(data)

def get_form16_service(db: Session) -> Form16Service:
    return Form16Service(db)