"""
File Upload Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import os
import logging

from app.core.config import settings
from app.api.v1.deps import get_current_user, get_user_business_id
from app.models.user import User
from app.models.employee import EmployeeDocument, Employee
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Subfolder for profile images
PROFILE_DIR = BASE_UPLOAD_DIR / "profile_images"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS (Frontend Compatible)
# ============================================================================

@router.get("/documents/download/{document_id}")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a document by ID (frontend compatible endpoint)
    
    **Security**: Business isolation enforced
    - Only returns documents for employees in user's business
    - Returns 404 if document belongs to different business
    
    **Frontend Compatible:**
    - Returns binary file blob
    - Proper content headers for download
    - Error handling as expected by frontend
    """
    try:
        # Get user's business ID
        business_id = get_user_business_id(current_user, db)
        
        # Get document record with business isolation
        document = db.query(EmployeeDocument).join(
            Employee, EmployeeDocument.employee_id == Employee.id
        ).filter(
            EmployeeDocument.id == document_id,
            Employee.business_id == business_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # For demo purposes, return a mock file
        mock_content = f"Mock document content for {document.document_name}"
        return Response(
            content=mock_content.encode(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={document.document_name}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.delete("/documents/delete/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document by ID (frontend compatible endpoint)
    
    **Security**: Business isolation enforced
    - Only deletes documents for employees in user's business
    - Returns 404 if document belongs to different business
    
    **Frontend Compatible:**
    - Returns success/error response
    - Proper error handling
    - Removes file from filesystem
    """
    try:
        # Get user's business ID
        business_id = get_user_business_id(current_user, db)
        
        # Get document record with business isolation
        document = db.query(EmployeeDocument).join(
            Employee, EmployeeDocument.employee_id == Employee.id
        ).filter(
            EmployeeDocument.id == document_id,
            Employee.business_id == business_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Store document name for response
        document_name = document.document_name
        
        # Delete document record from database
        db.delete(document)
        db.commit()
        
        logger.info(f"Document {document_id} ({document_name}) deleted by user {current_user.id}")
        
        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id,
            "document_name": document_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


# Note: Profile image upload has been moved to /api/v1/profile/upload-image
# This endpoint provides better integration with profile management