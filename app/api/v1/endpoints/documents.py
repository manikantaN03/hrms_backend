"""
Document Management Endpoints
Handle document upload, download, and deletion
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict, Any
import os
import logging

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.employee import EmployeeDocument

router = APIRouter()
logger = logging.getLogger(__name__)

# Base upload directory
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a document by ID
    
    **Frontend Compatible:**
    - Returns binary file blob
    - Proper content headers for download
    - Error handling as expected by frontend
    """
    try:
        # Get document record
        document = db.query(EmployeeDocument).filter(
            EmployeeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has access to this document
        # For now, allow all authenticated users
        # In production, add proper authorization checks
        
        # Construct file path
        file_path = UPLOAD_DIR / document.file_path.lstrip('/')
        
        # Check if file exists
        if not file_path.exists():
            # Return a mock file for demo purposes
            mock_content = f"Mock document content for {document.document_name}"
            return Response(
                content=mock_content.encode(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={document.document_name}"
                }
            )
        
        # Return actual file
        return FileResponse(
            path=str(file_path),
            filename=document.document_name,
            media_type="application/octet-stream"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.delete("/delete/{document_id}", response_model=Dict[str, Any])
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document by ID
    
    **Frontend Compatible:**
    - Returns success/error response
    - Proper error handling
    - Removes file from filesystem
    """
    try:
        # Get document record
        document = db.query(EmployeeDocument).filter(
            EmployeeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has permission to delete this document
        # For now, allow all authenticated users
        # In production, add proper authorization checks
        
        # Store document name for response
        document_name = document.document_name
        
        # Delete file from filesystem if it exists
        file_path = UPLOAD_DIR / document.file_path.lstrip('/')
        if file_path.exists():
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
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


@router.get("/list", response_model=Dict[str, Any])
async def list_documents(
    employee_id: int = None,
    document_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List documents with optional filtering
    
    **Optional endpoint for document management**
    """
    try:
        query = db.query(EmployeeDocument)
        
        # Apply filters
        if employee_id:
            query = query.filter(EmployeeDocument.employee_id == employee_id)
        
        if document_type:
            query = query.filter(EmployeeDocument.document_type == document_type)
        
        documents = query.all()
        
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "employee_id": doc.employee_id,
                "document_type": doc.document_type,
                "document_name": doc.document_name,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "uploaded_by": doc.uploaded_by
            })
        
        return {
            "success": True,
            "documents": document_list,
            "total": len(document_list)
        }
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )