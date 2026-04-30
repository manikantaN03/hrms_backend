# app/services/setup/Integrations/sqlserver.py

from typing import Optional, List
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.setup.Integrations.sqlserver import (
    SqlServerSourceCreate,
    SqlServerSourceUpdate,
    SqlServerSourceOut,
    SqlServerSyncLogOut,
)
from app.repositories.setup.Integrations import sqlserver as repo
from app.models.setup.Integrations.sqlserver import SqlServerSource
from app.models.business import Business
import os

# Allow configuring the maximum number of SQL Server sources per tenant
# via environment variable `MAX_SQL_SOURCES_PER_TENANT`. Falls back to 3
# to match the frontend limit if not provided.
try:
    MAX_SQL_SOURCES_PER_TENANT = int(
        os.environ.get("MAX_SQL_SOURCES_PER_TENANT", "3")
    )
except (TypeError, ValueError):
    MAX_SQL_SOURCES_PER_TENANT = 3


# ---------- SOURCES ----------

def list_sources_service(
    db: Session,
    business_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> List[SqlServerSourceOut]:
    # Note: business_id is accepted for API compatibility but currently SQL Server sources
    # are filtered by tenant_id only. This can be extended in future if needed.
    sources = repo.list_sources(db, tenant_id=tenant_id)
    return [SqlServerSourceOut.model_validate(s) for s in sources]


def create_source_service(
    db: Session,
    payload,
    tenant_id: Optional[int] = None,
) -> SqlServerSourceOut:
    # Accept either a Pydantic model or a dict payload (handler injects business_id)
    if isinstance(payload, dict):
        p = payload
    else:
        # model
        try:
            p = payload.model_dump()
        except Exception:
            p = payload.dict()

    business_id = p.get("business_id")
    # ✅ Validate that the business exists before creating source
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} does not exist"
        )

    # enforce 3-source limit
    current_count = repo.count_sources(db, tenant_id=tenant_id)
    if current_count >= MAX_SQL_SOURCES_PER_TENANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_SQL_SOURCES_PER_TENANT} SQL Server sources allowed.",
        )

    src = repo.create_source(
        db,
        business_id=business_id,
        source_name=p.get("source_name"),
        server_address=p.get("server_address"),
        database_name=p.get("database_name"),
        database_username=p.get("database_username"),
        database_password=p.get("database_password"),
        table_name=p.get("table_name"),
        user_id_column=p.get("user_id_column"),
        time_column=p.get("time_column"),
        is_active=p.get("is_active"),
        tenant_id=tenant_id or p.get("tenant_id"),
    )

    return SqlServerSourceOut.model_validate(src)


def update_source_service(
    db: Session,
    source_id: int,
    payload: SqlServerSourceUpdate,
) -> SqlServerSourceOut:
    src = repo.get_source(db, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="SQL Server source not found")

    # ✅ Validate that the new business exists (if business_id is being updated)
    if payload.business_id is not None:
        business = db.query(Business).filter(Business.id == payload.business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business with ID {payload.business_id} does not exist"
            )

    src = repo.update_source(
        db,
        src,
        business_id=payload.business_id,
        source_name=payload.source_name,
        server_address=payload.server_address,
        database_name=payload.database_name,
        database_username=payload.database_username,
        database_password=payload.database_password,
        table_name=payload.table_name,
        user_id_column=payload.user_id_column,
        time_column=payload.time_column,
        is_active=payload.is_active,
    )

    return SqlServerSourceOut.model_validate(src)


def delete_source_service(db: Session, source_id: int) -> None:
    src = repo.get_source(db, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="SQL Server source not found")
    repo.delete_source(db, src)


# ---------- LOGS ----------

def list_logs_service(
    db: Session,
    source_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[SqlServerSyncLogOut]:
    src = repo.get_source(db, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="SQL Server source not found")

    logs = repo.list_logs_for_source(
        db, source_id=source_id, start_date=start_date, end_date=end_date
    )
    return [SqlServerSyncLogOut.model_validate(l) for l in logs]
