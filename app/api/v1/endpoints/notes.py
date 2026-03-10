"""
Notes API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.notes_service import NotesService
from app.schemas.notes import (
    NoteCreate, NoteUpdate, NoteResponse, NoteSummary,
    NoteShareCreate, NoteShareUpdate, NoteShareResponse,
    NoteAttachmentResponse, NoteFilters, NotesAnalytics,
    NoteBulkAction, NoteBulkUpdate, NoteSearchResponse,
    NoteCategory, NotePriority
)

router = APIRouter()


# Note Endpoints
@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new note
    
    **Required fields:**
    - title: Note title (max 255 characters)
    - content: Note content (max 10,000 characters)
    
    **Optional fields:**
    - category: Note category (default: general)
    - priority: Note priority (default: medium)
    - tags: Array of tags (max 20 tags, 50 chars each)
    - is_pinned: Pin note to top (default: false)
    - is_archived: Archive note (default: false)
    - is_favorite: Mark as favorite (default: false)
    - color: Hex color code (default: #ffffff)
    - reminder_date: Reminder date/time
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        note = service.create_note(note_data, business_id, current_user.id)
        
        return note
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get("/", response_model=List[NoteSummary])
async def get_notes(
    category: Optional[List[NoteCategory]] = Query(None),
    priority: Optional[List[NotePriority]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None, description="Filter archived notes"),
    is_favorite: Optional[bool] = Query(None),
    is_shared: Optional[bool] = Query(None),
    has_reminder: Optional[bool] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=255, description="Search in title, content, and tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notes with optional filters
    
    **Query Parameters:**
    - category: Filter by note categories
    - priority: Filter by note priorities
    - tags: Filter by tags
    - is_pinned: Filter pinned notes
    - is_archived: Filter archived notes
    - is_favorite: Filter favorite notes
    - is_shared: Filter shared notes
    - has_reminder: Filter notes with reminders
    - is_overdue: Filter overdue reminders
    - search: Search in title, content, and tags
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        # Create filters
        filters = NoteFilters(
            category=category,
            priority=priority,
            tags=tags,
            is_pinned=is_pinned,
            is_archived=is_archived,
            is_favorite=is_favorite,
            is_shared=is_shared,
            has_reminder=has_reminder,
            is_overdue=is_overdue,
            search=search
        )
        
        service = NotesService(db)
        notes = service.get_notes(business_id, filters, skip, limit, current_user.id)
        
        return notes
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notes: {str(e)}"
        )


# Search Endpoint
@router.get("/search/", response_model=NoteSearchResponse)
async def search_notes(
    q: str = Query(..., min_length=1, max_length=255, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search notes with full-text search
    
    **Query Parameters:**
    - q: Search query (searches in title, content, and tags)
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    
    **Returns:**
    - Search results with highlighted content
    - Total count of matching notes
    - Search time in milliseconds
    - Search suggestions
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        search_results = service.search_notes(business_id, q, current_user.id, skip, limit)
        
        return search_results
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search notes: {str(e)}"
        )


# Analytics Endpoint
@router.get("/analytics/", response_model=NotesAnalytics)
async def get_notes_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notes analytics and metrics
    
    **Returns:**
    - Total notes count
    - Notes by category breakdown
    - Notes by priority breakdown
    - Status counts (pinned, archived, favorite, shared)
    - Reminder statistics
    - Time-based statistics
    - Most used tags
    - Recent activity
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        analytics = service.get_notes_analytics(business_id, current_user.id)
        
        return analytics
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notes analytics: {str(e)}"
        )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get note by ID"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        note = service.get_note(note_id, business_id, current_user.id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return note
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get note: {str(e)}"
        )


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update note"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        note = service.update_note(note_id, business_id, note_data, current_user.id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return note
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update note: {str(e)}"
        )


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete note"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        success = service.delete_note(note_id, business_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return {"message": "Note deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete note: {str(e)}"
        )


# Bulk Operations
@router.post("/bulk/update")
async def bulk_update_notes(
    bulk_data: NoteBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update notes
    
    **Request Body:**
    - note_ids: Array of note IDs to update (1-100 items)
    - category: New category (optional)
    - priority: New priority (optional)
    - tags: New tags array (optional)
    - color: New color (optional)
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        result = service.bulk_update_notes(bulk_data, business_id, current_user.id)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update notes: {str(e)}"
        )


@router.post("/bulk/action")
async def bulk_action_notes(
    bulk_action: NoteBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform bulk actions on notes
    
    **Request Body:**
    - note_ids: Array of note IDs (1-100 items)
    - action: Action to perform (archive, unarchive, pin, unpin, favorite, unfavorite, delete)
    
    **Available Actions:**
    - archive: Archive selected notes
    - unarchive: Unarchive selected notes
    - pin: Pin selected notes
    - unpin: Unpin selected notes
    - favorite: Mark selected notes as favorite
    - unfavorite: Unmark selected notes as favorite
    - delete: Delete selected notes (permanent)
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        result = service.bulk_action_notes(bulk_action, business_id, current_user.id)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk action: {str(e)}"
        )


# Note Sharing Endpoints
@router.post("/{note_id}/share", response_model=NoteShareResponse)
async def share_note(
    note_id: int,
    share_data: NoteShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Share a note with another user
    
    **Required fields:**
    - Either shared_with_user_id or shared_with_employee_id
    
    **Optional fields:**
    - can_edit: Allow recipient to edit the note (default: false)
    - can_delete: Allow recipient to delete the note (default: false)
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        # Set note_id from URL
        share_data.note_id = note_id
        
        service = NotesService(db)
        share = service.share_note(share_data, business_id, current_user.id)
        
        return share
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share note: {str(e)}"
        )


@router.get("/{note_id}/shares", response_model=List[NoteShareResponse])
async def get_note_shares(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shares for a note"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        shares = service.get_note_shares(note_id, business_id, current_user.id)
        
        return shares
    
    except Exception as e:
        error_msg = str(e)
        # Check if it's a not found error
        if "not found" in error_msg.lower() or "access denied" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found or access denied"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get note shares: {error_msg}"
        )


@router.delete("/shares/{share_id}")
async def remove_note_share(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a note share"""
    try:
        service = NotesService(db)
        success = service.remove_note_share(share_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note share not found"
            )
        
        return {"message": "Note share removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove note share: {str(e)}"
        )


