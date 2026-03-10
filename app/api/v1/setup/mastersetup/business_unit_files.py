# app/api/v1/endpoints/business_unit_files.py

import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings, BASE_URL
from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business
from app.repositories.business_unit_repository import BusinessUnitRepository


router = APIRouter()


# ============================================================================
# Upload Directories
# ============================================================================

BASE_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

BU_HEADERS_DIR = BASE_UPLOAD_DIR / "business_units" / "headers"
BU_FOOTERS_DIR = BASE_UPLOAD_DIR / "business_units" / "footers"
BU_HEADERS_DIR.mkdir(parents=True, exist_ok=True)
BU_FOOTERS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Helpers
# ============================================================================

def _save_file_to_disk(upload: UploadFile, target_dir: Path) -> str:
    original_name = upload.filename or "upload"
    ext = original_name.split(".")[-1] if "." in original_name else "bin"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = target_dir / filename

    with open(file_path, "wb") as f:
        f.write(upload.file.read())

    return filename


def _resolve_unit_image_path(unit, kind: str) -> Path | None:
    url = unit.header_image_url if kind == "header" else unit.footer_image_url
    if not url:
        return None

    filename = Path(url).name
    base_dir = BU_HEADERS_DIR if kind == "header" else BU_FOOTERS_DIR
    file_path = base_dir / filename

    return file_path if file_path.is_file() else None


def _get_unit_and_business(db: Session, unit_id: int, business_id: int = None):
    repo = BusinessUnitRepository(db)
    unit = repo.get(unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business unit not found",
        )

    # Verify business_id matches if provided
    if business_id and unit.business_id != business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business unit not found in this business",
        )

    business = db.query(Business).filter(Business.id == unit.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return unit


# ============================================================================
# Upload Header Image (ADMIN / SUPERADMIN)
# ============================================================================

@router.post(
    "/upload-header/{unit_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Upload header image for a business unit",
)
def upload_header_image(
    unit_id: int,
    business_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    unit = _get_unit_and_business(db, unit_id, business_id)

    filename = _save_file_to_disk(file, BU_HEADERS_DIR)
    file_url = f"{BASE_URL}/{settings.UPLOAD_DIR}/business_units/headers/{filename}"

    repo = BusinessUnitRepository(db)
    repo.update(unit, {"header_image_url": file_url})

    return {
        "message": "Header image uploaded successfully",
        "file_url": file_url,
    }


# ============================================================================
# Upload Footer Image (ADMIN / SUPERADMIN)
# ============================================================================

@router.post(
    "/upload-footer/{unit_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Upload footer image for a business unit",
)
def upload_footer_image(
    unit_id: int,
    business_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    unit = _get_unit_and_business(db, unit_id, business_id)

    filename = _save_file_to_disk(file, BU_FOOTERS_DIR)
    file_url = f"{BASE_URL}/{settings.UPLOAD_DIR}/business_units/footers/{filename}"

    repo = BusinessUnitRepository(db)
    repo.update(unit, {"footer_image_url": file_url})

    return {
        "message": "Footer image uploaded successfully",
        "file_url": file_url,
    }


# ============================================================================
# Get Header Image (AUTH REQUIRED)
# ============================================================================

@router.get(
    "/unit/{unit_id}/header",
    status_code=status.HTTP_200_OK,
    summary="Get header image for a business unit",
)
def get_business_unit_header(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    unit = _get_unit_and_business(db, unit_id)

    file_path = _resolve_unit_image_path(unit, "header")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Header image not found",
        )

    return FileResponse(str(file_path))


# ============================================================================
# Get Footer Image (AUTH REQUIRED)
# ============================================================================

@router.get(
    "/unit/{unit_id}/footer",
    status_code=status.HTTP_200_OK,
    summary="Get footer image for a business unit",
)
def get_business_unit_footer(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    unit = _get_unit_and_business(db, unit_id)

    file_path = _resolve_unit_image_path(unit, "footer")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Footer image not found",
        )

    return FileResponse(str(file_path))
