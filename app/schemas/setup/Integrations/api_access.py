from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CamelModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class APIAccessBase(CamelModel):
    is_enabled: bool = Field(
        alias="apiEnabled",
        serialization_alias="apiEnabled",
        description="Whether API access is enabled for this business"
    )
    api_key: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="apiKey",
        serialization_alias="apiKey",
        description="Generated API key for authentication"
    )
    business_id: int = Field(
        gt=0,
        alias="businessId",
        serialization_alias="businessId",
        description="Business ID this API access belongs to"
    )


class APIAccessCreate(CamelModel):
    api_enabled: bool = Field(
        alias="apiEnabled",
        description="Whether to enable API access"
    )
    business_id: int = Field(
        gt=0,
        alias="businessId",
        description="Business ID to create API access for"
    )
    
    @field_validator('business_id')
    @classmethod
    def validate_business_id(cls, v: int) -> int:
        """Validate business_id is positive"""
        if v <= 0:
            raise ValueError("business_id must be a positive integer")
        return v


class APIAccessUpdate(CamelModel):
    api_enabled: Optional[bool] = Field(
        default=None,
        alias="apiEnabled",
        description="Whether to enable/disable API access"
    )
    api_key: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="apiKey",
        description="Custom API key (optional, auto-generated if not provided)"
    )
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key format if provided"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) < 10:
                raise ValueError("API key must be at least 10 characters long")
        return v


class APIAccessResponse(CamelModel):
    id: int = Field(description="Unique identifier for API access configuration")
    is_enabled: bool = Field(
        alias="apiEnabled",
        serialization_alias="apiEnabled",
        description="Whether API access is enabled"
    )
    api_key: Optional[str] = Field(
        default=None,
        alias="apiKey",
        serialization_alias="apiKey",
        description="API key for authentication"
    )
    business_id: int = Field(
        alias="businessId",
        serialization_alias="businessId",
        description="Business ID this configuration belongs to"
    )
