"""
Project Management Repository
Data access layer for Project Management operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, extract, Integer
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.project_management import (
    Project, Task, TimeEntry, ProjectMember, ProjectActivityLog,
    ProjectStatus, TaskStatus, MemberRole
)
from app.models.user import User
from app.models.employee import Employee
from app.schemas.project_management import (
    ProjectCreate, ProjectUpdate, TaskCreate, TaskUpdate,
    TimeEntryCreate, TimeEntryUpdate, ProjectMemberCreate, ProjectMemberUpdate,
    ProjectFilters, TaskFilters, TimeEntryFilters
)


class ProjectRepository:
    """Repository for project operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project_data: ProjectCreate, business_id: int, created_by: int) -> Project:
        """Create a new project"""
        project = Project(
            business_id=business_id,
            name=project_data.name,
            client=project_data.client,
            description=project_data.description,
            start_date=project_data.start_date,
            end_date=project_data.end_date,
            status=project_data.status,
            is_active=project_data.is_active,
            is_completed=project_data.is_completed,
            created_by=created_by
        )
        
        self.db.add(project)
        self.db.flush()
        
        # Create initial activity log
        activity_log = ProjectActivityLog(
            project_id=project.id,
            message="Project created",
            activity_type="general",
            created_by=created_by
        )
        self.db.add(activity_log)
        
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_by_id(self, project_id: int, business_id: int) -> Optional[Project]:
        """Get project by ID"""
        return self.db.query(Project).options(
            joinedload(Project.tasks),
            joinedload(Project.members),
            joinedload(Project.activity_logs)
        ).filter(
            Project.id == project_id,
            Project.business_id == business_id
        ).first()

    def get_projects(self, business_id: int, filters: Optional[ProjectFilters] = None, 
                    skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects with optional filters"""
        query = self.db.query(Project).filter(Project.business_id == business_id)

        if filters:
            if filters.status:
                query = query.filter(Project.status.in_(filters.status))
            
            if filters.client:
                query = query.filter(Project.client.ilike(f"%{filters.client}%"))
            
            if filters.start_date_from:
                query = query.filter(Project.start_date >= filters.start_date_from)
            
            if filters.start_date_to:
                query = query.filter(Project.start_date <= filters.start_date_to)
            
            if filters.end_date_from:
                query = query.filter(Project.end_date >= filters.end_date_from)
            
            if filters.end_date_to:
                query = query.filter(Project.end_date <= filters.end_date_to)
            
            if filters.is_overdue is not None:
                today = date.today()
                if filters.is_overdue:
                    query = query.filter(
                        and_(
                            Project.end_date < today,
                            Project.status != ProjectStatus.COMPLETED
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            Project.end_date >= today,
                            Project.status == ProjectStatus.COMPLETED
                        )
                    )
            
            if filters.created_by:
                query = query.filter(Project.created_by == filters.created_by)

        return query.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()

    def update_project(self, project_id: int, business_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """Update project"""
        project = self.get_project_by_id(project_id, business_id)
        if not project:
            return None

        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int, business_id: int) -> bool:
        """Delete project"""
        project = self.get_project_by_id(project_id, business_id)
        if not project:
            return False

        self.db.delete(project)
        self.db.commit()
        return True

    def update_project_metrics(self, project_id: int):
        """Update project metrics (tasks, members, work hours)"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        # Update task counts
        total_tasks = self.db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar() or 0
        completed_tasks = self.db.query(func.count(Task.id)).filter(
            Task.project_id == project_id,
            Task.is_completed == True
        ).scalar() or 0

        # Update member count
        total_members = self.db.query(func.count(ProjectMember.id)).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        ).scalar() or 0

        # Update total work hours
        total_work_minutes = self.db.query(func.sum(TimeEntry.total_minutes)).join(Task).filter(
            Task.project_id == project_id
        ).scalar() or 0
        total_work_hours = Decimal(total_work_minutes) / 60

        # Update project
        project.total_tasks = total_tasks
        project.completed_tasks = completed_tasks
        project.total_members = total_members
        project.total_work_hours = total_work_hours
        project.updated_at = datetime.utcnow()

        self.db.commit()

    def get_project_analytics(self, business_id: int) -> Dict[str, Any]:
        """Get project analytics"""
        # Basic counts
        total_projects = self.db.query(func.count(Project.id)).filter(Project.business_id == business_id).scalar() or 0
        
        active_projects = self.db.query(func.count(Project.id)).filter(
            Project.business_id == business_id,
            Project.status == ProjectStatus.ACTIVE
        ).scalar() or 0
        
        completed_projects = self.db.query(func.count(Project.id)).filter(
            Project.business_id == business_id,
            Project.status == ProjectStatus.COMPLETED
        ).scalar() or 0
        
        on_hold_projects = self.db.query(func.count(Project.id)).filter(
            Project.business_id == business_id,
            Project.status == ProjectStatus.ON_HOLD
        ).scalar() or 0
        
        cancelled_projects = self.db.query(func.count(Project.id)).filter(
            Project.business_id == business_id,
            Project.status == ProjectStatus.CANCELLED
        ).scalar() or 0

        # Overdue projects
        today = date.today()
        overdue_projects = self.db.query(func.count(Project.id)).filter(
            Project.business_id == business_id,
            Project.end_date < today,
            Project.status != ProjectStatus.COMPLETED
        ).scalar() or 0

        # On-time completion
        on_time_completed = self.db.query(func.count(Project.id)).filter(
            Project.business_id == business_id,
            Project.status == ProjectStatus.COMPLETED,
            Project.completed_at <= Project.end_date
        ).scalar() or 0

        # Task analytics
        total_tasks = self.db.query(func.count(Task.id)).join(Project).filter(
            Project.business_id == business_id
        ).scalar() or 0
        
        completed_tasks = self.db.query(func.count(Task.id)).join(Project).filter(
            Project.business_id == business_id,
            Task.is_completed == True
        ).scalar() or 0

        # Work hours
        total_work_minutes = self.db.query(func.sum(TimeEntry.total_minutes)).join(Task).join(Project).filter(
            Project.business_id == business_id
        ).scalar() or 0
        total_work_hours = Decimal(total_work_minutes) / 60

        # Calculate rates
        completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
        on_time_completion_rate = (on_time_completed / completed_projects * 100) if completed_projects > 0 else 0
        task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Average project duration (in days)
        avg_duration_query = self.db.query(
            func.avg(func.cast(Project.end_date - Project.start_date, Integer))
        ).filter(Project.business_id == business_id)
        average_project_duration = avg_duration_query.scalar() or 0

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "on_hold_projects": on_hold_projects,
            "cancelled_projects": cancelled_projects,
            "completion_rate": round(completion_rate, 2),
            "on_time_completion_rate": round(on_time_completion_rate, 2),
            "overdue_projects": overdue_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_rate": round(task_completion_rate, 2),
            "total_work_hours": total_work_hours,
            "average_project_duration": round(average_project_duration, 2)
        }


