# app/repositories/sqlserver.py
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy.orm import Session

from app.models.setup.Integrations.sqlserver import (
    SqlServerSource,
    SqlServerSyncLog,
)


# ---------- SOURCES ----------

def list_sources(db: Session, business_id: Optional[int] = None, tenant_id: Optional[int] = None) -> List[SqlServerSource]:
    q = db.query(SqlServerSource)
    if business_id is not None:
        q = q.filter(SqlServerSource.business_id == business_id)
    if tenant_id is not None:
        q = q.filter(SqlServerSource.tenant_id == tenant_id)
    return q.order_by(SqlServerSource.created_at.desc()).all()


def count_sources(db: Session, tenant_id: Optional[int] = None) -> int:
    q = db.query(SqlServerSource)
    if tenant_id is not None:
        q = q.filter(SqlServerSource.tenant_id == tenant_id)
    return q.count()


def get_source(db: Session, source_id: int) -> Optional[SqlServerSource]:
    return db.get(SqlServerSource, source_id)


def create_source(
    db: Session,
    *,
    business_id: int,
    source_name: str,
    server_address: str,
    database_name: str,
    database_username: Optional[str],
    database_password: Optional[str],
    table_name: str,
    user_id_column: str,
    time_column: str,
    is_active: bool,
    tenant_id: Optional[int],
) -> SqlServerSource:
    src = SqlServerSource(
        business_id=business_id,
        source_name=source_name,
        server_address=server_address,
        database_name=database_name,
        database_username=database_username,
        database_password=database_password,
        table_name=table_name,
        user_id_column=user_id_column,
        time_column=time_column,
        is_active=is_active,
        tenant_id=tenant_id,
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


def update_source(
    db: Session,
    src: SqlServerSource,
    *,
    business_id: Optional[int] = None,
    source_name: Optional[str] = None,
    server_address: Optional[str] = None,
    database_name: Optional[str] = None,
    database_username: Optional[str] = None,
    database_password: Optional[str] = None,
    table_name: Optional[str] = None,
    user_id_column: Optional[str] = None,
    time_column: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> SqlServerSource:
    if business_id is not None:
        src.business_id = business_id
    if source_name is not None:
        src.source_name = source_name
    if server_address is not None:
        src.server_address = server_address
    if database_name is not None:
        src.database_name = database_name
    if database_username is not None:
        src.database_username = database_username
    if database_password is not None:
        src.database_password = database_password
    if table_name is not None:
        src.table_name = table_name
    if user_id_column is not None:
        src.user_id_column = user_id_column
    if time_column is not None:
        src.time_column = time_column
    if is_active is not None:
        src.is_active = is_active

    db.commit()
    db.refresh(src)
    return src


def delete_source(db: Session, src: SqlServerSource) -> None:
    db.delete(src)
    db.commit()


# ---------- LOGS ----------

def list_logs_for_source(
    db: Session,
    source_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[SqlServerSyncLog]:
    q = db.query(SqlServerSyncLog).filter(SqlServerSyncLog.source_id == source_id)

    if start_date:
        q = q.filter(
            SqlServerSyncLog.synced_at >= datetime.combine(
                start_date, datetime.min.time()
            )
        )
    if end_date:
        q = q.filter(
            SqlServerSyncLog.synced_at <= datetime.combine(
                end_date, datetime.max.time()
            )
        )

    return q.order_by(SqlServerSyncLog.synced_at.desc()).all()


def create_sync_log(
    db: Session,
    *,
    source_id: int,
    status: str,
    message: Optional[str],
) -> SqlServerSyncLog:
    log = SqlServerSyncLog(
        source_id=source_id,
        status=status,
        message=message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
