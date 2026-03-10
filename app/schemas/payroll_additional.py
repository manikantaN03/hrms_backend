"""
Additional Pydantic schemas for Payroll endpoints
Replaces Dict[str, Any] with proper typed schemas for Swagger/OpenAPI documentation
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class ResetPayrollPeriodRequest(BaseModel):
    """Schema for resetting payroll period data"""
    
    selectedItems: List[str] = Field(
        ...,
        description="List of items to reset (duplicatePunches, attendance, salaryRevisions, deductions, etc.)",
        example=["duplicatePunches", "attendance"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "selectedItems": ["duplicatePunches", "attendance", "salaryRevisions"]
            }
        }


class DeleteLeaveEncashmentRequest(BaseModel):
    """Schema for deleting leave encashments"""
    
    encashment_ids: List[int] = Field(
        ...,
        description="List of leave encashment IDs to delete",
        example=[1, 2, 3]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "encashment_ids": [1, 2, 3]
            }
        }


class StatutoryBonusCreateRequest(BaseModel):
    """Schema for creating statutory bonus"""
    
    period_id: int = Field(..., description="Payroll period ID", example=1)
    employee_ids: List[int] = Field(..., description="List of employee IDs", example=[1, 2, 3])
    bonus_type: str = Field(..., description="Type of bonus", example="Annual Bonus")
    amount: float = Field(..., description="Bonus amount", example=5000.0)
    calculation_method: Optional[str] = Field(
        default="Fixed",
        description="Calculation method (Fixed/Percentage)",
        example="Fixed"
    )
    comments: Optional[str] = Field(
        default=None,
        description="Additional comments",
        example="Annual performance bonus"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_id": 1,
                "employee_ids": [1, 2, 3],
                "bonus_type": "Annual Bonus",
                "amount": 5000.0,
                "calculation_method": "Fixed",
                "comments": "Annual performance bonus"
            }
        }


class StatutoryBonusGenerateRequest(BaseModel):
    """Schema for generating statutory bonus summary"""
    
    period_id: int = Field(..., description="Payroll period ID", example=1)
    bonus_type: str = Field(..., description="Type of bonus", example="Annual Bonus")
    filters: Optional[dict] = Field(
        default=None,
        description="Filters for employee selection",
        example={"department_id": 1}
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_id": 1,
                "bonus_type": "Annual Bonus",
                "filters": {"department_id": 1}
            }
        }


class StatutoryBonusProcessRequest(BaseModel):
    """Schema for processing statutory bonuses"""
    
    period_id: int = Field(..., description="Payroll period ID", example=1)
    bonus_ids: List[int] = Field(..., description="List of bonus IDs to process", example=[1, 2, 3])
    process_type: Optional[str] = Field(
        default="approve",
        description="Process type (approve/reject)",
        example="approve"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_id": 1,
                "bonus_ids": [1, 2, 3],
                "process_type": "approve"
            }
        }


class DeleteStatutoryBonusRequest(BaseModel):
    """Schema for deleting statutory bonuses"""
    
    bonus_ids: List[int] = Field(
        ...,
        description="List of statutory bonus IDs to delete",
        example=[1, 2, 3]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "bonus_ids": [1, 2, 3]
            }
        }


class GratuityCreateRequest(BaseModel):
    """Schema for creating gratuity"""
    
    employee_id: int = Field(..., description="Employee ID", example=1)
    period_id: int = Field(..., description="Payroll period ID", example=1)
    gratuity_amount: float = Field(..., description="Gratuity amount", example=50000.0)
    years_of_service: float = Field(..., description="Years of service", example=5.5)
    last_drawn_salary: float = Field(..., description="Last drawn salary", example=50000.0)
    calculation_method: Optional[str] = Field(
        default="Standard",
        description="Calculation method",
        example="Standard"
    )
    comments: Optional[str] = Field(
        default=None,
        description="Additional comments",
        example="Gratuity on separation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 1,
                "period_id": 1,
                "gratuity_amount": 50000.0,
                "years_of_service": 5.5,
                "last_drawn_salary": 50000.0,
                "calculation_method": "Standard",
                "comments": "Gratuity on separation"
            }
        }


class GratuityGenerateRequest(BaseModel):
    """Schema for generating gratuity summary"""
    
    period_id: int = Field(..., description="Payroll period ID", example=1)
    employee_ids: Optional[List[int]] = Field(
        default=None,
        description="List of employee IDs (optional)",
        example=[1, 2, 3]
    )
    separation_date: Optional[date] = Field(
        default=None,
        description="Separation date filter",
        example="2026-01-31"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_id": 1,
                "employee_ids": [1, 2, 3],
                "separation_date": "2026-01-31"
            }
        }


class GratuityProcessRequest(BaseModel):
    """Schema for processing gratuities"""
    
    period_id: int = Field(..., description="Payroll period ID", example=1)
    gratuity_ids: List[int] = Field(..., description="List of gratuity IDs to process", example=[1, 2, 3])
    process_type: Optional[str] = Field(
        default="approve",
        description="Process type (approve/reject)",
        example="approve"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_id": 1,
                "gratuity_ids": [1, 2, 3],
                "process_type": "approve"
            }
        }


class DeleteGratuityRequest(BaseModel):
    """Schema for deleting gratuities"""
    
    gratuity_ids: List[int] = Field(
        ...,
        description="List of gratuity IDs to delete",
        example=[1, 2, 3]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "gratuity_ids": [1, 2, 3]
            }
        }
