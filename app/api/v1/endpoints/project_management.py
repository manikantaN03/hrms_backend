"""
Project Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.models.user import User
from app.services.project_management_service import ProjectManagementService
from app.schemas.project_management import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSummary,
    TaskCreate, TaskUpdate, TaskResponse, TaskSummary,
    TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse,
    ProjectActivityLogResponse, ProjectAnalytics, TaskAnalytics, TimeTrackingAnalytics,
    ProjectFilters, TaskFilters, TimeEntryFilters, TimeValidationResponse,
    ProjectStatus, TaskStatus
)

router = APIRouter()


# Project Endpoints
@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project
    
    **Required fields:**
    - name: Project name (max 255 characters)
    - client: Client name (max 255 characters)
    - start_date: Project start date
    - end_date: Project end date (must be after start date)
    
    **Optional fields:**
    - description: Project description
    - status: Project status (default: active)
    - is_active: Active flag (default: true)
    - is_completed: Completion flag (default: false)
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        project = service.create_project(project_data, business_id, current_user.id)
        
        return project
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/projects", response_model=List[ProjectSummary])
async def get_projects(
    status_filter: Optional[List[ProjectStatus]] = Query(None),
    client: Optional[str] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects with optional filters
    
    **Query Parameters:**
    - status_filter: Filter by project status
    - client: Filter by client name (partial match)
    - is_overdue: Filter overdue projects
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        # Create filters
        filters = ProjectFilters(
            status=status_filter,
            client=client,
            is_overdue=is_overdue
        )
        
        service = ProjectManagementService(db)
        projects = service.get_projects(business_id, filters, skip, limit)
        
        return projects
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get projects: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project by ID"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        project = service.get_project(project_id, business_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        project = service.update_project(project_id, business_id, project_data, current_user.id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete project
    
    **Requires admin privileges**
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        success = service.delete_project(project_id, business_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {"message": "Project deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


# Task Endpoints
@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task with time validation
    
    **Required fields:**
    - project_id: ID of the project this task belongs to
    - name: Task name (max 255 characters)
    - start_date: Task start date
    - end_date: Task end date (must be after start date)
    - At least one of: projected_days, projected_hours, projected_minutes
    
    **Time Validation:**
    - Projected time cannot exceed available working hours in date range
    - Working days calculated excluding weekends (8 hours per day)
    - Returns error if time validation fails
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        task = service.create_task(task_data, business_id, current_user.id)
        
        return task
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/tasks", response_model=List[TaskSummary])
async def get_tasks(
    project_id: Optional[int] = Query(None),
    status_filter: Optional[List[TaskStatus]] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    has_time_mismatch: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks with optional filters
    
    **Query Parameters:**
    - project_id: Filter by project ID
    - status_filter: Filter by task status
    - is_overdue: Filter overdue tasks
    - has_time_mismatch: Filter tasks with time validation issues
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        # Create filters
        filters = TaskFilters(
            project_id=project_id,
            status=status_filter,
            is_overdue=is_overdue,
            has_time_mismatch=has_time_mismatch
        )
        
        service = ProjectManagementService(db)
        tasks = service.get_tasks(business_id, filters, skip, limit)
        
        return tasks
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task by ID"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        task = service.get_task(task_id, business_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task with time validation"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        task = service.update_task(task_id, business_id, task_data, current_user.id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        success = service.delete_task(task_id, business_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return {"message": "Task deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.post("/tasks/validate-time", response_model=TimeValidationResponse)
async def validate_task_time(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    projected_days: int = Query(0, ge=0, description="Projected days"),
    projected_hours: int = Query(0, ge=0, le=23, description="Projected hours"),
    projected_minutes: int = Query(0, ge=0, le=59, description="Projected minutes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate task time against available working hours
    
    **Returns:**
    - is_valid: Whether the projected time is valid
    - available_working_days: Number of working days in date range
    - available_working_hours: Total available working hours
    - projected_hours: Total projected hours
    - has_mismatch: Whether there's a time mismatch
    - shortage_hours: Hours over the available time (if any)
    - buffer_hours: Remaining hours (if any)
    - warning_message: Warning message (if applicable)
    - error_message: Error message (if validation fails)
    """
    try:
        from datetime import datetime
        
        # Parse dates
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = ProjectManagementService(db)
        validation = service.validate_task_time(
            start_date_obj, end_date_obj, projected_days, projected_hours, projected_minutes
        )
        
        return validation
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate task time: {str(e)}"
        )


