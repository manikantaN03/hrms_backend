"""
Business Unit Utilities
Hybrid logic for handling business units vs businesses based on user role
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.business_unit import BusinessUnit
from app.models.employee import Employee
from app.models.user import User


def get_business_unit_options(
    db: Session, 
    current_user: User, 
    business_id: Optional[int] = None
) -> List[str]:
    """
    Get business unit options based on user role
    
    Args:
        db: Database session
        current_user: Current user object
        business_id: Optional business ID filter
        
    Returns:
        List of business unit names (businesses for superadmin, business units for others)
    """
    user_role = getattr(current_user, 'role', 'admin')
    
    if user_role == "superadmin" or str(user_role) == "UserRole.SUPERADMIN":
        # For superadmin: show businesses (companies)
        bu_query = db.query(Business.business_name).filter(Business.is_active == True)
        business_units = [bu[0] for bu in bu_query.distinct().all()]
    else:
        # For company admin: show business units (divisions)
        bu_query = db.query(BusinessUnit.name).filter(BusinessUnit.is_active == True)
        if business_id:
            bu_query = bu_query.filter(BusinessUnit.business_id == business_id)
        business_units = [bu[0] for bu in bu_query.distinct().all()]
    
    return ["All Business Units"] + business_units


def get_business_unit_dropdown_options(
    db: Session, 
    current_user: User, 
    business_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get business unit dropdown options with IDs based on user role
    
    Args:
        db: Database session
        current_user: Current user object
        business_id: Optional business ID filter
        
    Returns:
        List of dicts with id and name (businesses for superadmin, business units for others)
    """
    user_role = getattr(current_user, 'role', 'admin')
    
    if user_role == "superadmin" or str(user_role) == "UserRole.SUPERADMIN":
        # For superadmin: show businesses (companies)
        bu_query = db.query(Business).filter(Business.is_active == True)
        business_units = [{"id": biz.id, "name": biz.business_name} for biz in bu_query.all()]
    else:
        # For company admin: show business units (divisions)
        bu_query = db.query(BusinessUnit).filter(BusinessUnit.is_active == True)
        if business_id:
            bu_query = bu_query.filter(BusinessUnit.business_id == business_id)
        business_units = [{"id": bu.id, "name": bu.name} for bu in bu_query.all()]
    
    return business_units


def apply_business_unit_filter(
    query,
    db: Session,
    current_user: User,
    business_unit: str,
    employee_model = Employee
):
    """
    Apply business unit filter to a query based on user role
    
    Args:
        query: SQLAlchemy query object
        db: Database session
        current_user: Current user object
        business_unit: Business unit name to filter by
        employee_model: Employee model class (default: Employee)
        
    Returns:
        Modified query with business unit filter applied
    """
    if not business_unit or business_unit == "All Business Units":
        return query
    
    user_role = getattr(current_user, 'role', 'admin')
    
    if user_role == "superadmin" or str(user_role) == "UserRole.SUPERADMIN":
        # For superadmin: filter by business (company)
        business_obj = db.query(Business).filter(Business.business_name == business_unit).first()
        if business_obj:
            query = query.filter(employee_model.business_id == business_obj.id)
    else:
        # For company admin: filter by business unit (division)
        bu_obj = db.query(BusinessUnit).filter(BusinessUnit.name == business_unit).first()
        if bu_obj:
            query = query.filter(employee_model.business_unit_id == bu_obj.id)
    
    return query


def is_superadmin(current_user: User) -> bool:
    """
    Check if current user is superadmin
    
    Args:
        current_user: Current user object
        
    Returns:
        True if user is superadmin, False otherwise
    """
    user_role = getattr(current_user, 'role', 'admin')
    # Handle both string and enum comparisons
    return (
        user_role == "SUPERADMIN" or 
        user_role == "superadmin" or 
        str(user_role) == "UserRole.SUPERADMIN" or
        str(user_role).upper() == "SUPERADMIN"
    )


def get_user_business_context(current_user: User, db: Session) -> Tuple[bool, Optional[int]]:
    """
    Get user's business context (is_superadmin, business_id)
    
    Args:
        current_user: Current user object
        db: Database session
        
    Returns:
        Tuple of (is_superadmin, business_id)
    """
    is_super = is_superadmin(current_user)
    
    # Query Business table to get business_id where owner_id matches current user
    if not is_super:
        business = db.query(Business).filter(Business.owner_id == current_user.id).first()
        business_id = business.id if business else None
    else:
        business_id = None  # Superadmin sees all businesses
    
    return is_super, business_id


def get_business_context(current_user: User) -> Dict[str, Any]:
    """
    Get business context for the current user
    
    Args:
        current_user: Current user object
        
    Returns:
        Dict with business_id and other context information
    """
    # Extract business_id from current_user
    business_id = getattr(current_user, 'business_id', None)
    user_role = getattr(current_user, 'role', 'admin')
    is_super = is_superadmin(current_user)
    
    # For superadmin, don't apply business filtering - they should see all data
    if is_super:
        business_id = None  # No business filtering for superadmin
    
    return {
        'business_id': business_id,
        'user_role': user_role,
        'is_superadmin': is_super
    }