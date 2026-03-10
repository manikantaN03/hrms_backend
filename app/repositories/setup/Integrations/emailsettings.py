# app/repositories/setup/integrations/emailsettings.py

from typing import Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.setup.Integrations.emailsettings import (
    EmailMailbox,
    EmailSmtpConfig,
    EmailOAuthConfig,
    EmailTestLog,
    EmailProvider,
    EmailOAuthProvider,
)
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data


# =====================================================
# MAILBOX
# =====================================================

def get_mailbox(db: Session, mailbox_id: int) -> Optional[EmailMailbox]:
    return db.get(EmailMailbox, mailbox_id)


def get_mailbox_by_email(db: Session, email: str) -> Optional[EmailMailbox]:
    return (
        db.query(EmailMailbox)
        .filter(EmailMailbox.email_address == email)
        .first()
    )


def create_mailbox(
    db: Session,
    *,
    display_name: str,
    email_address: str,
    business_id: int,
    tenant_id: Optional[int] = None,
) -> EmailMailbox:
    """
    Create mailbox (initially ACTIVE to match frontend behavior).
    """
    mailbox = EmailMailbox(
        display_name=display_name,
        email_address=email_address,
        business_id=business_id,
        tenant_id=tenant_id,
        is_active=True,
    )
    db.add(mailbox)
    db.commit()
    db.refresh(mailbox)
    return mailbox


def delete_mailbox(db: Session, mailbox: EmailMailbox) -> None:
    db.delete(mailbox)
    db.commit()


def toggle_mailbox_active(db: Session, mailbox: EmailMailbox) -> EmailMailbox:
    mailbox.is_active = not mailbox.is_active
    db.commit()
    db.refresh(mailbox)
    return mailbox


# =====================================================
# SMTP CONFIG
# =====================================================

def get_smtp_by_mailbox(
    db: Session,
    mailbox_id: int,
) -> Optional[EmailSmtpConfig]:
    return (
        db.query(EmailSmtpConfig)
        .filter(EmailSmtpConfig.mailbox_id == mailbox_id)
        .first()
    )


def upsert_smtp_config(
    db: Session,
    *,
    mailbox_id: int,
    username: str,
    password: str,
    server: str,
    port: int,
    use_ssl: bool,
) -> EmailSmtpConfig:
    """
    Create or update SMTP config (1:1 with mailbox).
    """
    smtp = get_smtp_by_mailbox(db, mailbox_id)

    # Encrypt the password
    encrypted_password = encrypt_sensitive_data(password)

    if smtp:
        smtp.username = username
        smtp.encrypted_password = encrypted_password
        smtp.server = server
        smtp.port = port
        smtp.use_ssl = use_ssl
    else:
        smtp = EmailSmtpConfig(
            mailbox_id=mailbox_id,
            username=username,
            encrypted_password=encrypted_password,
            server=server,
            port=port,
            use_ssl=use_ssl,
        )
        db.add(smtp)

    db.commit()
    db.refresh(smtp)
    return smtp


def get_smtp_password(smtp_config: EmailSmtpConfig) -> str:
    """
    Decrypt and return the SMTP password.
    """
    return decrypt_sensitive_data(smtp_config.encrypted_password)


def delete_smtp_by_mailbox(db: Session, mailbox_id: int) -> None:
    db.query(EmailSmtpConfig).filter(
        EmailSmtpConfig.mailbox_id == mailbox_id
    ).delete(synchronize_session=False)
    db.commit()


# =====================================================
# OAUTH CONFIG (GMAIL / MICROSOFT)
# =====================================================

def delete_oauth_by_mailbox(db: Session, mailbox_id: int) -> None:
    """
    Delete ALL OAuth configs for a mailbox.
    """
    db.query(EmailOAuthConfig).filter(
        EmailOAuthConfig.mailbox_id == mailbox_id
    ).delete(synchronize_session=False)
    db.commit()


def get_oauth_by_mailbox_and_provider(
    db: Session,
    mailbox_id: int,
    provider: Union[EmailOAuthProvider, str],
) -> Optional[EmailOAuthConfig]:
    if isinstance(provider, str):
        provider = EmailOAuthProvider(provider.upper())

    return (
        db.query(EmailOAuthConfig)
        .filter(
            EmailOAuthConfig.mailbox_id == mailbox_id,
            EmailOAuthConfig.provider == provider,
        )
        .first()
    )


def create_oauth_config(
    db: Session,
    *,
    mailbox_id: int,
    provider: Union[EmailOAuthProvider, str],
) -> EmailOAuthConfig:
    """
    Safe upsert for OAuth config (avoids UNIQUE constraint violation).
    """
    if isinstance(provider, str):
        provider = EmailOAuthProvider(provider.upper())

    oauth = get_oauth_by_mailbox_and_provider(db, mailbox_id, provider)

    if oauth:
        oauth.is_configured = True
    else:
        oauth = EmailOAuthConfig(
            mailbox_id=mailbox_id,
            provider=provider,
            is_configured=True,
        )
        db.add(oauth)

    db.commit()
    db.refresh(oauth)
    return oauth


def upsert_oauth_tokens(
    db: Session,
    *,
    mailbox_id: int,
    provider: Union[EmailOAuthProvider, str],
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> EmailOAuthConfig:
    """
    Upsert OAuth tokens after callback.
    """
    if isinstance(provider, str):
        provider = EmailOAuthProvider(provider.upper())

    oauth = get_oauth_by_mailbox_and_provider(db, mailbox_id, provider)

    if not oauth:
        oauth = EmailOAuthConfig(
            mailbox_id=mailbox_id,
            provider=provider,
            is_configured=True,
        )
        db.add(oauth)

    if access_token is not None:
        oauth.access_token = access_token
    if refresh_token is not None:
        oauth.refresh_token = refresh_token
    if expires_at is not None:
        oauth.token_expires_at = expires_at

    oauth.is_configured = True
    db.commit()
    db.refresh(oauth)
    return oauth


# =====================================================
# TEST MAIL LOG
# =====================================================

def create_test_log(
    db: Session,
    *,
    mailbox_id: int,
    provider: Union[EmailProvider, str],
    status: str,
    message: str,
) -> EmailTestLog:
    """
    Store test mail results.
    status: SUCCESS | FAILED
    """
    if isinstance(provider, str):
        provider = EmailProvider(provider.upper())

    log = EmailTestLog(
        mailbox_id=mailbox_id,
        provider=provider.value,  # stored as string (model uses String)
        status=status,
        message=message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
