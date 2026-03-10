"""
Notes Service
Business logic layer for Notes operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import json
import time

from app.repositories.notes_repository import NotesRepository, NoteShareRepository, NoteAttachmentRepository
from app.schemas.notes import (
    NoteCreate, NoteUpdate, NoteResponse, NoteSummary,
    NoteShareCreate, NoteShareUpdate, NoteShareResponse,
    NoteAttachmentResponse, NoteFilters, NotesAnalytics,
    NoteBulkAction, NoteBulkUpdate, NoteSearchResult, NoteSearchResponse
)


class NotesService:
    """Service for notes management operations"""

    def __init__(self, db: Session):
        self.db = db
        self.notes_repo = NotesRepository(db)
        self.share_repo = NoteShareRepository(db)
        self.attachment_repo = NoteAttachmentRepository(db)

    # Note Operations
    def create_note(self, note_data: NoteCreate, business_id: int, created_by: int) -> NoteResponse:
        """Create a new note"""
        try:
            note = self.notes_repo.create_note(note_data, business_id, created_by)
            return self._convert_note_to_response(note)
        except Exception as e:
            raise Exception(f"Failed to create note: {str(e)}")

    def get_note(self, note_id: int, business_id: int, user_id: int) -> Optional[NoteResponse]:
        """Get note by ID with permission check"""
        try:
            note = self.notes_repo.get_note_by_id(note_id, business_id)
            if not note:
                return None
            
            # Check if user has access to this note
            if not self._user_has_access_to_note(note, user_id):
                return None
            
            return self._convert_note_to_response(note)
        except Exception as e:
            raise Exception(f"Failed to get note: {str(e)}")

    def get_notes(self, business_id: int, filters: Optional[NoteFilters] = None,
                 skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[NoteSummary]:
        """Get notes with optional filters"""
        try:
            notes = self.notes_repo.get_notes(business_id, filters, skip, limit, user_id)
            return [self._convert_note_to_summary(note) for note in notes]
        except Exception as e:
            raise Exception(f"Failed to get notes: {str(e)}")

    def update_note(self, note_id: int, business_id: int, note_data: NoteUpdate, 
                   updated_by: int) -> Optional[NoteResponse]:
        """Update note with permission check"""
        try:
            # Check if user has access to this note
            existing_note = self.notes_repo.get_note_by_id(note_id, business_id)
            if not existing_note:
                return None
            
            if not self._user_can_edit_note(existing_note, updated_by):
                raise Exception("Permission denied: Cannot edit this note")
            
            note = self.notes_repo.update_note(note_id, business_id, note_data, updated_by)
            return self._convert_note_to_response(note) if note else None
        except Exception as e:
            raise Exception(f"Failed to update note: {str(e)}")

    def delete_note(self, note_id: int, business_id: int, user_id: int) -> bool:
        """Delete note with permission check"""
        try:
            # Check if user has access to this note
            existing_note = self.notes_repo.get_note_by_id(note_id, business_id)
            if not existing_note:
                return False
            
            if not self._user_can_delete_note(existing_note, user_id):
                raise Exception("Permission denied: Cannot delete this note")
            
            return self.notes_repo.delete_note(note_id, business_id)
        except Exception as e:
            raise Exception(f"Failed to delete note: {str(e)}")

    def search_notes(self, business_id: int, search_query: str, user_id: Optional[int] = None,
                    skip: int = 0, limit: int = 50) -> NoteSearchResponse:
        """Search notes with full-text search"""
        try:
            start_time = time.time()
            
            results, total_count = self.notes_repo.search_notes(
                business_id, search_query, user_id, skip, limit
            )
            
            search_time_ms = (time.time() - start_time) * 1000
            
            search_results = []
            for note in results:
                # Create highlighted content preview
                content_highlight = self._create_content_highlight(note.content, search_query)
                
                search_result = NoteSearchResult(
                    id=note.id,
                    title=note.title,
                    content_highlight=content_highlight,
                    category=note.category,
                    priority=note.priority,
                    tags=json.loads(note.tags) if note.tags else None,
                    creator_name=note.creator.name if note.creator else "Unknown",
                    created_at=note.created_at,
                    updated_at=note.updated_at,
                    relevance_score=self._calculate_relevance_score(note, search_query)
                )
                search_results.append(search_result)
            
            return NoteSearchResponse(
                results=search_results,
                total_count=total_count,
                search_query=search_query,
                search_time_ms=round(search_time_ms, 2),
                suggestions=self._generate_search_suggestions(search_query)
            )
        except Exception as e:
            raise Exception(f"Failed to search notes: {str(e)}")

    def get_notes_analytics(self, business_id: int, user_id: Optional[int] = None) -> NotesAnalytics:
        """Get notes analytics"""
        try:
            analytics_data = self.notes_repo.get_notes_analytics(business_id, user_id)
            return NotesAnalytics(**analytics_data)
        except Exception as e:
            raise Exception(f"Failed to get notes analytics: {str(e)}")

    def bulk_update_notes(self, bulk_data: NoteBulkUpdate, business_id: int, updated_by: int) -> Dict[str, Any]:
        """Bulk update notes"""
        try:
            updated_count = self.notes_repo.bulk_update_notes(
                bulk_data.note_ids, business_id, bulk_data, updated_by
            )
            
            return {
                "updated_count": updated_count,
                "message": f"Successfully updated {updated_count} notes"
            }
        except Exception as e:
            raise Exception(f"Failed to bulk update notes: {str(e)}")

    def bulk_action_notes(self, bulk_action: NoteBulkAction, business_id: int, updated_by: int) -> Dict[str, Any]:
        """Perform bulk actions on notes"""
        try:
            affected_count = self.notes_repo.bulk_action_notes(
                bulk_action.note_ids, business_id, bulk_action.action, updated_by
            )
            
            action_messages = {
                "archive": "archived",
                "unarchive": "unarchived",
                "pin": "pinned",
                "unpin": "unpinned",
                "favorite": "marked as favorite",
                "unfavorite": "unmarked as favorite",
                "delete": "deleted"
            }
            
            action_message = action_messages.get(bulk_action.action, "processed")
            
            return {
                "affected_count": affected_count,
                "action": bulk_action.action,
                "message": f"Successfully {action_message} {affected_count} notes"
            }
        except Exception as e:
            raise Exception(f"Failed to perform bulk action: {str(e)}")

    # Note Sharing Operations
    def share_note(self, share_data: NoteShareCreate, business_id: int, shared_by: int) -> NoteShareResponse:
        """Share a note with another user"""
        try:
            # Verify the note exists and user has permission to share
            note = self.notes_repo.get_note_by_id(share_data.note_id, business_id)
            if not note:
                raise Exception("Note not found")
            
            if not self._user_can_share_note(note, shared_by):
                raise Exception("Permission denied: Cannot share this note")
            
            share_dict = share_data.dict()
            share_dict['shared_by'] = shared_by
            
            share = self.share_repo.create_share(share_dict)
            
            # Update note's is_shared flag
            if not note.is_shared:
                self.notes_repo.update_note(
                    note.id, business_id, 
                    NoteUpdate(is_shared=True), 
                    shared_by
                )
            
            return self._convert_share_to_response(share)
        except Exception as e:
            raise Exception(f"Failed to share note: {str(e)}")

    def get_note_shares(self, note_id: int, business_id: int, user_id: int) -> List[NoteShareResponse]:
        """Get all shares for a note"""
        try:
            # Verify user has access to the note
            note = self.notes_repo.get_note_by_id(note_id, business_id)
            if not note or not self._user_has_access_to_note(note, user_id):
                raise Exception("Note not found or access denied")
            
            shares = self.share_repo.get_note_shares(note_id)
            return [self._convert_share_to_response(share) for share in shares]
        except Exception as e:
            raise Exception(f"Failed to get note shares: {str(e)}")

    def remove_note_share(self, share_id: int, user_id: int) -> bool:
        """Remove a note share"""
        try:
            # Additional permission checks would go here
            return self.share_repo.delete_share(share_id)
        except Exception as e:
            raise Exception(f"Failed to remove note share: {str(e)}")

    # Helper Methods
    def _user_has_access_to_note(self, note, user_id: int) -> bool:
        """Check if user has access to read the note"""
        # User is the creator
        if note.created_by == user_id:
            return True
        
        # Check if note is shared with the user
        for share in note.shared_notes:
            if share.shared_with_user_id == user_id:
                return True
        
        return False

    def _user_can_edit_note(self, note, user_id: int) -> bool:
        """Check if user can edit the note"""
        # User is the creator
        if note.created_by == user_id:
            return True
        
        # Check if note is shared with edit permission
        for share in note.shared_notes:
            if share.shared_with_user_id == user_id and share.can_edit:
                return True
        
        return False

    def _user_can_delete_note(self, note, user_id: int) -> bool:
        """Check if user can delete the note"""
        # User is the creator
        if note.created_by == user_id:
            return True
        
        # Check if note is shared with delete permission
        for share in note.shared_notes:
            if share.shared_with_user_id == user_id and share.can_delete:
                return True
        
        return False

    def _user_can_share_note(self, note, user_id: int) -> bool:
        """Check if user can share the note"""
        # Only the creator can share notes (for now)
        return note.created_by == user_id

    def _convert_note_to_response(self, note) -> NoteResponse:
        """Convert note model to response schema"""
        # Parse tags from JSON
        tags = None
        if note.tags:
            try:
                tags = json.loads(note.tags)
            except:
                tags = []
        
        # Count shares and attachments
        share_count = len(note.shared_notes) if note.shared_notes else 0
        attachment_count = 0  # Would implement with attachment relationship
        
        return NoteResponse(
            id=note.id,
            business_id=note.business_id,
            title=note.title,
            content=note.content,
            category=note.category,
            priority=note.priority,
            tags=tags,
            is_pinned=note.is_pinned,
            is_archived=note.is_archived,
            is_favorite=note.is_favorite,
            is_shared=note.is_shared,
            color=note.color,
            reminder_date=note.reminder_date,
            created_by=note.created_by,
            updated_by=note.updated_by,
            creator_name=note.creator.name if note.creator else "Unknown",
            updater_name=note.updater.name if note.updater else None,
            created_at=note.created_at,
            updated_at=note.updated_at,
            share_count=share_count,
            attachment_count=attachment_count
        )

    def _convert_note_to_summary(self, note) -> NoteSummary:
        """Convert note model to summary schema"""
        # Parse tags from JSON
        tags = None
        if note.tags:
            try:
                tags = json.loads(note.tags)
            except:
                tags = []
        
        # Create content preview (first 100 characters)
        content_preview = note.content[:100] + "..." if len(note.content) > 100 else note.content
        
        # Check if reminder is overdue
        is_overdue = (
            note.reminder_date is not None and 
            note.reminder_date < datetime.utcnow()
        )
        
        # Count shares and attachments
        share_count = len(note.shared_notes) if note.shared_notes else 0
        attachment_count = 0  # Would implement with attachment relationship
        
        return NoteSummary(
            id=note.id,
            title=note.title,
            content_preview=content_preview,
            category=note.category,
            priority=note.priority,
            tags=tags,
            is_pinned=note.is_pinned,
            is_archived=note.is_archived,
            is_favorite=note.is_favorite,
            is_shared=note.is_shared,
            color=note.color,
            reminder_date=note.reminder_date,
            creator_name=note.creator.name if note.creator else "Unknown",
            created_at=note.created_at,
            updated_at=note.updated_at,
            share_count=share_count,
            attachment_count=attachment_count,
            is_overdue=is_overdue
        )

    def _convert_share_to_response(self, share) -> NoteShareResponse:
        """Convert share model to response schema"""
        shared_with_name = "Unknown"
        if share.shared_with_user:
            shared_with_name = share.shared_with_user.name
        elif share.shared_with_employee:
            shared_with_name = f"{share.shared_with_employee.first_name} {share.shared_with_employee.last_name}"
        
        shared_by_name = share.sharer.name if share.sharer else "Unknown"
        
        return NoteShareResponse(
            id=share.id,
            note_id=share.note_id,
            shared_with_user_id=share.shared_with_user_id,
            shared_with_employee_id=share.shared_with_employee_id,
            can_edit=share.can_edit,
            can_delete=share.can_delete,
            shared_by=share.shared_by,
            shared_at=share.shared_at,
            shared_with_name=shared_with_name,
            shared_by_name=shared_by_name
        )

    def _create_content_highlight(self, content: str, search_query: str) -> str:
        """Create highlighted content preview for search results"""
        # Simple implementation - would use more sophisticated highlighting in production
        if not search_query or not content:
            return content[:200] + "..." if len(content) > 200 else content
        
        # Find the first occurrence of search term
        lower_content = content.lower()
        lower_query = search_query.lower()
        
        index = lower_content.find(lower_query)
        if index == -1:
            return content[:200] + "..." if len(content) > 200 else content
        
        # Extract context around the match
        start = max(0, index - 50)
        end = min(len(content), index + len(search_query) + 50)
        
        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."
        
        return excerpt

    def _calculate_relevance_score(self, note, search_query: str) -> float:
        """Calculate relevance score for search results"""
        # Simple scoring algorithm
        score = 0.0
        lower_query = search_query.lower()
        
        # Title match gets highest score
        if lower_query in note.title.lower():
            score += 10.0
        
        # Content match gets medium score
        if lower_query in note.content.lower():
            score += 5.0
        
        # Tag match gets medium score
        if note.tags and lower_query in note.tags.lower():
            score += 7.0
        
        # Recent notes get slight boost
        days_old = (datetime.utcnow() - note.created_at).days
        if days_old < 7:
            score += 2.0
        elif days_old < 30:
            score += 1.0
        
        return score

    def _generate_search_suggestions(self, search_query: str) -> List[str]:
        """Generate search suggestions"""
        # Simple implementation - would use more sophisticated suggestions in production
        suggestions = []
        
        if len(search_query) > 2:
            # Add some common variations
            suggestions.append(f"{search_query}*")
            if " " not in search_query:
                suggestions.append(f"*{search_query}*")
        
        return suggestions[:5]  # Limit to 5 suggestions