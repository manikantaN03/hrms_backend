"""
Separation Service
Business logic layer for separation operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.repositories.separation_repository import SeparationRepository
from app.models.separation import (
    SeparationRequest, SeparationClearance, ExitInterview,
    SeparationType, SeparationStatus, ClearanceStatus
)
from app.models.employee import Employee
from app.models.user import User
from app.schemas.separation import (
    SeparationRequestCreate, SeparationRequestUpdate, SeparationRequestResponse,
    SeparationClearanceCreate, SeparationClearanceUpdate, SeparationClearanceResponse,
    ExitInterviewCreate, ExitInterviewUpdate, ExitInterviewResponse,
    SeparationSearchRequest, SeparationDashboardResponse,
    PaginatedSeparationResponse, PaginatedExEmployeeResponse,
    ExEmployeeResponse, SeparationActionRequest, SeparationActionResponse
)
from app.core.exceptions import HTTPException
from fastapi import status


class SeparationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SeparationRepository(db)

    def create_separation_request(
        self, 
        separation_data: SeparationRequestCreate, 
        business_id: int, 
        initiated_by_user: int
    ) -> SeparationRequestResponse:
        """Create new separation request"""
        try:
            # Validate employee exists and is active
            employee = self.db.query(Employee).filter(
                Employee.id == separation_data.employee_id,
                Employee.business_id == business_id,
                Employee.is_active == True
            ).first()
            
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found or inactive"
                )
            
            # Check if employee already has pending separation
            if self.repository.check_employee_pending_separation(separation_data.employee_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employee already has a pending separation request"
                )
            
            # Create separation request
            separation = self.repository.create_separation_request(
                separation_data, business_id, initiated_by_user
            )
            
            # Auto-create clearance items if enabled
            settings = self.repository.get_separation_settings(business_id)
            if settings and settings.auto_create_clearance:
                self._create_default_clearance_items(separation.id, settings)
            
            return self._build_separation_response(separation)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create separation request: {str(e)}"
            )

    def get_separation_by_id(self, separation_id: int, business_id: Optional[int] = None) -> Optional[SeparationRequestResponse]:
        """Get separation request by ID"""
        separation = self.repository.get_separation_by_id(separation_id, business_id)
        if not separation:
            return None
        
        return self._build_separation_response(separation)

    def get_separations(
        self,
        business_id: Optional[int] = None,
        status: Optional[SeparationStatus] = None,
        separation_type: Optional[SeparationType] = None,
        employee_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SeparationRequestResponse]:
        """Get separation requests with filters"""
        separations = self.repository.get_separations(
            business_id, status, separation_type, employee_id, skip, limit
        )
        
        return [self._build_separation_response(sep) for sep in separations]

    def search_separations(
        self, 
        search_params: SeparationSearchRequest, 
        business_id: Optional[int] = None
    ) -> PaginatedSeparationResponse:
        """Search separation requests with pagination"""
        separations, total = self.repository.search_separations(search_params, business_id)
        
        items = [self._build_separation_response(sep) for sep in separations]
        pages = (total + search_params.size - 1) // search_params.size
        
        return PaginatedSeparationResponse(
            items=items,
            total=total,
            page=search_params.page,
            size=search_params.size,
            pages=pages
        )

    def update_separation_request(
        self, 
        separation_id: int, 
        update_data: SeparationRequestUpdate, 
        business_id: Optional[int] = None
    ) -> Optional[SeparationRequestResponse]:
        """Update separation request"""
        separation = self.repository.update_separation_request(separation_id, update_data, business_id)
        if not separation:
            return None
        
        return self._build_separation_response(separation)

    def approve_separation(
        self, 
        separation_id: int, 
        action_data: SeparationActionRequest, 
        approved_by: int, 
        business_id: Optional[int] = None
    ) -> SeparationActionResponse:
        """Approve separation request and auto-complete if last working date has passed"""
        separation = self.repository.get_separation_by_id(separation_id, business_id)
        if not separation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Separation request not found"
            )
        
        if separation.status not in [SeparationStatus.INITIATED, SeparationStatus.PENDING_APPROVAL]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only initiated or pending separations can be approved"
            )
        
        # Set approval fields
        separation.approved_by = approved_by
        separation.approved_at = datetime.now()
        separation.updated_at = datetime.now()
        
        if action_data.notes:
            separation.admin_notes = action_data.notes
        if action_data.actual_separation_date:
            separation.actual_separation_date = action_data.actual_separation_date
        if action_data.final_settlement_amount:
            separation.final_settlement_amount = action_data.final_settlement_amount
        
        # Check if last working date has passed - auto-complete if yes
        from datetime import date
        last_working_date = separation.actual_separation_date or separation.last_working_date
        
        if last_working_date <= date.today():
            # Auto-complete the separation
            separation.status = SeparationStatus.COMPLETED
            separation.completed_at = datetime.now()
            
            # Update employee status to inactive
            employee = self.db.query(Employee).filter(Employee.id == separation.employee_id).first()
            if employee:
                from app.models.employee import EmployeeStatus
                employee.employee_status = EmployeeStatus.INACTIVE
                employee.updated_at = datetime.now()
            
            message = "Separation request approved and completed successfully"
        else:
            # Just approve, will be completed later
            separation.status = SeparationStatus.APPROVED
            message = "Separation request approved successfully"
        
        self.db.commit()
        
        return SeparationActionResponse(
            success=True,
            message=message,
            separation_id=separation_id,
            action="approve",
            timestamp=datetime.now()
        )

    def reject_separation(
        self, 
        separation_id: int, 
        action_data: SeparationActionRequest, 
        rejected_by: int, 
        business_id: Optional[int] = None
    ) -> SeparationActionResponse:
        """Reject separation request"""
        separation = self.repository.get_separation_by_id(separation_id, business_id)
        if not separation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Separation request not found"
            )
        
        if separation.status not in [SeparationStatus.INITIATED, SeparationStatus.PENDING_APPROVAL]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only initiated or pending separations can be rejected"
            )
        
        # Update separation
        separation.status = SeparationStatus.REJECTED
        separation.rejected_by = rejected_by
        separation.rejected_at = datetime.now()
        separation.updated_at = datetime.now()
        
        if action_data.reason:
            separation.rejection_reason = action_data.reason
        if action_data.notes:
            separation.admin_notes = action_data.notes
        
        self.db.commit()
        
        return SeparationActionResponse(
            success=True,
            message="Separation request rejected successfully",
            separation_id=separation_id,
            action="reject",
            timestamp=datetime.now()
        )

    def delete_separation_request(self, separation_id: int, business_id: Optional[int] = None) -> bool:
        """Delete separation request"""
        return self.repository.delete_separation_request(separation_id, business_id)

    # Employee Search
    def search_employees_for_separation(self, query: str, business_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search active employees for separation initiation"""
        employees = self.repository.search_active_employees(query, business_id)
        
        result = []
        for emp in employees:
            # Check if employee has pending separation
            has_pending = self.repository.check_employee_pending_separation(emp.id)
            
            result.append({
                "id": emp.id,
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "email": emp.email,
                "mobile": emp.mobile,
                "department_name": emp.department.name if emp.department else None,
                "designation_name": emp.designation.name if emp.designation else None,
                "location_name": emp.location.name if emp.location else None,
                "date_of_joining": emp.date_of_joining.isoformat() if emp.date_of_joining else None,
                "has_pending_separation": has_pending,
                "profile_image": "/assets/img/users/user-01.jpg"  # Default image
            })
        
        return result

    # Dashboard and Statistics
    def get_dashboard_stats(self, business_id: Optional[int] = None) -> SeparationDashboardResponse:
        """Get separation dashboard statistics"""
        stats = self.repository.get_separation_dashboard_stats(business_id)
        
        return SeparationDashboardResponse(
            total_separations=stats["total_separations"],
            pending_approvals=stats["pending_approvals"],
            in_progress_separations=stats["in_progress_separations"],
            completed_separations=stats["completed_separations"],
            pending_clearances=stats["pending_clearances"],
            exit_interviews_pending=stats["exit_interviews_pending"],
            recent_separations=stats["recent_separations"],
            monthly_stats=[],  # Can be implemented later
            separation_by_type={},  # Can be implemented later
            average_notice_period=None  # Can be implemented later
        )

    # Ex-Employees
    def get_ex_employees(
        self, 
        business_id: Optional[int] = None, 
        page: int = 1, 
        size: int = 100
    ) -> PaginatedExEmployeeResponse:
        """Get paginated list of ex-employees"""
        skip = (page - 1) * size
        ex_employees_data = self.repository.get_ex_employees(business_id, skip, size)
        
        # Get total count
        total_query = self.db.query(SeparationRequest).filter(SeparationRequest.status == SeparationStatus.COMPLETED)
        if business_id:
            total_query = total_query.filter(SeparationRequest.business_id == business_id)
        total = total_query.count()
        
        items = [ExEmployeeResponse(**emp_data) for emp_data in ex_employees_data]
        pages = (total + size - 1) // size
        
        return PaginatedExEmployeeResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    # Clearance Operations
    def get_separation_clearances(self, separation_id: int) -> List[SeparationClearanceResponse]:
        """Get clearance items for separation"""
        clearances = self.repository.get_separation_clearances(separation_id)
        
        result = []
        for clearance in clearances:
            clearance_dict = {
                "id": clearance.id,
                "separation_id": clearance.separation_id,
                "department": clearance.department,
                "item_name": clearance.item_name,
                "description": clearance.description,
                "status": clearance.status,
                "is_mandatory": clearance.is_mandatory,
                "assigned_to": clearance.assigned_to,
                "cleared_by": clearance.cleared_by,
                "due_date": clearance.due_date,
                "cleared_at": clearance.cleared_at,
                "clearance_notes": clearance.clearance_notes,
                "pending_amount": clearance.pending_amount,
                "created_at": clearance.created_at,
                "updated_at": clearance.updated_at,
                "assigned_user_name": clearance.assigned_user.name if clearance.assigned_user else None,
                "clearer_name": clearance.clearer.name if clearance.clearer else None
            }
            result.append(SeparationClearanceResponse(**clearance_dict))
        
        return result

    def create_clearance_item(self, separation_id: int, clearance_data: SeparationClearanceCreate) -> SeparationClearanceResponse:
        """Create clearance item"""
        clearance = self.repository.create_clearance_item(separation_id, clearance_data)
        
        # Build response with user details
        clearance_dict = {
            "id": clearance.id,
            "separation_id": clearance.separation_id,
            "department": clearance.department,
            "item_name": clearance.item_name,
            "description": clearance.description,
            "status": clearance.status,
            "is_mandatory": clearance.is_mandatory,
            "assigned_to": clearance.assigned_to,
            "cleared_by": clearance.cleared_by,
            "due_date": clearance.due_date,
            "cleared_at": clearance.cleared_at,
            "clearance_notes": clearance.clearance_notes,
            "pending_amount": clearance.pending_amount,
            "created_at": clearance.created_at,
            "updated_at": clearance.updated_at,
            "assigned_user_name": None,
            "clearer_name": None
        }
        
        if clearance.assigned_to:
            assigned_user = self.db.query(User).filter(User.id == clearance.assigned_to).first()
            clearance_dict["assigned_user_name"] = assigned_user.name if assigned_user else None
        
        return SeparationClearanceResponse(**clearance_dict)

    # Helper Methods
    def _build_separation_response(self, separation: SeparationRequest) -> SeparationRequestResponse:
        """Build separation response with employee details"""
        response_dict = {
            "id": separation.id,
            "business_id": separation.business_id,
            "employee_id": separation.employee_id,
            "separation_type": separation.separation_type,
            "status": separation.status,
            "request_date": separation.request_date,
            "last_working_date": separation.last_working_date,
            "actual_separation_date": separation.actual_separation_date,
            "notice_period_days": separation.notice_period_days,
            "reason": separation.reason,
            "detailed_reason": separation.detailed_reason,
            "initiated_by": separation.initiated_by,
            "final_settlement_amount": separation.final_settlement_amount,
            "pending_dues": separation.pending_dues,
            "recovery_amount": separation.recovery_amount,
            "initiated_by_user": separation.initiated_by_user,
            "approved_by": separation.approved_by,
            "rejected_by": separation.rejected_by,
            "created_at": separation.created_at,
            "approved_at": separation.approved_at,
            "rejected_at": separation.rejected_at,
            "completed_at": separation.completed_at,
            "rejection_reason": separation.rejection_reason,
            "admin_notes": separation.admin_notes,
            "hr_notes": separation.hr_notes,
            "employee_name": separation.employee.full_name if separation.employee else None,
            "employee_code": separation.employee.employee_code if separation.employee else None,
            "department_name": separation.employee.department.name if separation.employee and separation.employee.department else None,
            "designation_name": separation.employee.designation.name if separation.employee and separation.employee.designation else None
        }
        
        return SeparationRequestResponse(**response_dict)

    def _create_default_clearance_items(self, separation_id: int, settings):
        """Create default clearance items for separation"""
        default_items = [
            {"department": "IT", "item_name": "Laptop Return", "description": "Return company laptop and accessories", "is_mandatory": True},
            {"department": "IT", "item_name": "Access Card Return", "description": "Return office access card", "is_mandatory": True},
            {"department": "HR", "item_name": "Exit Interview", "description": "Complete exit interview process", "is_mandatory": True},
            {"department": "Finance", "item_name": "Final Settlement", "description": "Process final salary and dues", "is_mandatory": True},
            {"department": "Admin", "item_name": "Office Keys", "description": "Return office keys and locker keys", "is_mandatory": False}
        ]
        
        for item_data in default_items:
            clearance_data = SeparationClearanceCreate(**item_data)
            self.repository.create_clearance_item(separation_id, clearance_data)