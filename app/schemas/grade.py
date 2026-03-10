from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GradeBase(BaseModel):
    name: str
    employees: int


class GradeCreate(BaseModel):
    name: str
    business_id: int


class GradeUpdate(BaseModel):
    name: Optional[str]
    business_id: int


class GradeOut(GradeBase):
    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)
