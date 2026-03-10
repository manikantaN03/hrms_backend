"""
Master Setup API Endpoints
Comprehensive API for all Master Setup modules
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.department import Department
from app.models.location import Location
from app.models.grades import Grade
from app.models.designations import Designation
from app.models.cost_center import CostCenter
from app.models.business_unit import BusinessUnit
from app.models.work_shifts import WorkShift
from app.models.shift_policy import ShiftPolicy
from app.models.weekoff_policy import WeekOffPolicy
from app.models.business_info import BusinessInformation
from app.models.visit_type import VisitType
from app.models.helpdesk_category import HelpdeskCategory
from app.models.workflow import Workflow
from app.models.employee_code_config import EmployeeCodeSetting
from app.models.exit_reason import ExitReason
from app.schemas.master_setup import *
from app.services.shift_policy_service import ShiftPolicyService
from app.services.weekoff_policy_service import WeekOffPolicyService
from app.services.business_info_service import BusinessInformationService
from app.services.visit_type_service import VisitTypeService
from app.services.helpdesk_category_service import (
    create_category_service, get_categories_service, get_category_service,
    update_category_service, delete_category_service
)
from app.services.workflow_service import (
    create_workflow_service, get_workflows_service, get_workflow_service,
    update_workflow_service, delete_workflow_service
)
from app.services.employee_code_service import (
    save_employee_code_setting, get_employee_code_setting, generate_preview_codes,
    regenerate_all_employee_codes
)
from app.services.exit_reason_service import (
    create_exit_reason_service, get_exit_reasons_service, update_exit_reason_service, delete_exit_reason_service
)
from app.schemas.shift_policy import (
    ShiftPolicyCreate, ShiftPolicyUpdate, ShiftPolicyDetailResponse
)
from app.schemas.weekoff_policy import (
    WeekOffPolicyCreate, WeekOffPolicyUpdate, WeekOffPolicyResponse
)
from app.schemas.business_info import (
    BusinessInformationCreate, BusinessInformationUpdate, BusinessInformationResponse
)
from app.schemas.visit_type import (
    VisitTypeCreate, VisitTypeUpdate, VisitTypeResponse
)
from app.schemas.helpdesk_category import (
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse
)
from app.schemas.employee_code_config import (
    EmployeeCodeCreate, EmployeeCodeResponse, RegenerateCodesRequest
)
from app.schemas.exit_reason import (
    ExitReasonCreate, ExitReasonUpdate, ExitReasonResponse
)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_business_id(current_user: User, db: Session) -> int:
    """Get business ID for current user - returns the business they OWN"""
    from app.models.business import Business
    
    # Get businesses owned by this user
    business = db.query(Business).filter(Business.owner_id == current_user.id).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No business found for current user"
        )
    
    return business.id


def validate_business_access(business_id: int, current_user: User, db: Session):
    """Validate user has access to business"""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    return business


# ============================================================================
# Dashboard Endpoint
# ============================================================================

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_master_setup_dashboard(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Master Setup dashboard with all module statistics"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get counts for each module
    departments_count = db.query(Department).filter(Department.business_id == business_id).count()
    locations_count = db.query(Location).filter(Location.business_id == business_id).count()
    grades_count = db.query(Grade).filter(Grade.business_id == business_id).count()
    designations_count = db.query(Designation).filter(Designation.business_id == business_id).count()
    cost_centers_count = db.query(CostCenter).filter(CostCenter.business_id == business_id).count()
    business_units_count = db.query(BusinessUnit).filter(BusinessUnit.business_id == business_id).count()
    work_shifts_count = db.query(WorkShift).filter(WorkShift.business_id == business_id).count()
    
    return {
        "dashboard": {
            "title": "Master Setup Dashboard",
            "description": "Centralized management for all organizational master data",
            "last_updated": datetime.now().isoformat(),
            "business_id": business_id
        },
        "statistics": {
            "total_modules": 15,
            "active_modules": 15,
            "total_records": departments_count + locations_count + grades_count + designations_count + cost_centers_count + business_units_count + work_shifts_count,
            "completion_rate": 100.0
        },
        "modules": [
            {
                "id": "departments",
                "name": "Departments",
                "description": "Organizational departments and hierarchy",
                "icon": "building",
                "url": "/setup/mastersetup/departments",
                "count": departments_count,
                "status": "active"
            },
            {
                "id": "locations",
                "name": "Locations",
                "description": "Office locations and work sites",
                "icon": "map-pin",
                "url": "/setup/mastersetup/locations",
                "count": locations_count,
                "status": "active"
            },
            {
                "id": "grades",
                "name": "Grades",
                "description": "Employee grades and levels",
                "icon": "star",
                "url": "/setup/mastersetup/grades",
                "count": grades_count,
                "status": "active"
            },
            {
                "id": "designations",
                "name": "Designations",
                "description": "Job titles and designations",
                "icon": "briefcase",
                "url": "/setup/mastersetup/designations",
                "count": designations_count,
                "status": "active"
            },
            {
                "id": "cost_centers",
                "name": "Cost Centers",
                "description": "Cost centers for financial tracking",
                "icon": "calculator",
                "url": "/setup/mastersetup/cost-centers",
                "count": cost_centers_count,
                "status": "active"
            },
            {
                "id": "work_shifts",
                "name": "Work Shifts",
                "description": "Employee work shift schedules and timing",
                "icon": "clock",
                "url": "/setup/mastersetup/workshifts",
                "count": work_shifts_count,
                "status": "active"
            },
            {
                "id": "business_units",
                "name": "Business Units",
                "description": "Manage business units and divisions",
                "icon": "building-bank",
                "url": "/setup/bussiness-unit",
                "count": business_units_count,
                "status": "active"
            }
        ]
    }


# ============================================================================
# Departments Endpoints
# ============================================================================

@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all departments for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    departments = db.query(Department).filter(
        Department.business_id == business_id,
        Department.is_active == True
    ).all()
    
    # Filter out departments with empty or whitespace-only names
    # Also handle empty/whitespace head and deputy_head fields
    valid_departments = []
    for dept in departments:
        if dept.name and dept.name.strip():
            # Clean head field - convert empty/whitespace to None
            head_value = dept.head.strip() if dept.head and dept.head.strip() else None
            
            # Clean deputy_head field - convert empty/whitespace to None
            deputy_head_value = dept.deputy_head.strip() if dept.deputy_head and dept.deputy_head.strip() else None
            
            valid_departments.append(
                DepartmentResponse(
                    id=dept.id,
                    business_id=dept.business_id,
                    name=dept.name.strip(),
                    head=head_value,
                    deputy_head=deputy_head_value,
                    is_default=dept.is_default,
                    employees=dept.employees,
                    is_active=dept.is_active,
                    created_at=dept.created_at.isoformat() if dept.created_at else None,
                    updated_at=dept.updated_at.isoformat() if dept.updated_at else None
                )
            )
    
    return valid_departments


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    department: DepartmentCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new department"""
    try:
        if not business_id:
            business_id = get_user_business_id(current_user, db)
        
        validate_business_access(business_id, current_user, db)
        
        # Check if department name already exists
        existing = db.query(Department).filter(
            Department.business_id == business_id,
            Department.name == department.name,
            Department.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department with this name already exists"
            )
        
        # If this is set as default, unset other defaults
        if department.is_default:
            db.query(Department).filter(
                Department.business_id == business_id
            ).update({"is_default": False})
        
        # Create new department
        new_department = Department(
            business_id=business_id,
            name=department.name,
            head=department.head,
            deputy_head=department.deputy_head,
            is_default=department.is_default,
            employees=0,
            is_active=True
        )
        
        db.add(new_department)
        db.commit()
        db.refresh(new_department)
        
        return DepartmentResponse(
            id=new_department.id,
            business_id=new_department.business_id,
            name=new_department.name,
            head=new_department.head,
            deputy_head=new_department.deputy_head,
            is_default=new_department.is_default,
            employees=new_department.employees,
            is_active=new_department.is_active,
            created_at=new_department.created_at.isoformat() if new_department.created_at else None,
            updated_at=new_department.updated_at.isoformat() if new_department.updated_at else None
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department: DepartmentUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a department"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing department
    existing_dept = db.query(Department).filter(
        Department.id == department_id,
        Department.business_id == business_id,
        Department.is_active == True
    ).first()
    
    if not existing_dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Update fields
    update_data = department.model_dump(exclude_unset=True)
    
    # Check for duplicate name if name is being updated
    if "name" in update_data:
        duplicate = db.query(Department).filter(
            Department.business_id == business_id,
            Department.name == update_data["name"],
            Department.id != department_id,
            Department.is_active == True
        ).first()
        
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another department with this name already exists"
            )
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(Department).filter(
            Department.business_id == business_id,
            Department.id != department_id
        ).update({"is_default": False})
    
    # Apply updates
    for field, value in update_data.items():
        setattr(existing_dept, field, value)
    
    existing_dept.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_dept)
    
    return DepartmentResponse(
        id=existing_dept.id,
        business_id=existing_dept.business_id,
        name=existing_dept.name,
        head=existing_dept.head,
        deputy_head=existing_dept.deputy_head,
        is_default=existing_dept.is_default,
        employees=existing_dept.employees,
        is_active=existing_dept.is_active,
        created_at=existing_dept.created_at.isoformat() if existing_dept.created_at else None,
        updated_at=existing_dept.updated_at.isoformat() if existing_dept.updated_at else None
    )


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    business_id: Optional[int] = Query(None),
    force: bool = Query(False, description="Force delete and reassign employees to default department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a department (soft delete)
    
    If force=true, employees will be automatically reassigned to the default department
    """
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing department
    existing_dept = db.query(Department).filter(
        Department.id == department_id,
        Department.business_id == business_id,
        Department.is_active == True
    ).first()
    
    if not existing_dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if department has employees
    if existing_dept.employees > 0:
        if not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete department with {existing_dept.employees} assigned employees. Use force=true to reassign them to default department."
            )
        
        # Force delete: reassign employees to default department
        from app.models.employee import Employee
        
        # Find default department
        default_dept = db.query(Department).filter(
            Department.business_id == business_id,
            Department.is_default == True,
            Department.is_active == True
        ).first()
        
        if not default_dept:
            # If no default department, find any other active department
            default_dept = db.query(Department).filter(
                Department.business_id == business_id,
                Department.id != department_id,
                Department.is_active == True
            ).first()
        
        if not default_dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete department: no other active department found to reassign employees"
            )
        
        # Reassign all employees from this department to default department
        employees_to_reassign = db.query(Employee).filter(
            Employee.department_id == department_id
        ).all()
        
        reassigned_count = len(employees_to_reassign)
        for employee in employees_to_reassign:
            employee.department_id = default_dept.id
        
        # Update employee counts
        default_dept.employees += existing_dept.employees
        existing_dept.employees = 0
    
    # Soft delete
    existing_dept.is_active = False
    existing_dept.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": "Department deleted successfully",
        "employees_reassigned": reassigned_count if force and existing_dept.employees > 0 else 0
    }


# ============================================================================
# Locations Endpoints
# ============================================================================

@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all locations for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    locations = db.query(Location).filter(
        Location.business_id == business_id,
        Location.is_active == True
    ).all()
    
    return [
        LocationResponse(
            id=loc.id,
            business_id=loc.business_id,
            name=loc.name,
            state=loc.state,
            location_head=loc.location_head,
            deputy_head=loc.deputy_head,
            employees=loc.employees,
            is_default=loc.is_default,
            map_url=loc.map_url,
            qr_code_url=loc.qr_code_url,
            is_active=loc.is_active,
            created_at=loc.created_at.isoformat() if loc.created_at else None,
            updated_at=loc.updated_at.isoformat() if loc.updated_at else None
        )
        for loc in locations
    ]


# Alias for singular form (frontend compatibility)
@router.get("/Location", response_model=List[LocationResponse])
async def get_locations_singular(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all locations for a business (singular alias for frontend compatibility)"""
    return await get_locations(business_id, db, current_user)


@router.post("/locations", response_model=LocationResponse)
async def create_location(
    location: LocationCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new location"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Check if location name already exists
    existing = db.query(Location).filter(
        Location.business_id == business_id,
        Location.name == location.name,
        Location.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location with this name already exists"
        )
    
    # If this is set as default, unset other defaults
    if location.is_default:
        db.query(Location).filter(
            Location.business_id == business_id
        ).update({"is_default": False})
    
    # Create new location
    new_location = Location(
        business_id=business_id,
        name=location.name,
        state=location.state,
        location_head=location.location_head,
        deputy_head=location.deputy_head,
        is_default=location.is_default,
        map_url=location.map_url,
        employees=0,
        is_active=True
    )
    
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return LocationResponse(
        id=new_location.id,
        business_id=new_location.business_id,
        name=new_location.name,
        state=new_location.state,
        location_head=new_location.location_head,
        deputy_head=new_location.deputy_head,
        employees=new_location.employees,
        is_default=new_location.is_default,
        map_url=new_location.map_url,
        qr_code_url=new_location.qr_code_url,
        is_active=new_location.is_active,
        created_at=new_location.created_at.isoformat() if new_location.created_at else None,
        updated_at=new_location.updated_at.isoformat() if new_location.updated_at else None
    )


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location: LocationUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a location"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing location
    existing_loc = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == business_id,
        Location.is_active == True
    ).first()
    
    if not existing_loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Update fields
    update_data = location.model_dump(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(Location).filter(
            Location.business_id == business_id,
            Location.id != location_id
        ).update({"is_default": False})
    
    # Apply updates
    for field, value in update_data.items():
        setattr(existing_loc, field, value)
    
    existing_loc.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_loc)
    
    return LocationResponse(
        id=existing_loc.id,
        business_id=existing_loc.business_id,
        name=existing_loc.name,
        state=existing_loc.state,
        location_head=existing_loc.location_head,
        deputy_head=existing_loc.deputy_head,
        employees=existing_loc.employees,
        is_default=existing_loc.is_default,
        map_url=existing_loc.map_url,
        qr_code_url=existing_loc.qr_code_url,
        is_active=existing_loc.is_active,
        created_at=existing_loc.created_at.isoformat() if existing_loc.created_at else None,
        updated_at=existing_loc.updated_at.isoformat() if existing_loc.updated_at else None
    )


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    business_id: Optional[int] = Query(None),
    force: bool = Query(False, description="Force delete and reassign employees to default location"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a location (soft delete)
    
    If force=true, employees will be automatically reassigned to the default location
    """
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing location
    existing_loc = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == business_id,
        Location.is_active == True
    ).first()
    
    if not existing_loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if location has employees
    if existing_loc.employees > 0:
        if not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete location with {existing_loc.employees} assigned employees. Use force=true to reassign them to default location."
            )
        
        # Force delete: reassign employees to default location
        from app.models.employee import Employee
        
        # Find default location
        default_location = db.query(Location).filter(
            Location.business_id == business_id,
            Location.is_default == True,
            Location.is_active == True
        ).first()
        
        if not default_location:
            # If no default location, find any other active location
            default_location = db.query(Location).filter(
                Location.business_id == business_id,
                Location.id != location_id,
                Location.is_active == True
            ).first()
        
        if not default_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete location: no other active location found to reassign employees"
            )
        
        # Reassign all employees from this location to default location
        employees_to_reassign = db.query(Employee).filter(
            Employee.location_id == location_id
        ).all()
        
        for employee in employees_to_reassign:
            employee.location_id = default_location.id
        
        # Update employee counts
        default_location.employees += existing_loc.employees
        existing_loc.employees = 0
    
    # Soft delete
    existing_loc.is_active = False
    existing_loc.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": "Location deleted successfully",
        "employees_reassigned": existing_loc.employees if force else 0
    }


# ============================================================================
# Location QR Code Endpoints
# ============================================================================

@router.post("/locations/generate-qr/{location_id}")
async def generate_location_qr(
    location_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Generate a QR code for a location
    
    The QR code contains a URL to the public location info page
    """
    import uuid
    import qrcode
    from pathlib import Path
    from app.core.config import settings, BASE_URL
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get location
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == business_id,
        Location.is_active == True
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    try:
        # Setup upload directories
        BASE_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
        BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        LOC_QR_DIR = BASE_UPLOAD_DIR / "locations" / "qr"
        LOC_QR_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate QR code with URL to public location info page
        qr_data = f"{BASE_URL}/api/v1/public/location-info/{location_id}?business_id={business_id}"
        qr_img = qrcode.make(qr_data)
        
        filename = f"{uuid.uuid4()}.png"
        filepath = LOC_QR_DIR / filename
        qr_img.save(str(filepath))
        
        qr_url = f"{BASE_URL}/{settings.UPLOAD_DIR}/locations/qr/{filename}"
        
        # Update location with QR code URL
        location.qr_code_url = qr_url
        location.updated_at = datetime.now()
        db.commit()
        
        return {
            "message": "QR Code generated successfully",
            "qrCodeUrl": qr_url,
            "qrData": qr_data,
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate QR code: {str(e)}"
        )


@router.get("/locations/{business_id}/qr/{location_id}")
async def get_location_qr(
    business_id: int,
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get QR code image for a location"""
    from pathlib import Path
    from fastapi.responses import FileResponse
    from app.core.config import settings
    
    validate_business_access(business_id, current_user, db)
    
    # Get location
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == business_id,
        Location.is_active == True
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    if not location.qr_code_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not generated for this location"
        )
    
    # Extract filename from URL and construct file path
    filename = Path(location.qr_code_url).name
    BASE_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
    LOC_QR_DIR = BASE_UPLOAD_DIR / "locations" / "qr"
    file_path = LOC_QR_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR image file not found"
        )
    
    return FileResponse(str(file_path))


# ============================================================================
# Grades Endpoints
# ============================================================================

@router.get("/grades", response_model=List[GradeResponse])
async def get_grades(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all grades for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    grades = db.query(Grade).filter(
        Grade.business_id == business_id,
        Grade.is_active == True
    ).all()
    
    # Filter out grades with empty or whitespace-only names
    valid_grades = []
    for grade in grades:
        if grade.name and grade.name.strip():
            valid_grades.append(
                GradeResponse(
                    id=grade.id,
                    business_id=grade.business_id,
                    name=grade.name.strip(),
                    employees=grade.employees,
                    created_at=grade.created_at.isoformat() if grade.created_at else None,
                    updated_at=grade.updated_at.isoformat() if grade.updated_at else None
                )
            )
    
    return valid_grades


@router.post("/grades", response_model=GradeResponse)
async def create_grade(
    grade: GradeCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new grade"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Check if grade name already exists
    existing = db.query(Grade).filter(
        Grade.business_id == business_id,
        Grade.name == grade.name,
        Grade.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grade with this name already exists"
        )
    
    # Create new grade
    new_grade = Grade(
        business_id=business_id,
        name=grade.name,
        employees=0,
        is_active=True
    )
    
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    
    return GradeResponse(
        id=new_grade.id,
        business_id=new_grade.business_id,
        name=new_grade.name,
        employees=new_grade.employees,
        created_at=new_grade.created_at.isoformat() if new_grade.created_at else None,
        updated_at=new_grade.updated_at.isoformat() if new_grade.updated_at else None
    )


@router.put("/grades/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: int,
    grade: GradeUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a grade"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing grade
    existing_grade = db.query(Grade).filter(
        Grade.id == grade_id,
        Grade.business_id == business_id,
        Grade.is_active == True
    ).first()
    
    if not existing_grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )
    
    # Update fields
    update_data = grade.model_dump(exclude_unset=True)
    
    # Apply updates
    for field, value in update_data.items():
        setattr(existing_grade, field, value)
    
    existing_grade.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_grade)
    
    return GradeResponse(
        id=existing_grade.id,
        business_id=existing_grade.business_id,
        name=existing_grade.name,
        employees=existing_grade.employees,
        created_at=existing_grade.created_at.isoformat() if existing_grade.created_at else None,
        updated_at=existing_grade.updated_at.isoformat() if existing_grade.updated_at else None
    )


@router.delete("/grades/{grade_id}")
async def delete_grade(
    grade_id: int,
    business_id: Optional[int] = Query(None),
    force: bool = Query(False, description="Force delete and set employees grade to NULL"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a grade (soft delete)
    
    If force=true, employees will have their grade set to NULL
    """
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing grade
    existing_grade = db.query(Grade).filter(
        Grade.id == grade_id,
        Grade.business_id == business_id,
        Grade.is_active == True
    ).first()
    
    if not existing_grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )
    
    # Check if grade has employees
    if existing_grade.employees > 0:
        if not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete grade with {existing_grade.employees} assigned employees. Use force=true to remove grade assignment."
            )
        
        # Force delete: remove grade from employees
        from app.models.employee import Employee
        
        employees_to_update = db.query(Employee).filter(
            Employee.grade_id == grade_id
        ).all()
        
        reassigned_count = len(employees_to_update)
        for employee in employees_to_update:
            employee.grade_id = None
        
        existing_grade.employees = 0
    
    # Soft delete
    existing_grade.is_active = False
    existing_grade.updated_at = datetime.now()
    db.commit()
    
    return {
        "message": "Grade deleted successfully",
        "employees_updated": reassigned_count if force and existing_grade.employees > 0 else 0
    }
    
    return {"message": "Grade deleted successfully"}


# ============================================================================
# Designations Endpoints
# ============================================================================

@router.get("/designations", response_model=List[DesignationResponse])
async def get_designations(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all designations for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    designations = db.query(Designation).filter(
        Designation.business_id == business_id,
        Designation.is_active == True
    ).all()
    
    return [
        DesignationResponse(
            id=desig.id,
            business_id=desig.business_id,
            name=desig.name,
            default=desig.default,
            employees=desig.employees,
            created_at=desig.created_at.isoformat() if desig.created_at else None,
            updated_at=desig.updated_at.isoformat() if desig.updated_at else None
        )
        for desig in designations
    ]


@router.post("/designations", response_model=DesignationResponse)
async def create_designation(
    designation: DesignationCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new designation"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Check if designation name already exists
    existing = db.query(Designation).filter(
        Designation.business_id == business_id,
        Designation.name == designation.name,
        Designation.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Designation with this name already exists"
        )
    
    # If this is set as default, unset other defaults
    if designation.default:
        db.query(Designation).filter(
            Designation.business_id == business_id
        ).update({"default": False})
    
    # Create new designation
    new_designation = Designation(
        business_id=business_id,
        name=designation.name,
        default=designation.default,
        employees=0,
        is_active=True
    )
    
    db.add(new_designation)
    db.commit()
    db.refresh(new_designation)
    
    return DesignationResponse(
        id=new_designation.id,
        business_id=new_designation.business_id,
        name=new_designation.name,
        default=new_designation.default,
        employees=new_designation.employees,
        created_at=new_designation.created_at.isoformat() if new_designation.created_at else None,
        updated_at=new_designation.updated_at.isoformat() if new_designation.updated_at else None
    )


@router.put("/designations/{designation_id}", response_model=DesignationResponse)
async def update_designation(
    designation_id: int,
    designation: DesignationUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a designation"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing designation
    existing_desig = db.query(Designation).filter(
        Designation.id == designation_id,
        Designation.business_id == business_id,
        Designation.is_active == True
    ).first()
    
    if not existing_desig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Designation not found"
        )
    
    # Update fields
    update_data = designation.model_dump(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get("default"):
        db.query(Designation).filter(
            Designation.business_id == business_id,
            Designation.id != designation_id
        ).update({"default": False})
    
    # Apply updates
    for field, value in update_data.items():
        setattr(existing_desig, field, value)
    
    existing_desig.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_desig)
    
    return DesignationResponse(
        id=existing_desig.id,
        business_id=existing_desig.business_id,
        name=existing_desig.name,
        default=existing_desig.default,
        employees=existing_desig.employees,
        created_at=existing_desig.created_at.isoformat() if existing_desig.created_at else None,
        updated_at=existing_desig.updated_at.isoformat() if existing_desig.updated_at else None
    )


@router.delete("/designations/{designation_id}")
async def delete_designation(
    designation_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a designation (soft delete)"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing designation
    existing_desig = db.query(Designation).filter(
        Designation.id == designation_id,
        Designation.business_id == business_id,
        Designation.is_active == True
    ).first()
    
    if not existing_desig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Designation not found"
        )
    
    # Check if designation has employees
    if existing_desig.employees > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete designation with assigned employees"
        )
    
    # Soft delete
    existing_desig.is_active = False
    existing_desig.updated_at = datetime.now()
    db.commit()
    
    return {"message": "Designation deleted successfully"}


# ============================================================================
# Work Shifts Endpoints
# ============================================================================

@router.get("/workshifts", response_model=List[WorkShiftResponse])
async def get_work_shifts(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all work shifts for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    work_shifts = db.query(WorkShift).filter(
        WorkShift.business_id == business_id,
        WorkShift.is_active == True
    ).all()
    
    return [
        WorkShiftResponse(
            id=ws.id,
            business_id=ws.business_id,
            code=ws.code,
            name=ws.name,
            payable_hours=ws.payable_hrs,
            rules=ws.rules,
            is_default=ws.default,
            timing=ws.timing,
            start_buffer=ws.start_buffer_hours,
            end_buffer=ws.end_buffer_hours,
            is_active=ws.is_active,
            created_at=ws.created_at.isoformat() if ws.created_at else None,
            updated_at=ws.updated_at.isoformat() if ws.updated_at else None
        )
        for ws in work_shifts
    ]


@router.post("/workshifts", response_model=WorkShiftResponse)
async def create_work_shift(
    work_shift: WorkShiftCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new work shift"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Check if work shift code already exists
    existing = db.query(WorkShift).filter(
        WorkShift.business_id == business_id,
        WorkShift.code == work_shift.code,
        WorkShift.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work shift with this code already exists"
        )
    
    # If this is set as default, unset other defaults
    if work_shift.is_default:
        db.query(WorkShift).filter(
            WorkShift.business_id == business_id
        ).update({"default": False})
    
    # Create new work shift
    new_work_shift = WorkShift(
        business_id=business_id,
        code=work_shift.code,
        name=work_shift.name,
        payable_hrs=work_shift.payable_hours,
        rules=work_shift.rules,
        default=work_shift.is_default,
        timing=work_shift.timing,
        start_buffer_hours=work_shift.start_buffer,
        end_buffer_hours=work_shift.end_buffer,
        is_active=True
    )
    
    db.add(new_work_shift)
    db.commit()
    db.refresh(new_work_shift)
    
    return WorkShiftResponse(
        id=new_work_shift.id,
        business_id=new_work_shift.business_id,
        code=new_work_shift.code,
        name=new_work_shift.name,
        payable_hours=new_work_shift.payable_hrs,
        rules=new_work_shift.rules,
        is_default=new_work_shift.default,
        timing=new_work_shift.timing,
        start_buffer=new_work_shift.start_buffer_hours,
        end_buffer=new_work_shift.end_buffer_hours,
        is_active=new_work_shift.is_active,
        created_at=new_work_shift.created_at.isoformat() if new_work_shift.created_at else None,
        updated_at=new_work_shift.updated_at.isoformat() if new_work_shift.updated_at else None
    )


@router.put("/workshifts/{work_shift_id}", response_model=WorkShiftResponse)
async def update_work_shift(
    work_shift_id: int,
    work_shift: WorkShiftUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a work shift"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing work shift
    existing_ws = db.query(WorkShift).filter(
        WorkShift.id == work_shift_id,
        WorkShift.business_id == business_id,
        WorkShift.is_active == True
    ).first()
    
    if not existing_ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work shift not found"
        )
    
    # Update fields
    update_data = work_shift.model_dump(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(WorkShift).filter(
            WorkShift.business_id == business_id,
            WorkShift.id != work_shift_id
        ).update({"default": False})
    
    # Apply updates with field mapping
    for field, value in update_data.items():
        if field == "payable_hours":
            setattr(existing_ws, "payable_hrs", value)
        elif field == "is_default":
            setattr(existing_ws, "default", value)
        elif field == "start_buffer":
            setattr(existing_ws, "start_buffer_hours", value)
        elif field == "end_buffer":
            setattr(existing_ws, "end_buffer_hours", value)
        else:
            setattr(existing_ws, field, value)
    
    existing_ws.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_ws)
    
    return WorkShiftResponse(
        id=existing_ws.id,
        business_id=existing_ws.business_id,
        code=existing_ws.code,
        name=existing_ws.name,
        payable_hours=existing_ws.payable_hrs,
        rules=existing_ws.rules,
        is_default=existing_ws.default,
        timing=existing_ws.timing,
        start_buffer=existing_ws.start_buffer_hours,
        end_buffer=existing_ws.end_buffer_hours,
        is_active=existing_ws.is_active,
        created_at=existing_ws.created_at.isoformat() if existing_ws.created_at else None,
        updated_at=existing_ws.updated_at.isoformat() if existing_ws.updated_at else None
    )


@router.delete("/workshifts/{work_shift_id}")
async def delete_work_shift(
    work_shift_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a work shift (soft delete)"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing work shift
    existing_ws = db.query(WorkShift).filter(
        WorkShift.id == work_shift_id,
        WorkShift.business_id == business_id,
        WorkShift.is_active == True
    ).first()
    
    if not existing_ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work shift not found"
        )
    
    # Soft delete
    existing_ws.is_active = False
    existing_ws.updated_at = datetime.now()
    db.commit()
    
    return {"message": "Work shift deleted successfully"}


# ============================================================================# ============================================================================
# Cost Centers Endpoints
# ============================================================================

@router.get("/cost-centers", response_model=List[CostCenterResponse])
async def get_cost_centers(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all cost centers for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    cost_centers = db.query(CostCenter).filter(
        CostCenter.business_id == business_id,
        CostCenter.is_active == True
    ).all()
    
    return [
        CostCenterResponse(
            id=cc.id,
            business_id=cc.business_id,
            name=cc.name,
            is_default=cc.is_default,
            employees=cc.employees,
            is_active=cc.is_active,
            created_at=cc.created_at.isoformat() if cc.created_at else None,
            updated_at=cc.updated_at.isoformat() if cc.updated_at else None
        )
        for cc in cost_centers
    ]


@router.post("/cost-centers", response_model=CostCenterResponse)
async def create_cost_center(
    cost_center: CostCenterCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new cost center
    
    - **name**: Cost center name (required, 1-255 characters)
    - **is_default**: Whether this should be the default cost center (optional, default: False)
    
    Returns the created cost center with auto-generated ID and timestamps.
    If a cost center with the same name exists, returns the existing one.
    """
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Validate name is not empty or whitespace only
    if not cost_center.name or not cost_center.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cost center name cannot be empty or whitespace only"
        )
    
    # Check if cost center name already exists
    existing = db.query(CostCenter).filter(
        CostCenter.business_id == business_id,
        CostCenter.name == cost_center.name.strip(),
        CostCenter.is_active == True
    ).first()
    
    if existing:
        # If exists and trying to set as default, update the existing one
        if cost_center.is_default and not existing.is_default:
            # Unset other defaults
            db.query(CostCenter).filter(
                CostCenter.business_id == business_id,
                CostCenter.id != existing.id
            ).update({"is_default": False})
            
            existing.is_default = True
            existing.updated_at = datetime.now()
            db.commit()
            db.refresh(existing)

        return CostCenterResponse(
            id=existing.id,
            business_id=existing.business_id,
            name=existing.name,
            is_default=existing.is_default,
            employees=existing.employees,
            is_active=existing.is_active,
            created_at=existing.created_at.isoformat() if existing.created_at else None,
            updated_at=existing.updated_at.isoformat() if existing.updated_at else None
        )
    
    # If this is set as default, unset other defaults
    if cost_center.is_default:
        db.query(CostCenter).filter(
            CostCenter.business_id == business_id
        ).update({"is_default": False})
    
    # Create new cost center
    new_cost_center = CostCenter(
        business_id=business_id,
        name=cost_center.name.strip(),
        is_default=cost_center.is_default,
        employees=0,
        is_active=True
    )
    
    db.add(new_cost_center)
    db.commit()
    db.refresh(new_cost_center)
    
    return CostCenterResponse(
        id=new_cost_center.id,
        business_id=new_cost_center.business_id,
        name=new_cost_center.name,
        is_default=new_cost_center.is_default,
        employees=new_cost_center.employees,
        is_active=new_cost_center.is_active,
        created_at=new_cost_center.created_at.isoformat() if new_cost_center.created_at else None,
        updated_at=new_cost_center.updated_at.isoformat() if new_cost_center.updated_at else None
    )


@router.put("/cost-centers/{cost_center_id}", response_model=CostCenterResponse)
async def update_cost_center(
    cost_center_id: int,
    cost_center: CostCenterUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a cost center
    
    - **name**: New cost center name (optional, 1-255 characters)
    - **is_default**: Whether this should be the default cost center (optional)
    
    Note: Employee count is auto-calculated and cannot be manually updated.
    Note: business_id cannot be changed after creation.
    """
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Validate at least one field is provided
    update_data = cost_center.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field must be provided for update"
        )
    
    # Get existing cost center
    existing_cc = db.query(CostCenter).filter(
        CostCenter.id == cost_center_id,
        CostCenter.business_id == business_id,
        CostCenter.is_active == True
    ).first()
    
    if not existing_cc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found"
        )
    
    # Validate name if provided
    if "name" in update_data:
        if not update_data["name"] or not update_data["name"].strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cost center name cannot be empty or whitespace only"
            )
        
        # Check for duplicate name
        duplicate = db.query(CostCenter).filter(
            CostCenter.business_id == business_id,
            CostCenter.name == update_data["name"].strip(),
            CostCenter.id != cost_center_id,
            CostCenter.is_active == True
        ).first()
        
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another cost center with this name already exists"
            )
        
        update_data["name"] = update_data["name"].strip()
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(CostCenter).filter(
            CostCenter.business_id == business_id,
            CostCenter.id != cost_center_id
        ).update({"is_default": False})
    
    # Apply updates
    for field, value in update_data.items():
        setattr(existing_cc, field, value)
    
    existing_cc.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_cc)
    
    return CostCenterResponse(
        id=existing_cc.id,
        business_id=existing_cc.business_id,
        name=existing_cc.name,
        is_default=existing_cc.is_default,
        employees=existing_cc.employees,
        is_active=existing_cc.is_active,
        created_at=existing_cc.created_at.isoformat() if existing_cc.created_at else None,
        updated_at=existing_cc.updated_at.isoformat() if existing_cc.updated_at else None
    )


@router.delete("/cost-centers/{cost_center_id}")
async def delete_cost_center(
    cost_center_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a cost center (soft delete)"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing cost center
    existing_cc = db.query(CostCenter).filter(
        CostCenter.id == cost_center_id,
        CostCenter.business_id == business_id,
        CostCenter.is_active == True
    ).first()
    
    if not existing_cc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found"
        )
    
    # Check if cost center has employees
    if existing_cc.employees > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete cost center with assigned employees"
        )
    
    # Soft delete
    existing_cc.is_active = False
    existing_cc.updated_at = datetime.now()
    
    db.commit()
    
    return {"message": "Cost center deleted successfully"}


