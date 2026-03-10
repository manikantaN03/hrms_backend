"""
Shift Roster Repository
Data access layer for shift roster operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.models.requests import Request, ShiftRosterRequest, RequestStatus, RequestType
from app.models.employee import Employee
from app.models.attendance import ShiftRoster
from app.schemas.requests import (
    ShiftRosterRequestCreate, ShiftRosterRequestUpdate, 
    ShiftRosterRequestResponse
)


class ShiftRosterRepository:
    """Repository for shift roster operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
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
        """Get shift roster requests with filtering and pagination"""
        
        # Base query
        query = self.db.query(Request).options(
            joinedload(Request.employee)
        ).filter(Request.request_type == RequestType.SHIFT_ROSTER)
        
        if business_id:
            query = query.filter(Request.business_id == business_id)
        
        # Apply filters
        if status and status != "All":
            if status == "Open":
                query = query.filter(Request.status == RequestStatus.PENDING)
            elif status == "Approved":
                query = query.filter(Request.status == RequestStatus.APPROVED)
            elif status == "Rejected":
                query = query.filter(Request.status == RequestStatus.REJECTED)
        
        if date_from:
            query = query.filter(Request.request_date >= date_from)
        
        if date_to:
            query = query.filter(Request.request_date <= date_to)
        
        if search:
            query = query.join(Employee).filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        offset = (page - 1) * size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(size).all()
        
        # Convert to response format
        result = []
        for req in requests:
            # Get shift roster details
            shift_details = self.db.query(ShiftRosterRequest).filter(
                ShiftRosterRequest.request_id == req.id
            ).first()
            
            # Map status
            status_map = {
                RequestStatus.PENDING: "Open",
                RequestStatus.IN_REVIEW: "Pending", 
                RequestStatus.APPROVED: "Approved",
                RequestStatus.REJECTED: "Rejected"
            }
            
            result.append({
                "id": req.id,
                "employee_id": req.employee_id,
                "employee_name": f"{req.employee.full_name} ({req.employee.employee_code})" if req.employee else "Unknown",
                "employee_code": req.employee.employee_code if req.employee else "N/A",
                "date_range": shift_details.requested_date.strftime("%b %d, %Y %H:%M:%S") if shift_details else req.request_date.strftime("%b %d, %Y %H:%M:%S"),
                "shift_type": shift_details.requested_shift_type if shift_details else "General",
                "note": shift_details.reason if shift_details else req.description,
                "status": status_map.get(req.status, "Open"),
                "location": shift_details.location if shift_details else "Hyderabad",
                "last_updated": req.updated_at or req.created_at,
                "requested_at": req.created_at
            })
        
        return result
    
    def create_shift_roster_request(
        self,
        request_data: ShiftRosterRequestCreate,
        business_id: int,
        created_by: int
    ) -> Dict[str, Any]:
        """Create new shift roster request"""
        
        # Create base request
        new_request = Request(
            business_id=business_id,
            employee_id=request_data.employee_id,
            request_type=RequestType.SHIFT_ROSTER,
            title=f"Shift Roster Change Request",
            description=request_data.note,
            status=RequestStatus.PENDING,
            request_date=date.today(),
            created_by=created_by
        )
        
        self.db.add(new_request)
        self.db.flush()  # Get the ID
        
        # Parse date from date_range
        try:
            # Extract date from "Oct 27, 2025 18:00:00" format
            date_str = request_data.date_range.split(" ")[0:3]
            requested_date = datetime.strptime(" ".join(date_str), "%b %d, %Y").date()
        except:
            requested_date = date.today()
        
        # Create shift roster request details
        shift_request = ShiftRosterRequest(
            request_id=new_request.id,
            requested_date=requested_date,
            requested_shift_type=request_data.shift_type,
            reason=request_data.note,
            location=request_data.location or "Hyderabad"
        )
        
        self.db.add(shift_request)
        self.db.commit()
        
        # Get employee details
        employee = self.db.query(Employee).filter(Employee.id == request_data.employee_id).first()
        
        return {
            "id": new_request.id,
            "employee_id": request_data.employee_id,
            "employee_name": f"{employee.full_name} ({employee.employee_code})" if employee else "Unknown",
            "employee_code": employee.employee_code if employee else "N/A",
            "date_range": request_data.date_range,
            "shift_type": request_data.shift_type,
            "note": request_data.note,
            "status": "Open",
            "location": request_data.location or "Hyderabad",
            "last_updated": new_request.created_at,
            "requested_at": new_request.created_at
        }
    
    def approve_shift_roster_request(
        self,
        request_id: int,
        approved_by: int,
        business_id: Optional[int] = None
    ) -> bool:
        """Approve shift roster request"""
        
        request = self.db.query(Request).filter(
            Request.id == request_id,
            Request.request_type == RequestType.SHIFT_ROSTER
        )
        
        if business_id:
            request = request.filter(Request.business_id == business_id)
        
        request = request.first()
        
        if not request:
            return False
        
        # Update request status
        request.status = RequestStatus.APPROVED
        request.approved_by = approved_by
        request.approved_date = datetime.now()
        request.approval_comments = "Shift roster request approved"
        
        self.db.commit()
        return True
    
    def reject_shift_roster_request(
        self,
        request_id: int,
        rejected_by: int,
        rejection_reason: Optional[str] = None,
        business_id: Optional[int] = None
    ) -> bool:
        """Reject shift roster request"""
        
        request = self.db.query(Request).filter(
            Request.id == request_id,
            Request.request_type == RequestType.SHIFT_ROSTER
        )
        
        if business_id:
            request = request.filter(Request.business_id == business_id)
        
        request = request.first()
        
        if not request:
            return False
        
        # Update request status
        request.status = RequestStatus.REJECTED
        request.approved_by = rejected_by
        request.approved_date = datetime.now()
        request.approval_comments = rejection_reason or "Shift roster request rejected"
        
        self.db.commit()
        return True
    
    def delete_shift_roster_request(
        self,
        request_id: int,
        business_id: Optional[int] = None
    ) -> bool:
        """Delete shift roster request"""
        
        request = self.db.query(Request).filter(
            Request.id == request_id,
            Request.request_type == RequestType.SHIFT_ROSTER
        )
        
        if business_id:
            request = request.filter(Request.business_id == business_id)
        
        request = request.first()
        
        if not request:
            return False
        
        # Delete shift roster details first
        self.db.query(ShiftRosterRequest).filter(
            ShiftRosterRequest.request_id == request_id
        ).delete()
        
        # Delete main request
        self.db.delete(request)
        self.db.commit()
        return True
    
    def get_shift_roster_filters(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """Get filter options for shift roster requests"""
        
        # Get unique locations from shift roster requests
        locations_query = self.db.query(ShiftRosterRequest.location).distinct()
        locations = [loc[0] for loc in locations_query.all() if loc[0]]
        
        # Default filter options
        return {
            "locations": ["All Locations"] + locations,
            "statuses": ["All", "Open", "Pending", "Processing", "Completed", "Approved", "Rejected"]
        }