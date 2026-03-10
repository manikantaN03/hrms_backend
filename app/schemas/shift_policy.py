from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.work_shift import WorkShiftOut

class ShiftPolicyBase(BaseModel):
    business_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: bool = False
    default_shift_id: Optional[int] = None
    weekly_shifts: Dict[str, Optional[int]] = Field(
        default_factory=lambda: {
            "Monday": None,
            "Tuesday": None,
            "Wednesday": None,
            "Thursday": None,
            "Friday": None,
            "Saturday": None,
            "Sunday": None
        }
    )
    
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

class ShiftPolicyCreate(ShiftPolicyBase):
    pass

class ShiftPolicyUpdate(BaseModel):
    business_id: int
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    default_shift_id: Optional[int] = None
    weekly_shifts: Optional[Dict[str, Optional[int]]] = None
    
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

class ShiftPolicyResponse(ShiftPolicyBase):
    id: int
    default_shift: Optional[WorkShiftOut] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ShiftPolicyDetailResponse(BaseModel):
    id: int
    business_id: int
    title: str
    description: Optional[str] = None
    is_default: bool
    default_shift: Optional[WorkShiftOut] = None
    weekly_shifts_detail: Dict[str, Optional[WorkShiftOut]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
