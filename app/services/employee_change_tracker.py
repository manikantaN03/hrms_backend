"""
Employee Change Tracker Service
Tracks and logs all changes made to employee data across different sections
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.reports import ActivityLog
from app.models.employee import Employee
from app.models.user import User


class EmployeeChangeTracker:
    """Service to track and log employee data changes"""
    
    # Section to module mapping
    SECTION_MODULES = {
        "summary": "Employee Summary",
        "basic_info": "Employee Basic Info",
        "addresses": "Employee Addresses",
        "identity": "Employee Identity",
        "work_profile": "Employee Work Profile",
        "policies": "Employee Policies",
        "salary": "Employee Salary",
        "documents": "Employee Documents",
        "assets": "Employee Assets",
        "family_members": "Employee Family Members",
        "additional_info": "Employee Additional Info",
        "permissions": "Employee Permissions",
        "login_access": "Employee Login & Access"
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_change(
        self,
        user_id: int,
        employee_id: int,
        section: str,
        action: str,
        changes: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """
        Log a change made to employee data
        
        Args:
            user_id: ID of user making the change
            employee_id: ID of employee being modified
            section: Section being modified (summary, basic_info, etc.)
            action: Description of the action
            changes: Dictionary of changed fields
            old_values: Previous values
            new_values: New values
            ip_address: IP address of the user
            user_agent: User agent string
        
        Returns:
            ActivityLog: Created activity log entry
        """
        
        # Get employee and user info
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        user = self.db.query(User).filter(User.id == user_id).first()
        
        employee_name = f"{employee.first_name} {employee.last_name}" if employee else f"Employee #{employee_id}"
        user_name = user.name if user else f"User #{user_id}"
        
        # Build details dictionary
        details = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "employee_code": employee.employee_code if employee else None,
            "section": section,
            "user_name": user_name
        }
        
        # Add change information
        if changes:
            details["changes"] = changes
        if old_values:
            details["old_values"] = old_values
        if new_values:
            details["new_values"] = new_values
        
        # Get module name from section
        module = self.SECTION_MODULES.get(section, "Employee Management")
        
        # Create activity log
        activity_log = ActivityLog(
            user_id=user_id,
            action=action,
            module=module,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        self.db.add(activity_log)
        self.db.commit()
        self.db.refresh(activity_log)
        
        return activity_log
    
    def log_create(
        self,
        user_id: int,
        employee_id: int,
        section: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log creation of new employee data"""
        
        action = f"Created {section.replace('_', ' ').title()} for employee"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section=section,
            action=action,
            new_values=data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_update(
        self,
        user_id: int,
        employee_id: int,
        section: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log update of employee data"""
        
        # Find changed fields
        changes = {}
        for key in new_data:
            if key in old_data and old_data[key] != new_data[key]:
                changes[key] = {
                    "old": old_data[key],
                    "new": new_data[key]
                }
        
        # Build action description
        changed_fields = list(changes.keys())
        if len(changed_fields) == 1:
            action = f"Updated {changed_fields[0].replace('_', ' ').title()} in {section.replace('_', ' ').title()}"
        elif len(changed_fields) <= 3:
            fields_str = ", ".join([f.replace('_', ' ').title() for f in changed_fields])
            action = f"Updated {fields_str} in {section.replace('_', ' ').title()}"
        else:
            action = f"Updated {len(changed_fields)} fields in {section.replace('_', ' ').title()}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section=section,
            action=action,
            changes=changes,
            old_values=old_data,
            new_values=new_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_delete(
        self,
        user_id: int,
        employee_id: int,
        section: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log deletion of employee data"""
        
        action = f"Deleted {section.replace('_', ' ').title()} for employee"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section=section,
            action=action,
            old_values=data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_document_upload(
        self,
        user_id: int,
        employee_id: int,
        document_name: str,
        document_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log document upload"""
        
        action = f"Uploaded {document_type} document: {document_name}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="documents",
            action=action,
            new_values={"document_name": document_name, "document_type": document_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_document_delete(
        self,
        user_id: int,
        employee_id: int,
        document_name: str,
        document_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log document deletion"""
        
        action = f"Deleted {document_type} document: {document_name}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="documents",
            action=action,
            old_values={"document_name": document_name, "document_type": document_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_asset_assignment(
        self,
        user_id: int,
        employee_id: int,
        asset_name: str,
        asset_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log asset assignment"""
        
        action = f"Assigned {asset_type} asset: {asset_name}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="assets",
            action=action,
            new_values={"asset_name": asset_name, "asset_type": asset_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_asset_return(
        self,
        user_id: int,
        employee_id: int,
        asset_name: str,
        asset_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log asset return"""
        
        action = f"Returned {asset_type} asset: {asset_name}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="assets",
            action=action,
            old_values={"asset_name": asset_name, "asset_type": asset_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_salary_revision(
        self,
        user_id: int,
        employee_id: int,
        old_salary: float,
        new_salary: float,
        effective_date: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log salary revision"""
        
        action = f"Revised salary from ₹{old_salary:,.2f} to ₹{new_salary:,.2f} effective {effective_date}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="salary",
            action=action,
            changes={"salary": {"old": old_salary, "new": new_salary}},
            new_values={"new_salary": new_salary, "effective_date": effective_date},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_policy_assignment(
        self,
        user_id: int,
        employee_id: int,
        policy_name: str,
        policy_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log policy assignment"""
        
        action = f"Assigned {policy_type} policy: {policy_name}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="policies",
            action=action,
            new_values={"policy_name": policy_name, "policy_type": policy_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_permission_change(
        self,
        user_id: int,
        employee_id: int,
        permission_name: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log permission change"""
        
        action = f"{'Granted' if granted else 'Revoked'} permission: {permission_name}"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="permissions",
            action=action,
            new_values={"permission": permission_name, "granted": granted},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_login_access_change(
        self,
        user_id: int,
        employee_id: int,
        access_type: str,
        action_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log login access change"""
        
        action = f"{action_type} {access_type} access"
        
        return self.log_change(
            user_id=user_id,
            employee_id=employee_id,
            section="login_access",
            action=action,
            new_values={"access_type": access_type, "action": action_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_employee_activity_summary(self, employee_id: int, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for an employee"""
        
        from datetime import timedelta
        
        # Get logs from last N days
        since_date = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(ActivityLog).filter(
            ActivityLog.details.op('->>')('employee_id') == str(employee_id),
            ActivityLog.created_at >= since_date
        ).order_by(ActivityLog.created_at.desc()).all()
        
        # Count by section
        section_counts = {}
        for log in logs:
            if log.details and 'section' in log.details:
                section = log.details['section']
                section_counts[section] = section_counts.get(section, 0) + 1
        
        # Count by action type
        action_counts = {
            "create": 0,
            "update": 0,
            "delete": 0
        }
        
        for log in logs:
            action_lower = log.action.lower()
            if 'created' in action_lower or 'added' in action_lower:
                action_counts["create"] += 1
            elif 'updated' in action_lower or 'modified' in action_lower or 'revised' in action_lower:
                action_counts["update"] += 1
            elif 'deleted' in action_lower or 'removed' in action_lower:
                action_counts["delete"] += 1
        
        return {
            "total_activities": len(logs),
            "section_counts": section_counts,
            "action_counts": action_counts,
            "most_active_section": max(section_counts.items(), key=lambda x: x[1])[0] if section_counts else None,
            "last_activity": logs[0].created_at.isoformat() if logs else None
        }


# Helper function to get client IP from request
def get_client_ip(request) -> Optional[str]:
    """Extract client IP address from request"""
    try:
        # Check for forwarded IP first (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
    except Exception:
        return None


# Helper function to get user agent from request
def get_user_agent(request) -> Optional[str]:
    """Extract user agent from request"""
    try:
        return request.headers.get("User-Agent")
    except Exception:
        return None
