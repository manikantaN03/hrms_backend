"""
Subscription Service
Business logic for subscription management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import logging

from app.repositories.subscription_repository import (
    SubscriptionRepository,
    SubscriptionPaymentRepository,
    SubscriptionPlanRepository
)
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionListResponse
)
from app.models.subscription import Subscription, SubscriptionPayment, SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.subscription_repo = SubscriptionRepository(db)
        self.payment_repo = SubscriptionPaymentRepository(db)
        self.plan_repo = SubscriptionPlanRepository(db)
    
    # ========================================================================
    # Subscription Management
    # ========================================================================
    
    def create_subscription(
        self,
        subscription_data: SubscriptionCreate,
        user_id: int
    ) -> Subscription:
        """
        Create a new subscription.
        
        Args:
            subscription_data: Subscription creation data
            user_id: ID of the user creating the subscription
        
        Returns:
            Created subscription
        """
        # Generate unique payment ID
        payment_id = self._generate_payment_id()
        
        # Ensure payment ID is unique
        while self.subscription_repo.payment_id_exists(payment_id):
            payment_id = self._generate_payment_id()
        
        # Create subscription record
        subscription_dict = subscription_data.model_dump()
        subscription_dict.update({
            "user_id": user_id,
            "payment_id": payment_id,
            "status": "Active",
            "is_active": True
        })
        
        subscription = self.subscription_repo.create(subscription_dict)
        
        logger.info(f"Subscription created: {subscription.id} for business {subscription.business_id}")
        return subscription
    
    def update_subscription(
        self,
        subscription_id: int,
        update_data: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """Update an existing subscription."""
        subscription = self.subscription_repo.get(subscription_id)
        if not subscription:
            return None
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated_subscription = self.subscription_repo.update(subscription, update_dict)
        
        logger.info(f"Subscription updated: {subscription_id}")
        return updated_subscription
    
    def cancel_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Cancel a subscription."""
        subscription = self.subscription_repo.get(subscription_id)
        if not subscription:
            return None
        
        updated_subscription = self.subscription_repo.update(subscription, {
            "status": "Cancelled",
            "is_active": False,
            "auto_renew": False
        })
        
        logger.info(f"Subscription cancelled: {subscription_id}")
        return updated_subscription
    
    def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a subscription."""
        subscription = self.subscription_repo.get(subscription_id)
        if not subscription:
            return False
        
        self.subscription_repo.delete(subscription_id)
        logger.info(f"Subscription deleted: {subscription_id}")
        return True
    
    # ========================================================================
    # Subscription Retrieval
    # ========================================================================
    
    def get_all_subscriptions(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        plan_filter: Optional[str] = None
    ) -> List[SubscriptionListResponse]:
        """
        Get all subscriptions formatted for frontend.
        
        Returns subscriptions in the format expected by the frontend component.
        """
        subscriptions = self.subscription_repo.get_all_with_details(
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            plan_filter=plan_filter
        )
        
        return [self._format_subscription_for_frontend(sub) for sub in subscriptions]
    
    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID with related data."""
        return self.subscription_repo.get(subscription_id)
    
    def search_subscriptions(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[SubscriptionListResponse]:
        """Search subscriptions and format for frontend."""
        subscriptions = self.subscription_repo.search_subscriptions(
            search_term=search_term,
            skip=skip,
            limit=limit
        )
        
        return [self._format_subscription_for_frontend(sub) for sub in subscriptions]
    
    # ========================================================================
    # Dashboard and Analytics
    # ========================================================================
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics for dashboard."""
        return self.subscription_repo.get_subscription_stats()
    
    def get_expiring_subscriptions(self, days: int = 30) -> List[Subscription]:
        """Get subscriptions expiring within specified days."""
        return self.subscription_repo.get_expiring_subscriptions(days)
    
    def get_revenue_by_plan(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by plan."""
        return self.subscription_repo.get_revenue_by_plan()
    
    # ========================================================================
    # Subscription Renewal and Billing
    # ========================================================================
    
    def renew_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Renew a subscription for another billing cycle."""
        subscription = self.subscription_repo.get(subscription_id)
        if not subscription:
            return None
        
        # Calculate new end date based on plan type
        if subscription.plan_type.lower() == "monthly":
            new_end_date = subscription.end_date + timedelta(days=30)
            new_billing_date = new_end_date + timedelta(days=30)
        else:  # Yearly
            new_end_date = subscription.end_date + timedelta(days=365)
            new_billing_date = new_end_date + timedelta(days=365)
        
        updated_subscription = self.subscription_repo.update(subscription, {
            "end_date": new_end_date,
            "next_billing_date": new_billing_date,
            "status": "Active"
        })
        
        logger.info(f"Subscription renewed: {subscription_id} until {new_end_date}")
        return updated_subscription
    
    def process_expired_subscriptions(self) -> int:
        """Process expired subscriptions and update their status."""
        now = datetime.utcnow()
        
        # Get active subscriptions that have expired
        expired_subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.is_active == True,
                Subscription.end_date < now,
                Subscription.status == "Active"
            )
            .all()
        )
        
        count = 0
        for subscription in expired_subscriptions:
            self.subscription_repo.update(subscription, {
                "status": "Expired",
                "is_active": False
            })
            count += 1
        
        logger.info(f"Processed {count} expired subscriptions")
        return count
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _generate_payment_id(self) -> str:
        """Generate a unique payment ID."""
        return str(uuid.uuid4().int)[:6]  # 6-digit payment ID
    
    def _format_subscription_for_frontend(self, subscription: Subscription) -> SubscriptionListResponse:
        """
        Format subscription data for frontend compatibility.
        
        Maps database fields to the format expected by the frontend component.
        """
        # Get business and user names
        business_name = subscription.business.business_name if subscription.business else "Unknown Business"
        
        # Format plan information
        plan_info = f"{subscription.plan_name} ({subscription.plan_type})"
        
        # Format dates
        created_date = subscription.created_at.strftime("%d %b %Y")
        expiring_date = subscription.end_date.strftime("%d %b %Y")
        
        # Format payment ID with #
        payment_id_formatted = f"#{subscription.payment_id}"
        
        return SubscriptionListResponse(
            id=subscription.id,
            name=business_name,
            plan=plan_info,
            cycle=subscription.billing_cycle,
            payment=subscription.payment_method,
            amount=float(subscription.amount),
            currency=subscription.currency,
            paymentId=payment_id_formatted,
            created=created_date,
            expiring=expiring_date,
            end_date=subscription.end_date.isoformat(),
            status=subscription.status
        )


class SubscriptionPlanService:
    """Service for subscription plan management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.plan_repo = SubscriptionPlanRepository(db)
    
    def get_active_plans(self) -> List[SubscriptionPlan]:
        """Get all active subscription plans."""
        return self.plan_repo.get_active_plans()
    
    def get_plan_by_name(self, name: str) -> Optional[SubscriptionPlan]:
        """Get plan by name."""
        return self.plan_repo.get_by_name(name)
    
    def create_plan(self, plan_data: Dict[str, Any]) -> SubscriptionPlan:
        """Create a new subscription plan."""
        return self.plan_repo.create(plan_data)
    
    def update_plan(self, plan_id: int, update_data: Dict[str, Any]) -> Optional[SubscriptionPlan]:
        """Update a subscription plan."""
        plan = self.plan_repo.get(plan_id)
        if not plan:
            return None
        
        return self.plan_repo.update(plan, update_data)
    
    def delete_plan(self, plan_id: int) -> bool:
        """Delete a subscription plan."""
        plan = self.plan_repo.get(plan_id)
        if not plan:
            return False
        
        self.plan_repo.delete(plan_id)
        return True