from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class ExitReasonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Exit reason name")
    esi_mapping: Optional[str] = Field(default=None, max_length=255, description="ESI mapping category")


class ExitReasonCreate(ExitReasonBase):
    pass


class ExitReasonUpdate(ExitReasonBase):
    pass


class ExitReasonResponse(ExitReasonBase):
    id: int
    business_id: int
    esi_mapping: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

