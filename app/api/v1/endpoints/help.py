"""
Help API Endpoints
HRMS help articles and documentation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from math import ceil

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.utils.business_unit_utils import get_business_context
from app.models.user import User
from app.models.business import Business
from app.schemas.help_article import (
    HelpArticleCreate,
    HelpArticleUpdate,
    HelpArticleResponse,
    HelpArticleListResponse,
    ArticleFeedback
)
from app.services.help_article_service import (
    create_article_service,
    get_articles_service,
    get_article_service,
    get_article_by_slug_service,
    update_article_service,
    delete_article_service,
    feedback_article_service,
    search_articles_service
)

router = APIRouter()


# ============================================================================
# Help Articles Endpoints
# ============================================================================

@router.get("/articles", response_model=HelpArticleListResponse)
async def get_help_articles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    article_type: Optional[str] = None,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all help articles with pagination and filtering
    
    **Filters:**
    - category: Filter by article category
    - article_type: Filter by article type (GUIDE, FAQ, VIDEO, etc.)
    - is_featured: Filter featured articles
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    
    **Returns:**
    - List of help articles with pagination info
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        # For superadmin without business_id, get first business
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if not first_business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No business found in the system"
                )
            business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Calculate pagination
        skip = (page - 1) * size
        
        # Get articles
        articles, total = get_articles_service(
            db, business_id, category, article_type, True, is_featured, skip, size
        )
        
        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 0
        
        return HelpArticleListResponse(
            articles=[HelpArticleResponse.model_validate(article) for article in articles],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch help articles: {str(e)}"
        )


@router.post("/articles", response_model=HelpArticleResponse)
async def create_help_article(
    article_data: HelpArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new help article
    
    **Requires:** Admin or Superadmin role
    
    **Request Body:**
    - title: Article title (5-255 characters)
    - category: Article category
    - article_type: Article type (GUIDE, FAQ, VIDEO, etc.)
    - summary: Brief summary (10-500 characters)
    - content: Full article content (min 20 characters)
    - thumbnail_url: Optional thumbnail image URL
    - video_url: Optional video URL
    - tags: Optional comma-separated tags
    - is_published: Publication status (default: true)
    - is_featured: Featured status (default: false)
    
    **Returns:**
    - Created help article with ID and slug
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if not first_business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No business found in the system"
                )
            business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Create article
        new_article = create_article_service(db, article_data, business_id)
        
        return HelpArticleResponse.model_validate(new_article)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create help article: {str(e)}"
        )


@router.get("/articles/search", response_model=HelpArticleListResponse)
async def search_help_articles(
    q: str = Query(..., min_length=2, max_length=200),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    article_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search help articles
    
    **Parameters:**
    - q: Search query (min 2 characters)
    - category: Optional category filter
    - article_type: Optional type filter
    - page: Page number
    - size: Items per page
    
    **Returns:**
    - List of matching articles with pagination
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if first_business:
                business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Calculate pagination
        skip = (page - 1) * size
        
        # Search articles
        articles, total = search_articles_service(
            db, business_id, q, category, article_type, skip, size
        )
        
        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 0
        
        return HelpArticleListResponse(
            articles=[HelpArticleResponse.model_validate(article) for article in articles],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search help articles: {str(e)}"
        )


@router.get("/articles/{article_id}", response_model=HelpArticleResponse)
async def get_help_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a help article by ID
    
    **Returns:**
    - Complete help article details
    - Increments view count
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if first_business:
                business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Get article
        article = get_article_service(db, article_id, business_id, increment_views=True)
        
        return HelpArticleResponse.model_validate(article)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch help article: {str(e)}"
        )


@router.put("/articles/{article_id}", response_model=HelpArticleResponse)
async def update_help_article(
    article_id: int,
    article_data: HelpArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update a help article
    
    **Requires:** Admin or Superadmin role
    
    **Returns:**
    - Updated help article
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if first_business:
                business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Update article
        article = update_article_service(db, article_id, business_id, article_data)
        
        return HelpArticleResponse.model_validate(article)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update help article: {str(e)}"
        )


@router.delete("/articles/{article_id}")
async def delete_help_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a help article
    
    **Requires:** Admin or Superadmin role
    
    **Returns:**
    - Success message
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if first_business:
                business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Delete article
        delete_article_service(db, article_id, business_id)
        
        return {"message": "Help article deleted successfully"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete help article: {str(e)}"
        )


@router.post("/articles/{article_id}/feedback")
async def submit_article_feedback(
    article_id: int,
    feedback: ArticleFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback for a help article
    
    **Request Body:**
    - helpful: Boolean indicating if article was helpful
    
    **Returns:**
    - Success message
    """
    try:
        # Get business context
        business_context = get_business_context(current_user)
        business_id = business_context.get('business_id')
        is_superadmin = business_context.get('is_superadmin', False)
        
        if not business_id and is_superadmin:
            first_business = db.query(Business).first()
            if first_business:
                business_id = first_business.id
        
        if not business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID is required"
            )
        
        # Record feedback
        feedback_article_service(db, article_id, business_id, feedback)
        
        return {"message": "Feedback recorded successfully"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )
