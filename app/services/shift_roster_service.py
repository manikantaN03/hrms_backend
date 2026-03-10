"""
Shift Roster Service
Business logic layer for shift roster operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.repositories.shift_roster_repository import ShiftRosterRepository
from app.schemas.requests import (
    ShiftRosterRequestCreate, ShiftRosterRequestUpdate,
    ShiftRosterRequestResponse
)
from app.models.employee import Employee


class ShiftRosterService:
    """Service for shift roster business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ShiftRosterRepository(db)
    
    def get_shift_roster_requests(
        self,
        business_id: Optional[int] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get shift roster requests with business logic validation"""
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10
        
        # Get requests from repository
        requests = self.repository.get_shift_roster_requests(
            business_id=business_id,
            location=location,
            status=status,
            date_from=date_from,
            date_to=date_to,
            search=search,
            page=page,
            size=size
        )
        
        # Apply business logic transformations
        for request in requests:
            # Format dates for frontend
            if isinstance(request["last_updated"], datetime):
                request["last_updated"] = request["last_updated"].strftime("%b %d, %Y %H:%M:%S")
            if isinstance(request["requested_at"], datetime):
                request["requested_at"] = request["requested_at"].strftime("%b %d, %Y %H:%M:%S")
        
        return requests
    
    def create_shift_roster_request(
        self,
        request_data: ShiftRosterRequestCreate,
        business_id: int,
        created_by: int
    ) -> Dict[str, Any]:
        """Create new shift roster request with validation"""
        
        # Validate employee exists and belongs to business
        employee = self.db.query(Employee).filter(
            Employee.id == request_data.employee_id,
            Employee.business_id == business_id,
            Employee.employee_status == "active"
        ).first()
        
        if not employee:
            raise ValueError("Employee not found or inactive")
        
        # Validate shift type
        valid_shift_types = ["General", "Regular", "Night", "Morning", "Evening"]
        if request_data.shift_type not in valid_shift_types:
            raise ValueError(f"Invalid shift type. Must be one of: {', '.join(valid_shift_types)}")
        
        # Validate note length
        if not request_data.note or len(request_data.note.strip()) < 10:
            raise ValueError("Note must be at least 10 characters long")
        
        # Create request through repository
        return self.repository.create_shift_roster_request(
            request_data=request_data,
            business_id=business_id,
            created_by=created_by
        )
    
    def approve_shift_roster_request(
        self,
        request_id: int,
        approved_by: int,
        business_id: Optional[int] = None
    ) -> Dict[str, str]:
        """Approve shift roster request with business logic"""
        
        # Validate approver exists
        approver = self.db.query(Employee).filter(Employee.id == approved_by).first()
        if not approver:
            raise ValueError("Approver not found")
        
        # Approve through repository
        success = self.repository.approve_shift_roster_request(
            request_id=request_id,
            approved_by=approved_by,
            business_id=business_id
        )
        
        if not success:
            raise ValueError("Request not found or cannot be approved")
        
        return {
            "message": f"Shift roster request #{request_id} approved successfully",
            "request_id": str(request_id),
            "status": "Approved",
            "approved_by": approver.email if hasattr(approver, 'email') else "System",
            "approved_at": datetime.now().isoformat()
        }
    
    def reject_shift_roster_request(
        self,
        request_id: int,
        rejected_by: int,
        rejection_reason: Optional[str] = None,
        business_id: Optional[int] = None
    ) -> Dict[str, str]:
        """Reject shift roster request with business logic"""
        
        # Validate rejector exists
        rejector = self.db.query(Employee).filter(Employee.id == rejected_by).first()
        if not rejector:
            raise ValueError("Rejector not found")
        
        # Validate rejection reason
        if not rejection_reason or len(rejection_reason.strip()) < 5:
            rejection_reason = "No specific reason provided"
        
        # Reject through repository
        success = self.repository.reject_shift_roster_request(
            request_id=request_id,
            rejected_by=rejected_by,
            rejection_reason=rejection_reason,
            business_id=business_id
        )
        
        if not success:
            raise ValueError("Request not found or cannot be rejected")
        
        return {
            "message": f"Shift roster request #{request_id} rejected",
            "request_id": str(request_id),
            "status": "Rejected",
            "rejection_reason": rejection_reason,
            "rejected_by": rejector.email if hasattr(rejector, 'email') else "System",
            "rejected_at": datetime.now().isoformat()
        }
    
    def delete_shift_roster_request(
        self,
        request_id: int,
        deleted_by: int,
        business_id: Optional[int] = None
    ) -> Dict[str, str]:
        """Delete shift roster request with business logic"""
        
        # Validate deleter exists
        deleter = self.db.query(Employee).filter(Employee.id == deleted_by).first()
        if not deleter:
            raise ValueError("User not found")
        
        # Delete through repository
        success = self.repository.delete_shift_roster_request(
            request_id=request_id,
            business_id=business_id
        )
        
        if not success:
            raise ValueError("Request not found or cannot be deleted")
        
        return {
            "message": f"Shift roster request #{request_id} deleted successfully",
            "request_id": str(request_id),
            "deleted_by": deleter.email if hasattr(deleter, 'email') else "System",
            "deleted_at": datetime.now().isoformat()
        }
    
    def get_shift_roster_filters(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """Get filter options for shift roster requests"""
        
        return self.repository.get_shift_roster_filters(business_id=business_id)
    
    def get_employee_search_suggestions(
        self,
        search: str,
        business_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get employee search suggestions for autocomplete"""
        
        if not search or len(search.strip()) < 2:
            return []
        
        query = self.db.query(Employee).filter(
            Employee.employee_status == "active"
        )
        
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Search by name or employee code
        query = query.filter(
            Employee.first_name.ilike(f"%{search}%") |
            Employee.last_name.ilike(f"%{search}%") |
            Employee.employee_code.ilike(f"%{search}%")
        )
        
        employees = query.limit(limit).all()
        
        return [
            {
                "id": emp.id,
                "name": f"{emp.full_name} ({emp.employee_code})",
                "code": emp.employee_code
            }
            for emp in employees
        ]