# ============================================================================
# Business Units Endpoints
# ============================================================================

@router.get("/business-units", response_model=List[BusinessUnitResponse])
async def get_business_units(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all business units for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    business_units = db.query(BusinessUnit).filter(
        BusinessUnit.business_id == business_id,
        BusinessUnit.is_active == True
    ).all()
    
    return [
        BusinessUnitResponse(
            id=bu.id,
            business_id=bu.business_id,
            name=bu.name,
            company=bu.business.business_name if bu.business else "Unknown Company",
            is_default=bu.is_default,
            employees=bu.employees,
            report_title=bu.report_title,
            header_image=bu.header_image_url,
            footer_image=bu.footer_image_url,
            is_active=bu.is_active,
            created_at=bu.created_at.isoformat() if bu.created_at else None,
            updated_at=bu.updated_at.isoformat() if bu.updated_at else None
        )
        for bu in business_units
    ]


@router.post("/business-units", response_model=BusinessUnitResponse)
async def create_business_unit(
    business_unit: BusinessUnitCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new business unit"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Check if business unit name already exists
    existing = db.query(BusinessUnit).filter(
        BusinessUnit.business_id == business_id,
        BusinessUnit.name == business_unit.name,
        BusinessUnit.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business unit with this name already exists"
        )
    
    # If this is set as default, unset other defaults
    if business_unit.is_default:
        db.query(BusinessUnit).filter(
            BusinessUnit.business_id == business_id
        ).update({"is_default": False})
    
    # Create new business unit
    new_business_unit = BusinessUnit(
        business_id=business_id,
        name=business_unit.name,
        report_title=business_unit.report_title,
        is_default=business_unit.is_default,
        employees=0,
        is_active=True
    )
    
    db.add(new_business_unit)
    db.commit()
    db.refresh(new_business_unit)
    
    return BusinessUnitResponse(
        id=new_business_unit.id,
        business_id=new_business_unit.business_id,
        name=new_business_unit.name,
        company=new_business_unit.business.business_name if new_business_unit.business else "Unknown Company",
        is_default=new_business_unit.is_default,
        employees=new_business_unit.employees,
        report_title=new_business_unit.report_title,
        header_image=new_business_unit.header_image_url,
        footer_image=new_business_unit.footer_image_url,
        is_active=new_business_unit.is_active,
        created_at=new_business_unit.created_at.isoformat() if new_business_unit.created_at else None,
        updated_at=new_business_unit.updated_at.isoformat() if new_business_unit.updated_at else None
    )


@router.put("/business-units/{business_unit_id}", response_model=BusinessUnitResponse)
async def update_business_unit(
    business_unit_id: int,
    business_unit: BusinessUnitUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a business unit"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing business unit
    existing_bu = db.query(BusinessUnit).filter(
        BusinessUnit.id == business_unit_id,
        BusinessUnit.business_id == business_id,
        BusinessUnit.is_active == True
    ).first()
    
    if not existing_bu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business unit not found"
        )
    
    # Update fields
    update_data = business_unit.model_dump(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(BusinessUnit).filter(
            BusinessUnit.business_id == business_id,
            BusinessUnit.id != business_unit_id
        ).update({"is_default": False})
    
    # Apply updates
    for field, value in update_data.items():
        setattr(existing_bu, field, value)
    
    existing_bu.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_bu)
    
    return BusinessUnitResponse(
        id=existing_bu.id,
        business_id=existing_bu.business_id,
        name=existing_bu.name,
        company=existing_bu.business.business_name if existing_bu.business else "Unknown Company",
        is_default=existing_bu.is_default,
        employees=existing_bu.employees,
        report_title=existing_bu.report_title,
        header_image=existing_bu.header_image_url,
        footer_image=existing_bu.footer_image_url,
        is_active=existing_bu.is_active,
        created_at=existing_bu.created_at.isoformat() if existing_bu.created_at else None,
        updated_at=existing_bu.updated_at.isoformat() if existing_bu.updated_at else None
    )


@router.delete("/business-units/{business_unit_id}")
async def delete_business_unit(
    business_unit_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a business unit (soft delete)"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Get existing business unit
    existing_bu = db.query(BusinessUnit).filter(
        BusinessUnit.id == business_unit_id,
        BusinessUnit.business_id == business_id,
        BusinessUnit.is_active == True
    ).first()
    
    if not existing_bu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business unit not found"
        )
    
    # Check if business unit has employees
    if existing_bu.employees > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete business unit with assigned employees"
        )
    
    # Soft delete
    existing_bu.is_active = False
    existing_bu.updated_at = datetime.now()
    
    db.commit()
    
    return {"message": "Business unit deleted successfully"}


# ============================================================================
# Shift Policy Editor Endpoints
# ============================================================================

@router.get("/shiftpolicyeditor", response_model=List[ShiftPolicyDetailResponse])
async def get_shift_policies(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shift policies for shift policy editor"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return ShiftPolicyService.get_all_policies(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/shiftpolicyeditor", response_model=ShiftPolicyDetailResponse)
async def create_shift_policy(
    shift_policy: ShiftPolicyCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new shift policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    shift_policy.business_id = business_id
    
    try:
        return ShiftPolicyService.create_policy(db, shift_policy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/shiftpolicyeditor/default", response_model=ShiftPolicyDetailResponse)
async def get_default_shift_policy(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the default shift policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return ShiftPolicyService.get_default_policy(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/shiftpolicyeditor/{policy_id}", response_model=ShiftPolicyDetailResponse)
async def get_shift_policy(
    policy_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific shift policy by ID"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return ShiftPolicyService.get_policy_by_id(db, policy_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/shiftpolicyeditor/{policy_id}", response_model=ShiftPolicyDetailResponse)
async def update_shift_policy(
    policy_id: int,
    shift_policy: ShiftPolicyUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a shift policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    shift_policy.business_id = business_id
    
    try:
        return ShiftPolicyService.update_policy(db, policy_id, business_id, shift_policy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/shiftpolicyeditor/{policy_id}")
async def delete_shift_policy(
    policy_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a shift policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        ShiftPolicyService.delete_policy(db, policy_id, business_id)
        return {"message": "Shift policy deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# Week Off Policy Endpoints
# ============================================================================

@router.get("/weekoff", response_model=List[WeekOffPolicyResponse])
async def get_weekoff_policies(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all week off policies"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return WeekOffPolicyService.get_all_policies(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/weekoff", response_model=WeekOffPolicyResponse)
async def create_weekoff_policy(
    weekoff_policy: WeekOffPolicyCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new week off policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    weekoff_policy.business_id = business_id
    
    try:
        return WeekOffPolicyService.create_policy(db, weekoff_policy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/weekoff/default", response_model=WeekOffPolicyResponse)
async def get_default_weekoff_policy(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the default week off policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return WeekOffPolicyService.get_default_policy(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/weekoff/{policy_id}", response_model=WeekOffPolicyResponse)
async def get_weekoff_policy(
    policy_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific week off policy by ID"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return WeekOffPolicyService.get_policy_by_id(db, policy_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/weekoff/{policy_id}", response_model=WeekOffPolicyResponse)
async def update_weekoff_policy(
    policy_id: int,
    weekoff_policy: WeekOffPolicyUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a week off policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    weekoff_policy.business_id = business_id
    
    try:
        return WeekOffPolicyService.update_policy(db, policy_id, business_id, weekoff_policy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/weekoff/{policy_id}")
async def delete_weekoff_policy(
    policy_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a week off policy"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        WeekOffPolicyService.delete_policy(db, policy_id, business_id)
        return {"message": "Week off policy deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# Business Info Endpoints
# ============================================================================

@router.get("/bussinesinfo", response_model=BusinessInformationResponse)
async def get_business_info(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get business information"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return BusinessInformationService.get_business_information(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/bussinesinfo", response_model=BusinessInformationResponse)
async def create_business_info(
    business_info: BusinessInformationCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create business information"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    business_info.business_id = business_id
    
    try:
        return BusinessInformationService.create_business_information(db, business_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/bussinesinfo", response_model=BusinessInformationResponse)
async def update_business_info(
    business_info: BusinessInformationUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update business information"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    business_info.business_id = business_id
    
    try:
        return BusinessInformationService.update_business_information(db, business_id, business_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/bussinesinfo")
async def delete_business_info(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete business information"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        BusinessInformationService.delete_business_information(db, business_id)
        return {"message": "Business information deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# Visit Types Endpoints
# ============================================================================

@router.get("/visit-types", response_model=List[VisitTypeResponse])
async def get_visit_types(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all visit types for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return VisitTypeService.get_all_visit_types(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/visit-types", response_model=VisitTypeResponse)
async def create_visit_type(
    visit_type: VisitTypeCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new visit type"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    visit_type.business_id = business_id
    
    try:
        return VisitTypeService.create_visit_type(db, visit_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/visit-types/{visit_type_id}", response_model=VisitTypeResponse)
async def get_visit_type(
    visit_type_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific visit type by ID"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return VisitTypeService.get_visit_type_by_id(db, visit_type_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/visit-types/{visit_type_id}", response_model=VisitTypeResponse)
async def update_visit_type(
    visit_type_id: int,
    visit_type: VisitTypeUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a visit type"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    visit_type.business_id = business_id
    
    try:
        return VisitTypeService.update_visit_type(db, visit_type_id, business_id, visit_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/visit-types/{visit_type_id}")
async def delete_visit_type(
    visit_type_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a visit type"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return VisitTypeService.delete_visit_type(db, visit_type_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# Helpdesk Categories Endpoints
# ============================================================================

@router.get("/helpdesk-categories", response_model=List[CategoryResponse])
async def get_helpdesk_categories(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all helpdesk categories for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return get_categories_service(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/helpdesk-categories", response_model=CategoryResponse)
async def create_helpdesk_category(
    category: CategoryCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new helpdesk category"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    category.business_id = business_id
    
    try:
        return create_category_service(db, category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/helpdesk-categories/{category_id}", response_model=CategoryResponse)
async def get_helpdesk_category(
    category_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific helpdesk category by ID"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return get_category_service(db, category_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/helpdesk-categories/{category_id}", response_model=CategoryResponse)
async def update_helpdesk_category(
    category_id: int,
    category: CategoryUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a helpdesk category"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    category.business_id = business_id
    
    try:
        return update_category_service(db, category_id, business_id, category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/helpdesk-categories/{category_id}")
async def delete_helpdesk_category(
    category_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a helpdesk category"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return delete_category_service(db, category_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# Employee Code Configuration Endpoints
# ============================================================================

@router.get("/employee-code/{business_id}", response_model=EmployeeCodeResponse)
async def get_employee_code_config(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee code configuration for a business"""
    
    validate_business_access(business_id, current_user, db)
    
    try:
        config = get_employee_code_setting(db, business_id)
        if not config:
            # Return default configuration if none exists
            return EmployeeCodeResponse(
                id=0,
                business_id=business_id,
                autoCode=True,
                prefix="EMP",
                length=3,
                suffix=""
            )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve employee code configuration: {str(e)}"
        )


@router.post("/employee-code", response_model=EmployeeCodeResponse)
async def save_employee_code_config(
    config: EmployeeCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Save or update employee code configuration"""
    
    # Get business_id from authenticated user
    business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Validate business_id in payload matches user's business
    if config.business_id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify configuration for a different business"
        )
    
    try:
        return save_employee_code_setting(db, business_id, config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save employee code configuration: {str(e)}"
        )


@router.get("/employee-code/{business_id}/preview")
async def preview_employee_codes(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview generated employee codes based on configuration"""
    
    validate_business_access(business_id, current_user, db)
    
    try:
        config = get_employee_code_setting(db, business_id)
        if not config:
            # Use default configuration for preview
            from app.schemas.employee_code_config import EmployeeCodeCreate
            config = EmployeeCodeCreate(
                business_id=business_id,
                autoCode=True,
                prefix="EMP",
                length=3,
                suffix=""
            )
        
        preview_samples = generate_preview_codes(config)
        
        return {
            "business_id": business_id,
            "configuration": config,
            "preview_samples": preview_samples,
            "description": "Sample employee codes generated based on current configuration"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/employee-code/{business_id}/regenerate")
async def regenerate_employee_codes(
    business_id: int,
    request: RegenerateCodesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Regenerate employee codes for all active employees.
    This will overwrite existing employee codes based on the current configuration.
    
    Parameters:
    - sort_by: Sort employees by 'dateJoining' (default) or 'employeeName'
    """
    
    validate_business_access(business_id, current_user, db)
    
    # Validate sort_by parameter
    if request.sort_by not in ["dateJoining", "employeeName"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_by must be either 'dateJoining' or 'employeeName'"
        )
    
    try:
        result = regenerate_all_employee_codes(db, business_id, request.sort_by)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to regenerate employee codes")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate employee codes: {str(e)}"
        )


# ============================================================================
# Exit Reasons Endpoints
# ============================================================================

@router.get("/exit-reasons", response_model=List[ExitReasonResponse])
async def get_exit_reasons(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all exit reasons for a business"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return get_exit_reasons_service(db, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/exit-reasons", response_model=ExitReasonResponse)
async def create_exit_reason(
    exit_reason: ExitReasonCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new exit reason"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    exit_reason.business_id = business_id
    
    try:
        return create_exit_reason_service(db, exit_reason)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/exit-reasons/{reason_id}", response_model=ExitReasonResponse)
async def update_exit_reason(
    reason_id: int,
    exit_reason: ExitReasonUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an exit reason"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    # Set business_id in the payload
    exit_reason.business_id = business_id
    
    try:
        return update_exit_reason_service(db, reason_id, business_id, exit_reason)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/exit-reasons/{reason_id}")
async def delete_exit_reason(
    reason_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete an exit reason"""
    
    if not business_id:
        business_id = get_user_business_id(current_user, db)
    
    validate_business_access(business_id, current_user, db)
    
    try:
        return delete_exit_reason_service(db, reason_id, business_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )