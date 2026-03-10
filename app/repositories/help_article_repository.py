"""
Help Article Repository
Database operations for help articles
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.help_article import HelpArticle, ArticleCategory, ArticleType
from app.schemas.help_article import HelpArticleCreate, HelpArticleUpdate
import re


def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug[:255]


def create_help_article(db: Session, article_data: HelpArticleCreate, business_id: int) -> HelpArticle:
    """Create a new help article"""
    slug = create_slug(article_data.title)
    
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while db.query(HelpArticle).filter(HelpArticle.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    new_article = HelpArticle(
        business_id=business_id,
        title=article_data.title,
        slug=slug,
        category=article_data.category.value,
        article_type=article_data.article_type.value,
        summary=article_data.summary,
        content=article_data.content,
        thumbnail_url=article_data.thumbnail_url,
        video_url=article_data.video_url,
        tags=article_data.tags,
        is_published=article_data.is_published,
        is_featured=article_data.is_featured,
        meta_description=article_data.meta_description,
        meta_keywords=article_data.meta_keywords
    )
    
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return new_article


def get_help_articles(
    db: Session,
    business_id: int,
    category: Optional[str] = None,
    article_type: Optional[str] = None,
    is_published: bool = True,
    is_featured: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[HelpArticle], int]:
    """Get help articles with filters and pagination"""
    query = db.query(HelpArticle).filter(HelpArticle.business_id == business_id)
    
    if is_published is not None:
        query = query.filter(HelpArticle.is_published == is_published)
    
    if is_featured is not None:
        query = query.filter(HelpArticle.is_featured == is_featured)
    
    if category:
        try:
            category_enum = ArticleCategory(category)
            query = query.filter(HelpArticle.category == category_enum.value)
        except ValueError:
            pass
    
    if article_type:
        try:
            type_enum = ArticleType(article_type)
            query = query.filter(HelpArticle.article_type == type_enum.value)
        except ValueError:
            pass
    
    total = query.count()
    articles = query.order_by(desc(HelpArticle.is_featured), desc(HelpArticle.created_at)).offset(skip).limit(limit).all()
    
    return articles, total


def get_help_article_by_id(db: Session, article_id: int, business_id: int) -> Optional[HelpArticle]:
    """Get a help article by ID"""
    return db.query(HelpArticle).filter(
        HelpArticle.id == article_id,
        HelpArticle.business_id == business_id
    ).first()


def get_help_article_by_slug(db: Session, slug: str, business_id: int) -> Optional[HelpArticle]:
    """Get a help article by slug"""
    return db.query(HelpArticle).filter(
        HelpArticle.slug == slug,
        HelpArticle.business_id == business_id
    ).first()


def update_help_article(
    db: Session,
    article_id: int,
    business_id: int,
    update_data: HelpArticleUpdate
) -> Optional[HelpArticle]:
    """Update a help article"""
    article = db.query(HelpArticle).filter(
        HelpArticle.id == article_id,
        HelpArticle.business_id == business_id
    ).first()
    
    if not article:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Update slug if title changed
    if 'title' in update_dict:
        update_dict['slug'] = create_slug(update_dict['title'])
    
    # Convert enums to values
    if 'category' in update_dict and update_dict['category']:
        update_dict['category'] = update_dict['category'].value
    if 'article_type' in update_dict and update_dict['article_type']:
        update_dict['article_type'] = update_dict['article_type'].value
    
    for field, value in update_dict.items():
        setattr(article, field, value)
    
    article.updated_at = datetime.now()
    
    db.commit()
    db.refresh(article)
    return article


def delete_help_article(db: Session, article_id: int, business_id: int) -> bool:
    """Delete a help article"""
    article = db.query(HelpArticle).filter(
        HelpArticle.id == article_id,
        HelpArticle.business_id == business_id
    ).first()
    
    if not article:
        return False
    
    db.delete(article)
    db.commit()
    return True


def increment_article_views(db: Session, article_id: int, business_id: int) -> bool:
    """Increment article view count"""
    article = db.query(HelpArticle).filter(
        HelpArticle.id == article_id,
        HelpArticle.business_id == business_id
    ).first()
    
    if not article:
        return False
    
    article.views += 1
    db.commit()
    return True


def record_article_feedback(db: Session, article_id: int, business_id: int, helpful: bool) -> bool:
    """Record article feedback"""
    article = db.query(HelpArticle).filter(
        HelpArticle.id == article_id,
        HelpArticle.business_id == business_id
    ).first()
    
    if not article:
        return False
    
    if helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1
    
    db.commit()
    return True


def search_help_articles(
    db: Session,
    business_id: int,
    query: str,
    category: Optional[str] = None,
    article_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[HelpArticle], int]:
    """Search help articles"""
    search_query = db.query(HelpArticle).filter(
        HelpArticle.business_id == business_id,
        HelpArticle.is_published == True,
        or_(
            HelpArticle.title.ilike(f"%{query}%"),
            HelpArticle.summary.ilike(f"%{query}%"),
            HelpArticle.content.ilike(f"%{query}%"),
            HelpArticle.tags.ilike(f"%{query}%")
        )
    )
    
    if category:
        try:
            category_enum = ArticleCategory(category)
            search_query = search_query.filter(HelpArticle.category == category_enum.value)
        except ValueError:
            pass
    
    if article_type:
        try:
            type_enum = ArticleType(article_type)
            search_query = search_query.filter(HelpArticle.article_type == type_enum.value)
        except ValueError:
            pass
    
    total = search_query.count()
    articles = search_query.order_by(desc(HelpArticle.views)).offset(skip).limit(limit).all()
    
    return articles, total
