# app/models/biometricsync.py
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.models.base import Base  # ✅ same Base used in other models (like email_settings)


class BiometricDevice(Base):
    __tablename__ = "biometric_devices"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Link each device to a Business (multi-business support)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(Integer, nullable=True, index=True)

    # Device Name (front-end: deviceName)
    name = Column(String(200), nullable=False)

    # front-end: code
    device_code = Column(String(50), nullable=False, unique=True)

    host_url = Column(
        String(255),
        nullable=False,
        default="https://in2.runtimehrms.com",
    )

    # front-end: lastSeen
    last_seen = Column(DateTime, nullable=True)

    activated = Column(Boolean, default=False)

    # front-end: appVersion
    app_version = Column(String(50), nullable=False, default="1.0")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # 🔄 relation to Business (one Business → many BiometricDevice)
    business = relationship(
        "Business",
        back_populates="biometric_devices",
    )

    # 🔗 1 device → many logs  (for LogsModal)
    logs = relationship(
        "BiometricSyncLog",
        back_populates="device",
        cascade="all, delete-orphan",
    )


class BiometricSyncLog(Base):
    __tablename__ = "biometric_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer,
        ForeignKey("biometric_devices.id", ondelete="CASCADE"),
        nullable=False,
    )

    synced_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False)  # SUCCESS / FAILED
    message = Column(Text, nullable=True)

    device = relationship("BiometricDevice", back_populates="logs")
