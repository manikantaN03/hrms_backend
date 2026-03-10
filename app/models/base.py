"""
Base Model
Common fields and methods for all database models
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, text
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields.
    
    Provides:
    - Auto-incrementing ID
    - Creation and update timestamps
    - Audit trail (created_by, updated_by)
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=datetime.utcnow
    )
    
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }