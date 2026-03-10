from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional


class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Trim whitespace and validate name is not empty"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or whitespace only')
        return v
    
    @field_validator('description')
    @classmethod
    def trim_description(cls, v):
        """Trim whitespace from description"""
        if v is not None:
            v = v.strip()
        return v if v else None


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow. business_id is set by backend from auth context."""
    pass


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow. All fields are optional."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Trim whitespace and validate name is not empty"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or whitespace only')
        return v
    
    @field_validator('description')
    @classmethod
    def trim_description(cls, v):
        """Trim whitespace from description"""
        if v is not None:
            v = v.strip()
        return v if v else None


class WorkflowResponse(WorkflowBase):
    id: int
    business_id: int
    fields: int
    steps: int

    model_config = ConfigDict(from_attributes=True)
