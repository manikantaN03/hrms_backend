"""
Week Off Policy Schemas
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Any
from datetime import datetime


class WeekOffPolicyBase(BaseModel):
    business_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: bool = False
    general_week_offs: List[str] = Field(default_factory=list)
    alternating_week_offs: List[List[str]] = Field(default_factory=list)
    weekoffs_payable: bool = False
    
    @model_validator(mode='before')
    @classmethod
    def trim_strings(cls, data: Any) -> Any:
        """Trim whitespace from string fields and validate"""
        if isinstance(data, dict):
            # Trim and validate title
            if 'title' in data and isinstance(data['title'], str):
                trimmed = data['title'].strip()
                if not trimmed:
                    raise ValueError('title cannot be empty or whitespace only')
                data['title'] = trimmed
            
            # Trim description (optional)
            if 'description' in data and isinstance(data['description'], str):
                trimmed = data['description'].strip()
                data['description'] = trimmed if trimmed else None
        
        return data


class WeekOffPolicyCreate(WeekOffPolicyBase):
    pass


class WeekOffPolicyUpdate(BaseModel):
    business_id: int
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    general_week_offs: Optional[List[str]] = None
    alternating_week_offs: Optional[List[List[str]]] = None
    weekoffs_payable: Optional[bool] = None
    
    @model_validator(mode='before')
    @classmethod
    def trim_strings(cls, data: Any) -> Any:
        """Trim whitespace from string fields and validate"""
        if isinstance(data, dict):
            # Trim and validate title (if provided)
            if 'title' in data and data['title'] is not None and isinstance(data['title'], str):
                trimmed = data['title'].strip()
                if not trimmed:
                    raise ValueError('title cannot be empty or whitespace only')
                data['title'] = trimmed
            
            # Trim description (optional, if provided)
            if 'description' in data and data['description'] is not None and isinstance(data['description'], str):
                trimmed = data['description'].strip()
                data['description'] = trimmed if trimmed else None
        
        return data


class WeekOffPolicyResponse(WeekOffPolicyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
