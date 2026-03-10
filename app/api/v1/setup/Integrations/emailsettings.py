# app/api/v1/setup/integrations/emailsettings.py

from typing import Optional, List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User

from app.schemas.setup.Integrations.emailsettings import (
    EmailMailboxCreate,
    EmailMailboxOut,
    EmailSmtpConfigCreateOrUpdate,
    EmailSmtpConfigOut,
    EmailOAuthCallbackRequest,
    EmailTestRequest,
    EmailTestResponse,
    EmailSettingsOut,
)

from app.services.setup.Integrations import emailsettings as svc


router = APIRouter(
    prefix="/integrations/email-settings",
)

# =====================================================
# LIST MAILBOXES
# =====================================================
@router.get(
    "/{business_id}/mailboxes",
    response_model=List[EmailMailboxOut],
)
def list_mailboxes(
    business_id: int,
    tenant_id: Optional[int] = Query(default=None, alias="tenantId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.list_mailboxes_service(
        db,
        business_id=business_id,
        tenant_id=tenant_id,
    )


# =====================================================
# FULL SETTINGS (PAGE LOAD)
# =====================================================
@router.get(
    "/{business_id}/mailbox/{mailbox_id}/settings",
    response_model=EmailSettingsOut,
)
def get_email_settings(
    business_id: int,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.get_email_settings_service(db, mailbox_id)


# =====================================================
# MAILBOX CRUD
# =====================================================
@router.post(
    "/mailbox",
    response_model=EmailMailboxOut,
    status_code=status.HTTP_201_CREATED,
)
def create_mailbox(
    payload: EmailMailboxCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.create_mailbox_service(db, payload)


@router.get(
    "/{business_id}/mailbox/{mailbox_id}",
    response_model=EmailMailboxOut,
)
def get_mailbox(
    business_id: int,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.get_mailbox_service(db, mailbox_id)


@router.delete(
    "/{business_id}/mailbox/{mailbox_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mailbox(
    business_id: int,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    svc.delete_mailbox_service(db, mailbox_id)
    return None


@router.patch(
    "/{business_id}/mailbox/{mailbox_id}/toggle-active",
    response_model=EmailMailboxOut,
)
def toggle_mailbox_active(
    business_id: int,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.toggle_mailbox_active_service(db, mailbox_id)


# =====================================================
# SMTP CONFIG
# =====================================================
@router.put(
    "/{business_id}/mailbox/{mailbox_id}/smtp",
    response_model=EmailSmtpConfigOut,
)
def save_smtp(
    business_id: int,
    mailbox_id: int,
    payload: EmailSmtpConfigCreateOrUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    smtp = svc.save_smtp_service(db, mailbox_id, payload)

    # 🔐 Mask password in response
    return EmailSmtpConfigOut(
        id=smtp.id,
        mailbox_id=smtp.mailbox_id,
        username=smtp.username,
        server=smtp.server,
        port=smtp.port,
        use_ssl=smtp.use_ssl,
        created_at=smtp.created_at,
        updated_at=smtp.updated_at,
    )


# =====================================================
# GMAIL OAUTH
# =====================================================
@router.post(
    "/{business_id}/mailbox/{mailbox_id}/gmail-auth",
    response_model=dict,
)
def gmail_auth(
    business_id: int,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.gmail_auth_service(db, mailbox_id)


@router.post(
    "/{business_id}/mailbox/{mailbox_id}/gmail-callback",
    response_model=dict,
)
def gmail_callback(
    business_id: int,
    mailbox_id: int,
    payload: EmailOAuthCallbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.exchange_google_code_service(db, mailbox_id, payload.code)


# =====================================================
# MICROSOFT OAUTH
# =====================================================
@router.post(
    "/{business_id}/mailbox/{mailbox_id}/microsoft-auth",
    response_model=dict,
)
def microsoft_auth(
    business_id: int,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.microsoft_auth_service(db, mailbox_id)


@router.post(
    "/{business_id}/mailbox/{mailbox_id}/microsoft-callback",
    response_model=dict,
)
def microsoft_callback(
    business_id: int,
    mailbox_id: int,
    payload: EmailOAuthCallbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.exchange_microsoft_code_service(db, mailbox_id, payload.code)


# =====================================================
# TEST EMAIL
# =====================================================
@router.post(
    "/{business_id}/mailbox/{mailbox_id}/test-email",
    response_model=EmailTestResponse,
)
def test_email(
    business_id: int,
    mailbox_id: int,
    payload: EmailTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return svc.send_test_mail_service(db, mailbox_id, payload)
