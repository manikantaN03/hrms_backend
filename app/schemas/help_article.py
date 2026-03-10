"""
Help Article Schemas
Pydantic schemas for help article validation
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ArticleCategory(str, Enum):
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


class ArticleType(str, Enum):
    """Help article type enumeration"""
    GUIDE = "GUIDE"
    FAQ = "FAQ"
    VIDEO = "VIDEO"
    QUICK_TIP = "QUICK_TIP"
    TUTORIAL = "TUTORIAL"


class HelpArticleBase(BaseModel):
    """Base help article schema"""
    title: str = Field(..., min_length=5, max_length=255, description="Article title")
    category: ArticleCategory = Field(..., description="Article category")
    article_type: ArticleType = Field(..., description="Article type")
    summary: str = Field(..., min_length=10, max_length=500, description="Article summary")
    content: str = Field(..., min_length=20, description="Article content")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Thumbnail URL")
    video_url: Optional[str] = Field(None, max_length=500, description="Video URL")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    is_published: bool = Field(True, description="Publication status")
    is_featured: bool = Field(False, description="Featured status")
    meta_description: Optional[str] = Field(None, max_length=500, description="Meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="Meta keywords")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()


class HelpArticleCreate(HelpArticleBase):
    """Schema for creating a help article"""
    pass


class HelpArticleUpdate(BaseModel):
    """Schema for updating a help article"""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    category: Optional[ArticleCategory] = None
    article_type: Optional[ArticleType] = None
    summary: Optional[str] = Field(None, min_length=10, max_length=500)
    content: Optional[str] = Field(None, min_length=20)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    tags: Optional[str] = Field(None, max_length=500)
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)


class HelpArticleResponse(HelpArticleBase):
    """Schema for help article response"""
    id: int
    business_id: int
    slug: str
    views: int
    helpful_count: int
    not_helpful_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class HelpArticleListResponse(BaseModel):
    """Schema for help article list response"""
    articles: List[HelpArticleResponse]
    total: int
    page: int
    size: int
    total_pages: int


class ArticleFeedback(BaseModel):
    """Schema for article feedback"""
    helpful: bool = Field(..., description="Whether the article was helpful")


class ArticleSearchRequest(BaseModel):
    """Schema for article search"""
    query: str = Field(..., min_length=2, max_length=200, description="Search query")
    category: Optional[ArticleCategory] = None
    article_type: Optional[ArticleType] = None
