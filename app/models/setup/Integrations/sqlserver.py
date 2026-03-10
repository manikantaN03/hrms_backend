# app/models/setup/Integrations/sqlserver.py
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base  # shared Base


class SqlServerSource(Base):
    __tablename__ = "sqlserver_sources"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Business relationship (each source belongs to one Business)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # (optional) tenant scope if you still use it
    tenant_id = Column(Integer, nullable=True, index=True)

    # Left side of the form (Server Configuration)
    source_name = Column(String(200), nullable=False)         # sourceName
    server_address = Column(String(255), nullable=False)      # serverAddress
    database_name = Column(String(200), nullable=False)       # databaseName
    database_username = Column(String(200), nullable=True)    # databaseUsername
    database_password = Column(Text, nullable=True)           # databasePassword (store encrypted in real apps)

    # Right side (Data Configuration)
    table_name = Column(String(200), nullable=False)          # tableName
    user_id_column = Column(String(200), nullable=False)      # userIdColumn
    time_column = Column(String(200), nullable=False)         # timeColumn

    is_active = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # 🔄 Relationship to Business (one Business → many SqlServerSource)
    business = relationship(
        "Business",
        back_populates="sqlserver_sources",
    )

    # 🔗 Relationship: one source → many sync logs
    logs = relationship(
        "SqlServerSyncLog",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class SqlServerSyncLog(Base):
    __tablename__ = "sqlserver_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(
        Integer,
        ForeignKey("sqlserver_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False)  # e.g. "SUCCESS" / "FAILED"
    message = Column(Text, nullable=True)

    source = relationship("SqlServerSource", back_populates="logs")
