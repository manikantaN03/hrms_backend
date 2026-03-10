"""
Employee Additional Info Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional


class AdditionalInfoUpdateRequest(BaseModel):
    """Schema for updating employee additional information"""
    field1: Optional[str] = Field(None, max_length=500, description="Other Info 1")
    field2: Optional[str] = Field(None, max_length=500, description="Other Info 2")
    field3: Optional[str] = Field(None, max_length=500, description="Other Info 3")
    field4: Optional[str] = Field(None, max_length=500, description="Other Info 4")
    field5: Optional[str] = Field(None, max_length=500, description="Other Info 5")
    field6: Optional[str] = Field(None, max_length=500, description="Other Info 6")
    field7: Optional[str] = Field(None, max_length=500, description="Other Info 7")
    field8: Optional[str] = Field(None, max_length=500, description="Other Info 8")
    field9: Optional[str] = Field(None, max_length=500, description="Other Info 9")
    field10: Optional[str] = Field(None, max_length=500, description="Other Info 10")

    @validator('field1', 'field2', 'field3', 'field4', 'field5', 
               'field6', 'field7', 'field8', 'field9', 'field10', pre=True)
    def validate_field(cls, v):
        if v is not None:
            # Strip whitespace and convert empty strings to None
            v = v.strip() if isinstance(v, str) else v
            if v == "":
                return None
        return v


class AdditionalInfoResponse(BaseModel):
    """Schema for additional info response"""
    field1: str = ""
    field2: str = ""
    field3: str = ""
    field4: str = ""
    field5: str = ""
    field6: str = ""
    field7: str = ""
    field8: str = ""
    field9: str = ""
    field10: str = ""


class EmployeeAdditionalInfoResponse(BaseModel):
    """Schema for employee additional info response"""
    id: int
    name: str
    code: str
    additional_info: AdditionalInfoResponse
    field_labels: dict


class AdditionalInfoSaveResponse(BaseModel):
    """Schema for save response"""
    success: bool
    message: str
    employee: dict
    additional_info: AdditionalInfoResponse