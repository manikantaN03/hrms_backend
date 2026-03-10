"""
Additional Pydantic schemas for Data Capture endpoints
Replaces Dict[str, Any] with proper typed schemas for Swagger/OpenAPI documentation
"""

from pydantic import BaseModel, Field
from typing import Optional


class TravelKmsImportRequest(BaseModel):
    """Schema for importing travel kilometers to salary units"""
    
    period: str = Field(
        default="JAN-2026",
        description="Period for salary units (e.g., 'JAN-2026')",
        example="JAN-2026"
    )
    location: str = Field(
        default="All Locations",
        description="Location filter for employees",
        example="All Locations"
    )
    department: str = Field(
        default="All Departments",
        description="Department filter for employees",
        example="All Departments"
    )
    component: str = Field(
        default="Travel Allowance",
        description="Salary component name",
        example="Travel Allowance"
    )
    distance_type: str = Field(
        default="Calculated",
        description="Type of distance calculation (Calculated/Manual)",
        example="Calculated"
    )
    comments: Optional[str] = Field(
        default="",
        description="Additional comments for the import",
        example="Monthly travel allowance import"
    )
    overwrite_existing: bool = Field(
        default=False,
        description="Whether to overwrite existing salary units",
        example=False
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": "JAN-2026",
                "location": "All Locations",
                "department": "All Departments",
                "component": "Travel Allowance",
                "distance_type": "Calculated",
                "comments": "Monthly travel allowance import",
                "overwrite_existing": False
            }
        }
