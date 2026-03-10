# app/models/email_settings.py
from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class EmailProvider(str, enum.Enum):
    SMTP = "SMTP"
    GMAIL = "GMAIL"
    MICROSOFT = "MICROSOFT"


class EmailOAuthProvider(str, enum.Enum):
    GMAIL = "GMAIL"
    MICROSOFT = "MICROSOFT"


class EmailMailbox(Base):
    __tablename__ = "email_mailboxes"
    __table_args__ = (
        UniqueConstraint("business_id", "email_address", name="uq_business_email"),
        Index("ix_email_mailbox_business", "business_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )

    tenant_id = Column(Integer, nullable=True, index=True)

    display_name = Column(String(200), nullable=False)
    email_address = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=False)

    selected_provider = Column(
        SAEnum(
            EmailProvider,
            name="email_mailbox_provider_enum",
        ),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    business = relationship("Business", back_populates="email_mailboxes")

    smtp_config = relationship(
        "EmailSmtpConfig",
        back_populates="mailbox",
        uselist=False,
        cascade="all, delete-orphan",
    )

    oauth_configs = relationship(
        "EmailOAuthConfig",
        back_populates="mailbox",
        cascade="all, delete-orphan",
    )

    test_logs = relationship(
        "EmailTestLog",
        back_populates="mailbox",
        cascade="all, delete-orphan",
    )


class EmailSmtpConfig(Base):
    __tablename__ = "email_smtp_configs"

    id = Column(Integer, primary_key=True, index=True)
    mailbox_id = Column(
        Integer,
        ForeignKey("email_mailboxes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    username = Column(String(255), nullable=False)
    encrypted_password = Column(String(512), nullable=False)
    server = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    use_ssl = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    mailbox = relationship("EmailMailbox", back_populates="smtp_config")


class EmailOAuthConfig(Base):
    __tablename__ = "email_oauth_configs"
    __table_args__ = (
        UniqueConstraint("mailbox_id", "provider", name="uq_mailbox_oauth_provider"),
        Index("ix_oauth_mailbox_provider", "mailbox_id", "provider"),
    )

    id = Column(Integer, primary_key=True, index=True)

    mailbox_id = Column(
        Integer,
        ForeignKey("email_mailboxes.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider = Column(
        SAEnum(
            EmailOAuthProvider,
            name="email_oauth_provider_enum",
        ),
        nullable=False,
    )

    is_configured = Column(Boolean, default=False)

    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    mailbox = relationship("EmailMailbox", back_populates="oauth_configs")


class EmailTestLog(Base):
    __tablename__ = "email_test_logs"
    __table_args__ = (
        Index("ix_testlog_mailbox_provider", "mailbox_id", "provider"),
    )

    id = Column(Integer, primary_key=True, index=True)

    mailbox_id = Column(
        Integer,
        ForeignKey("email_mailboxes.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider = Column(
        SAEnum(
            EmailProvider,
            name="email_test_provider_enum",
        ),
        nullable=False,
    )

    requested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False)  # SUCCESS / FAILED
    message = Column(Text, nullable=True)

    mailbox = relationship("EmailMailbox", back_populates="test_logs")
