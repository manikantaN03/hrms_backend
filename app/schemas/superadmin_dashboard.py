"""
SuperAdmin Dashboard Schemas
Pydantic models for superadmin dashboard API responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class StatisticValue(BaseModel):
    """Individual statistic with growth percentage"""
    value: int = Field(..., ge=0, description="Statistic value")
    growth: float = Field(..., description="Growth percentage")
    growth_positive: bool = Field(..., description="Whether growth is positive")
    formatted: Optional[str] = Field(None, description="Formatted value (for currency)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "value": 1234,
                "growth": 19.01,
                "growth_positive": True,
                "formatted": "₹1,234"
            }
        }


class DashboardStatistics(BaseModel):
    """Dashboard statistics section"""
    total_companies: StatisticValue
    active_companies: StatisticValue
    total_subscribers: StatisticValue
    total_earnings: StatisticValue
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_companies": {"value": 1234, "growth": 19.01, "growth_positive": True},
                "active_companies": {"value": 1100, "growth": -12.0, "growth_positive": False},
                "total_subscribers": {"value": 5678, "growth": 6.0, "growth_positive": True},
                "total_earnings": {"value": 3000, "formatted": "₹3,000", "growth": -16.0, "growth_positive": False}
            }
        }


# ============================================================================
# CHARTS SCHEMAS
# ============================================================================

class CompanyChartData(BaseModel):
    """Company chart data point"""
    name: str = Field(..., description="Day name (M, T, W, etc.)")
    value: int = Field(..., ge=0, description="Number of companies")
    fullName: str = Field(..., description="Full day name")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    
    @validator('date')
    def validate_date_format(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class RevenueChartData(BaseModel):
    """Revenue chart data point"""
    month: str = Field(..., description="Month name (Jan, Feb, etc.)")
    income: float = Field(..., ge=0, description="Income amount")
    expenses: float = Field(..., ge=0, description="Expenses amount")
    date: Optional[str] = Field(None, description="Date in YYYY-MM format")


class TopPlanData(BaseModel):
    """Top plan data point"""
    name: str = Field(..., description="Plan name")
    value: int = Field(..., ge=0, le=100, description="Percentage value")
    color: str = Field(..., description="Color code for chart")
    
    @validator('color')
    def validate_color(cls, v):
        """Validate color format"""
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be in #RRGGBB format')
        return v


class DashboardCharts(BaseModel):
    """Dashboard charts section"""
    companies_weekly: List[CompanyChartData] = Field(..., description="Weekly companies data")
    revenue_monthly: List[RevenueChartData] = Field(..., description="Monthly revenue data")
    top_plans: List[TopPlanData] = Field(..., description="Top plans distribution")
    
    @validator('companies_weekly')
    def validate_companies_weekly(cls, v):
        """Validate companies weekly data"""
        if len(v) > 31:  # Max 31 days in a month
            raise ValueError('Companies weekly data cannot exceed 31 days')
        return v
    
    @validator('revenue_monthly')
    def validate_revenue_monthly(cls, v):
        """Validate revenue monthly data"""
        if len(v) > 12:  # Max 12 months
            raise ValueError('Revenue monthly data cannot exceed 12 months')
        return v


# ============================================================================
# RECENT ACTIVITIES SCHEMAS
# ============================================================================

class RecentTransaction(BaseModel):
    """Recent transaction item"""
    id: str = Field(..., description="Transaction ID")
    company: str = Field(..., description="Company name")
    date: str = Field(..., description="Transaction date")
    amount: str = Field(..., description="Transaction amount")
    plan: str = Field(..., description="Plan details")
    logo: str = Field(..., description="Company logo/initials")


class RegisteredCompany(BaseModel):
    """Recently registered company"""
    company: str = Field(..., description="Company name")
    plan: str = Field(..., description="Plan details")
    users: str = Field(..., description="Number of users")
    domain: str = Field(..., description="Company domain")
    logo: str = Field(..., description="Company logo/initials")
    date: Optional[str] = Field(None, description="Registration date")


class ExpiredPlan(BaseModel):
    """Expired plan item"""
    company: str = Field(..., description="Company name")
    expired: str = Field(..., description="Expiration date")
    plan: str = Field(..., description="Plan details")
    logo: str = Field(..., description="Company logo/initials")


class RecentActivities(BaseModel):
    """Recent activities section"""
    transactions: List[RecentTransaction] = Field(..., description="Recent transactions")
    registered_companies: List[RegisteredCompany] = Field(..., description="Recently registered companies")
    expired_plans: List[ExpiredPlan] = Field(..., description="Recently expired plans")


# ============================================================================
# METADATA SCHEMAS
# ============================================================================

class DateFilter(BaseModel):
    """Date filter metadata"""
    start_date: Optional[str] = Field(None, description="Start date filter")
    end_date: Optional[str] = Field(None, description="End date filter")
    filtered: bool = Field(..., description="Whether date filter is applied")


class DashboardMetadata(BaseModel):
    """Dashboard metadata"""
    generated_at: str = Field(..., description="Generation timestamp")
    generated_by: str = Field(..., description="User who generated the dashboard")
    data_source: str = Field(..., description="Data source (database)")
    total_businesses: int = Field(..., ge=0, description="Total businesses count")
    total_employees: int = Field(..., ge=0, description="Total employees count")
    date_filter: DateFilter = Field(..., description="Date filter information")
    
    @validator('data_source')
    def validate_data_source(cls, v):
        """Validate data source"""
        if v != "database":
            raise ValueError('Data source must be "database" - no static data allowed')
        return v


# ============================================================================
# MAIN DASHBOARD RESPONSE
# ============================================================================

class SuperAdminDashboardResponse(BaseModel):
    """Complete superadmin dashboard response"""
    statistics: DashboardStatistics = Field(..., description="Dashboard statistics")
    charts: DashboardCharts = Field(..., description="Dashboard charts data")
    recent_activities: RecentActivities = Field(..., description="Recent activities")
    metadata: DashboardMetadata = Field(..., description="Dashboard metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "statistics": {
                    "total_companies": {"value": 1234, "growth": 19.01, "growth_positive": True},
                    "active_companies": {"value": 1100, "growth": -12.0, "growth_positive": False},
                    "total_subscribers": {"value": 5678, "growth": 6.0, "growth_positive": True},
                    "total_earnings": {"value": 3000, "formatted": "₹3,000", "growth": -16.0, "growth_positive": False}
                },
                "charts": {
                    "companies_weekly": [
                        {"name": "M", "value": 40, "fullName": "Monday", "date": "2026-02-10"}
                    ],
                    "revenue_monthly": [
                        {"month": "Jan", "income": 40, "expenses": 60}
                    ],
                    "top_plans": [
                        {"name": "Basic", "value": 60, "color": "#1B84FF"}
                    ]
                },
                "recent_activities": {
                    "transactions": [],
                    "registered_companies": [],
                    "expired_plans": []
                },
                "metadata": {
                    "generated_at": "2026-02-15T16:49:56.449410",
                    "generated_by": "superadmin@levitica.com",
                    "data_source": "database",
                    "total_businesses": 1,
                    "total_employees": 67,
                    "date_filter": {
                        "start_date": None,
                        "end_date": None,
                        "filtered": False
                    }
                }
            }
        }


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class DashboardDateFilter(BaseModel):
    """Dashboard date filter request"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate end date is after start date"""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            start = datetime.strptime(values['start_date'], "%Y-%m-%d")
            end = datetime.strptime(v, "%Y-%m-%d")
            if end < start:
                raise ValueError('End date must be after start date')
        return v
