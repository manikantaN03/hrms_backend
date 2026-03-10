"""
Credit System Schemas
Pydantic models for credit system API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class UserCreditsResponse(BaseModel):
    credits: int
    user_id: int
    business_id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


class CreditPurchaseRequest(BaseModel):
    credits_to_purchase: int = Field(..., ge=1, le=10000)
    payment_method: Optional[str] = Field("mock", max_length=100)


class CreditPurchaseResponse(BaseModel):
    success: bool
    message: str
    credits_purchased: int
    new_balance: int
    transaction_id: str
    payment_amount: Optional[Decimal] = None
    timestamp: datetime


class CreditTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    description: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreditPricingResponse(BaseModel):
    service_name: str
    service_display_name: str
    credits_required: int
    is_free: bool
    
    class Config:
        from_attributes = True


class CreditUsageRequest(BaseModel):
    service_name: str = Field(..., max_length=100)
    quantity: int = Field(1, ge=1)
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class CreditUsageResponse(BaseModel):
    success: bool
    message: str
    credits_used: int
    new_balance: int
    transaction_id: int