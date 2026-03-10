# app/models/setup/Integrations/gatekeeper.py
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.models.base import Base  # your shared Base


class GatekeeperDevice(Base):
    __tablename__ = "gatekeeper_devices"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Business relationship: each device belongs to one business
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # still keep tenant if you use it
    tenant_id = Column(Integer, nullable=True, index=True)

    # matches frontend: d.name
    name = Column(String(200), nullable=False)

    # matches frontend: d.deviceModel
    device_model = Column(String(100), nullable=True)

    # shown in UI as "Never" / something else
    last_seen = Column(DateTime, nullable=True)

    # shown in UI: appVersion ("Not Activated", etc.)
    app_version = Column(String(50), nullable=False, default="Not Activated")

    # the code displayed in "Show Code" modal
    device_code = Column(String(20), nullable=False, unique=True)

    # optional: if later you want activation toggle
    activated = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # 🔄 Relationship back to Business (one Business → many GatekeeperDevice)
    business = relationship(
        "Business",
        back_populates="gatekeeper_devices",
    )

    # no logs table for GateKeeper right now
