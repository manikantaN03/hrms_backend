# app/schemas/sqlserver.py
from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, field_validator


class CamelModel(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True


# ---------- CREATE / UPDATE ----------

class SqlServerSourceCreate(CamelModel):
    """Schema for creating a new SQL Server source"""
    source_name: str = Field(
        alias="sourceName",
        min_length=1,
        max_length=200,
        description="Source name (e.g., 'Main Office Attendance')"
    )
    server_address: str = Field(
        alias="serverAddress",
        min_length=1,
        max_length=255,
        description="Server address (IP or hostname)"
    )
    database_name: str = Field(
        alias="databaseName",
        min_length=1,
        max_length=200,
        description="Database name"
    )
    database_username: Optional[str] = Field(
        alias="databaseUsername",
        default=None,
        max_length=200,
        description="Database username (optional)"
    )
    database_password: Optional[str] = Field(
        alias="databasePassword",
        default=None,
        description="Database password (optional, will be encrypted)"
    )
    table_name: str = Field(
        alias="tableName",
        min_length=1,
        max_length=200,
        description="Table name (supports dynamic keys: %M, %MM, %YY, %YYYY)"
    )
    user_id_column: str = Field(
        alias="userIdColumn",
        min_length=1,
        max_length=200,
        description="User ID column name"
    )
    time_column: str = Field(
        alias="timeColumn",
        min_length=1,
        max_length=200,
        description="Time column name"
    )
    is_active: bool = Field(
        alias="isActive",
        default=False,
        description="Active status"
    )

    # 🔹 Business relationship (required)
    business_id: int = Field(
        alias="businessId",
        gt=0,
        description="Business ID to which this source belongs"
    )

    # 🔹 Optional tenant context
    tenant_id: Optional[int] = Field(
        default=None,
        alias="tenantId",
        gt=0,
        description="Optional tenant ID for multi-tenant setup"
    )
    
    @field_validator("source_name", "server_address", "database_name", "table_name", "user_id_column", "time_column")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate required fields are not empty or whitespace"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()
    
    @field_validator("database_username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username is not empty if provided"""
        if v is not None and v.strip():
            return v.strip()
        return None


class SqlServerSourceUpdate(CamelModel):
    """Schema for updating an existing SQL Server source"""
    source_name: Optional[str] = Field(
        alias="sourceName",
        default=None,
        min_length=1,
        max_length=200
    )
    server_address: Optional[str] = Field(
        alias="serverAddress",
        default=None,
        min_length=1,
        max_length=255
    )
    database_name: Optional[str] = Field(
        alias="databaseName",
        default=None,
        min_length=1,
        max_length=200
    )
    database_username: Optional[str] = Field(
        alias="databaseUsername",
        default=None,
        max_length=200
    )
    database_password: Optional[str] = Field(
        alias="databasePassword",
        default=None
    )
    table_name: Optional[str] = Field(
        alias="tableName",
        default=None,
        min_length=1,
        max_length=200
    )
    user_id_column: Optional[str] = Field(
        alias="userIdColumn",
        default=None,
        min_length=1,
        max_length=200
    )
    time_column: Optional[str] = Field(
        alias="timeColumn",
        default=None,
        min_length=1,
        max_length=200
    )
    is_active: Optional[bool] = Field(
        alias="isActive",
        default=None
    )

    # 🔹 Allow changing business/tenant if needed
    business_id: Optional[int] = Field(
        default=None,
        alias="businessId",
        gt=0
    )
    tenant_id: Optional[int] = Field(
        default=None,
        alias="tenantId",
        gt=0
    )
    
    @field_validator("source_name", "server_address", "database_name", "table_name", "user_id_column", "time_column")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate fields are not empty or whitespace if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip() if v else None


# ---------- OUT ----------

class SqlServerSourceOut(CamelModel):
    """Schema for SQL Server source output"""
    id: int = Field(description="Source ID")
    source_name: str = Field(
        serialization_alias="sourceName",
        description="Source name"
    )
    server_address: str = Field(
        serialization_alias="serverAddress",
        description="Server address"
    )
    database_name: str = Field(
        serialization_alias="databaseName",
        description="Database name"
    )
    database_username: Optional[str] = Field(
        default=None,
        serialization_alias="databaseUsername",
        description="Database username"
    )
    database_password: Optional[str] = Field(
        default=None,
        serialization_alias="databasePassword",
        description="Database password (encrypted)"
    )
    table_name: str = Field(
        serialization_alias="tableName",
        description="Table name"
    )
    user_id_column: str = Field(
        serialization_alias="userIdColumn",
        description="User ID column"
    )
    time_column: str = Field(
        serialization_alias="timeColumn",
        description="Time column"
    )
    is_active: bool = Field(
        serialization_alias="isActive",
        description="Active status"
    )

    # 🔹 Business + tenant info in response
    business_id: Optional[int] = Field(
        default=None,
        serialization_alias="businessId",
        description="Business ID"
    )
    tenant_id: Optional[int] = Field(
        default=None,
        serialization_alias="tenantId",
        description="Tenant ID"
    )

    created_at: datetime = Field(
        serialization_alias="createdAt",
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        serialization_alias="updatedAt",
        description="Last update timestamp"
    )


class SqlServerSyncLogOut(CamelModel):
    """Schema for SQL Server sync log output"""
    id: int = Field(description="Log ID")
    source_id: int = Field(
        serialization_alias="sourceId",
        description="Source ID"
    )
    synced_at: datetime = Field(
        serialization_alias="syncedAt",
        description="Sync timestamp"
    )
    status: Literal["SUCCESS", "FAILED", "WARNING", "PARTIAL"] = Field(
        description="Sync status"
    )
    message: Optional[str] = Field(
        default=None,
        description="Sync message or error details"
    )


class SqlServerSourceWithLogsOut(SqlServerSourceOut):
    """Schema for SQL Server source with logs"""
    logs: List[SqlServerSyncLogOut] = Field(
        default=[],
        description="List of sync logs"
    )
