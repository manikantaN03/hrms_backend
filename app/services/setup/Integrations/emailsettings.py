# app/services/setup/Integrations/emailsettings.py

import smtplib
import os

from email.message import EmailMessage
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.setup.Integrations.emailsettings import (
    EmailMailbox,
    EmailProvider,
    EmailOAuthProvider,
)
from app.repositories.setup.Integrations import emailsettings as repo
from app.schemas.setup.Integrations.emailsettings import (
    EmailMailboxCreate,
    EmailSmtpConfigCreateOrUpdate,
    EmailTestRequest,
    EmailSettingsOut,
)

# =========================================================
# LIST MAILBOXES
# =========================================================

def list_mailboxes_service(
    db: Session,
    business_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
):
    query = db.query(EmailMailbox)
    if business_id is not None:
        query = query.filter(EmailMailbox.business_id == business_id)
    if tenant_id is not None:
        query = query.filter(EmailMailbox.tenant_id == tenant_id)
    return query.all()


# =========================================================
# MAILBOX CRUD
# =========================================================

def create_mailbox_service(db: Session, payload: EmailMailboxCreate) -> EmailMailbox:
    if repo.get_mailbox_by_email(db, payload.email_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mailbox already exists for this email",
        )

    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return repo.create_mailbox(
        db,
        display_name=payload.display_name,
        email_address=payload.email_address,
        business_id=payload.business_id,
        tenant_id=payload.tenant_id,
    )


def delete_mailbox_service(db: Session, mailbox_id: int):
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    repo.delete_mailbox(db, mailbox)


def toggle_mailbox_active_service(db: Session, mailbox_id: int):
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    return repo.toggle_mailbox_active(db, mailbox)


def get_mailbox_service(db: Session, mailbox_id: int):
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    return mailbox


# =========================================================
# SMTP CONFIG SAVE
# =========================================================

def save_smtp_service(
    db: Session,
    mailbox_id: int,
    payload: EmailSmtpConfigCreateOrUpdate,
):
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    # Clear OAuth when SMTP is saved
    repo.delete_oauth_by_mailbox(db, mailbox_id)

    smtp = repo.upsert_smtp_config(
        db,
        mailbox_id=mailbox_id,
        username=payload.username,
        password=payload.password,
        server=payload.server,
        port=payload.port,
        use_ssl=payload.use_ssl,
    )

    mailbox.is_active = True
    mailbox.selected_provider = EmailProvider.SMTP
    db.commit()
    db.refresh(mailbox)

    return smtp


# =========================================================
# REAL SMTP SEND
# =========================================================

def _send_test_mail_via_smtp(
    mailbox: EmailMailbox,
    smtp_config,
    to_email: str,
):
    msg = EmailMessage()
    msg["Subject"] = "Test email from HRMS"
    msg["From"] = smtp_config.username
    msg["To"] = to_email
    msg.set_content("This is a test email from HRMS Email Settings.")

    # Decrypt password for use
    password = repo.get_smtp_password(smtp_config)

    try:
        if smtp_config.use_ssl:
            with smtplib.SMTP_SSL(
                smtp_config.server,
                smtp_config.port,
                timeout=20,
            ) as server:
                server.login(smtp_config.username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(
                smtp_config.server,
                smtp_config.port,
                timeout=20,
            ) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_config.username, password)
                server.send_message(msg)

        return True, "Test mail sent successfully via SMTP"

    except Exception as exc:
        return False, f"SMTP send failed: {exc}"


# =========================================================
# SEND TEST MAIL
# =========================================================

def send_test_mail_service(
    db: Session,
    mailbox_id: int,
    payload: EmailTestRequest,
):
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    provider_type = payload.provider.value.upper()

    # Handle SMTP test mail
    if provider_type == "SMTP":
        smtp_config = repo.get_smtp_by_mailbox(db, mailbox_id)
        if not smtp_config:
            raise HTTPException(
                status_code=400,
                detail="SMTP is not configured for this mailbox",
            )

        success, message = _send_test_mail_via_smtp(
            mailbox,
            smtp_config,
            payload.to_email or mailbox.email_address,
        )

        repo.create_test_log(
            db,
            mailbox_id=mailbox.id,
            provider=EmailProvider.SMTP,
            status="SUCCESS" if success else "FAILED",
            message=message,
        )

        if not success:
            raise HTTPException(status_code=502, detail=message)

        mailbox.is_active = True
        mailbox.selected_provider = EmailProvider.SMTP
        db.commit()

        return {
            "message": message,
            "mailbox_active": mailbox.is_active,
        }

    # Handle Gmail OAuth test mail (stub)
    elif provider_type == "GMAIL":
        gmail_oauth = repo.get_oauth_by_mailbox_and_provider(
            db, mailbox_id, EmailOAuthProvider.GMAIL
        )
        if not gmail_oauth or not gmail_oauth.is_configured:
            raise HTTPException(
                status_code=400,
                detail="Gmail OAuth is not configured for this mailbox",
            )

        # In production, this would use Gmail API to send test email
        # For now, return stub success response
        message = "Gmail test mail feature is configured (stub mode - actual sending not implemented)"
        
        repo.create_test_log(
            db,
            mailbox_id=mailbox.id,
            provider=EmailProvider.GMAIL,
            status="SUCCESS",
            message=message,
        )

        mailbox.is_active = True
        mailbox.selected_provider = EmailProvider.GMAIL
        db.commit()

        return {
            "message": message,
            "mailbox_active": mailbox.is_active,
        }

    # Handle Microsoft OAuth test mail (stub)
    elif provider_type == "MICROSOFT":
        microsoft_oauth = repo.get_oauth_by_mailbox_and_provider(
            db, mailbox_id, EmailOAuthProvider.MICROSOFT
        )
        if not microsoft_oauth or not microsoft_oauth.is_configured:
            raise HTTPException(
                status_code=400,
                detail="Microsoft OAuth is not configured for this mailbox",
            )

        # In production, this would use Microsoft Graph API to send test email
        # For now, return stub success response
        message = "Microsoft test mail feature is configured (stub mode - actual sending not implemented)"
        
        repo.create_test_log(
            db,
            mailbox_id=mailbox.id,
            provider=EmailProvider.MICROSOFT,
            status="SUCCESS",
            message=message,
        )

        mailbox.is_active = True
        mailbox.selected_provider = EmailProvider.MICROSOFT
        db.commit()

        return {
            "message": message,
            "mailbox_active": mailbox.is_active,
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider_type}",
        )


