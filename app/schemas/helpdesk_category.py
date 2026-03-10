from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, Any

class CategoryBase(BaseModel):
    business_id: int
    name: str = Field(..., min_length=1, max_length=255)
    primary_approver: Optional[str] = Field(None, max_length=255)
    backup_approver: Optional[str] = Field(None, max_length=255)
    is_active: bool = False
    
    @model_validator(mode='before')
    @classmethod
    def trim_strings(cls, data: Any) -> Any:
        """Trim whitespace from string fields and validate"""
        if isinstance(data, dict):
            # Trim and validate name
            if 'name' in data and isinstance(data['name'], str):
                trimmed = data['name'].strip()
                if not trimmed:
                    raise ValueError('name cannot be empty or whitespace only')
                data['name'] = trimmed
            
            # Trim primary_approver (optional)
            if 'primary_approver' in data and data['primary_approver'] is not None and isinstance(data['primary_approver'], str):
                trimmed = data['primary_approver'].strip()
                data['primary_approver'] = trimmed if trimmed else None
            
            # Trim backup_approver (optional)
            if 'backup_approver' in data and data['backup_approver'] is not None and isinstance(data['backup_approver'], str):
                trimmed = data['backup_approver'].strip()
                data['backup_approver'] = trimmed if trimmed else None
        
        return data

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
