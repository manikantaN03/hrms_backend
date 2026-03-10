"""
Purchase Transaction Schemas
Pydantic models for purchase transaction validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Purchase Transaction Schemas
# ============================================================================

class PurchaseTransactionBase(BaseModel):
    """Base purchase transaction schema"""
    
    business_id: int = Field(..., description="Business ID")
    user_id: int = Field(..., description="User ID")
    subscription_id: Optional[int] = Field(None, description="Subscription ID")
    invoice_id: str = Field(..., min_length=1, max_length=50, description="Invoice ID")
    due_date: Optional[datetime] = Field(None, description="Payment due date")
    subtotal: Decimal = Field(..., gt=0, description="Subtotal amount")
    tax_amount: Decimal = Field(default=0.0, ge=0, description="Tax amount")
    total_amount: Decimal = Field(..., gt=0, description="Total amount")
    currency: str = Field(default="INR", max_length=10, description="Currency code")
    payment_method: str = Field(..., min_length=1, max_length=100, description="Payment method")
    payment_status: str = Field(default="Pending", max_length=50, description="Payment status")
    payment_reference: Optional[str] = Field(None, max_length=255, description="Payment reference")
    plan_name: str = Field(..., min_length=1, max_length=100, description="Plan name")
    billing_cycle: str = Field(..., min_length=1, max_length=50, description="Billing cycle")
    service_start_date: Optional[datetime] = Field(None, description="Service start date")
    service_end_date: Optional[datetime] = Field(None, description="Service end date")
    invoice_from_name: str = Field(default="DCM", max_length=255, description="Invoice from name")
    invoice_from_address: Optional[str] = Field(None, description="Invoice from address")
    invoice_from_email: Optional[str] = Field(None, max_length=255, description="Invoice from email")
    invoice_to_name: str = Field(..., min_length=1, max_length=255, description="Invoice to name")
    invoice_to_address: Optional[str] = Field(None, description="Invoice to address")
    invoice_to_email: str = Field(..., min_length=1, max_length=255, description="Invoice to email")
    description: Optional[str] = Field(None, description="Transaction description")
    notes: Optional[str] = Field(None, description="Additional notes")


class PurchaseTransactionCreate(PurchaseTransactionBase):
    """Schema for creating a new purchase transaction"""
    pass


class PurchaseTransactionUpdate(BaseModel):
    """Schema for updating a purchase transaction"""
    
    payment_status: Optional[str] = Field(None, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=255)
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class PaymentStatusUpdate(BaseModel):
    """Schema for updating payment status"""
    
    payment_status: str = Field(..., max_length=50, description="New payment status")
    payment_reference: Optional[str] = Field(None, max_length=255, description="Payment reference")
    gateway_response: Optional[str] = Field(None, description="Gateway response")
    
    @validator('payment_status')
    def validate_payment_status(cls, v):
        allowed_statuses = ['Pending', 'Paid', 'Failed', 'Refunded', 'Cancelled']
        if v not in allowed_statuses:
            raise ValueError(f'Payment status must be one of: {", ".join(allowed_statuses)}')
        return v


class PurchaseTransactionResponse(PurchaseTransactionBase):
    """Schema for purchase transaction responses"""
    
    id: int
    transaction_date: datetime
    payment_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Frontend compatibility fields
    company: Optional[str] = None  # Business name
    email: Optional[str] = None  # Business email
    date: Optional[str] = None  # Formatted transaction date
    amount: Optional[float] = None  # Total amount as float
    method: Optional[str] = None  # Payment method
    status: Optional[str] = None  # Payment status
    logo: Optional[str] = None  # Business logo
    
    # Invoice details for frontend
    from_info: Optional[Dict[str, Any]] = None
    to_info: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Transaction Line Item Schemas
# ============================================================================

class TransactionLineItemBase(BaseModel):
    """Base transaction line item schema"""
    
    item_name: str = Field(..., min_length=1, max_length=255, description="Item name")
    item_description: Optional[str] = Field(None, description="Item description")
    quantity: int = Field(default=1, gt=0, description="Quantity")
    unit_price: Decimal = Field(..., gt=0, description="Unit price")
    total_price: Decimal = Field(..., gt=0, description="Total price")
    item_type: Optional[str] = Field(None, max_length=100, description="Item type")
    item_reference: Optional[str] = Field(None, max_length=255, description="Item reference")


class TransactionLineItemCreate(TransactionLineItemBase):
    """Schema for creating a transaction line item"""
    
    transaction_id: int = Field(..., description="Transaction ID")


class TransactionLineItemResponse(TransactionLineItemBase):
    """Schema for transaction line item responses"""
    
    id: int
    transaction_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Payment Log Schemas
# ============================================================================

class PaymentLogBase(BaseModel):
    """Base payment log schema"""
    
    payment_gateway: Optional[str] = Field(None, max_length=100, description="Payment gateway")
    gateway_transaction_id: Optional[str] = Field(None, max_length=255, description="Gateway transaction ID")
    gateway_response: Optional[str] = Field(None, description="Gateway response JSON")
    status: str = Field(..., max_length=50, description="Payment status")
    attempt_number: int = Field(default=1, gt=0, description="Attempt number")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    error_code: Optional[str] = Field(None, max_length=100, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


class PaymentLogCreate(PaymentLogBase):
    """Schema for creating a payment log"""
    
    transaction_id: int = Field(..., description="Transaction ID")


class PaymentLogResponse(PaymentLogBase):
    """Schema for payment log responses"""
    
    id: int
    transaction_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Frontend Compatibility Schemas
# ============================================================================

class TransactionListResponse(BaseModel):
    """Response for transaction list with frontend compatibility"""
    
    id: str  # Invoice ID
    company: str  # Business name
    email: str  # Business email
    date: str  # Formatted transaction date
    amount: float  # Total amount
    method: str  # Payment method
    status: str  # Payment status
    logo: str  # Business logo URL
    
    # Invoice details
    from_info: Dict[str, str]
    to_info: Dict[str, str]
    plan: str
    billingCycle: str
    createdDate: str
    expiringOn: str
    subtotal: float
    tax: float
    total: float
    dueDate: str
    
    model_config = ConfigDict(from_attributes=True)


class TransactionSummary(BaseModel):
    """Transaction summary for dashboard"""
    
    total_transactions: int
    total_revenue: Decimal
    paid_transactions: int
    unpaid_transactions: int
    pending_transactions: int
    failed_transactions: int
    average_transaction_amount: Decimal


class TransactionAnalytics(BaseModel):
    """Transaction analytics data"""
    
    monthly_revenue: List[Dict[str, Any]]
    payment_method_stats: List[Dict[str, Any]]
    status_distribution: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]


# ============================================================================
# Filter and Search Schemas
# ============================================================================

class TransactionFilters(BaseModel):
    """Filters for transaction queries"""
    
    status: Optional[str] = None
    payment_method: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    business_id: Optional[int] = None
    plan_name: Optional[str] = None
    search_term: Optional[str] = None
    sort_by: Optional[str] = Field(default="transaction_date", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")