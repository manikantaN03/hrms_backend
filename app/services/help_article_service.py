"""
Help Article Service
Business logic for help articles
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional, Tuple

from app.repositories.help_article_repository import (
    create_help_article,
    get_help_articles,
    get_help_article_by_id,
    get_help_article_by_slug,
    update_help_article,
    delete_help_article,
    increment_article_views,
    record_article_feedback,
    search_help_articles
)
from app.schemas.help_article import (
    HelpArticleCreate,
    HelpArticleUpdate,
    ArticleFeedback
)
from app.models.help_article import HelpArticle


def create_article_service(
    db: Session,
    article_data: HelpArticleCreate,
    business_id: int
) -> HelpArticle:
    """Create a new help article"""
    try:
        return create_help_article(db, article_data, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create help article: {str(e)}"
        )


def get_articles_service(
    db: Session,
    business_id: int,
    category: Optional[str] = None,
    article_type: Optional[str] = None,
    is_published: bool = True,
    is_featured: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[HelpArticle], int]:
    """Get help articles with filters"""
    return get_help_articles(db, business_id, category, article_type, is_published, is_featured, skip, limit)


def get_article_service(db: Session, article_id: int, business_id: int, increment_views: bool = True) -> HelpArticle:
    """Get a help article by ID"""
    article = get_help_article_by_id(db, article_id, business_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    
    if increment_views:
        increment_article_views(db, article_id, business_id)
    
    return article


def get_article_by_slug_service(db: Session, slug: str, business_id: int, increment_views: bool = True) -> HelpArticle:
    """Get a help article by slug"""
    article = get_help_article_by_slug(db, slug, business_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    
    if increment_views and article:
        increment_article_views(db, article.id, business_id)
    
    return article


def update_article_service(
    db: Session,
    article_id: int,
    business_id: int,
    update_data: HelpArticleUpdate
) -> HelpArticle:
    """Update a help article"""
    article = update_help_article(db, article_id, business_id, update_data)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    return article


def delete_article_service(db: Session, article_id: int, business_id: int) -> bool:
    """Delete a help article"""
    deleted = delete_help_article(db, article_id, business_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    return True


def feedback_article_service(
    db: Session,
    article_id: int,
    business_id: int,
    feedback: ArticleFeedback
) -> bool:
    """Record article feedback"""
    success = record_article_feedback(db, article_id, business_id, feedback.helpful)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    return True


def search_articles_service(
    db: Session,
    business_id: int,
    query: str,
    category: Optional[str] = None,
    article_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[HelpArticle], int]:
    """Search help articles"""
    return search_help_articles(db, business_id, query, category, article_type, skip, limit)
