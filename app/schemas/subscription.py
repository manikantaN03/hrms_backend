"""
Subscription Schemas
Pydantic models for subscription request/response validation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    
    business_id: int = Field(..., description="Business ID")
    plan_name: str = Field(..., min_length=1, max_length=100, description="Plan name")
    plan_type: str = Field(..., min_length=1, max_length=50, description="Plan type (Monthly/Yearly)")
    billing_cycle: str = Field(..., min_length=1, max_length=100, description="Billing cycle description")
    payment_method: str = Field(..., min_length=1, max_length=100, description="Payment method")
    amount: Decimal = Field(..., gt=0, description="Subscription amount")
    currency: str = Field(default="USD", max_length=10, description="Currency code")
    auto_renew: bool = Field(default=True, description="Auto-renewal enabled")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a new subscription"""
    
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: datetime = Field(..., description="Subscription end date")
    next_billing_date: Optional[datetime] = Field(None, description="Next billing date")


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    
    plan_name: Optional[str] = Field(None, min_length=1, max_length=100)
    plan_type: Optional[str] = Field(None, min_length=1, max_length=50)
    billing_cycle: Optional[str] = Field(None, min_length=1, max_length=100)
    payment_method: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = Field(None, max_length=50)
    auto_renew: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)
    next_billing_date: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription responses"""
    
    id: int
    user_id: int
    payment_id: str
    start_date: datetime
    end_date: datetime
    next_billing_date: Optional[datetime]
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Computed fields for frontend compatibility
    name: Optional[str] = None  # Business/subscriber name
    plan: Optional[str] = None  # Combined plan info
    cycle: Optional[str] = None  # Billing cycle
    payment: Optional[str] = None  # Payment method
    paymentId: Optional[str] = None  # Payment ID
    created: Optional[str] = None  # Formatted created date
    expiring: Optional[str] = None  # Formatted expiring date
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Subscription Payment Schemas
# ============================================================================

class SubscriptionPaymentBase(BaseModel):
    """Base payment schema"""
    
    subscription_id: int = Field(..., description="Subscription ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", max_length=10, description="Currency code")
    payment_method: str = Field(..., min_length=1, max_length=100, description="Payment method")
    due_date: datetime = Field(..., description="Payment due date")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")


class SubscriptionPaymentCreate(SubscriptionPaymentBase):
    """Schema for creating a payment record"""
    
    transaction_id: Optional[str] = Field(None, max_length=100, description="Transaction ID")
    gateway: Optional[str] = Field(None, max_length=100, description="Payment gateway")


class SubscriptionPaymentUpdate(BaseModel):
    """Schema for updating a payment record"""
    
    status: Optional[str] = Field(None, max_length=50, description="Payment status")
    payment_date: Optional[datetime] = Field(None, description="Actual payment date")
    transaction_id: Optional[str] = Field(None, max_length=100)
    gateway_response: Optional[str] = Field(None, description="Gateway response JSON")
    failure_reason: Optional[str] = Field(None, max_length=500, description="Failure reason")


class SubscriptionPaymentResponse(SubscriptionPaymentBase):
    """Schema for payment responses"""
    
    id: int
    payment_id: str
    transaction_id: Optional[str]
    gateway: Optional[str]
    gateway_response: Optional[str]
    status: str
    payment_date: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Subscription Plan Schemas
# ============================================================================

class SubscriptionPlanBase(BaseModel):
    """Base plan schema"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Plan name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name")
    description: Optional[str] = Field(None, max_length=1000, description="Plan description")
    monthly_price: Decimal = Field(..., ge=0, description="Monthly price")
    yearly_price: Decimal = Field(..., ge=0, description="Yearly price")
    currency: str = Field(default="USD", max_length=10, description="Currency code")
    max_employees: int = Field(default=0, ge=0, description="Max employees (0 = unlimited)")
    max_businesses: int = Field(default=1, ge=1, description="Max businesses")
    features: Optional[str] = Field(None, description="Features JSON")
    trial_days: int = Field(default=0, ge=0, description="Trial period in days")
    is_popular: bool = Field(default=False, description="Popular plan flag")
    sort_order: int = Field(default=0, description="Display order")


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Schema for creating a subscription plan"""
    pass


class SubscriptionPlanUpdate(BaseModel):
    """Schema for updating a subscription plan"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    monthly_price: Optional[Decimal] = Field(None, ge=0)
    yearly_price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    max_employees: Optional[int] = Field(None, ge=0)
    max_businesses: Optional[int] = Field(None, ge=1)
    features: Optional[str] = None
    trial_days: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None
    sort_order: Optional[int] = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Schema for plan responses"""
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Dashboard and Summary Schemas
# ============================================================================

class SubscriptionSummary(BaseModel):
    """Subscription summary for dashboard"""
    
    total_subscriptions: int
    active_subscriptions: int
    expired_subscriptions: int
    total_revenue: Decimal
    monthly_revenue: Decimal
    yearly_revenue: Decimal


class SubscriptionListResponse(BaseModel):
    """Response for subscription list with frontend compatibility"""
    
    id: int
    name: str  # Subscriber name
    plan: str  # Plan with type
    cycle: str  # Billing cycle
    payment: str  # Payment method
    amount: float  # Amount as float for frontend
    currency: str  # Currency code (INR, USD, EUR)
    paymentId: str  # Payment ID with #
    created: str  # Formatted created date
    expiring: str  # Formatted expiring date
    end_date: str  # ISO format end date for frontend logic
    status: str  # Status
    
    model_config = ConfigDict(from_attributes=True)