from pydantic import BaseModel, ConfigDict
from typing import Optional


class DepartmentCreate(BaseModel):
    business_id: int
    name: str
    head: str
    deputyHead: Optional[str] = None
    isDefault: bool = False


class DepartmentUpdate(BaseModel):
    business_id: int

    name: Optional[str] = None
    head: Optional[str] = None
    deputyHead: Optional[str] = None
    employees: Optional[int] = None
    isDefault: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: int
    business_id: int
    name: str
    head: str
    deputy_head: Optional[str]
    is_default: bool
    employees: int

    model_config = ConfigDict(from_attributes=True)
