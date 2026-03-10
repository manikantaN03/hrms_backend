"""
Additional Reports Schemas
Pydantic models for reports API endpoints that were missing proper schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date


# ============================================================================
# User Feedback Report Filters Schema
# ============================================================================

class UserFeedbackReportFilters(BaseModel):
    """User feedback report filters"""
    startDate: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format", example="2026-01-01")
    endDate: Optional[str] = Field(None, description="End date in YYYY-MM-DD format", example="2026-02-19")
    status: Optional[str] = Field(None, description="Feedback status", example="pending")
    rating: Optional[int] = Field(None, description="Feedback rating (1-5)", ge=1, le=5, example=5)
    category: Optional[str] = Field(None, description="Feedback category", example="bug")
    employeeId: Optional[int] = Field(None, description="Employee ID", gt=0, example=123)
    business_id: Optional[int] = None  # SECURITY: Filter by business_id
    
    class Config:
        json_schema_extra = {
            "example": {
                "startDate": "2026-01-01",
                "endDate": "2026-02-19",
                "status": "pending",
                "rating": 5,
                "category": "bug",
                "employeeId": 123
            }
        }


# ============================================================================
# System Alerts Report Filters Schema
# ============================================================================

class SystemAlertsReportFilters(BaseModel):
    """System alerts report filters"""
    startDate: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format", example="2026-01-01")
    endDate: Optional[str] = Field(None, description="End date in YYYY-MM-DD format", example="2026-02-19")
    severity: Optional[str] = Field(None, description="Alert severity: low, medium, high, critical", example="high")
    status: Optional[str] = Field(None, description="Alert status: active, resolved, dismissed", example="active")
    alertType: Optional[str] = Field(None, description="Alert type", example="security")
    module: Optional[str] = Field(None, description="Module name", example="attendance")
    business_id: Optional[int] = None  # SECURITY: Filter by business_id
    
    class Config:
        json_schema_extra = {
            "example": {
                "startDate": "2026-01-01",
                "endDate": "2026-02-19",
                "severity": "high",
                "status": "active",
                "alertType": "security",
                "module": "attendance"
            }
        }


# ============================================================================
# Salary Slip Preferences Schema
# ============================================================================

class SalarySlipPreferences(BaseModel):
    """Salary slip report preferences"""
    showGrossSalary: Optional[bool] = Field(True, description="Show gross salary", example=True)
    showDeductions: Optional[bool] = Field(True, description="Show deductions", example=True)
    showNetSalary: Optional[bool] = Field(True, description="Show net salary", example=True)
    showEarnings: Optional[bool] = Field(True, description="Show earnings breakdown", example=True)
    showAttendance: Optional[bool] = Field(False, description="Show attendance summary", example=False)
    showLeaveBalance: Optional[bool] = Field(False, description="Show leave balance", example=False)
    includeCompanyLogo: Optional[bool] = Field(True, description="Include company logo", example=True)
    includeEmployeePhoto: Optional[bool] = Field(False, description="Include employee photo", example=False)
    dateFormat: Optional[str] = Field("DD-MM-YYYY", description="Date format preference", example="DD-MM-YYYY")
    currency: Optional[str] = Field("INR", description="Currency code", example="INR")
    
    class Config:
        json_schema_extra = {
            "example": {
                "showGrossSalary": True,
                "showDeductions": True,
                "showNetSalary": True,
                "showEarnings": True,
                "showAttendance": False,
                "showLeaveBalance": False,
                "includeCompanyLogo": True,
                "includeEmployeePhoto": False,
                "dateFormat": "DD-MM-YYYY",
                "currency": "INR"
            }
        }
