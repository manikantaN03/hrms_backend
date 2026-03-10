from typing import Optional
from pydantic import BaseModel, ConfigDict


class WorkShiftBase(BaseModel):
    code: str
    name: str
    payable_hrs: str
    rules: int
    default: bool
    timing: Optional[str]
    start_buffer_hours: int
    end_buffer_hours: int


class WorkShiftCreate(WorkShiftBase):
    business_id: int


class WorkShiftUpdate(BaseModel):
    code: Optional[str]
    name: Optional[str]
    payable_hrs: Optional[str]
    rules: Optional[int]
    default: Optional[bool]
    timing: Optional[str]
    start_buffer_hours: Optional[int]
    end_buffer_hours: Optional[int]
    business_id: int


class WorkShiftOut(WorkShiftBase):
    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)
