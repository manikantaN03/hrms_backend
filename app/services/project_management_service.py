"""
Project Management Service
Business logic layer for Project Management operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.project_management import Project, ProjectMember
from app.repositories.project_management_repository import (
    ProjectRepository, TaskRepository, TimeEntryRepository,
    ProjectMemberRepository, ProjectActivityLogRepository
)
from app.schemas.project_management import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSummary,
    TaskCreate, TaskUpdate, TaskResponse, TaskSummary,
    TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse,
    ProjectActivityLogResponse, ProjectAnalytics, TaskAnalytics, TimeTrackingAnalytics,
    ProjectFilters, TaskFilters, TimeEntryFilters, TimeValidationResponse,
    ProjectStatus, TaskStatus
)


class ProjectManagementService:
    """Service for project management operations"""

    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)
        self.time_entry_repo = TimeEntryRepository(db)
        self.member_repo = ProjectMemberRepository(db)
        self.activity_repo = ProjectActivityLogRepository(db)

    # Project Operations
    def create_project(self, project_data: ProjectCreate, business_id: int, created_by: int) -> ProjectResponse:
        """Create a new project"""
        try:
            project = self.project_repo.create_project(project_data, business_id, created_by)
            return self._convert_project_to_response(project)
        except Exception as e:
            raise Exception(f"Failed to create project: {str(e)}")

    def get_project(self, project_id: int, business_id: int) -> Optional[ProjectResponse]:
        """Get project by ID"""
        try:
            project = self.project_repo.get_project_by_id(project_id, business_id)
            return self._convert_project_to_response(project) if project else None
        except Exception as e:
            raise Exception(f"Failed to get project: {str(e)}")

    def get_projects(self, business_id: int, filters: Optional[ProjectFilters] = None,
                    skip: int = 0, limit: int = 100) -> List[ProjectSummary]:
        """Get projects with optional filters"""
        try:
            projects = self.project_repo.get_projects(business_id, filters, skip, limit)
            return [self._convert_project_to_summary(project) for project in projects]
        except Exception as e:
            raise Exception(f"Failed to get projects: {str(e)}")

    def update_project(self, project_id: int, business_id: int, project_data: ProjectUpdate, updated_by: int) -> Optional[ProjectResponse]:
        """Update project"""
        try:
            project = self.project_repo.update_project(project_id, business_id, project_data)
            if not project:
                return None

            # Create activity log for update
            self.activity_repo.create_activity_log({
                "project_id": project_id,
                "message": "Project updated",
                "activity_type": "general",
                "created_by": updated_by
            })

            return self._convert_project_to_response(project)
        except Exception as e:
            raise Exception(f"Failed to update project: {str(e)}")

    def delete_project(self, project_id: int, business_id: int) -> bool:
        """Delete project"""
        try:
            return self.project_repo.delete_project(project_id, business_id)
        except Exception as e:
            raise Exception(f"Failed to delete project: {str(e)}")

    def get_project_analytics(self, business_id: int) -> ProjectAnalytics:
        """Get project analytics"""
        try:
            analytics_data = self.project_repo.get_project_analytics(business_id)
            return ProjectAnalytics(**analytics_data)
        except Exception as e:
            raise Exception(f"Failed to get project analytics: {str(e)}")

    # Task Operations
    def create_task(self, task_data: TaskCreate, business_id: int, created_by: int) -> TaskResponse:
        """Create a new task with time validation"""
        try:
            # Validate that the project belongs to the business
            project = self.project_repo.get_project_by_id(task_data.project_id, business_id)
            if not project:
                raise Exception("Project not found")

            # Validate time before creating task
            validation = self.validate_task_time(
                task_data.start_date,
                task_data.end_date,
                task_data.projected_days,
                task_data.projected_hours,
                task_data.projected_minutes
            )

            if not validation.is_valid:
                raise Exception(validation.error_message or "Time validation failed")

            task = self.task_repo.create_task(task_data, created_by)
            
            # Update project metrics
            self.project_repo.update_project_metrics(task_data.project_id)
            
            return self._convert_task_to_response(task)
        except Exception as e:
            raise Exception(f"Failed to create task: {str(e)}")

    def get_task(self, task_id: int, business_id: int) -> Optional[TaskResponse]:
        """Get task by ID"""
        try:
            task = self.task_repo.get_task_by_id(task_id, business_id)
            return self._convert_task_to_response(task) if task else None
        except Exception as e:
            raise Exception(f"Failed to get task: {str(e)}")

    def get_tasks(self, business_id: int, filters: Optional[TaskFilters] = None,
                 skip: int = 0, limit: int = 100) -> List[TaskSummary]:
        """Get tasks with optional filters"""
        try:
            tasks = self.task_repo.get_tasks(business_id, filters, skip, limit)
            return [self._convert_task_to_summary(task) for task in tasks]
        except Exception as e:
            raise Exception(f"Failed to get tasks: {str(e)}")

    def update_task(self, task_id: int, business_id: int, task_data: TaskUpdate, updated_by: int) -> Optional[TaskResponse]:
        """Update task with time validation"""
        try:
            # Get existing task
            existing_task = self.task_repo.get_task_by_id(task_id, business_id)
            if not existing_task:
                return None

            # Validate time if time-related fields are being updated
            if any(field in task_data.dict(exclude_unset=True) for field in 
                  ['start_date', 'end_date', 'projected_days', 'projected_hours', 'projected_minutes']):
                
                start_date = task_data.start_date or existing_task.start_date
                end_date = task_data.end_date or existing_task.end_date
                projected_days = task_data.projected_days if task_data.projected_days is not None else existing_task.projected_days
                projected_hours = task_data.projected_hours if task_data.projected_hours is not None else existing_task.projected_hours
                projected_minutes = task_data.projected_minutes if task_data.projected_minutes is not None else existing_task.projected_minutes

                validation = self.validate_task_time(start_date, end_date, projected_days, projected_hours, projected_minutes)
                if not validation.is_valid:
                    raise Exception(validation.error_message or "Time validation failed")

            task = self.task_repo.update_task(task_id, business_id, task_data)
            if not task:
                return None

            # Create activity log
            self.activity_repo.create_activity_log({
                "project_id": task.project_id,
                "message": f"Task '{task.name}' updated",
                "activity_type": "task",
                "task_id": task_id,
                "created_by": updated_by
            })

            # Update project metrics
            self.project_repo.update_project_metrics(task.project_id)

            return self._convert_task_to_response(task)
        except Exception as e:
            raise Exception(f"Failed to update task: {str(e)}")

    def delete_task(self, task_id: int, business_id: int, deleted_by: int) -> bool:
        """Delete task"""
        try:
            task = self.task_repo.get_task_by_id(task_id, business_id)
            if not task:
                return False

            project_id = task.project_id
            task_name = task.name

            success = self.task_repo.delete_task(task_id, business_id)
            if success:
                # Create activity log
                self.activity_repo.create_activity_log({
                    "project_id": project_id,
                    "message": f"Task '{task_name}' deleted",
                    "activity_type": "task",
                    "created_by": deleted_by
                })

                # Update project metrics
                self.project_repo.update_project_metrics(project_id)

            return success
        except Exception as e:
            raise Exception(f"Failed to delete task: {str(e)}")

    def validate_task_time(self, start_date: date, end_date: date, 
                          projected_days: int, projected_hours: int, projected_minutes: int) -> TimeValidationResponse:
        """Validate task time against available working hours"""
        try:
            # Calculate working days (excluding weekends)
            working_days = self._calculate_working_days(start_date, end_date)
            available_hours = Decimal(working_days * 8)  # 8 hours per working day

            # Calculate projected hours
            total_projected_minutes = projected_days * 24 * 60 + projected_hours * 60 + projected_minutes
            projected_hours_decimal = Decimal(total_projected_minutes) / 60

            # Validation
            is_valid = projected_hours_decimal <= available_hours
            shortage = max(Decimal(0), projected_hours_decimal - available_hours)
            buffer = max(Decimal(0), available_hours - projected_hours_decimal)

            warning_message = None
            error_message = None

            if not is_valid:
                error_message = f"Projected time ({projected_hours_decimal:.1f}h) exceeds available working hours ({available_hours:.1f}h) by {shortage:.1f}h"
            elif buffer < Decimal(4):  # Less than 4 hours buffer
                warning_message = f"Low time buffer: only {buffer:.1f}h remaining"

            return TimeValidationResponse(
                is_valid=is_valid,
                available_working_days=working_days,
                available_working_hours=available_hours,
                projected_hours=projected_hours_decimal,
                has_mismatch=not is_valid,
                shortage_hours=shortage,
                buffer_hours=buffer,
                warning_message=warning_message,
                error_message=error_message
            )
        except Exception as e:
            return TimeValidationResponse(
                is_valid=False,
                available_working_days=0,
                available_working_hours=Decimal(0),
                projected_hours=Decimal(0),
                has_mismatch=True,
                shortage_hours=Decimal(0),
                buffer_hours=Decimal(0),
                error_message=f"Validation error: {str(e)}"
            )

    # Time Entry Operations
    def create_time_entry(self, time_entry_data: TimeEntryCreate, business_id: int, created_by: int) -> TimeEntryResponse:
        """Create a new time entry"""
        try:
            # Validate that the task belongs to the business
            task = self.task_repo.get_task_by_id(time_entry_data.task_id, business_id)
            if not task:
                raise Exception("Task not found")

            time_entry = self.time_entry_repo.create_time_entry(time_entry_data, created_by)
            
            # Update task time spent
            self.task_repo.update_task_time_spent(time_entry_data.task_id)
            
            # Update project metrics
            self.project_repo.update_project_metrics(task.project_id)
            
            return self._convert_time_entry_to_response(time_entry)
        except Exception as e:
            raise Exception(f"Failed to create time entry: {str(e)}")

    def get_time_entry(self, time_entry_id: int, business_id: int) -> Optional[TimeEntryResponse]:
        """Get time entry by ID"""
        try:
            time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_id, business_id)
            return self._convert_time_entry_to_response(time_entry) if time_entry else None
        except Exception as e:
            raise Exception(f"Failed to get time entry: {str(e)}")

    def get_time_entries(self, business_id: int, filters: Optional[TimeEntryFilters] = None,
                        skip: int = 0, limit: int = 100) -> List[TimeEntryResponse]:
        """Get time entries with optional filters"""
        try:
            time_entries = self.time_entry_repo.get_time_entries(business_id, filters, skip, limit)
            return [self._convert_time_entry_to_response(entry) for entry in time_entries]
        except Exception as e:
            raise Exception(f"Failed to get time entries: {str(e)}")

    def update_time_entry(self, time_entry_id: int, business_id: int, time_entry_data: TimeEntryUpdate, updated_by: int) -> Optional[TimeEntryResponse]:
        """Update time entry"""
        try:
            time_entry = self.time_entry_repo.update_time_entry(time_entry_id, business_id, time_entry_data)
            if not time_entry:
                return None

            # Update task time spent
            self.task_repo.update_task_time_spent(time_entry.task_id)
            
            # Update project metrics
            task = self.task_repo.get_task_by_id(time_entry.task_id, business_id)
            if task:
                self.project_repo.update_project_metrics(task.project_id)

            return self._convert_time_entry_to_response(time_entry)
        except Exception as e:
            raise Exception(f"Failed to update time entry: {str(e)}")

    def delete_time_entry(self, time_entry_id: int, business_id: int) -> bool:
        """Delete time entry"""
        try:
            time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_id, business_id)
            if not time_entry:
                return False

            task_id = time_entry.task_id
            success = self.time_entry_repo.delete_time_entry(time_entry_id, business_id)
            
            if success:
                # Update task time spent
                self.task_repo.update_task_time_spent(task_id)
                
                # Update project metrics
                task = self.task_repo.get_task_by_id(task_id, business_id)
                if task:
                    self.project_repo.update_project_metrics(task.project_id)

            return success
        except Exception as e:
            raise Exception(f"Failed to delete time entry: {str(e)}")

    # Project Member Operations
    def add_project_member(self, member_data: ProjectMemberCreate, business_id: int, created_by: int) -> ProjectMemberResponse:
        """Add member to project"""
        try:
            # Validate that the project belongs to the business
            project = self.project_repo.get_project_by_id(member_data.project_id, business_id)
            if not project:
                raise Exception("Project not found")

            member = self.member_repo.create_project_member(member_data, created_by)
            
            # Update project metrics
            self.project_repo.update_project_metrics(member_data.project_id)
            
            # Create activity log
            member_name = "New member"
            if member.user:
                member_name = member.user.name
            elif member.employee:
                member_name = f"{member.employee.first_name} {member.employee.last_name}"

            self.activity_repo.create_activity_log({
                "project_id": member_data.project_id,
                "message": f"{member_name} added to project",
                "activity_type": "member",
                "member_id": member.id,
                "created_by": created_by
            })
            
            return self._convert_member_to_response(member)
        except Exception as e:
            raise Exception(f"Failed to add project member: {str(e)}")

    def get_project_members(self, project_id: int, business_id: int) -> List[ProjectMemberResponse]:
        """Get project members"""
        try:
            members = self.member_repo.get_project_members(project_id, business_id)
            return [self._convert_member_to_response(member) for member in members]
        except Exception as e:
            raise Exception(f"Failed to get project members: {str(e)}")

    def update_project_member(self, member_id: int, business_id: int, member_data: ProjectMemberUpdate, updated_by: int) -> Optional[ProjectMemberResponse]:
        """Update project member"""
        try:
            member = self.member_repo.update_project_member(member_id, business_id, member_data)
            if not member:
                return None

            # Create activity log
            member_name = "Member"
            if member.user:
                member_name = member.user.name
            elif member.employee:
                member_name = f"{member.employee.first_name} {member.employee.last_name}"

            self.activity_repo.create_activity_log({
                "project_id": member.project_id,
                "message": f"{member_name} role updated",
                "activity_type": "member",
                "member_id": member_id,
                "created_by": updated_by
            })

            return self._convert_member_to_response(member)
        except Exception as e:
            raise Exception(f"Failed to update project member: {str(e)}")

    def remove_project_member(self, member_id: int, business_id: int, removed_by: int) -> bool:
        """Remove member from project"""
        try:
            # Get member info for activity log
            member = self.db.query(ProjectMember).join(Project).filter(
                ProjectMember.id == member_id,
                Project.business_id == business_id
            ).first()
            
            if not member:
                return False

            project_id = member.project_id
            member_name = "Member"
            if member.user:
                member_name = member.user.name
            elif member.employee:
                member_name = f"{member.employee.first_name} {member.employee.last_name}"

            success = self.member_repo.delete_project_member(member_id, business_id)
            
            if success:
                # Update project metrics
                self.project_repo.update_project_metrics(project_id)
                
                # Create activity log
                self.activity_repo.create_activity_log({
                    "project_id": project_id,
                    "message": f"{member_name} removed from project",
                    "activity_type": "member",
                    "created_by": removed_by
                })

            return success
        except Exception as e:
            raise Exception(f"Failed to remove project member: {str(e)}")

    # Activity Log Operations
    def get_project_activity_logs(self, project_id: int, business_id: int, limit: int = 50) -> List[ProjectActivityLogResponse]:
        """Get project activity logs"""
        try:
            logs = self.activity_repo.get_project_activity_logs(project_id, business_id, limit)
            return [self._convert_activity_log_to_response(log) for log in logs]
        except Exception as e:
            raise Exception(f"Failed to get project activity logs: {str(e)}")

    # Helper Methods
    def _calculate_working_days(self, start_date: date, end_date: date) -> int:
        """Calculate working days between two dates (excluding weekends)"""
        if start_date > end_date:
            return 0
        
        current = start_date
        working_days = 0
        
        while current <= end_date:
            # Monday = 0, Sunday = 6
            if current.weekday() < 5:  # Monday to Friday
                working_days += 1
            current += timedelta(days=1)
        
        return working_days

    def _convert_project_to_response(self, project) -> ProjectResponse:
        """Convert project model to response schema"""
        return ProjectResponse(
            id=project.id,
            business_id=project.business_id,
            name=project.name,
            client=project.client,
            description=project.description,
            start_date=project.start_date,
            end_date=project.end_date,
            completed_at=project.completed_at,
            status=project.status,
            is_active=project.is_active,
            is_completed=project.is_completed,
            total_tasks=project.total_tasks,
            completed_tasks=project.completed_tasks,
            total_members=project.total_members,
            total_work_hours=project.total_work_hours,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at
        )

    def _convert_project_to_summary(self, project) -> ProjectSummary:
        """Convert project model to summary schema"""
        completion_percentage = (project.completed_tasks / project.total_tasks * 100) if project.total_tasks > 0 else 0
        is_overdue = project.end_date < date.today() and project.status != ProjectStatus.COMPLETED
        
        return ProjectSummary(
            id=project.id,
            name=project.name,
            client=project.client,
            start_date=project.start_date,
            end_date=project.end_date,
            status=project.status,
            total_tasks=project.total_tasks,
            completed_tasks=project.completed_tasks,
            total_members=project.total_members,
            completion_percentage=round(completion_percentage, 2),
            is_overdue=is_overdue
        )

    def _convert_task_to_response(self, task) -> TaskResponse:
        """Convert task model to response schema"""
        return TaskResponse(
            id=task.id,
            project_id=task.project_id,
            project_name=task.project.name,
            name=task.name,
            description=task.description,
            start_date=task.start_date,
            end_date=task.end_date,
            status=task.status,
            is_completed=task.is_completed,
            projected_days=task.projected_days,
            projected_hours=task.projected_hours,
            projected_minutes=task.projected_minutes,
            total_projected_minutes=task.total_projected_minutes,
            time_spent_minutes=task.time_spent_minutes,
            date_range_display=task.date_range_display,
            projected_time_display=task.projected_time_display,
            time_spent_display=task.time_spent_display,
            available_working_days=task.available_working_days,
            available_working_hours=task.available_working_hours,
            has_time_mismatch=task.has_time_mismatch,
            time_shortage_hours=task.time_shortage_hours,
            time_buffer_hours=task.time_buffer_hours,
            created_by=task.created_by,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

    def _convert_task_to_summary(self, task) -> TaskSummary:
        """Convert task model to summary schema"""
        is_overdue = task.end_date < date.today() and not task.is_completed
        
        return TaskSummary(
            id=task.id,
            name=task.name,
            project_name=task.project.name,
            status=task.status,
            date_range_display=task.date_range_display or "",
            projected_time_display=task.projected_time_display or "",
            time_spent_display=task.time_spent_display or "",
            has_time_mismatch=task.has_time_mismatch,
            is_overdue=is_overdue
        )

    def _convert_time_entry_to_response(self, time_entry) -> TimeEntryResponse:
        """Convert time entry model to response schema"""
        return TimeEntryResponse(
            id=time_entry.id,
            task_id=time_entry.task_id,
            task_name=time_entry.task.name,
            project_name=time_entry.task.project.name,
            date=time_entry.date,
            hours=time_entry.hours,
            minutes=time_entry.minutes,
            total_minutes=time_entry.total_minutes,
            duration_display=time_entry.duration_display,
            description=time_entry.description,
            created_by=time_entry.created_by,
            created_at=time_entry.created_at,
            updated_at=time_entry.updated_at
        )

    def _convert_member_to_response(self, member) -> ProjectMemberResponse:
        """Convert project member model to response schema"""
        member_name = "Unknown"
        member_email = None
        
        if member.user:
            member_name = member.user.name
            member_email = member.user.email
        elif member.employee:
            member_name = f"{member.employee.first_name} {member.employee.last_name}"
            member_email = member.employee.email
        
        return ProjectMemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            employee_id=member.employee_id,
            role=member.role,
            joined_date=member.joined_date,
            is_active=member.is_active,
            member_name=member_name,
            member_email=member_email,
            created_at=member.created_at
        )

    def _convert_activity_log_to_response(self, log) -> ProjectActivityLogResponse:
        """Convert activity log model to response schema"""
        creator_name = log.creator.name if log.creator else "System"
        
        return ProjectActivityLogResponse(
            id=log.id,
            project_id=log.project_id,
            message=log.message,
            activity_type=log.activity_type,
            task_id=log.task_id,
            member_id=log.member_id,
            created_by=log.created_by,
            creator_name=creator_name,
            created_at=log.created_at
        )