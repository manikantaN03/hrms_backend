# app/schemas/business_unit.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class BusinessUnitBase(BaseModel):
    business_id: int
    
    name: str = Field(
        ..., min_length=2, max_length=255, description="Name of Unit"
    )
    report_title: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Title to be shown on reports",
    )
    is_default: bool = Field(
        default=False,
        description="Mark this business unit as default for the business",
    )


class BusinessUnitCreate(BusinessUnitBase):
    """Schema used when creating a new business unit."""
    pass


class BusinessUnitUpdate(BaseModel):
    """Schema used when updating an existing business unit."""
    business_id: int

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    report_title: Optional[str] = Field(None, min_length=2, max_length=255)
    is_default: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class BusinessUnitResponse(BusinessUnitBase):
    """Response schema for a business unit."""

    id: int
    is_active: bool
    header_image_url: Optional[str] = None
    footer_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
