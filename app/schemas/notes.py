"""
Notes Schemas
Pydantic models for Notes API validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class NoteCategory(str, Enum):
    """Note category enumeration"""
    GENERAL = "general"
    MEETING = "meeting"
    IDEA = "idea"
    REMINDER = "reminder"
    TASK = "task"
    PERSONAL = "personal"
    WORK = "work"
    PROJECT = "project"


class NotePriority(str, Enum):
    """Note priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Base Schemas
class NoteBase(BaseModel):
    """Base note schema"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    category: NoteCategory = NoteCategory.GENERAL
    priority: NotePriority = NotePriority.MEDIUM
    tags: Optional[List[str]] = Field(None, max_items=20)
    is_pinned: bool = False
    is_archived: bool = False
    is_favorite: bool = False
    is_shared: bool = False
    color: Optional[str] = Field("#ffffff", pattern=r"^#[0-9A-Fa-f]{6}$")
    reminder_date: Optional[datetime] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Ensure each tag is not empty and not too long
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tags cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Each tag must be 50 characters or less')
        return v


class NoteCreate(NoteBase):
    """Schema for creating notes"""
    business_id: Optional[int] = None  # Will be set from current user


class NoteUpdate(BaseModel):
    """Schema for updating notes"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    category: Optional[NoteCategory] = None
    priority: Optional[NotePriority] = None
    tags: Optional[List[str]] = Field(None, max_items=20)
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_shared: Optional[bool] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    reminder_date: Optional[datetime] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tags cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Each tag must be 50 characters or less')
        return v


class NoteResponse(BaseModel):
    """Schema for note response"""
    id: int
    business_id: int
    title: str
    content: str
    category: NoteCategory
    priority: NotePriority
    tags: Optional[List[str]] = None
    is_pinned: bool
    is_archived: bool
    is_favorite: bool
    is_shared: bool
    color: Optional[str] = None
    reminder_date: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None
    creator_name: str
    updater_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    share_count: int = 0
    attachment_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class NoteSummary(BaseModel):
    """Schema for note summary (list view)"""
    id: int
    title: str
    content_preview: str  # First 100 characters
    category: NoteCategory
    priority: NotePriority
    tags: Optional[List[str]] = None
    is_pinned: bool
    is_archived: bool
    is_favorite: bool
    is_shared: bool
    color: Optional[str] = None
    reminder_date: Optional[datetime] = None
    creator_name: str
    created_at: datetime
    updated_at: datetime
    share_count: int = 0
    attachment_count: int = 0
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)


# Note Share Schemas
class NoteShareBase(BaseModel):
    """Base note share schema"""
    can_edit: bool = False
    can_delete: bool = False


class NoteShareCreate(NoteShareBase):
    """Schema for creating note shares"""
    note_id: int
    shared_with_user_id: Optional[int] = None
    shared_with_employee_id: Optional[int] = None

    @validator('shared_with_employee_id')
    def validate_share_target(cls, v, values):
        user_id = values.get('shared_with_user_id')
        if not user_id and not v:
            raise ValueError('Either shared_with_user_id or shared_with_employee_id must be provided')
        return v


class NoteShareUpdate(BaseModel):
    """Schema for updating note shares"""
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None


class NoteShareResponse(BaseModel):
    """Schema for note share response"""
    id: int
    note_id: int
    shared_with_user_id: Optional[int] = None
    shared_with_employee_id: Optional[int] = None
    can_edit: bool
    can_delete: bool
    shared_by: int
    shared_at: datetime
    shared_with_name: str
    shared_by_name: str

    model_config = ConfigDict(from_attributes=True)


# Note Attachment Schemas
class NoteAttachmentResponse(BaseModel):
    """Schema for note attachment response"""
    id: int
    note_id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_by: int
    uploader_name: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Filter Schemas
class NoteFilters(BaseModel):
    """Schema for note filters"""
    category: Optional[List[NoteCategory]] = None
    priority: Optional[List[NotePriority]] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_shared: Optional[bool] = None
    has_reminder: Optional[bool] = None
    is_overdue: Optional[bool] = None
    created_by: Optional[int] = None
    created_date_from: Optional[date] = None
    created_date_to: Optional[date] = None
    updated_date_from: Optional[date] = None
    updated_date_to: Optional[date] = None
    search: Optional[str] = Field(None, max_length=255)


# Analytics Schemas
class NotesAnalytics(BaseModel):
    """Schema for notes analytics"""
    total_notes: int
    notes_by_category: Dict[str, int]
    notes_by_priority: Dict[str, int]
    pinned_notes: int
    archived_notes: int
    favorite_notes: int
    shared_notes: int
    notes_with_reminders: int
    overdue_reminders: int
    notes_created_today: int
    notes_created_this_week: int
    notes_created_this_month: int
    most_used_tags: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


# Bulk Operations Schemas
class NoteBulkAction(BaseModel):
    """Schema for bulk note actions"""
    note_ids: List[int] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern=r"^(archive|unarchive|pin|unpin|favorite|unfavorite|delete)$")


class NoteBulkUpdate(BaseModel):
    """Schema for bulk note updates"""
    note_ids: List[int] = Field(..., min_items=1, max_items=100)
    category: Optional[NoteCategory] = None
    priority: Optional[NotePriority] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


# Search Schemas
class NoteSearchResult(BaseModel):
    """Schema for note search results"""
    id: int
    title: str
    content_highlight: str  # Content with search terms highlighted
    category: NoteCategory
    priority: NotePriority
    tags: Optional[List[str]] = None
    creator_name: str
    created_at: datetime
    updated_at: datetime
    relevance_score: float

    model_config = ConfigDict(from_attributes=True)


class NoteSearchResponse(BaseModel):
    """Schema for note search response"""
    results: List[NoteSearchResult]
    total_count: int
    search_query: str
    search_time_ms: float
    suggestions: List[str] = []