class TaskRepository:
    """Repository for task operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_data: TaskCreate, created_by: int) -> Task:
        """Create a new task"""
        # Calculate total projected minutes
        total_projected_minutes = (
            task_data.projected_days * 24 * 60 +
            task_data.projected_hours * 60 +
            task_data.projected_minutes
        )

        task = Task(
            project_id=task_data.project_id,
            name=task_data.name,
            description=task_data.description,
            start_date=task_data.start_date,
            end_date=task_data.end_date,
            status=task_data.status,
            is_completed=task_data.is_completed,
            projected_days=task_data.projected_days,
            projected_hours=task_data.projected_hours,
            projected_minutes=task_data.projected_minutes,
            total_projected_minutes=total_projected_minutes,
            created_by=created_by
        )

        # Calculate display fields and validation
        self._calculate_task_fields(task)
        
        self.db.add(task)
        self.db.flush()
        
        # Create activity log
        activity_log = ProjectActivityLog(
            project_id=task.project_id,
            message=f"Task '{task.name}' created",
            activity_type="task",
            task_id=task.id,
            created_by=created_by
        )
        self.db.add(activity_log)
        
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task_by_id(self, task_id: int, business_id: int) -> Optional[Task]:
        """Get task by ID"""
        return self.db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.time_entries)
        ).join(Project).filter(
            Task.id == task_id,
            Project.business_id == business_id
        ).first()

    def get_tasks(self, business_id: int, filters: Optional[TaskFilters] = None,
                 skip: int = 0, limit: int = 100) -> List[Task]:
        """Get tasks with optional filters"""
        query = self.db.query(Task).join(Project).filter(Project.business_id == business_id)

        if filters:
            if filters.project_id:
                query = query.filter(Task.project_id == filters.project_id)
            
            if filters.status:
                query = query.filter(Task.status.in_(filters.status))
            
            if filters.start_date_from:
                query = query.filter(Task.start_date >= filters.start_date_from)
            
            if filters.start_date_to:
                query = query.filter(Task.start_date <= filters.start_date_to)
            
            if filters.end_date_from:
                query = query.filter(Task.end_date >= filters.end_date_from)
            
            if filters.end_date_to:
                query = query.filter(Task.end_date <= filters.end_date_to)
            
            if filters.is_overdue is not None:
                today = date.today()
                if filters.is_overdue:
                    query = query.filter(
                        and_(
                            Task.end_date < today,
                            Task.is_completed == False
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            Task.end_date >= today,
                            Task.is_completed == True
                        )
                    )
            
            if filters.has_time_mismatch is not None:
                query = query.filter(Task.has_time_mismatch == filters.has_time_mismatch)
            
            if filters.created_by:
                query = query.filter(Task.created_by == filters.created_by)

        return query.options(joinedload(Task.project)).order_by(desc(Task.created_at)).offset(skip).limit(limit).all()

    def update_task(self, task_id: int, business_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update task"""
        task = self.get_task_by_id(task_id, business_id)
        if not task:
            return None

        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # Recalculate total projected minutes if time fields changed
        if any(field in update_data for field in ['projected_days', 'projected_hours', 'projected_minutes']):
            task.total_projected_minutes = (
                task.projected_days * 24 * 60 +
                task.projected_hours * 60 +
                task.projected_minutes
            )

        # Recalculate display fields and validation
        self._calculate_task_fields(task)
        
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task_id: int, business_id: int) -> bool:
        """Delete task"""
        task = self.get_task_by_id(task_id, business_id)
        if not task:
            return False

        self.db.delete(task)
        self.db.commit()
        return True

    def update_task_time_spent(self, task_id: int):
        """Update task time spent from time entries"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        total_minutes = self.db.query(func.sum(TimeEntry.total_minutes)).filter(
            TimeEntry.task_id == task_id
        ).scalar() or 0

        task.time_spent_minutes = total_minutes
        task.time_spent_display = self._format_time_display(0, total_minutes)
        task.updated_at = datetime.utcnow()

        self.db.commit()

    def _calculate_task_fields(self, task: Task):
        """Calculate display fields and time validation for task"""
        # Format date range display
        task.date_range_display = f"{task.start_date.strftime('%d %b %Y')} to {task.end_date.strftime('%d %b %Y')}"
        
        # Format projected time display
        task.projected_time_display = f"{task.projected_days:02d}d {task.projected_hours:02d}h {task.projected_minutes:02d}m"
        
        # Format time spent display
        task.time_spent_display = self._format_time_display(0, task.time_spent_minutes)
        
        # Calculate working days and hours
        working_days = self._calculate_working_days(task.start_date, task.end_date)
        task.available_working_days = working_days
        task.available_working_hours = Decimal(working_days * 8)  # 8 hours per working day
        
        # Calculate projected hours
        projected_hours = Decimal(task.total_projected_minutes) / 60
        
        # Time validation
        if projected_hours > task.available_working_hours:
            task.has_time_mismatch = True
            task.time_shortage_hours = projected_hours - task.available_working_hours
            task.time_buffer_hours = Decimal(0)
        else:
            task.has_time_mismatch = False
            task.time_shortage_hours = Decimal(0)
            task.time_buffer_hours = task.available_working_hours - projected_hours

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

    def _format_time_display(self, hours: int, minutes: int) -> str:
        """Format time for display"""
        if isinstance(minutes, int) and minutes >= 60:
            total_hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{total_hours:02d}h {remaining_minutes:02d}m"
        else:
            return f"{hours:02d}h {minutes:02d}m"


class TimeEntryRepository:
    """Repository for time entry operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_time_entry(self, time_entry_data: TimeEntryCreate, created_by: int) -> TimeEntry:
        """Create a new time entry"""
        total_minutes = time_entry_data.hours * 60 + time_entry_data.minutes
        
        time_entry = TimeEntry(
            task_id=time_entry_data.task_id,
            date=time_entry_data.date,
            hours=time_entry_data.hours,
            minutes=time_entry_data.minutes,
            total_minutes=total_minutes,
            description=time_entry_data.description,
            duration_display=f"{time_entry_data.hours:02d}h {time_entry_data.minutes:02d}m",
            created_by=created_by
        )
        
        self.db.add(time_entry)
        self.db.commit()
        self.db.refresh(time_entry)
        return time_entry

    def get_time_entry_by_id(self, time_entry_id: int, business_id: int) -> Optional[TimeEntry]:
        """Get time entry by ID"""
        return self.db.query(TimeEntry).options(
            joinedload(TimeEntry.task).joinedload(Task.project)
        ).join(Task).join(Project).filter(
            TimeEntry.id == time_entry_id,
            Project.business_id == business_id
        ).first()

    def get_time_entries(self, business_id: int, filters: Optional[TimeEntryFilters] = None,
                        skip: int = 0, limit: int = 100) -> List[TimeEntry]:
        """Get time entries with optional filters"""
        query = self.db.query(TimeEntry).join(Task).join(Project).filter(Project.business_id == business_id)

        if filters:
            if filters.task_id:
                query = query.filter(TimeEntry.task_id == filters.task_id)
            
            if filters.project_id:
                query = query.filter(Task.project_id == filters.project_id)
            
            if filters.date_from:
                query = query.filter(TimeEntry.date >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(TimeEntry.date <= filters.date_to)
            
            if filters.created_by:
                query = query.filter(TimeEntry.created_by == filters.created_by)

        return query.options(
            joinedload(TimeEntry.task).joinedload(Task.project)
        ).order_by(desc(TimeEntry.date), desc(TimeEntry.created_at)).offset(skip).limit(limit).all()

    def update_time_entry(self, time_entry_id: int, business_id: int, time_entry_data: TimeEntryUpdate) -> Optional[TimeEntry]:
        """Update time entry"""
        time_entry = self.get_time_entry_by_id(time_entry_id, business_id)
        if not time_entry:
            return None

        update_data = time_entry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(time_entry, field, value)

        # Recalculate total minutes and display if time changed
        if 'hours' in update_data or 'minutes' in update_data:
            time_entry.total_minutes = time_entry.hours * 60 + time_entry.minutes
            time_entry.duration_display = f"{time_entry.hours:02d}h {time_entry.minutes:02d}m"

        time_entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(time_entry)
        return time_entry

    def delete_time_entry(self, time_entry_id: int, business_id: int) -> bool:
        """Delete time entry"""
        time_entry = self.get_time_entry_by_id(time_entry_id, business_id)
        if not time_entry:
            return False

        self.db.delete(time_entry)
        self.db.commit()
        return True


class ProjectMemberRepository:
    """Repository for project member operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_project_member(self, member_data: ProjectMemberCreate, created_by: int) -> ProjectMember:
        """Create a new project member"""
        member = ProjectMember(
            project_id=member_data.project_id,
            user_id=member_data.user_id,
            employee_id=member_data.employee_id,
            role=member_data.role,
            joined_date=member_data.joined_date,
            created_by=created_by
        )
        
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_project_members(self, project_id: int, business_id: int) -> List[ProjectMember]:
        """Get all members of a project"""
        return self.db.query(ProjectMember).options(
            joinedload(ProjectMember.user),
            joinedload(ProjectMember.employee)
        ).join(Project).filter(
            ProjectMember.project_id == project_id,
            Project.business_id == business_id,
            ProjectMember.is_active == True
        ).all()

    def update_project_member(self, member_id: int, business_id: int, member_data: ProjectMemberUpdate) -> Optional[ProjectMember]:
        """Update project member"""
        member = self.db.query(ProjectMember).join(Project).filter(
            ProjectMember.id == member_id,
            Project.business_id == business_id
        ).first()
        
        if not member:
            return None

        update_data = member_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)

        self.db.commit()
        self.db.refresh(member)
        return member

    def delete_project_member(self, member_id: int, business_id: int) -> bool:
        """Delete project member"""
        member = self.db.query(ProjectMember).join(Project).filter(
            ProjectMember.id == member_id,
            Project.business_id == business_id
        ).first()
        
        if not member:
            return False

        self.db.delete(member)
        self.db.commit()
        return True


class ProjectActivityLogRepository:
    """Repository for project activity log operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_activity_log(self, log_data: Dict[str, Any]) -> ProjectActivityLog:
        """Create a new activity log"""
        activity_log = ProjectActivityLog(**log_data)
        self.db.add(activity_log)
        self.db.commit()
        self.db.refresh(activity_log)
        return activity_log

    def get_project_activity_logs(self, project_id: int, business_id: int, limit: int = 50) -> List[ProjectActivityLog]:
        """Get activity logs for a project"""
        return self.db.query(ProjectActivityLog).options(
            joinedload(ProjectActivityLog.creator)
        ).join(Project).filter(
            ProjectActivityLog.project_id == project_id,
            Project.business_id == business_id
        ).order_by(desc(ProjectActivityLog.created_at)).limit(limit).all()