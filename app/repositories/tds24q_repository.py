import re
from typing import Union
from sqlalchemy.orm import Session
from app.models.tds24q_models import TDS24Q
from app.schemas.tds24q_schemas import TDS24QCreate, TDS24QUpdate


class _TDS24QRepository:
    def _camel_to_snake(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def create_tds24q(self, db: Session, data: Union[TDS24QCreate, dict]) -> dict:
        """
        Accept a Pydantic TDS24QCreate OR a plain dict (camelCase keys),
        normalize keys to snake_case, persist and return a plain dict.
        """
        if isinstance(data, dict):
            raw = data
        else:
            raw = data.model_dump() if hasattr(data, "model_dump") else data.dict()

        # convert camelCase keys to snake_case for SQLAlchemy model
        payload = {self._camel_to_snake(k): v for k, v in raw.items() if v is not None}

        tds = TDS24Q(**payload)
        db.add(tds)
        db.commit()
        db.refresh(tds)
        return {k: v for k, v in tds.__dict__.items() if not k.startswith("_")}

    def get_all_tds24q(self, db: Session, skip: int = 0, limit: int = 100) -> list:
        """Return paginated TDS24Q records as plain dicts."""
        items = db.query(TDS24Q).offset(skip).limit(limit).all()
        return [{k: v for k, v in item.__dict__.items() if not k.startswith("_")} for item in items]

    def get_tds24q(self, db: Session, record_id: int) -> dict | None:
        item = db.query(TDS24Q).filter(TDS24Q.id == record_id).first()
        if not item:
            return None
        return {k: v for k, v in item.__dict__.items() if not k.startswith("_")}

    def update_tds24q(self, db: Session, record_id: int, data: Union[TDS24QUpdate, dict]) -> dict | None:
        item = db.query(TDS24Q).filter(TDS24Q.id == record_id).first()
        if not item:
            return None
        raw = data.model_dump() if hasattr(data, "model_dump") else (data if isinstance(data, dict) else data.dict())
        for k, v in raw.items():
            if v is None:
                continue
            snake = self._camel_to_snake(k)
            if hasattr(item, snake):
                setattr(item, snake, v)
        db.add(item)
        db.commit()
        db.refresh(item)
        return {k: v for k, v in item.__dict__.items() if not k.startswith("_")}

    def delete_tds24q(self, db: Session, record_id: int) -> bool:
        item = db.query(TDS24Q).filter(TDS24Q.id == record_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

tds24q_repository = _TDS24QRepository()