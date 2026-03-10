"""
Visit Type Schemas
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any
from datetime import datetime


class VisitTypeBase(BaseModel):
    business_id: int
    name: str = Field(..., min_length=1, max_length=255)
    
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
        
        return data


class VisitTypeCreate(VisitTypeBase):
    pass


class VisitTypeUpdate(BaseModel):
    business_id: int
    name: str = Field(..., min_length=1, max_length=255)
    
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
        
        return data


class VisitTypeResponse(VisitTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
