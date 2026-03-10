from pydantic import BaseModel, ConfigDict
from typing import Optional


class LocationBase(BaseModel):
    business_id: int
    name: str
    state: str
    locationHead: Optional[str] = None   # ✅ RENAMED
    deputyHead: Optional[str] = None
    isDefault: bool = False
    mapUrl: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class GenerateQRRequest(BaseModel):
    business_id: int



class LocationUpdate(BaseModel):
    business_id: int
    name: Optional[str] = None
    state: Optional[str] = None
    locationHead: Optional[str] = None   #  RENAMED
    deputyHead: Optional[str] = None
    isDefault: Optional[bool] = None
    mapUrl: Optional[str] = None


class LocationResponse(LocationBase):
    id: int
    employees: int
    qrCodeUrl: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    
    model_config = ConfigDict(from_attributes=True)