# =========================================================
# GMAIL / MICROSOFT AUTH (SAFE)
# =========================================================

def gmail_auth_service(db: Session, mailbox_id: int) -> dict:
    """
    Initiate Gmail OAuth flow.
    In production, this would generate OAuth URL and redirect user.
    For now, returns stub response that simulates successful configuration.
    """
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    
    # Create OAuth config record
    repo.create_oauth_config(db, mailbox_id=mailbox_id, provider=EmailOAuthProvider.GMAIL)
    
    # Clear other OAuth configs
    microsoft_oauth = repo.get_oauth_by_mailbox_and_provider(db, mailbox_id, EmailOAuthProvider.MICROSOFT)
    if microsoft_oauth:
        db.delete(microsoft_oauth)
    
    # Clear SMTP config
    repo.delete_smtp_by_mailbox(db, mailbox_id)
    
    # Update mailbox to use Gmail
    mailbox.selected_provider = EmailProvider.GMAIL
    mailbox.is_active = True
    db.commit()
    db.refresh(mailbox)
    
    return {
        "success": True,
        "configured": True,
        "provider": "GMAIL",
        "message": "Gmail authentication configured successfully (stub mode)",
    }


def microsoft_auth_service(db: Session, mailbox_id: int) -> dict:
    """
    Initiate Microsoft OAuth flow.
    In production, this would generate OAuth URL and redirect user.
    For now, returns stub response that simulates successful configuration.
    """
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    
    # Create OAuth config record
    repo.create_oauth_config(db, mailbox_id=mailbox_id, provider=EmailOAuthProvider.MICROSOFT)
    
    # Clear other OAuth configs
    gmail_oauth = repo.get_oauth_by_mailbox_and_provider(db, mailbox_id, EmailOAuthProvider.GMAIL)
    if gmail_oauth:
        db.delete(gmail_oauth)
    
    # Clear SMTP config
    repo.delete_smtp_by_mailbox(db, mailbox_id)
    
    # Update mailbox to use Microsoft
    mailbox.selected_provider = EmailProvider.MICROSOFT
    mailbox.is_active = True
    db.commit()
    db.refresh(mailbox)
    
    return {
        "success": True,
        "configured": True,
        "provider": "MICROSOFT",
        "message": "Microsoft authentication configured successfully (stub mode)",
    }


# =========================================================
# OAUTH CALLBACKS (CRITICAL FIX)
# =========================================================

def exchange_google_code_service(db: Session, mailbox_id: int, code: str) -> dict:
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    repo.create_oauth_config(db, mailbox_id=mailbox_id, provider=EmailOAuthProvider.GMAIL)
    mailbox.selected_provider = EmailProvider.GMAIL
    mailbox.is_active = True
    db.commit()

    return {
        "configured": True,
        "provider": "GMAIL",
        "message": "Gmail OAuth callback handled (stub)",
    }


def exchange_microsoft_code_service(db: Session, mailbox_id: int, code: str) -> dict:
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    repo.create_oauth_config(db, mailbox_id=mailbox_id, provider=EmailOAuthProvider.MICROSOFT)
    mailbox.selected_provider = EmailProvider.MICROSOFT
    mailbox.is_active = True
    db.commit()

    return {
        "configured": True,
        "provider": "MICROSOFT",
        "message": "Microsoft OAuth callback handled (stub)",
    }


# =========================================================
# FULL SETTINGS
# =========================================================

def get_email_settings_service(
    db: Session,
    mailbox_id: int,
) -> EmailSettingsOut:
    mailbox = repo.get_mailbox(db, mailbox_id)
    if not mailbox:
        return EmailSettingsOut()

    smtp = repo.get_smtp_by_mailbox(db, mailbox_id)
    gmail = repo.get_oauth_by_mailbox_and_provider(db, mailbox_id, EmailOAuthProvider.GMAIL)
    microsoft = repo.get_oauth_by_mailbox_and_provider(db, mailbox_id, EmailOAuthProvider.MICROSOFT)

    return EmailSettingsOut(
        mailbox=mailbox,
        smtp=smtp,
        gmail_configured=bool(gmail and gmail.is_configured),
        microsoft_configured=bool(microsoft and microsoft.is_configured),
    )
