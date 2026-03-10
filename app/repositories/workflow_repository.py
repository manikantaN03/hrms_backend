from sqlalchemy.orm import Session
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


# ✅ Create Workflow (BUSINESS-SCOPED)
def create_workflow(db: Session, payload: WorkflowCreate, business_id: int):
    # Check for duplicate name within the same business
    existing = db.query(Workflow).filter(
        Workflow.business_id == business_id,
        Workflow.name == payload.name
    ).first()
    
    if existing:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Workflow with name '{payload.name}' already exists for this business"
        )
    
    workflow = Workflow(
        business_id=business_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        fields=0,
        steps=0,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


# ✅ Get All Workflows (BUSINESS-SCOPED)
def get_all_workflows(db: Session, business_id: int):
    return (
        db.query(Workflow)
        .filter(Workflow.business_id == business_id)   # ✅ TENANT SAFE
        .order_by(Workflow.id.desc())
        .all()
    )


# ✅ Get One Workflow (BUSINESS-SCOPED)
def get_workflow_by_id(db: Session, workflow_id: int, business_id: int):
    return (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.business_id == business_id      # ✅ TENANT SAFE
        )
        .first()
    )


# ✅ Update Workflow (BUSINESS-SCOPED)
def update_workflow(db: Session, workflow_id: int, business_id: int, payload: WorkflowUpdate):
    workflow = get_workflow_by_id(db, workflow_id, business_id)
    if not workflow:
        return None
    
    # Check for duplicate name if name is being updated
    if payload.name and payload.name != workflow.name:
        existing = db.query(Workflow).filter(
            Workflow.business_id == business_id,
            Workflow.name == payload.name,
            Workflow.id != workflow_id
        ).first()
        
        if existing:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Workflow with name '{payload.name}' already exists for this business"
            )

    # Only update fields that are provided (not None)
    if payload.name is not None:
        workflow.name = payload.name
    if payload.description is not None:
        workflow.description = payload.description
    if payload.is_active is not None:
        workflow.is_active = payload.is_active

    db.commit()
    db.refresh(workflow)
    return workflow


#  Delete Workflow (BUSINESS-SCOPED)
def delete_workflow(db: Session, workflow_id: int, business_id: int):
    workflow = get_workflow_by_id(db, workflow_id, business_id)
    if not workflow:
        return False

    db.delete(workflow)
    db.commit()
    return True
