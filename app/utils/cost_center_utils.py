"""
Cost Center Utility Functions
Provides helper functions for cost center operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cost_center import CostCenter
from app.models.employee import Employee


def sync_cost_center_employee_counts(db: Session, business_id: int = None):
    """
    Synchronize employee counts for cost centers
    
    Args:
        db: Database session
        business_id: Optional business ID to filter cost centers
        
    Returns:
        Number of cost centers updated
    """
    query = db.query(CostCenter)
    
    if business_id:
        query = query.filter(CostCenter.business_id == business_id)
    
    cost_centers = query.all()
    updated_count = 0
    
    for cc in cost_centers:
        # Count active employees assigned to this cost center
        count = db.query(func.count(Employee.id)).filter(
            Employee.cost_center_id == cc.id,
            Employee.employee_status == 'active'
        ).scalar()
        
        if cc.employees != count:
            cc.employees = count or 0
            updated_count += 1
    
    if updated_count > 0:
        db.commit()
    
    return updated_count


def sync_single_cost_center_employee_count(db: Session, cost_center_id: int):
    """
    Synchronize employee count for a single cost center
    
    Args:
        db: Database session
        cost_center_id: Cost center ID
        
    Returns:
        Updated employee count
    """
    cost_center = db.query(CostCenter).filter(CostCenter.id == cost_center_id).first()
    
    if not cost_center:
        return None
    
    # Count active employees assigned to this cost center
    count = db.query(func.count(Employee.id)).filter(
        Employee.cost_center_id == cost_center_id,
        Employee.employee_status == 'active'
    ).scalar()
    
    cost_center.employees = count or 0
    db.commit()
    
    return cost_center.employees
