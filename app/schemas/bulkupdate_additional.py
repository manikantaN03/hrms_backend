"""
Additional Bulk Update Schemas
Pydantic models for bulk update API endpoints that were missing proper schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============================================================================
# Filtered Employees Request Schema
# ============================================================================

class FilteredEmployeesRequest(BaseModel):
    """Filtered employees request"""
    business_units: Optional[List[int]] = Field(None, description="List of business unit IDs", example=[1, 2])
    locations: Optional[List[int]] = Field(None, description="List of location IDs", example=[1, 2, 3])
    cost_centers: Optional[List[int]] = Field(None, description="List of cost center IDs", example=[1])
    departments: Optional[List[int]] = Field(None, description="List of department IDs", example=[1, 2])
    designations: Optional[List[int]] = Field(None, description="List of designation IDs", example=[1, 2, 3])
    grades: Optional[List[int]] = Field(None, description="List of grade IDs", example=[1])
    employment_types: Optional[List[str]] = Field(None, description="List of employment types", example=["Full-time", "Part-time"])
    
    class Config:
        json_schema_extra = {
            "example": {
                "business_units": [1, 2],
                "locations": [1, 2, 3],
                "cost_centers": [1],
                "departments": [1, 2],
                "designations": [1, 2, 3],
                "grades": [1],
                "employment_types": ["Full-time"]
            }
        }


# ============================================================================
# Bulk Update Options Base Schema
# ============================================================================

class BulkUpdateOptionsRequest(BaseModel):
    """Base bulk update options request"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to update", min_items=1, example=[123, 456, 789])
    options: Dict[str, Any] = Field(..., description="Options to update")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [123, 456, 789],
                "options": {
                    "calculate_overtime": True,
                    "esi_applicable": True,
                    "pf_applicable": True
                }
            }
        }


# ============================================================================
# Salary Options Update Schema
# ============================================================================

class SalaryOptionsUpdateRequest(BaseModel):
    """Salary options bulk update request"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to update", min_items=1, example=[123, 456, 789])
    options: Dict[str, Any] = Field(..., description="Salary calculation options", example={
        "calculate_overtime": True,
        "esi_applicable": True,
        "pf_applicable": True,
        "pt_applicable": True,
        "income_tax_regime": "new",
        "lwf_state": "Karnataka"
    })
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [123, 456, 789],
                "options": {
                    "calculate_overtime": True,
                    "esi_applicable": True,
                    "pf_applicable": True,
                    "pt_applicable": True,
                    "income_tax_regime": "new",
                    "lwf_state": "Karnataka"
                }
            }
        }


# ============================================================================
# Attendance Options Update Schema
# ============================================================================

class AttendanceOptionsUpdateRequest(BaseModel):
    """Attendance options bulk update request"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to update", min_items=1, example=[123, 456, 789])
    options: Dict[str, Any] = Field(..., description="Attendance calculation options", example={
        "track_attendance": True,
        "allow_remote_punch": True,
        "require_geo_location": False,
        "auto_approve_regularization": False
    })
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [123, 456, 789],
                "options": {
                    "track_attendance": True,
                    "allow_remote_punch": True,
                    "require_geo_location": False,
                    "auto_approve_regularization": False
                }
            }
        }


# ============================================================================
# Travel Options Update Schema
# ============================================================================

class TravelOptionsUpdateRequest(BaseModel):
    """Travel options bulk update request"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to update", min_items=1, example=[123, 456, 789])
    options: Dict[str, Any] = Field(..., description="Travel calculation options", example={
        "travel_allowance_applicable": True,
        "conveyance_rate_per_km": 10.0,
        "max_travel_limit": 5000.0
    })
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [123, 456, 789],
                "options": {
                    "travel_allowance_applicable": True,
                    "conveyance_rate_per_km": 10.0,
                    "max_travel_limit": 5000.0
                }
            }
        }


# ============================================================================
# Community Options Update Schema
# ============================================================================

class CommunityOptionsUpdateRequest(BaseModel):
    """Community options bulk update request"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to update", min_items=1, example=[123, 456, 789])
    options: Dict[str, Any] = Field(..., description="Community/demographic options", example={
        "community": "General",
        "category": "OC",
        "minority": False
    })
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [123, 456, 789],
                "options": {
                    "community": "General",
                    "category": "OC",
                    "minority": False
                }
            }
        }


# ============================================================================
# Workman Options Update Schema
# ============================================================================

class WorkmanOptionsUpdateRequest(BaseModel):
    """Workman status bulk update request"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to update", min_items=1, example=[123, 456, 789])
    options: Dict[str, Any] = Field(..., description="Workman status options", example={
        "is_workman": True,
        "workman_category": "Skilled",
        "bonus_applicable": True
    })
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [123, 456, 789],
                "options": {
                    "is_workman": True,
                    "workman_category": "Skilled",
                    "bonus_applicable": True
                }
            }
        }
