from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.workflow_repository import (
    create_workflow,
    get_all_workflows,
    get_workflow_by_id,
    update_workflow,
    delete_workflow,
)
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


# ✅ Create Workflow (business_id passed as parameter)
def create_workflow_service(db: Session, payload: WorkflowCreate, business_id: int):
    return create_workflow(db, payload, business_id)


# ✅ Get All Workflows (BUSINESS-SCOPED)
def get_workflows_service(db: Session, business_id: int):
    return get_all_workflows(db, business_id)


# ✅ Get One Workflow (BUSINESS-SCOPED)
def get_workflow_service(db: Session, workflow_id: int, business_id: int):
    workflow = get_workflow_by_id(db, workflow_id, business_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


# ✅ Update Workflow (BUSINESS-SCOPED)
def update_workflow_service(
    db: Session,
    workflow_id: int,
    business_id: int,
    payload: WorkflowUpdate
):
    updated = update_workflow(db, workflow_id, business_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return updated


# ✅ Delete Workflow (BUSINESS-SCOPED)
def delete_workflow_service(db: Session, workflow_id: int, business_id: int):
    deleted = delete_workflow(db, workflow_id, business_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted successfully"}
