from typing import Optional
from pydantic import BaseModel, ConfigDict


class DesignationBase(BaseModel):
    name: str
    default: bool


class DesignationCreate(DesignationBase):
    business_id: int


class DesignationUpdate(BaseModel):
    name: Optional[str]
    default: Optional[bool]
    business_id: int


class DesignationOut(DesignationBase):
    id: int
    employees: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)
