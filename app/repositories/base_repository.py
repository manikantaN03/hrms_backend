"""
Base Repository
Generic CRUD operations for all models
"""

from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session

from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common database operations.
    
    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: Session):
                super().__init__(User, db)
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Primary key value
        
        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of model instances
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, data: dict) -> ModelType:
        """
        Create a new record.
        
        Args:
            data: Dictionary of field values
        
        Returns:
            Created model instance
        """
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def update(self, instance: ModelType, data: dict) -> ModelType:
        """
        Update an existing record.
        
        Args:
            instance: Model instance to update
            data: Dictionary of fields to update
        
        Returns:
            Updated model instance
        """
        for field, value in data.items():
            setattr(instance, field, value)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def delete(self, id: int) -> bool:
        """
        Delete a record.
        
        Args:
            id: Primary key value
        
        Returns:
            True if deleted, False if not found
        """
        instance = self.get(id)
        if instance:
            self.db.delete(instance)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """
        Count total records.
        
        Returns:
            Number of records in table
        """
        return self.db.query(self.model).count()