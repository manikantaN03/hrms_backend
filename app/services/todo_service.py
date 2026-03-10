"""
TODO/Task Service
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, date

from app.models.todo import TodoTask, TaskStatus, TaskPriority, TaskCategory
from app.models.user import User
from app.schemas.todo import TaskCreate, TaskUpdate, TaskResponse, TaskStats, TaskFilters


class TodoService:
    """Service for managing tasks"""

    def __init__(self, db: Session):
        self.db = db

    def get_tasks(
        self, 
        user_id: int, 
        filters: Optional[TaskFilters] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResponse]:
        """Get tasks for a user with filters"""
        query = self.db.query(TodoTask).filter(TodoTask.user_id == user_id)

        if filters:
            if filters.status:
                query = query.filter(TodoTask.status.in_(filters.status))
            
            if filters.priority:
                query = query.filter(TodoTask.priority.in_(filters.priority))
            
            if filters.category:
                query = query.filter(TodoTask.category.in_(filters.category))
            
            if filters.assigned_to_id:
                query = query.filter(TodoTask.assigned_to_id == filters.assigned_to_id)
            
            if filters.is_pinned is not None:
                query = query.filter(TodoTask.is_pinned == filters.is_pinned)
            
            if filters.overdue_only:
                query = query.filter(
                    and_(
                        TodoTask.due_date < date.today(),
                        TodoTask.status != TaskStatus.COMPLETED
                    )
                )
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        TodoTask.title.ilike(search_term),
                        TodoTask.description.ilike(search_term),
                        TodoTask.tags.ilike(search_term)
                    )
                )

        # Order by: pinned first, then by due date, then by priority
        query = query.order_by(
            TodoTask.is_pinned.desc(),
            TodoTask.due_date.asc().nullslast(),
            TodoTask.priority.desc(),
            TodoTask.created_at.desc()
        )

        tasks = query.offset(skip).limit(limit).all()
        
        return [self._convert_to_response(task) for task in tasks]

    def get_task_by_id(self, task_id: int, user_id: int) -> Optional[TaskResponse]:
        """Get a single task by ID"""
        task = self.db.query(TodoTask).filter(
            TodoTask.id == task_id,
            TodoTask.user_id == user_id
        ).first()
        
        if task:
            return self._convert_to_response(task)
        return None

    def create_task(self, task_data: TaskCreate, user_id: int) -> TaskResponse:
        """Create a new task"""
        task = TodoTask(
            user_id=user_id,
            business_id=task_data.business_id,
            title=task_data.title,
            description=task_data.description,
            category=task_data.category,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            assigned_to_id=task_data.assigned_to_id,
            tags=task_data.tags,
            is_pinned=task_data.is_pinned,
            reminder_minutes=task_data.reminder_minutes
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return self._convert_to_response(task)

    def update_task(self, task_id: int, user_id: int, task_data: TaskUpdate) -> Optional[TaskResponse]:
        """Update a task"""
        task = self.db.query(TodoTask).filter(
            TodoTask.id == task_id,
            TodoTask.user_id == user_id
        ).first()
        
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        
        # If status is being changed to completed, set completed_at
        if 'status' in update_data and update_data['status'] == TaskStatus.COMPLETED:
            update_data['completed_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        
        return self._convert_to_response(task)

    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete a task"""
        task = self.db.query(TodoTask).filter(
            TodoTask.id == task_id,
            TodoTask.user_id == user_id
        ).first()
        
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        
        return True

    def get_task_stats(self, user_id: int) -> TaskStats:
        """Get task statistics for a user"""
        total_tasks = self.db.query(func.count(TodoTask.id)).filter(TodoTask.user_id == user_id).scalar()
        
        todo_count = self.db.query(func.count(TodoTask.id)).filter(
            TodoTask.user_id == user_id,
            TodoTask.status == TaskStatus.TODO
        ).scalar()
        
        in_progress_count = self.db.query(func.count(TodoTask.id)).filter(
            TodoTask.user_id == user_id,
            TodoTask.status == TaskStatus.IN_PROGRESS
        ).scalar()
        
        completed_count = self.db.query(func.count(TodoTask.id)).filter(
            TodoTask.user_id == user_id,
            TodoTask.status == TaskStatus.COMPLETED
        ).scalar()
        
        overdue_count = self.db.query(func.count(TodoTask.id)).filter(
            TodoTask.user_id == user_id,
            TodoTask.due_date < date.today(),
            TodoTask.status != TaskStatus.COMPLETED
        ).scalar()
        
        high_priority_count = self.db.query(func.count(TodoTask.id)).filter(
            TodoTask.user_id == user_id,
            TodoTask.priority.in_([TaskPriority.HIGH, TaskPriority.URGENT]),
            TodoTask.status != TaskStatus.COMPLETED
        ).scalar()
        
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return TaskStats(
            total_tasks=total_tasks or 0,
            todo_count=todo_count or 0,
            in_progress_count=in_progress_count or 0,
            completed_count=completed_count or 0,
            overdue_count=overdue_count or 0,
            high_priority_count=high_priority_count or 0,
            completion_rate=round(completion_rate, 2)
        )

    def _convert_to_response(self, task: TodoTask) -> TaskResponse:
        """Convert task model to response schema"""
        assigned_to_name = None
        if task.assigned_to_id and task.assigned_to:
            assigned_to_name = task.assigned_to.name
        
        is_overdue = False
        if task.due_date and task.status != TaskStatus.COMPLETED:
            is_overdue = task.due_date < date.today()
        
        return TaskResponse(
            id=task.id,
            user_id=task.user_id,
            business_id=task.business_id,
            title=task.title,
            description=task.description,
            category=task.category,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            completed_at=task.completed_at,
            assigned_to_id=task.assigned_to_id,
            assigned_to_name=assigned_to_name,
            tags=task.tags,
            is_pinned=task.is_pinned,
            reminder_minutes=task.reminder_minutes,
            created_at=task.created_at,
            updated_at=task.updated_at,
            is_overdue=is_overdue
        )
