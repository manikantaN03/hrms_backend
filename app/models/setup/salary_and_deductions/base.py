from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy import Column, DateTime


class Base(DeclarativeBase):
    metadata = MetaData(schema=None)  # if you want a specific schema, set here

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore
        return cls.__name__.lower()

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
