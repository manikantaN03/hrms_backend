"""
TODO/Task API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.todo_service import TodoService
from app.schemas.todo import (
    TaskCreate, TaskUpdate, TaskResponse, TaskStats, TaskFilters,
    TaskStatus, TaskPriority, TaskCategory
)

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[List[TaskStatus]] = Query(None),
    priority: Optional[List[TaskPriority]] = Query(None),
    category: Optional[List[TaskCategory]] = Query(None),
    assigned_to_id: Optional[int] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    overdue_only: bool = Query(False),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks for current user with filters
    
    **Query Parameters:**
    - status: Filter by task status (can be multiple)
    - priority: Filter by priority (can be multiple)
    - category: Filter by category (can be multiple)
    - assigned_to_id: Filter by assigned user
    - is_pinned: Filter pinned tasks
    - overdue_only: Show only overdue tasks
    - search: Search in title, description, tags
    - skip: Pagination offset
    - limit: Pagination limit
    """
    try:
        filters = TaskFilters(
            status=status,
            priority=priority,
            category=category,
            assigned_to_id=assigned_to_id,
            is_pinned=is_pinned,
            overdue_only=overdue_only,
            search=search
        )
        
        service = TodoService(db)
        tasks = service.get_tasks(current_user.id, filters, skip, limit)
        
        return tasks
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )


@router.get("/stats", response_model=TaskStats)
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get task statistics for current user
    
    **Returns:**
    - Total tasks count
    - Count by status (todo, in_progress, completed)
    - Overdue tasks count
    - High priority tasks count
    - Completion rate percentage
    """
    try:
        service = TodoService(db)
        stats = service.get_task_stats(current_user.id)
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task stats: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single task by ID"""
    try:
        service = TodoService(db)
        task = service.get_task_by_id(task_id, current_user.id)
        
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
            detail=f"Failed to fetch task: {str(e)}"
        )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task
    
    **Required fields:**
    - title: Task title (1-255 characters)
    
    **Optional fields:**
    - description: Task description
    - category: Task category (default: work)
    - status: Task status (default: todo)
    - priority: Task priority (default: medium)
    - due_date: Due date
    - assigned_to_id: Assign to user
    - tags: Comma-separated tags
    - is_pinned: Pin task (default: false)
    - reminder_minutes: Reminder before due date
    """
    try:
        service = TodoService(db)
        task = service.create_task(task_data, current_user.id)
        
        return task
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task
    
    **All fields are optional**
    - Only provided fields will be updated
    - Changing status to 'completed' automatically sets completed_at timestamp
    """
    try:
        service = TodoService(db)
        task = service.update_task(task_id, current_user.id, task_data)
        
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


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    try:
        service = TodoService(db)
        success = service.delete_task(task_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )
