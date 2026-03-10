"""
Subscription Endpoints
API endpoints for subscription management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_db
from app.api.v1.deps import get_current_superadmin
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse,
    SubscriptionSummary,
    SubscriptionPlanResponse
)
from app.services.subscription_service import SubscriptionService, SubscriptionPlanService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SUPERADMIN SUBSCRIPTION MANAGEMENT
# ============================================================================

@router.get("/", response_model=List[SubscriptionListResponse])
def get_all_subscriptions(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records"),
    status: Optional[str] = Query(None, description="Filter by status"),
    plan: Optional[str] = Query(None, description="Filter by plan"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Get all subscriptions for superadmin dashboard.
    
    Returns subscriptions in the format expected by frontend:
    - id, name, plan, cycle, payment, amount, paymentId, created, expiring, status
    """
    try:
        service = SubscriptionService(db)
        
        if search:
            subscriptions = service.search_subscriptions(
                search_term=search,
                skip=skip,
                limit=limit
            )
        else:
            subscriptions = service.get_all_subscriptions(
                skip=skip,
                limit=limit,
                status_filter=status,
                plan_filter=plan
            )
        
        logger.info(f"User {current_user.email} retrieved {len(subscriptions)} subscriptions")
        return subscriptions
        
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscriptions: {str(e)}"
        )


@router.get("/summary", response_model=SubscriptionSummary)
def get_subscription_summary(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get subscription statistics summary for dashboard.
    """
    try:
        service = SubscriptionService(db)
        stats = service.get_subscription_stats()
        
        summary = SubscriptionSummary(
            total_subscriptions=stats["total_subscriptions"],
            active_subscriptions=stats["active_subscriptions"],
            expired_subscriptions=stats["expired_subscriptions"],
            total_revenue=stats["total_revenue"],
            monthly_revenue=stats["monthly_revenue"],
            yearly_revenue=stats["yearly_revenue"]
        )
        
        logger.info(f"Subscription summary retrieved by {superadmin.email}")
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching subscription summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscription summary: {str(e)}"
        )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get subscription details by ID.
    """
    try:
        service = SubscriptionService(db)
        subscription = service.get_subscription_by_id(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        logger.info(f"Subscription {subscription_id} retrieved by {superadmin.email}")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subscription {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscription: {str(e)}"
        )


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Create a new subscription.
    """
    try:
        service = SubscriptionService(db)
        subscription = service.create_subscription(
            subscription_data=subscription_data,
            user_id=superadmin.id
        )
        
        logger.info(f"Subscription created by {superadmin.email}: {subscription.id}")
        return subscription
        
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating subscription: {str(e)}"
        )


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Update an existing subscription.
    """
    try:
        service = SubscriptionService(db)
        subscription = service.update_subscription(subscription_id, update_data)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        logger.info(f"Subscription {subscription_id} updated by {superadmin.email}")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating subscription: {str(e)}"
        )


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Delete a subscription.
    """
    try:
        service = SubscriptionService(db)
        success = service.delete_subscription(subscription_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        logger.info(f"Subscription {subscription_id} deleted by {superadmin.email}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting subscription: {str(e)}"
        )


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Cancel a subscription.
    """
    try:
        service = SubscriptionService(db)
        subscription = service.cancel_subscription(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        logger.info(f"Subscription {subscription_id} cancelled by {superadmin.email}")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling subscription: {str(e)}"
        )


@router.patch("/{subscription_id}/renew", response_model=SubscriptionResponse)
def renew_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Renew a subscription for another billing cycle.
    """
    try:
        service = SubscriptionService(db)
        subscription = service.renew_subscription(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        logger.info(f"Subscription {subscription_id} renewed by {superadmin.email}")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renewing subscription {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error renewing subscription: {str(e)}"
        )


# ============================================================================
# SUBSCRIPTION ANALYTICS
# ============================================================================

@router.get("/analytics/revenue", response_model=List[Dict[str, Any]])
def get_revenue_analytics(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get revenue analytics by plan.
    """
    try:
        service = SubscriptionService(db)
        revenue_data = service.get_revenue_by_plan()
        
        analytics = []
        for plan_name, count, revenue in revenue_data:
            analytics.append({
                "plan": plan_name,
                "subscriptions": count,
                "revenue": float(revenue or 0)
            })
        
        logger.info(f"Revenue analytics retrieved by {superadmin.email}")
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching revenue analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching revenue analytics: {str(e)}"
        )


@router.get("/analytics/expiring", response_model=List[SubscriptionResponse])
def get_expiring_subscriptions(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get subscriptions expiring within specified days.
    """
    try:
        service = SubscriptionService(db)
        expiring_subscriptions = service.get_expiring_subscriptions(days)
        
        logger.info(f"Expiring subscriptions retrieved by {superadmin.email}: {len(expiring_subscriptions)} found")
        return expiring_subscriptions
        
    except Exception as e:
        logger.error(f"Error fetching expiring subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching expiring subscriptions: {str(e)}"
        )


# ============================================================================
# SUBSCRIPTION PLANS MANAGEMENT
# ============================================================================

@router.get("/plans/", response_model=List[SubscriptionPlanResponse])
def get_subscription_plans(
    active_only: bool = Query(True, description="Show only active plans"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get all subscription plans (ADMIN).
    """
    try:
        plan_service = SubscriptionPlanService(db)
        
        if active_only:
            plans = plan_service.get_active_plans()
        else:
            # Get all plans (would need to implement in service)
            plans = plan_service.get_active_plans()  # For now, just return active
        
        logger.info(f"Subscription plans retrieved by {superadmin.email}: {len(plans)} plans")
        return plans
        
    except Exception as e:
        logger.error(f"Error fetching subscription plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscription plans: {str(e)}"
        )


@router.get("/public/plans/", response_model=List[SubscriptionPlanResponse])
def get_public_subscription_plans(
    db: Session = Depends(get_db)
):
    """
    Get all active subscription plans (PUBLIC - No Auth Required).
    This endpoint is for displaying pricing on the public website.
    """
    try:
        plan_service = SubscriptionPlanService(db)
        plans = plan_service.get_active_plans()
        
        logger.info(f"Public subscription plans retrieved: {len(plans)} plans")
        return plans
        
    except Exception as e:
        logger.error(f"Error fetching public subscription plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscription plans: {str(e)}"
        )


# ============================================================================
# MAINTENANCE OPERATIONS
# ============================================================================

@router.post("/maintenance/process-expired", response_model=Dict[str, Any])
def process_expired_subscriptions(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Process expired subscriptions and update their status.
    """
    try:
        service = SubscriptionService(db)
        count = service.process_expired_subscriptions()
        
        logger.info(f"Expired subscriptions processed by {superadmin.email}: {count} updated")
        return {
            "message": f"Processed {count} expired subscriptions",
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Error processing expired subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing expired subscriptions: {str(e)}"
        )