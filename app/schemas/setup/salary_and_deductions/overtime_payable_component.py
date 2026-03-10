from pydantic import BaseModel
from typing import Optional


class OvertimePayableComponentCreate(BaseModel):
    business_id: int
    policy_id: int
    component_id: int
    is_payable: bool = True


class OvertimePayableComponentUpdate(BaseModel):
    is_payable: bool


class OvertimePayableComponentOut(BaseModel):
    id: int
    business_id: int
    policy_id: int
    component_id: int
    is_payable: bool

    class Config:
        from_attributes = True
