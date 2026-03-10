"""
Activity Log Service
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import json

from app.models.reports import ActivityLog
from app.models.employee import Employee
from app.models.user import User
from app.schemas.activity_logs import (
    ActivityLogCreate, 
    ActivityLogUpdate, 
    ActivityLogResponse,
    ActivityLogListResponse,
    ActivityLogFilterRequest,
    EmployeeActivityResponse
)

class ActivityLogService:
    """Service for managing activity logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_activity_log(
        self, 
        activity_data: ActivityLogCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Create a new activity log entry"""
        
        # Create the activity log
        activity_log = ActivityLog(
            user_id=activity_data.user_id,
            action=activity_data.action,
            module=activity_data.module.value,
            details=activity_data.details,
            ip_address=ip_address or activity_data.ip_address,
            user_agent=user_agent or activity_data.user_agent,
            created_at=datetime.utcnow()
        )
        
        # Add employee_id to details if provided
        if activity_data.employee_id:
            if not activity_log.details:
                activity_log.details = {}
            activity_log.details['employee_id'] = activity_data.employee_id
        
        self.db.add(activity_log)
        self.db.commit()
        self.db.refresh(activity_log)
        
        return activity_log
    
    def get_activity_logs(
        self, 
        filters: ActivityLogFilterRequest
    ) -> ActivityLogListResponse:
        """Get activity logs with filtering and pagination"""
        
        # Build base query
        query = self.db.query(ActivityLog).options(
            joinedload(ActivityLog.user)
        )
        
        # Apply filters
        if filters.employee_id:
            # Filter by employee_id in details JSON field
            query = query.filter(
                ActivityLog.details.op('->>')('employee_id') == str(filters.employee_id)
            )
        
        if filters.user_id:
            query = query.filter(ActivityLog.user_id == filters.user_id)
        
        if filters.module:
            query = query.filter(ActivityLog.module == filters.module.value)
        
        if filters.action_contains:
            query = query.filter(
                ActivityLog.action.ilike(f"%{filters.action_contains}%")
            )
        
        if filters.date_from:
            query = query.filter(ActivityLog.created_at >= filters.date_from)
        
        if filters.date_to:
            # Add one day to include the entire day
            end_date = filters.date_to + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        logs = query.order_by(desc(ActivityLog.created_at)).offset(
            (filters.page - 1) * filters.per_page
        ).limit(filters.per_page).all()
        
        # Convert to response format
        log_responses = []
        for log in logs:
            # Get employee name if employee_id is in details
            employee_name = None
            employee_id = None
            if log.details and 'employee_id' in log.details:
                employee_id = int(log.details['employee_id'])
                employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
                if employee:
                    employee_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
            
            log_response = ActivityLogResponse(
                id=log.id,
                user_id=log.user_id,
                employee_id=employee_id,
                action=log.action,
                module=log.module,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
                user_name=log.user.name if log.user else None,
                employee_name=employee_name
            )
            log_responses.append(log_response)
        
        # Calculate pagination info
        total_pages = (total + filters.per_page - 1) // filters.per_page
        
        return ActivityLogListResponse(
            logs=log_responses,
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            total_pages=total_pages
        )
    
    def get_employee_activity(self, employee_id: int) -> EmployeeActivityResponse:
        """Get comprehensive activity data for an employee"""
        
        # Get employee
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        employee_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
        employee_code = employee.employee_code or f"EMP{employee.id:03d}"
        
        # Get activity logs related to this employee
        activity_logs = self.db.query(ActivityLog).filter(
            ActivityLog.details.op('->>')('employee_id') == str(employee_id)
        ).options(joinedload(ActivityLog.user)).order_by(
            desc(ActivityLog.created_at)
        ).limit(50).all()
        
        # Convert to system logs format
        system_logs = []
        for log in activity_logs:
            # Convert UTC to IST (UTC+5:30)
            ist_time = log.created_at + timedelta(hours=5, minutes=30)
            
            system_logs.append({
                "id": f"system_log_{log.id}",
                "action": log.action,
                "type": self._get_activity_type(log.action),
                "user": log.user.name if log.user else "System",
                "icon": self._get_activity_icon(log.action, log.module),
                "timestamp": ist_time.strftime("%d/%m/%Y %H:%M:%S"),
                "date": ist_time.strftime("%Y-%m-%d"),
                "module": log.module,
                "details": log.details  # Include full details for before/after comparison
            })
        
        # Get general database logs (not employee-specific) - simplified approach
        general_logs = self.db.query(ActivityLog).options(
            joinedload(ActivityLog.user)
        ).order_by(desc(ActivityLog.created_at)).limit(20).all()
        
        # Filter out employee-specific logs
        filtered_general_logs = []
        for log in general_logs:
            if not log.details or 'employee_id' not in log.details:
                filtered_general_logs.append(log)
            if len(filtered_general_logs) >= 10:  # Limit to 10 general logs
                break
        
        database_logs = []
        for log in filtered_general_logs:
            # Convert UTC to IST (UTC+5:30)
            ist_time = log.created_at + timedelta(hours=5, minutes=30)
            
            database_logs.append({
                "id": f"db_log_{log.id}",
                "action": log.action,
                "type": "system",
                "user": log.user.name if log.user else "System",
                "icon": "bi-database-fill",
                "timestamp": ist_time.strftime("%d/%m/%Y %H:%M:%S"),
                "date": ist_time.strftime("%Y-%m-%d"),
                "module": log.module,
                "details": log.details  # Include full details
            })
        
        # Generate recent activities (last 7 days of employee-related activities)
        recent_activities = []
        for i, log in enumerate(activity_logs[:7]):
            # Convert UTC to IST (UTC+5:30)
            ist_time = log.created_at + timedelta(hours=5, minutes=30)
            
            recent_activities.append({
                "id": f"activity_{employee_id}_{i}",
                "date": ist_time.strftime("%Y-%m-%d"),
                "type": self._get_activity_type(log.action),
                "description": log.action,
                "status": "completed",
                "time": ist_time.strftime("%H:%M:%S"),
                "user": log.user.name if log.user else "System",
                "module": log.module
            })
        
        # Create response
        response = EmployeeActivityResponse(
            id=employee.id,
            name=employee_name,
            code=employee_code,
            activity=EmployeeActivityResponse.ActivityData(
                system_logs=system_logs,
                database_logs=database_logs,
                recent_activities=recent_activities
            )
        )
        
        return response
    
    def _get_activity_type(self, action: str) -> str:
        """Determine activity type based on action"""
        action_lower = action.lower()
        
        if any(word in action_lower for word in ['add', 'create', 'insert', 'new']):
            return "add"
        elif any(word in action_lower for word in ['delete', 'remove', 'cancel']):
            return "delete"
        elif any(word in action_lower for word in ['update', 'edit', 'modify', 'change']):
            return "update"
        elif any(word in action_lower for word in ['approve', 'accept']):
            return "approve"
        elif any(word in action_lower for word in ['reject', 'deny']):
            return "reject"
        else:
            return "system"
    
    def _get_activity_icon(self, action: str, module: str) -> str:
        """Get appropriate icon based on action and module"""
        action_lower = action.lower()
        module_lower = module.lower()
        
        # Module-specific icons
        if 'employee' in module_lower:
            if 'add' in action_lower or 'create' in action_lower:
                return "bi-person-plus-fill"
            elif 'update' in action_lower or 'edit' in action_lower:
                return "bi-person-check-fill"
            elif 'delete' in action_lower:
                return "bi-person-x-fill"
            else:
                return "bi-person-fill"
        
        elif 'document' in module_lower:
            if 'upload' in action_lower or 'add' in action_lower:
                return "bi-file-earmark-plus-fill"
            elif 'delete' in action_lower:
                return "bi-file-earmark-x-fill"
            else:
                return "bi-file-earmark-fill"
        
        elif 'payroll' in module_lower or 'salary' in action_lower:
            return "bi-currency-dollar"
        
        elif 'attendance' in module_lower:
            return "bi-clock-fill"
        
        elif 'leave' in module_lower:
            return "bi-calendar-check-fill"
        
        elif 'asset' in module_lower:
            return "bi-laptop-fill"
        
        elif 'policy' in action_lower or 'policies' in module_lower:
            return "bi-clipboard-check-fill"
        
        # Action-specific icons
        elif 'approve' in action_lower:
            return "bi-check-circle-fill"
        elif 'reject' in action_lower:
            return "bi-x-circle-fill"
        elif 'login' in action_lower:
            return "bi-box-arrow-in-right"
        elif 'logout' in action_lower:
            return "bi-box-arrow-right"
        
        # Default icon
        return "bi-activity"
    
    def log_employee_activity(
        self,
        user_id: int,
        employee_id: int,
        action: str,
        module: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Convenience method to log employee-related activity"""
        
        activity_data = ActivityLogCreate(
            user_id=user_id,
            employee_id=employee_id,
            action=action,
            module=module,
            details=details or {}
        )
        
        return self.create_activity_log(
            activity_data=activity_data,
            ip_address=ip_address,
            user_agent=user_agent
        )