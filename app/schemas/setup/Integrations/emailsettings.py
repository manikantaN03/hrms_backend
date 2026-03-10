# app/schemas/setup/Integrations/emailsettings.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer, field_validator
from app.models.setup.Integrations.emailsettings import EmailProvider


# =========================================================
# BASE CAMEL CASE MODEL
# =========================================================

class CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        },
    )


# =========================================================
# MAILBOX
# =========================================================

class EmailMailboxCreate(CamelModel):
    display_name: str = Field(..., alias="displayName", min_length=1, max_length=255, description="Display name for the mailbox")
    email_address: EmailStr = Field(..., alias="emailAddress", description="Email address for the mailbox")
    tenant_id: Optional[int] = Field(default=None, alias="tenantId", gt=0, description="Tenant ID (optional)")
    business_id: int = Field(..., alias="businessId", gt=0, description="Business ID")

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Display name cannot be empty or whitespace")
        return v.strip()


class EmailMailboxOut(CamelModel):
    id: int
    display_name: str = Field(alias="displayName")
    email_address: EmailStr = Field(alias="emailAddress")
    is_active: bool = Field(alias="isActive")

    # SMTP | GMAIL | MICROSOFT
    selected_provider: Optional[str] = Field(
        default=None, alias="selectedIntegration"
    )

    tenant_id: Optional[int] = Field(default=None, alias="tenantId")
    business_id: int = Field(alias="businessId")

    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    @field_serializer('selected_provider')
    def serialize_provider(self, value: Optional[EmailProvider], _info):
        """Convert enum to string value"""
        if value is None:
            return None
        if isinstance(value, EmailProvider):
            return value.value
        return value


# =========================================================
# SMTP CONFIG
# =========================================================

class EmailSmtpConfigCreateOrUpdate(CamelModel):
    username: str = Field(..., alias="smtpUsername", min_length=1, max_length=255, description="SMTP username")
    password: str = Field(..., alias="smtpPassword", min_length=1, max_length=255, description="SMTP password")
    server: str = Field(..., alias="smtpServer", min_length=1, max_length=255, description="SMTP server address")
    port: int = Field(..., alias="smtpPort", ge=1, le=65535, description="SMTP port number")
    use_ssl: bool = Field(..., alias="useSSL", description="Use SSL/TLS for SMTP connection")

    @field_validator('username', 'password', 'server')
    @classmethod
    def validate_not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace")
        return v.strip()


class EmailSmtpConfigOut(CamelModel):
    id: int
    mailbox_id: int = Field(alias="mailboxId")

    username: str = Field(alias="smtpUsername")
    server: str = Field(alias="smtpServer")
    port: int = Field(alias="smtpPort")
    use_ssl: bool = Field(alias="useSSL")

    # 🔐 Always masked (never expose real password)
    smtp_password: str = Field(default="********", alias="smtpPassword")

    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")


# =========================================================
# OAUTH CONFIG (READ ONLY)
# =========================================================

class EmailOAuthConfigOut(CamelModel):
    id: int
    mailbox_id: int = Field(alias="mailboxId")

    # "GMAIL" | "MICROSOFT"
    provider: str

    is_configured: bool = Field(alias="configured")

    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")


# =========================================================
# TEST MAIL
# =========================================================

class EmailTestRequest(CamelModel):
    provider: EmailProvider = Field(alias="type")
    to_email: Optional[EmailStr] = Field(default=None, alias="toEmail")


class EmailTestResponse(CamelModel):
    message: str
    mailbox_active: bool = Field(alias="mailboxActive")


# =========================================================
# OAUTH CALLBACK
# =========================================================

class EmailOAuthCallbackRequest(CamelModel):
    code: str


# =========================================================
# FULL SETTINGS RESPONSE (PAGE LOAD)
# =========================================================

class EmailSettingsOut(CamelModel):
    mailbox: Optional[EmailMailboxOut] = None
    smtp: Optional[EmailSmtpConfigOut] = None

    gmail_configured: bool = Field(alias="gmailConfigured", default=False)
    microsoft_configured: bool = Field(alias="microsoftConfigured", default=False)
