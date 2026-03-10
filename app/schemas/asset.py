"""
Asset Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
from decimal import Decimal
from enum import Enum


class AssetTypeEnum(str, Enum):
    LAPTOP = "laptop"
    DESKTOP = "desktop"
    MONITOR = "monitor"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    MOBILE = "mobile"
    TABLET = "tablet"
    PRINTER = "printer"
    HEADSET = "headset"
    WEBCAM = "webcam"
    CHAIR = "chair"
    DESK = "desk"
    OTHER = "other"


class AssetConditionEnum(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class AssetStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"
    MAINTENANCE = "maintenance"
    LOST = "lost"
    DAMAGED = "damaged"


class AssetCreateRequest(BaseModel):
    asset_type: AssetTypeEnum = Field(..., description="Type of asset")
    name: str = Field(..., min_length=1, max_length=200, description="Asset name")
    brand: Optional[str] = Field(None, max_length=100, description="Asset brand")
    model: Optional[str] = Field(None, max_length=100, description="Asset model")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    estimated_value: Optional[Decimal] = Field(0, ge=0, description="Estimated value")
    assigned_date: date = Field(..., description="Date when asset was assigned")
    warranty_end_date: Optional[date] = Field(None, description="Warranty end date")
    description: Optional[str] = Field(None, max_length=500, description="Asset description")
    condition: AssetConditionEnum = Field(AssetConditionEnum.GOOD, description="Asset condition")

    @validator('warranty_end_date')
    def validate_warranty_date(cls, v, values):
        if v and 'assigned_date' in values and v < values['assigned_date']:
            raise ValueError('Warranty end date cannot be before assigned date')
        return v

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Asset name cannot be empty')
        return v.strip()

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0
        }


class AssetUpdateRequest(BaseModel):
    asset_type: AssetTypeEnum = Field(..., description="Type of asset")
    name: str = Field(..., min_length=1, max_length=200, description="Asset name")
    brand: Optional[str] = Field(None, max_length=100, description="Asset brand")
    model: Optional[str] = Field(None, max_length=100, description="Asset model")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    estimated_value: Optional[Decimal] = Field(0, ge=0, description="Estimated value")
    assigned_date: date = Field(..., description="Date when asset was assigned")
    warranty_end_date: Optional[date] = Field(None, description="Warranty end date")
    description: Optional[str] = Field(None, max_length=500, description="Asset description")
    condition: AssetConditionEnum = Field(AssetConditionEnum.GOOD, description="Asset condition")

    @validator('warranty_end_date')
    def validate_warranty_date(cls, v, values):
        if v and 'assigned_date' in values and v < values['assigned_date']:
            raise ValueError('Warranty end date cannot be before assigned date')
        return v

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Asset name cannot be empty')
        return v.strip()

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0
        }


class AssetResponse(BaseModel):
    id: int
    asset_code: str
    name: str
    type: str
    brand: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    estimated_value: float
    assigned_date: Optional[str]
    warranty_end_date: Optional[str]
    condition: str
    status: str
    description: Optional[str]
    warranty_status: Optional[str]

    class Config:
        from_attributes = True


class AssetTypeOption(BaseModel):
    value: str
    label: str


class EmployeeAssetsResponse(BaseModel):
    id: int
    name: str
    code: str
    assets: List[AssetResponse]
    total_assets: int
    asset_types: List[AssetTypeOption]

    class Config:
        from_attributes = True


class AssetCreateResponse(BaseModel):
    success: bool
    message: str
    asset: AssetResponse

    class Config:
        from_attributes = True


class AssetUpdateResponse(BaseModel):
    success: bool
    message: str
    asset: AssetResponse

    class Config:
        from_attributes = True


class AssetDeleteResponse(BaseModel):
    success: bool
    message: str

    class Config:
        from_attributes = True