# Time Entry Endpoints
@router.post("/timesheets", response_model=TimeEntryResponse)
async def create_time_entry(
    time_entry_data: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new time entry
    
    **Required fields:**
    - task_id: ID of the task this time entry belongs to
    - date: Date of the time entry
    - At least one of: hours, minutes (must be > 0)
    
    **Optional fields:**
    - description: Description of the work done
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        time_entry = service.create_time_entry(time_entry_data, business_id, current_user.id)
        
        return time_entry
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create time entry: {str(e)}"
        )


@router.get("/timesheets", response_model=List[TimeEntryResponse])
async def get_time_entries(
    task_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all time entries with optional filters
    
    **Query Parameters:**
    - task_id: Filter by task ID
    - project_id: Filter by project ID
    - date_from: Filter by start date (YYYY-MM-DD)
    - date_to: Filter by end date (YYYY-MM-DD)
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        # Parse dates if provided
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
                )
        
        # Create filters
        filters = TimeEntryFilters(
            task_id=task_id,
            project_id=project_id,
            date_from=date_from_obj,
            date_to=date_to_obj
        )
        
        service = ProjectManagementService(db)
        time_entries = service.get_time_entries(business_id, filters, skip, limit)
        
        return time_entries
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time entries: {str(e)}"
        )


@router.get("/timesheets/{time_entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(
    time_entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get time entry by ID"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        time_entry = service.get_time_entry(time_entry_id, business_id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        return time_entry
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time entry: {str(e)}"
        )


@router.put("/timesheets/{time_entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    time_entry_id: int,
    time_entry_data: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update time entry"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        time_entry = service.update_time_entry(time_entry_id, business_id, time_entry_data, current_user.id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        return time_entry
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update time entry: {str(e)}"
        )


@router.delete("/timesheets/{time_entry_id}")
async def delete_time_entry(
    time_entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete time entry"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        success = service.delete_time_entry(time_entry_id, business_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        return {"message": "Time entry deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete time entry: {str(e)}"
        )


# Project Member Endpoints
@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add member to project"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        # Set project_id from URL
        member_data.project_id = project_id
        
        service = ProjectManagementService(db)
        member = service.add_project_member(member_data, business_id, current_user.id)
        
        return member
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add project member: {str(e)}"
        )


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
async def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project members"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        members = service.get_project_members(project_id, business_id)
        
        return members
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project members: {str(e)}"
        )


@router.put("/project-members/{member_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    member_id: int,
    member_data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project member"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        member = service.update_project_member(member_id, business_id, member_data, current_user.id)
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project member not found"
            )
        
        return member
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project member: {str(e)}"
        )


@router.delete("/project-members/{member_id}")
async def remove_project_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove member from project"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        success = service.remove_project_member(member_id, business_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project member not found"
            )
        
        return {"message": "Project member removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove project member: {str(e)}"
        )


# Activity Log Endpoints
@router.get("/projects/{project_id}/activity-logs", response_model=List[ProjectActivityLogResponse])
async def get_project_activity_logs(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project activity logs"""
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        logs = service.get_project_activity_logs(project_id, business_id, limit)
        
        return logs
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project activity logs: {str(e)}"
        )


# Analytics Endpoints
@router.get("/analytics/projects", response_model=ProjectAnalytics)
async def get_project_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project analytics and metrics
    
    **Returns:**
    - Total projects count
    - Projects by status breakdown
    - Completion rates
    - On-time completion rate
    - Overdue projects count
    - Task metrics
    - Work hours summary
    - Average project duration
    """
    try:
        from app.api.v1.deps import get_user_business_id
        
        # Get business_id from current user
        business_id = get_user_business_id(current_user, db)
        
        service = ProjectManagementService(db)
        analytics = service.get_project_analytics(business_id)
        
        return analytics
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project analytics: {str(e)}"
        )