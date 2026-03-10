"""
Notes Models
Database models for Notes Management System
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from app.models.base import Base


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


class Note(Base):
    """Note model for notes management"""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    
    # Basic note information
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Categorization and organization
    category = Column(SQLEnum(NoteCategory, native_enum=False), nullable=False, default=NoteCategory.GENERAL)
    priority = Column(SQLEnum(NotePriority, native_enum=False), nullable=False, default=NotePriority.MEDIUM)
    tags = Column(Text, nullable=True)  # JSON string of tags array
    
    # Status flags
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    color = Column(String(7), nullable=True, default="#ffffff")  # Hex color code
    reminder_date = Column(DateTime, nullable=True)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="notes")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    shared_notes = relationship("NoteShare", back_populates="note", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}', category='{self.category}')>"


class NoteShare(Base):
    """Note sharing model for collaborative notes"""
    __tablename__ = "note_shares"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    shared_with_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    
    # Permissions
    can_edit = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    note = relationship("Note", back_populates="shared_notes")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    shared_with_employee = relationship("Employee", foreign_keys=[shared_with_employee_id])
    sharer = relationship("User", foreign_keys=[shared_by])

    def __repr__(self):
        return f"<NoteShare(id={self.id}, note_id={self.note_id}, shared_with_user_id={self.shared_with_user_id})>"


class NoteAttachment(Base):
    """Note attachment model for file attachments"""
    __tablename__ = "note_attachments"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    
    # Audit fields
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    note = relationship("Note")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<NoteAttachment(id={self.id}, note_id={self.note_id}, filename='{self.filename}')>"