from pydantic import BaseModel, Field, ConfigDict
import datetime
from typing import Optional, List


class HolidayBase(BaseModel):
    location_id: Optional[int] = None
    date: datetime.date
    name: str

    model_config = ConfigDict(populate_by_name=True)


class HolidayCreate(HolidayBase):
    business_id: Optional[int] = None


class HolidayUpdate(BaseModel):
    location_id: Optional[int] = None
    date: Optional[datetime.date] = None
    name: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class HolidayResponse(BaseModel):
    id: int
    business_id: int
    location_id: int
    date: datetime.date
    name: str
    day: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LocationCreate(BaseModel):
    name: str


class LocationResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LocationUpdate(BaseModel):
    name: Optional[str] = None


class CopyHolidaysRequest(BaseModel):
    from_location: str = Field(..., alias="fromLocation")
    to_location: str = Field(..., alias="toLocation")
    from_year: int = Field(..., alias="fromYear")
    to_year: int = Field(..., alias="toYear")

    model_config = ConfigDict(populate_by_name=True)


class PayableSettingResponse(BaseModel):
    is_payable: bool

    model_config = ConfigDict(from_attributes=True)


class SettingBase(BaseModel):
    key: str
    value: str


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: str


class SettingResponse(SettingBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
