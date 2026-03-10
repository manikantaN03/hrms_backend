"""
Subscription Repository
Data access layer for subscription operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from app.models.subscription import Subscription, SubscriptionPayment, SubscriptionPlan
from app.models.business import Business
from app.models.user import User


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for subscription-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Subscription, db)
    
    # ========================================================================
    # Get Subscriptions with Related Data
    # ========================================================================
    
    def get_all_with_details(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        plan_filter: Optional[str] = None
    ) -> List[Subscription]:
        """
        Get all subscriptions with business and user details.
        
        Args:
            skip: Pagination offset
            limit: Maximum records
            status_filter: Filter by status
            plan_filter: Filter by plan name
        
        Returns:
            List of subscriptions with related data
        """
        query = (
            self.db.query(Subscription)
            .options(
                joinedload(Subscription.business),
                joinedload(Subscription.user)
            )
        )
        
        if status_filter:
            query = query.filter(Subscription.status == status_filter)
        
        if plan_filter:
            query = query.filter(Subscription.plan_name == plan_filter)
        
        return (
            query
            .order_by(desc(Subscription.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_business_id(self, business_id: int) -> List[Subscription]:
        """Get all subscriptions for a specific business"""
        return (
            self.db.query(Subscription)
            .filter(Subscription.business_id == business_id)
            .order_by(desc(Subscription.created_at))
            .all()
        )
    
    def get_active_subscription(self, business_id: int) -> Optional[Subscription]:
        """Get the active subscription for a business"""
        return (
            self.db.query(Subscription)
            .filter(
                and_(
                    Subscription.business_id == business_id,
                    Subscription.is_active == True,
                    Subscription.status == "Active"
                )
            )
            .first()
        )
    
    # ========================================================================
    # Search and Filter
    # ========================================================================
    
    def search_subscriptions(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subscription]:
        """
        Search subscriptions by business name or payment ID.
        
        Args:
            search_term: Search query
            skip: Pagination offset
            limit: Maximum records
        
        Returns:
            List of matching subscriptions
        """
        search = f"%{search_term}%"
        
        return (
            self.db.query(Subscription)
            .join(Business, Subscription.business_id == Business.id)
            .filter(
                or_(
                    Business.business_name.ilike(search),
                    Subscription.payment_id.ilike(search),
                    Subscription.plan_name.ilike(search)
                )
            )
            .options(
                joinedload(Subscription.business),
                joinedload(Subscription.user)
            )
            .order_by(desc(Subscription.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_expiring_subscriptions(self, days: int = 30) -> List[Subscription]:
        """Get subscriptions expiring within specified days"""
        expiry_date = datetime.utcnow() + timedelta(days=days)
        
        return (
            self.db.query(Subscription)
            .filter(
                and_(
                    Subscription.is_active == True,
                    Subscription.end_date <= expiry_date,
                    Subscription.end_date >= datetime.utcnow()
                )
            )
            .options(
                joinedload(Subscription.business),
                joinedload(Subscription.user)
            )
            .order_by(Subscription.end_date)
            .all()
        )
    
    # ========================================================================
    # Statistics and Analytics
    # ========================================================================
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics for dashboard"""
        
        # Total subscriptions
        total = self.db.query(Subscription).count()
        
        # Active subscriptions (truly active - not expired)
        active = (
            self.db.query(Subscription)
            .filter(
                and_(
                    Subscription.is_active == True,
                    Subscription.status.in_(["Active", "Paid"]),
                    Subscription.end_date >= datetime.utcnow()  # Not yet expired
                )
            )
            .count()
        )
        
        # Expired subscriptions (explicitly expired OR past end date)
        expired = (
            self.db.query(Subscription)
            .filter(
                or_(
                    Subscription.status == "Expired",
                    Subscription.status == "Cancelled",
                    and_(
                        Subscription.status.in_(["Active", "Paid"]),
                        Subscription.end_date < datetime.utcnow()
                    )
                )
            )
            .count()
        )
        
        # Revenue calculations
        total_revenue = (
            self.db.query(func.sum(Subscription.amount))
            .filter(Subscription.status.in_(["Active", "Paid"]))
            .scalar() or 0
        )
        
        monthly_revenue = (
            self.db.query(func.sum(Subscription.amount))
            .filter(
                and_(
                    Subscription.status.in_(["Active", "Paid"]),
                    Subscription.plan_type == "Monthly"
                )
            )
            .scalar() or 0
        )
        
        yearly_revenue = (
            self.db.query(func.sum(Subscription.amount))
            .filter(
                and_(
                    Subscription.status.in_(["Active", "Paid"]),
                    Subscription.plan_type == "Yearly"
                )
            )
            .scalar() or 0
        )
        
        return {
            "total_subscriptions": total,
            "active_subscriptions": active,
            "expired_subscriptions": expired,
            "total_revenue": float(total_revenue),
            "monthly_revenue": float(monthly_revenue),
            "yearly_revenue": float(yearly_revenue)
        }
    
    def get_revenue_by_plan(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by plan"""
        return (
            self.db.query(
                Subscription.plan_name,
                func.count(Subscription.id).label("count"),
                func.sum(Subscription.amount).label("revenue")
            )
            .filter(Subscription.status.in_(["Active", "Paid"]))
            .group_by(Subscription.plan_name)
            .all()
        )
    
    # ========================================================================
    # Validation Helpers
    # ========================================================================
    
    def payment_id_exists(self, payment_id: str, exclude_id: Optional[int] = None) -> bool:
        """Check if payment ID already exists"""
        query = self.db.query(Subscription).filter(Subscription.payment_id == payment_id)
        
        if exclude_id:
            query = query.filter(Subscription.id != exclude_id)
        
        return query.first() is not None


class SubscriptionPaymentRepository(BaseRepository[SubscriptionPayment]):
    """Repository for subscription payment operations."""
    
    def __init__(self, db: Session):
        super().__init__(SubscriptionPayment, db)
    
    def get_by_subscription_id(self, subscription_id: int) -> List[SubscriptionPayment]:
        """Get all payments for a subscription"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.subscription_id == subscription_id)
            .order_by(desc(SubscriptionPayment.created_at))
            .all()
        )
    
    def get_pending_payments(self) -> List[SubscriptionPayment]:
        """Get all pending payments"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.status == "Pending")
            .order_by(SubscriptionPayment.due_date)
            .all()
        )


class SubscriptionPlanRepository(BaseRepository[SubscriptionPlan]):
    """Repository for subscription plan operations."""
    
    def __init__(self, db: Session):
        super().__init__(SubscriptionPlan, db)
    
    def get_active_plans(self) -> List[SubscriptionPlan]:
        """Get all active subscription plans"""
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.sort_order, SubscriptionPlan.monthly_price)
            .all()
        )
    
    def get_by_name(self, name: str) -> Optional[SubscriptionPlan]:
        """Get plan by name"""
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.name == name)
            .first()
        )
    
    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if plan name already exists"""
        query = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.name == name)
        
        if exclude_id:
            query = query.filter(SubscriptionPlan.id != exclude_id)
        
        return query.first() is not None