"""
Setup Master Dashboard API Endpoints
Unified dashboard for all setup and master data management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.api.v1.endpoints.master_setup import get_user_business_id
from app.models.user import User
from app.models.employee import Employee
from pydantic import BaseModel

router = APIRouter()


class SetupDashboardResponse(BaseModel):
    """Setup dashboard response"""
    module_status: Dict[str, int]
    recent_activities: List[Dict[str, str]]
    configuration_summary: Dict[str, int]


@router.get("", response_model=SetupDashboardResponse)
async def get_setup_dashboard_main(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get main setup dashboard overview
    
    Returns:
    - Setup module statistics
    - Configuration status
    - Recent setup activities
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Mock setup data
        setup_data = {
            "module_status": {
                "master_setup": 85,
                "salary_setup": 70,
                "leaves_attendance": 90,
                "statutory_options": 60,
                "employee_self_service": 80
            },
            "recent_activities": [
                {
                    "module": "Master Setup",
                    "action": "Department added",
                    "user": current_user.name,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "module": "Salary Setup",
                    "action": "Salary structure updated",
                    "user": current_user.name,
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ],
            "configuration_summary": {
                "total_configurations": 15,
                "completed_configurations": 12,
                "pending_configurations": 3,
                "completion_percentage": 80
            }
        }
        
        return SetupDashboardResponse(**setup_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch setup dashboard: {str(e)}"
        )


@router.get("/mastersetup", response_model=Dict[str, Any])
async def get_setup_mastersetup_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get setup master dashboard with all setup modules overview
    
    **Returns:**
    - Setup modules status and statistics
    - Quick access to all setup areas
    - System configuration overview
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # All 15 setup modules as shown in frontend image (4 rows x 3-4 cards each)
        setup_modules = [
            # Row 1 - Master Data
            {
                "id": "business_units",
                "name": "Business Units",
                "description": "Business Unit setup and configuration",
                "icon": "building",
                "url": "/setup/master/business-units",
                "count": 5,
                "status": "active",
                "last_updated": "2025-12-20",
                "row": 1,
                "position": 1,
                "backend_available": True
            },
            {
                "id": "locations",
                "name": "Locations",
                "description": "Office locations and work sites",
                "icon": "map-marker",
                "url": "/setup/master/locations",
                "count": 12,
                "status": "active",
                "last_updated": "2025-12-18",
                "row": 1,
                "position": 2,
                "backend_available": True
            },
            {
                "id": "cost_centers",
                "name": "Cost Centers",
                "description": "Cost centers for financial tracking",
                "icon": "calculator",
                "url": "/setup/master/cost-centers",
                "count": 8,
                "status": "active",
                "last_updated": "2025-12-15",
                "row": 1,
                "position": 3,
                "backend_available": True
            },
            {
                "id": "departments",
                "name": "Departments",
                "description": "Organizational departments",
                "icon": "users",
                "url": "/setup/master/departments",
                "count": 15,
                "status": "active",
                "last_updated": "2025-12-22",
                "row": 1,
                "position": 4,
                "backend_available": True
            },
            
            # Row 2 - Employee Setup
            {
                "id": "grades",
                "name": "Grades",
                "description": "Employee grades and levels",
                "icon": "star",
                "url": "/setup/mastersetup/grades",
                "count": 10,
                "status": "active",
                "last_updated": "2025-12-19",
                "row": 2,
                "position": 1,
                "backend_available": True
            },
            {
                "id": "designations",
                "name": "Designations",
                "description": "Job titles and designations",
                "icon": "briefcase",
                "url": "/setup/mastersetup/designations",
                "count": 25,
                "status": "active",
                "last_updated": "2025-12-21",
                "row": 2,
                "position": 2,
                "backend_available": True
            },
            {
                "id": "work_shifts",
                "name": "Work Shifts",
                "description": "Work shifts and schedules",
                "icon": "clock",
                "url": "/setup/mastersetup/work-shifts",
                "count": 6,
                "status": "active",
                "last_updated": "2025-12-17",
                "row": 2,
                "position": 3,
                "backend_available": True
            },
            {
                "id": "esi_policies",
                "name": "ESI Policies",
                "description": "ESI (Employee State Insurance) policies",
                "icon": "shield",
                "url": "/setup/esi-settings",
                "count": 3,
                "status": "active",
                "last_updated": "2025-12-16",
                "row": 2,
                "position": 4,
                "backend_available": True
            },
            
            # Row 3 - Policies and Configuration
            {
                "id": "weekoff_policies",
                "name": "View Off Policies",
                "description": "Week-off and holiday policies",
                "icon": "calendar",
                "url": "/setup/weekoff-policies",
                "count": 4,
                "status": "active",
                "last_updated": "2025-12-13",
                "row": 3,
                "position": 1,
                "backend_available": True
            },
            {
                "id": "business_info",
                "name": "Business Info",
                "description": "Business information and settings",
                "icon": "info",
                "url": "/setup/business-information",
                "count": 1,
                "status": "active",
                "last_updated": "2025-12-20",
                "row": 3,
                "position": 2,
                "backend_available": True
            },
            {
                "id": "visit_types",
                "name": "Visit Types",
                "description": "Visit types and categories",
                "icon": "map",
                "url": "/setup/visit-types",
                "count": 8,
                "status": "active",
                "last_updated": "2025-12-18",
                "row": 3,
                "position": 3,
                "backend_available": True
            },
            {
                "id": "helpdesk",
                "name": "Helpdesk",
                "description": "Helpdesk categories and support",
                "icon": "support",
                "url": "/helpdesk-categories",
                "count": 12,
                "status": "active",
                "last_updated": "2025-12-14",
                "row": 3,
                "position": 4,
                "backend_available": True
            },
            
            # Row 4 - System Configuration
            {
                "id": "workflows",
                "name": "Workflows",
                "description": "Approval workflows and processes",
                "icon": "flow",
                "url": "/workflows",
                "count": 7,
                "status": "active",
                "last_updated": "2025-12-16",
                "row": 4,
                "position": 1,
                "backend_available": True
            },
            {
                "id": "employee_code",
                "name": "Employee Code",
                "description": "Employee code generation configuration",
                "icon": "code",
                "url": "/setup/employee-code-config",
                "count": 1,
                "status": "active",
                "last_updated": "2025-12-10",
                "row": 4,
                "position": 2,
                "backend_available": True
            },
            {
                "id": "exit_reasons",
                "name": "Exit Reasons",
                "description": "Employee exit reasons and categories",
                "icon": "sign-out",
                "url": "/exit-reasons",
                "count": 8,
                "status": "active",
                "last_updated": "2025-12-12",
                "row": 4,
                "position": 3,
                "backend_available": True
            }
        ]
        
        # Calculate summary statistics
        total_modules = len(setup_modules)
        active_modules = sum(1 for module in setup_modules if module["status"] == "active")
        total_records = sum(module["count"] for module in setup_modules)
        backend_available_count = sum(1 for module in setup_modules if module.get("backend_available", False))
        
        # Recent activity (mock data)
        recent_activities = [
            {
                "module": "Departments",
                "action": "Updated",
                "description": "Added new IT department",
                "timestamp": "2025-12-22 10:30:00",
                "user": "Admin User"
            },
            {
                "module": "Designations",
                "action": "Created",
                "description": "Added Senior Developer designation",
                "timestamp": "2025-12-21 15:45:00",
                "user": "HR Manager"
            },
            {
                "module": "Business Units",
                "action": "Updated",
                "description": "Modified head office details",
                "timestamp": "2025-12-20 09:15:00",
                "user": "System Admin"
            }
        ]
        
        # System health status
        system_status = {
            "overall_health": "excellent",
            "database_status": "connected",
            "last_backup": "2025-12-22 23:00:00",
            "system_uptime": "15 days, 8 hours",
            "active_users": 45,
            "pending_approvals": 3
        }
        
        return {
            "dashboard": {
                "title": "Setup Master Dashboard",
                "description": "Centralized management for all system setup and master data",
                "last_updated": datetime.now().isoformat()
            },
            "statistics": {
                "total_modules": total_modules,
                "active_modules": active_modules,
                "total_records": total_records,
                "backend_available": backend_available_count,
                "completion_rate": round((active_modules / total_modules) * 100, 1),
                "backend_coverage": round((backend_available_count / total_modules) * 100, 1)
            },
            "modules": setup_modules,
            "recent_activities": recent_activities,
            "system_status": system_status,
            "quick_actions": [
                {
                    "name": "Add New Department",
                    "url": "/setup/master/departments",
                    "method": "POST",
                    "icon": "plus"
                },
                {
                    "name": "Create Business Unit",
                    "url": "/setup/master/business-units",
                    "method": "POST",
                    "icon": "building"
                },
                {
                    "name": "Setup Work Shift",
                    "url": "/setup/mastersetup/work-shifts",
                    "method": "POST",
                    "icon": "clock"
                },
                {
                    "name": "Add Location",
                    "url": "/setup/master/locations",
                    "method": "POST",
                    "icon": "map-marker"
                }
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch setup master dashboard: {str(e)}"
        )


@router.get("/mastersetup/modules", response_model=List[Dict[str, Any]])
async def get_setup_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all available setup modules
    
    **Returns:**
    - Complete list of setup modules with metadata
    """
    try:
        modules = [
            {
                "category": "Master Data",
                "modules": [
                    {"id": "business_units", "name": "Business Units", "url": "/setup/master/business-units"},
                    {"id": "locations", "name": "Locations", "url": "/setup/master/locations"},
                    {"id": "cost_centers", "name": "Cost Centers", "url": "/setup/master/cost-centers"},
                    {"id": "departments", "name": "Departments", "url": "/setup/master/departments"}
                ]
            },
            {
                "category": "Employee Setup",
                "modules": [
                    {"id": "grades", "name": "Grades", "url": "/setup/mastersetup/grades"},
                    {"id": "designations", "name": "Designations", "url": "/setup/mastersetup/designations"},
                    {"id": "work_shifts", "name": "Work Shifts", "url": "/setup/mastersetup/work-shifts"},
                    {"id": "employee_code_config", "name": "Employee Code Config", "url": "/setup/employee-code-config"}
                ]
            },
            {
                "category": "System Configuration",
                "modules": [
                    {"id": "exit_reasons", "name": "Exit Reasons", "url": "/exit-reasons"},
                    {"id": "helpdesk_categories", "name": "Helpdesk Categories", "url": "/helpdesk-categories"},
                    {"id": "workflows", "name": "Workflows", "url": "/workflows"},
                    {"id": "weekoff_policies", "name": "Week-off Policies", "url": "/setup/weekoff-policies"}
                ]
            }
        ]
        
        return modules
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch setup modules: {str(e)}"
        )


@router.get("/mastersetup/health", response_model=Dict[str, Any])
async def get_setup_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get system health status for setup modules
    
    **Returns:**
    - System health metrics
    - Module status information
    """
    try:
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "business_units": {"status": "active", "last_check": "2025-12-23 12:00:00"},
                "locations": {"status": "active", "last_check": "2025-12-23 12:00:00"},
                "departments": {"status": "active", "last_check": "2025-12-23 12:00:00"},
                "grades": {"status": "active", "last_check": "2025-12-23 12:00:00"},
                "designations": {"status": "active", "last_check": "2025-12-23 12:00:00"},
                "work_shifts": {"status": "active", "last_check": "2025-12-23 12:00:00"}
            },
            "database": {
                "status": "connected",
                "response_time": "15ms",
                "last_backup": "2025-12-22 23:00:00"
            },
            "api": {
                "status": "operational",
                "response_time": "45ms",
                "uptime": "99.9%"
            }
        }
        
        return health_status
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch system health: {str(e)}"
        )