# app/api/v1/setup/Integrations/sqlserver.py

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.Integrations.sqlserver import (
    SqlServerSourceCreate,
    SqlServerSourceUpdate,
    SqlServerSourceOut,
    SqlServerSyncLogOut,
)
from app.services.setup.Integrations import sqlserver as svc

router = APIRouter(
    prefix="/integrations/sql-server",
)

# ---------- SOURCES ----------

@router.get(
    "/{business_id}",
    response_model=List[SqlServerSourceOut],
)
def list_sql_sources(
    business_id: int,
    tenant_id: Optional[int] = Query(default=None, alias="tenantId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List SQL Server sources for a given business (and optional tenant).
    """
    return svc.list_sources_service(
        db,
        business_id=business_id,
        tenant_id=tenant_id,
    )


@router.post(
    "",
    response_model=SqlServerSourceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_sql_source(
    payload: SqlServerSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new SQL Server source.
    """
    return svc.create_source_service(db, payload)


@router.put(
    "/{business_id}/{source_id}",
    response_model=SqlServerSourceOut,
)
def update_sql_source(
    business_id: int,
    source_id: int,
    payload: SqlServerSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an existing SQL Server source by ID.
    """
    return svc.update_source_service(db, source_id, payload)


@router.delete(
    "/{business_id}/{source_id}",
    status_code=status.HTTP_200_OK,
)
def delete_sql_source(
    business_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a SQL Server source by ID.
    """
    svc.delete_source_service(db, source_id)
    return {"message": "SQL Server source deleted"}


# ---------- LOGS ----------

@router.get(
    "/{business_id}/{source_id}/logs",
    response_model=List[SqlServerSyncLogOut],
)
def list_sql_source_logs(
    business_id: int,
    source_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List sync logs for a specific SQL Server source.
    """
    return svc.list_logs_service(db, source_id, start_date, end_date)