# Quick Actions
@router.post("/{note_id}/pin")
async def pin_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pin/unpin a note"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        
        # Get current note to toggle pin status
        note = service.get_note(note_id, business_id, current_user.id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Toggle pin status
        updated_note = service.update_note(
            note_id, business_id, 
            NoteUpdate(is_pinned=not note.is_pinned), 
            current_user.id
        )
        
        action = "pinned" if updated_note.is_pinned else "unpinned"
        return {"message": f"Note {action} successfully", "is_pinned": updated_note.is_pinned}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pin/unpin note: {str(e)}"
        )


@router.post("/{note_id}/favorite")
async def favorite_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark/unmark a note as favorite"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        
        # Get current note to toggle favorite status
        note = service.get_note(note_id, business_id, current_user.id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Toggle favorite status
        updated_note = service.update_note(
            note_id, business_id, 
            NoteUpdate(is_favorite=not note.is_favorite), 
            current_user.id
        )
        
        action = "marked as favorite" if updated_note.is_favorite else "unmarked as favorite"
        return {"message": f"Note {action} successfully", "is_favorite": updated_note.is_favorite}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to favorite/unfavorite note: {str(e)}"
        )


@router.post("/{note_id}/archive")
async def archive_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive/unarchive a note"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = NotesService(db)
        
        # Get current note to toggle archive status
        note = service.get_note(note_id, business_id, current_user.id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Toggle archive status
        updated_note = service.update_note(
            note_id, business_id, 
            NoteUpdate(is_archived=not note.is_archived), 
            current_user.id
        )
        
        action = "archived" if updated_note.is_archived else "unarchived"
        return {"message": f"Note {action} successfully", "is_archived": updated_note.is_archived}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive/unarchive note: {str(e)}"
        )