"""
Help Article Model
Model for HRMS help documentation and guides
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel


class ArticleCategory(PyEnum):
    """Help article category enumeration"""
    GETTING_STARTED = "GETTING_STARTED"
    ATTENDANCE = "ATTENDANCE"
    LEAVE_MANAGEMENT = "LEAVE_MANAGEMENT"
    PAYROLL = "PAYROLL"
    EMPLOYEE_MANAGEMENT = "EMPLOYEE_MANAGEMENT"
    REPORTS = "REPORTS"
    SETTINGS = "SETTINGS"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    FAQ = "FAQ"
    VIDEO_TUTORIAL = "VIDEO_TUTORIAL"


class ArticleType(PyEnum):
    """Help article type enumeration"""
    GUIDE = "GUIDE"
    FAQ = "FAQ"
    VIDEO = "VIDEO"
    QUICK_TIP = "QUICK_TIP"
    TUTORIAL = "TUTORIAL"


class HelpArticle(BaseModel):
    """Help article model for HRMS documentation"""
    __tablename__ = "help_articles"

    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    
    # Article Details
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(SQLEnum(ArticleCategory, name='articlecategory', create_type=False), nullable=False, index=True)
    article_type = Column(SQLEnum(ArticleType, name='articletype', create_type=False), nullable=False)
    
    # Content
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    
    # Media
    thumbnail_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    
    # Metadata
    tags = Column(Text, nullable=True)  # Comma-separated tags
    views = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    
    # Status
    is_published = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # SEO
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    
    # Relationships
    business = relationship("Business")
