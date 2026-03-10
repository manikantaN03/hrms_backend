"""
Separation Repository
Data access layer for separation operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, case
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.models.separation import (
    SeparationRequest, SeparationClearance, ExitInterview, 
    SeparationDocument, SeparationSettings, SeparationTemplate,
    SeparationType, SeparationStatus, ClearanceStatus
)
from app.models.employee import Employee, EmployeeStatus
from app.models.user import User
from app.models.business import Business
from app.schemas.separation import (
    SeparationRequestCreate, SeparationRequestUpdate,
    SeparationClearanceCreate, SeparationClearanceUpdate,
    ExitInterviewCreate, ExitInterviewUpdate,
    SeparationSearchRequest
)


class SeparationRepository:
    def __init__(self, db: Session):
        self.db = db

    # Separation Request CRUD Operations
    def create_separation_request(self, separation_data: SeparationRequestCreate, business_id: int, initiated_by_user: int) -> SeparationRequest:
        """Create new separation request"""
        separation = SeparationRequest(
            business_id=business_id,
            initiated_by_user=initiated_by_user,
            **separation_data.dict()
        )
        self.db.add(separation)
        self.db.commit()
        self.db.refresh(separation)
        return separation

    def get_separation_by_id(self, separation_id: int, business_id: Optional[int] = None) -> Optional[SeparationRequest]:
        """Get separation request by ID"""
        query = self.db.query(SeparationRequest).options(
            joinedload(SeparationRequest.employee),
            joinedload(SeparationRequest.initiator),
            joinedload(SeparationRequest.approver),
            joinedload(SeparationRequest.rejector)
        ).filter(SeparationRequest.id == separation_id)
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        return query.first()

    def get_separations(
        self, 
        business_id: Optional[int] = None,
        status: Optional[SeparationStatus] = None,
        separation_type: Optional[SeparationType] = None,
        employee_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SeparationRequest]:
        """Get separation requests with filters"""
        query = self.db.query(SeparationRequest).options(
            joinedload(SeparationRequest.employee).joinedload(Employee.department),
            joinedload(SeparationRequest.employee).joinedload(Employee.designation),
            joinedload(SeparationRequest.employee).joinedload(Employee.location),
            joinedload(SeparationRequest.initiator)
        )
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        if status:
            query = query.filter(SeparationRequest.status == status)
        
        if separation_type:
            query = query.filter(SeparationRequest.separation_type == separation_type)
        
        if employee_id:
            query = query.filter(SeparationRequest.employee_id == employee_id)
        
        return query.order_by(desc(SeparationRequest.created_at)).offset(skip).limit(limit).all()

    def search_separations(self, search_params: SeparationSearchRequest, business_id: Optional[int] = None) -> tuple[List[SeparationRequest], int]:
        """Search separation requests with pagination"""
        query = self.db.query(SeparationRequest).options(
            joinedload(SeparationRequest.employee).joinedload(Employee.department),
            joinedload(SeparationRequest.employee).joinedload(Employee.designation),
            joinedload(SeparationRequest.employee).joinedload(Employee.location),
            joinedload(SeparationRequest.initiator)
        )
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        # Apply filters
        if search_params.status:
            query = query.filter(SeparationRequest.status == search_params.status)
        
        if search_params.separation_type:
            query = query.filter(SeparationRequest.separation_type == search_params.separation_type)
        
        if search_params.date_from:
            query = query.filter(SeparationRequest.request_date >= search_params.date_from)
        
        if search_params.date_to:
            query = query.filter(SeparationRequest.request_date <= search_params.date_to)
        
        if search_params.initiated_by:
            query = query.filter(SeparationRequest.initiated_by == search_params.initiated_by)
        
        # Text search
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.join(Employee).filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    SeparationRequest.reason.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        skip = (search_params.page - 1) * search_params.size
        items = query.order_by(desc(SeparationRequest.created_at)).offset(skip).limit(search_params.size).all()
        
        return items, total

    def update_separation_request(self, separation_id: int, update_data: SeparationRequestUpdate, business_id: Optional[int] = None) -> Optional[SeparationRequest]:
        """Update separation request"""
        query = self.db.query(SeparationRequest).filter(SeparationRequest.id == separation_id)
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        separation = query.first()
        if not separation:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(separation, field, value)
        
        separation.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(separation)
        return separation

    def delete_separation_request(self, separation_id: int, business_id: Optional[int] = None) -> bool:
        """Delete separation request"""
        query = self.db.query(SeparationRequest).filter(SeparationRequest.id == separation_id)
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        separation = query.first()
        if not separation:
            return False
        
        self.db.delete(separation)
        self.db.commit()
        return True

    # Employee Search for Separation
    def search_active_employees(self, query: str, business_id: Optional[int] = None, limit: int = 20) -> List[Employee]:
        """Search active employees for separation initiation"""
        search_term = f"%{query}%"
        
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation),
            joinedload(Employee.location)
        ).filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_code.ilike(search_term)
            ),
            Employee.is_active == True,
            Employee.employee_status == EmployeeStatus.ACTIVE
        )
        
        if business_id:
            employee_query = employee_query.filter(Employee.business_id == business_id)
        
        return employee_query.limit(limit).all()

    def check_employee_pending_separation(self, employee_id: int) -> bool:
        """Check if employee has pending separation"""
        return self.db.query(SeparationRequest).filter(
            and_(
                SeparationRequest.employee_id == employee_id,
                SeparationRequest.status.in_([
                    SeparationStatus.INITIATED,
                    SeparationStatus.PENDING_APPROVAL,
                    SeparationStatus.APPROVED,
                    SeparationStatus.IN_PROGRESS
                ])
            )
        ).first() is not None

    # Separation Statistics and Dashboard
    def get_separation_dashboard_stats(self, business_id: Optional[int] = None) -> Dict[str, Any]:
        """Get separation dashboard statistics"""
        query = self.db.query(SeparationRequest)
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        # Basic counts
        total_separations = query.count()
        pending_approvals = query.filter(SeparationRequest.status == SeparationStatus.PENDING_APPROVAL).count()
        in_progress = query.filter(SeparationRequest.status == SeparationStatus.IN_PROGRESS).count()
        completed = query.filter(SeparationRequest.status == SeparationStatus.COMPLETED).count()
        
        # Pending clearances count
        clearance_query = self.db.query(SeparationClearance).join(SeparationRequest)
        if business_id:
            clearance_query = clearance_query.filter(SeparationRequest.business_id == business_id)
        
        pending_clearances = clearance_query.filter(SeparationClearance.status == ClearanceStatus.PENDING).count()
        
        # Exit interviews pending
        exit_interview_query = self.db.query(ExitInterview).join(SeparationRequest)
        if business_id:
            exit_interview_query = exit_interview_query.filter(SeparationRequest.business_id == business_id)
        
        exit_interviews_pending = exit_interview_query.filter(ExitInterview.is_completed == False).count()
        
        # Recent separations
        recent_separations = query.options(
            joinedload(SeparationRequest.employee)
        ).order_by(desc(SeparationRequest.created_at)).limit(5).all()
        
        return {
            "total_separations": total_separations,
            "pending_approvals": pending_approvals,
            "in_progress_separations": in_progress,
            "completed_separations": completed,
            "pending_clearances": pending_clearances,
            "exit_interviews_pending": exit_interviews_pending,
            "recent_separations": [
                {
                    "id": sep.id,
                    "employee_name": sep.employee.full_name if sep.employee else "Unknown",
                    "employee_code": sep.employee.employee_code if sep.employee else "N/A",
                    "separation_type": sep.separation_type.value,
                    "status": sep.status.value,
                    "request_date": sep.request_date.isoformat() if sep.request_date else None,
                    "last_working_date": sep.last_working_date.isoformat() if sep.last_working_date else None
                }
                for sep in recent_separations
            ]
        }

    # Ex-Employees
    def get_ex_employees(self, business_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of ex-employees (completed separations)"""
        query = self.db.query(SeparationRequest).options(
            joinedload(SeparationRequest.employee).joinedload(Employee.department),
            joinedload(SeparationRequest.employee).joinedload(Employee.designation)
        ).filter(SeparationRequest.status == SeparationStatus.COMPLETED)
        
        if business_id:
            query = query.filter(SeparationRequest.business_id == business_id)
        
        separations = query.order_by(desc(SeparationRequest.completed_at)).offset(skip).limit(limit).all()
        
        ex_employees = []
        for sep in separations:
            if sep.employee:
                ex_employees.append({
                    "id": sep.employee.id,
                    "employee_code": sep.employee.employee_code,
                    "full_name": sep.employee.full_name,
                    "email": sep.employee.email,
                    "department_name": sep.employee.department.name if sep.employee.department else None,
                    "designation_name": sep.employee.designation.name if sep.employee.designation else None,
                    "date_of_joining": sep.employee.date_of_joining.isoformat() if sep.employee.date_of_joining else None,
                    "date_of_termination": sep.actual_separation_date.isoformat() if sep.actual_separation_date else sep.last_working_date.isoformat(),
                    "separation_type": sep.separation_type.value,
                    "separation_reason": sep.reason,
                    "final_settlement_amount": float(sep.final_settlement_amount) if sep.final_settlement_amount else None
                })
        
        return ex_employees

    # Clearance Operations
    def get_separation_clearances(self, separation_id: int) -> List[SeparationClearance]:
        """Get clearance items for separation"""
        return self.db.query(SeparationClearance).options(
            joinedload(SeparationClearance.assigned_user),
            joinedload(SeparationClearance.clearer)
        ).filter(SeparationClearance.separation_id == separation_id).all()

    def create_clearance_item(self, separation_id: int, clearance_data: SeparationClearanceCreate) -> SeparationClearance:
        """Create clearance item"""
        clearance = SeparationClearance(
            separation_id=separation_id,
            **clearance_data.dict()
        )
        self.db.add(clearance)
        self.db.commit()
        self.db.refresh(clearance)
        return clearance

    def update_clearance_item(self, clearance_id: int, update_data: SeparationClearanceUpdate, cleared_by: Optional[int] = None) -> Optional[SeparationClearance]:
        """Update clearance item"""
        clearance = self.db.query(SeparationClearance).filter(SeparationClearance.id == clearance_id).first()
        if not clearance:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(clearance, field, value)
        
        # Set cleared_by and cleared_at if status is completed
        if update_data.status == ClearanceStatus.COMPLETED and cleared_by:
            clearance.cleared_by = cleared_by
            clearance.cleared_at = datetime.now()
        
        clearance.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(clearance)
        return clearance

    # Settings
    def get_separation_settings(self, business_id: int) -> Optional[SeparationSettings]:
        """Get separation settings for business"""
        return self.db.query(SeparationSettings).filter(SeparationSettings.business_id == business_id).first()

    def create_default_settings(self, business_id: int, created_by: int) -> SeparationSettings:
        """Create default separation settings"""
        settings = SeparationSettings(
            business_id=business_id,
            created_by=created_by,
            default_notice_period_days=30,
            allow_notice_period_buyout=True,
            require_manager_approval=True,
            require_hr_approval=True,
            require_admin_approval=False,
            mandatory_exit_interview=True,
            auto_create_clearance=True,
            notify_manager=True,
            notify_hr=True,
            notify_admin=False
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings