"""
Maintenance API Endpoints
Handles system maintenance operations like salary recalculation and work profile updates
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.services.maintenance_service import MaintenanceService
from app.schemas.maintenance_schema import (
    MaintenanceResponse,
    RecalculateSalaryRequest,
    RecalculateSalaryResponse,
    UpdateWorkProfileRequest,
    UpdateWorkProfileResponse
)

router = APIRouter()


@router.post(
    "/maintenance/recalculate-salary",
    response_model=RecalculateSalaryResponse,
    summary="Recalculate Salary Totals",
    description="Recalculates salary totals for salary revisions. Use this if you have deleted any salary component or deduction and the salary totals are not updated."
)
async def recalculate_salary_totals(
    request: Optional[RecalculateSalaryRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> RecalculateSalaryResponse:
    """
    Recalculate salary totals for all employees or specific employees.
    This function recalculates salary totals for salary revisions.
    """
    try:
        business_id = getattr(current_user, 'business_id', 1)
        
        service = MaintenanceService(db)
        result = service.recalculate_salary_totals(
            business_id=business_id,
            employee_ids=request.employee_ids if request else None,
            updated_by=current_user.id
        )
        
        return RecalculateSalaryResponse(
            success=True,
            message="Salary totals recalculated successfully",
            total_employees=result["total_employees"],
            updated_employees=result["updated_employees"],
            failed_employees=result["failed_employees"],
            errors=result.get("errors", []),
            execution_time=result["execution_time"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate salary totals: {str(e)}"
        )


@router.post(
    "/maintenance/update-work-profile",
    response_model=UpdateWorkProfileResponse,
    summary="Update Work Profile Records",
    description="Updates missing work profile records and fixes duplicate work profile records. Use this if employee record exists but not appearing in All Employees list."
)
async def update_work_profile_records(
    request: Optional[UpdateWorkProfileRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> UpdateWorkProfileResponse:
    """
    Update work profile records for employees.
    This function updates missing work profile records and fixes duplicate work profile records.
    """
    try:
        business_id = getattr(current_user, 'business_id', 1)
        
        service = MaintenanceService(db)
        result = service.update_work_profile_records(
            business_id=business_id,
            employee_ids=request.employee_ids if request else None,
            fix_duplicates=request.fix_duplicates if request else True,
            updated_by=current_user.id
        )
        
        return UpdateWorkProfileResponse(
            success=True,
            message="Work profile records updated successfully",
            total_employees=result["total_employees"],
            updated_employees=result["updated_employees"],
            created_profiles=result["created_profiles"],
            fixed_duplicates=result["fixed_duplicates"],
            failed_employees=result["failed_employees"],
            errors=result.get("errors", []),
            execution_time=result["execution_time"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update work profile records: {str(e)}"
        )


@router.get(
    "/maintenance/status",
    response_model=MaintenanceResponse,
    summary="Get Maintenance Status",
    description="Get current maintenance status and statistics"
)
async def get_maintenance_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> MaintenanceResponse:
    """Get maintenance status and statistics"""
    try:
        business_id = getattr(current_user, 'business_id', 1)
        
        service = MaintenanceService(db)
        status_info = service.get_maintenance_status(business_id)
        
        return MaintenanceResponse(
            success=True,
            message="Maintenance status retrieved successfully",
            data=status_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get maintenance status: {str(e)}"
        )


@router.post(
    "/maintenance/validate-data",
    response_model=MaintenanceResponse,
    summary="Validate Data Integrity",
    description="Validate data integrity and identify potential issues"
)
async def validate_data_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> MaintenanceResponse:
    """Validate data integrity and identify potential issues"""
    try:
        business_id = getattr(current_user, 'business_id', 1)
        
        service = MaintenanceService(db)
        validation_result = service.validate_data_integrity(business_id)
        
        return MaintenanceResponse(
            success=True,
            message="Data validation completed",
            data=validation_result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate data integrity: {str(e)}"
        )