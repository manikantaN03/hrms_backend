from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class ExitReasonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Exit reason name")
    esi_mapping: Optional[str] = Field(default=None, max_length=255, description="ESI mapping category")


class ExitReasonCreate(ExitReasonBase):
    business_id: int = Field(..., gt=0, description="Business ID")


class ExitReasonUpdate(ExitReasonBase):
    business_id: int = Field(..., gt=0, description="Business ID")


class ExitReasonResponse(ExitReasonBase):
    id: int
    business_id: int
    esi_mapping: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

