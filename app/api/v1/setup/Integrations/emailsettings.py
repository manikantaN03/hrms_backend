# app/api/v1/setup/integrations/emailsettings.py

from typing import Optional, List

from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, validate_business_access
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
    "/mailboxes",
    response_model=List[EmailMailboxOut],
)
def list_mailboxes(
    business_id: int = Path(...),
    tenant_id: Optional[int] = Query(default=None, alias="tenantId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.list_mailboxes_service(
        db,
        business_id=business_id,
        tenant_id=tenant_id,
    )


# =====================================================
# FULL SETTINGS (PAGE LOAD)
# =====================================================
@router.get(
    "/mailbox/{mailbox_id}/settings",
    response_model=EmailSettingsOut,
)
def get_email_settings(
    mailbox_id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
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
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.create_mailbox_service(db, business_id, payload)


@router.get(
    "/mailbox/{mailbox_id}",
    response_model=EmailMailboxOut,
)
def get_mailbox(
    mailbox_id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.get_mailbox_service(db, mailbox_id)


@router.delete(
    "/mailbox/{mailbox_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mailbox(
    mailbox_id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    svc.delete_mailbox_service(db, mailbox_id)
    return None


@router.patch(
    "/mailbox/{mailbox_id}/toggle-active",
    response_model=EmailMailboxOut,
)
def toggle_mailbox_active(
    mailbox_id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.toggle_mailbox_active_service(db, mailbox_id)


# =====================================================
# SMTP CONFIG
# =====================================================
@router.put(
    "/mailbox/{mailbox_id}/smtp",
    response_model=EmailSmtpConfigOut,
)
def save_smtp(
    mailbox_id: int,
    payload: EmailSmtpConfigCreateOrUpdate,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
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
    "/mailbox/{mailbox_id}/gmail-auth",
    response_model=dict,
)
def gmail_auth(
    mailbox_id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.gmail_auth_service(db, mailbox_id)


@router.post(
    "/mailbox/{mailbox_id}/gmail-callback",
    response_model=dict,
)
def gmail_callback(
    mailbox_id: int,
    payload: EmailOAuthCallbackRequest,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.exchange_google_code_service(db, mailbox_id, payload.code)


# =====================================================
# MICROSOFT OAUTH
# =====================================================
@router.post(
    "/mailbox/{mailbox_id}/microsoft-auth",
    response_model=dict,
)
def microsoft_auth(
    mailbox_id: int,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.microsoft_auth_service(db, mailbox_id)


@router.post(
    "/mailbox/{mailbox_id}/microsoft-callback",
    response_model=dict,
)
def microsoft_callback(
    mailbox_id: int,
    payload: EmailOAuthCallbackRequest,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.exchange_microsoft_code_service(db, mailbox_id, payload.code)


# =====================================================
# TEST EMAIL
# =====================================================
@router.post(
    "/mailbox/{mailbox_id}/test-email",
    response_model=EmailTestResponse,
)
def test_email(
    mailbox_id: int,
    payload: EmailTestRequest,
    business_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    validate_business_access(business_id, current_user, db)
    return svc.send_test_mail_service(db, mailbox_id, payload)
