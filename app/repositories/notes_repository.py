"""
Notes Repository
Data access layer for Notes operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import json

from app.models.notes import Note, NoteShare, NoteAttachment, NoteCategory, NotePriority
from app.models.user import User
from app.models.employee import Employee
from app.schemas.notes import (
    NoteCreate, NoteUpdate, NoteFilters, NoteBulkAction, NoteBulkUpdate
)


class NotesRepository:
    """Repository for notes operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_note(self, note_data: NoteCreate, business_id: int, created_by: int) -> Note:
        """Create a new note"""
        # Convert tags list to JSON string
        tags_json = json.dumps(note_data.tags) if note_data.tags else None
        
        note = Note(
            business_id=business_id,
            title=note_data.title,
            content=note_data.content,
            category=note_data.category,
            priority=note_data.priority,
            tags=tags_json,
            is_pinned=note_data.is_pinned,
            is_archived=note_data.is_archived,
            is_favorite=note_data.is_favorite,
            is_shared=note_data.is_shared,
            color=note_data.color,
            reminder_date=note_data.reminder_date,
            created_by=created_by
        )
        
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_note_by_id(self, note_id: int, business_id: int) -> Optional[Note]:
        """Get note by ID"""
        return self.db.query(Note).options(
            joinedload(Note.creator),
            joinedload(Note.updater),
            joinedload(Note.shared_notes)
        ).filter(
            Note.id == note_id,
            Note.business_id == business_id
        ).first()

    def get_notes(self, business_id: int, filters: Optional[NoteFilters] = None, 
                 skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[Note]:
        """Get notes with optional filters"""
        query = self.db.query(Note).options(
            joinedload(Note.creator),
            joinedload(Note.updater)
        ).filter(Note.business_id == business_id)

        # Apply user-specific filtering (own notes + shared notes)
        if user_id:
            shared_note_ids = self.db.query(NoteShare.note_id).filter(
                NoteShare.shared_with_user_id == user_id
            ).subquery()
            
            query = query.filter(
                or_(
                    Note.created_by == user_id,
                    Note.id.in_(shared_note_ids)
                )
            )

        if filters:
            if filters.category:
                query = query.filter(Note.category.in_(filters.category))
            
            if filters.priority:
                query = query.filter(Note.priority.in_(filters.priority))
            
            if filters.tags:
                # Search for any of the specified tags in the JSON tags field
                tag_conditions = []
                for tag in filters.tags:
                    tag_conditions.append(Note.tags.like(f'%"{tag}"%'))
                query = query.filter(or_(*tag_conditions))
            
            if filters.is_pinned is not None:
                query = query.filter(Note.is_pinned == filters.is_pinned)
            
            if filters.is_archived is not None:
                query = query.filter(Note.is_archived == filters.is_archived)
            
            if filters.is_favorite is not None:
                query = query.filter(Note.is_favorite == filters.is_favorite)
            
            if filters.is_shared is not None:
                query = query.filter(Note.is_shared == filters.is_shared)
            
            if filters.has_reminder is not None:
                if filters.has_reminder:
                    query = query.filter(Note.reminder_date.isnot(None))
                else:
                    query = query.filter(Note.reminder_date.is_(None))
            
            if filters.is_overdue is not None and filters.is_overdue:
                query = query.filter(
                    and_(
                        Note.reminder_date.isnot(None),
                        Note.reminder_date < datetime.utcnow()
                    )
                )
            
            if filters.created_by:
                query = query.filter(Note.created_by == filters.created_by)
            
            if filters.created_date_from:
                query = query.filter(func.date(Note.created_at) >= filters.created_date_from)
            
            if filters.created_date_to:
                query = query.filter(func.date(Note.created_at) <= filters.created_date_to)
            
            if filters.updated_date_from:
                query = query.filter(func.date(Note.updated_at) >= filters.updated_date_from)
            
            if filters.updated_date_to:
                query = query.filter(func.date(Note.updated_at) <= filters.updated_date_to)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Note.title.ilike(search_term),
                        Note.content.ilike(search_term),
                        Note.tags.ilike(search_term)
                    )
                )

        # Order by: pinned first, then by updated_at desc
        return query.order_by(
            desc(Note.is_pinned),
            desc(Note.updated_at)
        ).offset(skip).limit(limit).all()

    def update_note(self, note_id: int, business_id: int, note_data: NoteUpdate, updated_by: int) -> Optional[Note]:
        """Update note"""
        note = self.get_note_by_id(note_id, business_id)
        if not note:
            return None

        update_data = note_data.dict(exclude_unset=True)
        
        # Handle tags conversion
        if 'tags' in update_data:
            update_data['tags'] = json.dumps(update_data['tags']) if update_data['tags'] else None
        
        # Set updated_by
        update_data['updated_by'] = updated_by
        update_data['updated_at'] = datetime.utcnow()

        for field, value in update_data.items():
            setattr(note, field, value)

        self.db.commit()
        self.db.refresh(note)
        return note

    def delete_note(self, note_id: int, business_id: int) -> bool:
        """Delete note"""
        note = self.get_note_by_id(note_id, business_id)
        if not note:
            return False

        self.db.delete(note)
        self.db.commit()
        return True

    def search_notes(self, business_id: int, search_query: str, user_id: Optional[int] = None,
                    skip: int = 0, limit: int = 50) -> Tuple[List[Note], int]:
        """Search notes with full-text search"""
        base_query = self.db.query(Note).filter(Note.business_id == business_id)
        
        # Apply user-specific filtering
        if user_id:
            shared_note_ids = self.db.query(NoteShare.note_id).filter(
                NoteShare.shared_with_user_id == user_id
            ).subquery()
            
            base_query = base_query.filter(
                or_(
                    Note.created_by == user_id,
                    Note.id.in_(shared_note_ids)
                )
            )

        # Search in title, content, and tags
        search_term = f"%{search_query}%"
        search_filter = or_(
            Note.title.ilike(search_term),
            Note.content.ilike(search_term),
            Note.tags.ilike(search_term)
        )
        
        # Get total count
        total_count = base_query.filter(search_filter).count()
        
        # Get results with relevance scoring (simple implementation)
        results = base_query.filter(search_filter).options(
            joinedload(Note.creator)
        ).order_by(
            # Title matches first, then content matches
            desc(Note.title.ilike(search_term)),
            desc(Note.updated_at)
        ).offset(skip).limit(limit).all()
        
        return results, total_count

    def get_notes_analytics(self, business_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get notes analytics"""
        base_query = self.db.query(Note).filter(Note.business_id == business_id)
        
        # Apply user-specific filtering
        if user_id:
            shared_note_ids = self.db.query(NoteShare.note_id).filter(
                NoteShare.shared_with_user_id == user_id
            ).subquery()
            
            base_query = base_query.filter(
                or_(
                    Note.created_by == user_id,
                    Note.id.in_(shared_note_ids)
                )
            )

        # Basic counts
        total_notes = base_query.count()
        pinned_notes = base_query.filter(Note.is_pinned == True).count()
        archived_notes = base_query.filter(Note.is_archived == True).count()
        favorite_notes = base_query.filter(Note.is_favorite == True).count()
        shared_notes = base_query.filter(Note.is_shared == True).count()
        notes_with_reminders = base_query.filter(Note.reminder_date.isnot(None)).count()
        
        # Overdue reminders
        overdue_reminders = base_query.filter(
            and_(
                Note.reminder_date.isnot(None),
                Note.reminder_date < datetime.utcnow()
            )
        ).count()

        # Notes by category
        category_counts = {}
        for category in NoteCategory:
            count = base_query.filter(Note.category == category).count()
            category_counts[category.value] = count

        # Notes by priority
        priority_counts = {}
        for priority in NotePriority:
            count = base_query.filter(Note.priority == priority).count()
            priority_counts[priority.value] = count

        # Time-based counts
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        notes_created_today = base_query.filter(
            func.date(Note.created_at) == today
        ).count()
        
        notes_created_this_week = base_query.filter(
            func.date(Note.created_at) >= week_ago
        ).count()
        
        notes_created_this_month = base_query.filter(
            func.date(Note.created_at) >= month_ago
        ).count()

        # Most used tags (simplified - would need better implementation for production)
        most_used_tags = []
        notes_with_tags = base_query.filter(Note.tags.isnot(None)).all()
        tag_counts = {}
        
        for note in notes_with_tags:
            if note.tags:
                try:
                    tags = json.loads(note.tags)
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except:
                    pass
        
        # Sort tags by count and take top 10
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_used_tags = [{"tag": tag, "count": count} for tag, count in sorted_tags]

        return {
            "total_notes": total_notes,
            "notes_by_category": category_counts,
            "notes_by_priority": priority_counts,
            "pinned_notes": pinned_notes,
            "archived_notes": archived_notes,
            "favorite_notes": favorite_notes,
            "shared_notes": shared_notes,
            "notes_with_reminders": notes_with_reminders,
            "overdue_reminders": overdue_reminders,
            "notes_created_today": notes_created_today,
            "notes_created_this_week": notes_created_this_week,
            "notes_created_this_month": notes_created_this_month,
            "most_used_tags": most_used_tags,
            "recent_activity": []  # Would implement with activity tracking
        }

    def bulk_update_notes(self, note_ids: List[int], business_id: int, 
                         bulk_data: NoteBulkUpdate, updated_by: int) -> int:
        """Bulk update notes"""
        query = self.db.query(Note).filter(
            Note.id.in_(note_ids),
            Note.business_id == business_id
        )
        
        update_data = bulk_data.dict(exclude_unset=True, exclude={'note_ids'})
        
        # Handle tags conversion
        if 'tags' in update_data:
            update_data['tags'] = json.dumps(update_data['tags']) if update_data['tags'] else None
        
        # Set updated fields
        update_data['updated_by'] = updated_by
        update_data['updated_at'] = datetime.utcnow()
        
        updated_count = query.update(update_data, synchronize_session=False)
        self.db.commit()
        
        return updated_count

    def bulk_action_notes(self, note_ids: List[int], business_id: int, 
                         action: str, updated_by: int) -> int:
        """Perform bulk actions on notes"""
        query = self.db.query(Note).filter(
            Note.id.in_(note_ids),
            Note.business_id == business_id
        )
        
        update_data = {
            'updated_by': updated_by,
            'updated_at': datetime.utcnow()
        }
        
        if action == "archive":
            update_data['is_archived'] = True
        elif action == "unarchive":
            update_data['is_archived'] = False
        elif action == "pin":
            update_data['is_pinned'] = True
        elif action == "unpin":
            update_data['is_pinned'] = False
        elif action == "favorite":
            update_data['is_favorite'] = True
        elif action == "unfavorite":
            update_data['is_favorite'] = False
        elif action == "delete":
            # For delete, we actually delete the records
            deleted_count = query.delete(synchronize_session=False)
            self.db.commit()
            return deleted_count
        
        updated_count = query.update(update_data, synchronize_session=False)
        self.db.commit()
        
        return updated_count


class NoteShareRepository:
    """Repository for note sharing operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_share(self, share_data: Dict[str, Any]) -> NoteShare:
        """Create a new note share"""
        share = NoteShare(**share_data)
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        return share

    def get_note_shares(self, note_id: int) -> List[NoteShare]:
        """Get all shares for a note"""
        return self.db.query(NoteShare).options(
            joinedload(NoteShare.shared_with_user),
            joinedload(NoteShare.shared_with_employee),
            joinedload(NoteShare.sharer)
        ).filter(NoteShare.note_id == note_id).all()

    def delete_share(self, share_id: int) -> bool:
        """Delete a note share"""
        share = self.db.query(NoteShare).filter(NoteShare.id == share_id).first()
        if not share:
            return False
        
        self.db.delete(share)
        self.db.commit()
        return True


class NoteAttachmentRepository:
    """Repository for note attachment operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_attachment(self, attachment_data: Dict[str, Any]) -> NoteAttachment:
        """Create a new note attachment"""
        attachment = NoteAttachment(**attachment_data)
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def get_note_attachments(self, note_id: int) -> List[NoteAttachment]:
        """Get all attachments for a note"""
        return self.db.query(NoteAttachment).options(
            joinedload(NoteAttachment.uploader)
        ).filter(NoteAttachment.note_id == note_id).all()

    def delete_attachment(self, attachment_id: int) -> bool:
        """Delete a note attachment"""
        attachment = self.db.query(NoteAttachment).filter(NoteAttachment.id == attachment_id).first()
        if not attachment:
            return False
        
        self.db.delete(attachment)
        self.db.commit()
        return True