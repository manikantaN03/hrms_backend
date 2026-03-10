from sqlalchemy.orm import Session
from app.models.employee_code_config import EmployeeCodeSetting
from app.schemas.employee_code_config import EmployeeCodeCreate, EmployeeCodeUpdate


def get_latest_setting(db: Session, business_id: int):
    """Get the latest employee code setting for a business"""
    return (
        db.query(EmployeeCodeSetting)
        .filter(EmployeeCodeSetting.business_id == business_id)
        .order_by(EmployeeCodeSetting.id.desc())
        .first()
    )


def save_setting(db: Session, business_id: int, payload: EmployeeCodeCreate):
    """Save or update employee code setting"""
    # Check if setting already exists
    existing = get_latest_setting(db, business_id)
    
    if existing:
        # Update existing setting
        existing.auto_code = payload.autoCode
        existing.prefix = payload.prefix
        existing.length = payload.length
        existing.suffix = payload.suffix
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new setting
        setting = EmployeeCodeSetting(
            business_id=business_id,
            auto_code=payload.autoCode,
            prefix=payload.prefix,
            length=payload.length,
            suffix=payload.suffix,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting


def regenerate_employee_codes(db: Session, business_id: int, sort_by: str = "dateJoining"):
    """Regenerate employee codes for all active employees"""
    from app.models.employee import Employee, EmployeeStatus
    from sqlalchemy import asc
    import uuid
    
    # Get current configuration
    config = get_latest_setting(db, business_id)
    if not config or not config.auto_code:
        return {"success": False, "message": "Auto code generation is disabled"}
    
    # Get all active employees sorted by specified field
    query = db.query(Employee).filter(
        Employee.business_id == business_id,
        Employee.employee_status == EmployeeStatus.ACTIVE
    )
    
    if sort_by == "employeeName":
        query = query.order_by(asc(Employee.first_name), asc(Employee.last_name))
    else:  # dateJoining
        query = query.order_by(asc(Employee.date_of_joining), asc(Employee.id))
    
    employees = query.all()
    
    # Generate new codes and store in a mapping
    new_codes = {}
    for index, employee in enumerate(employees, start=1):
        num = str(index).zfill(config.length)
        new_code = f"{config.prefix}{num}{config.suffix}"
        new_codes[employee.id] = new_code
    
    # Step 1: Assign UNIQUE temporary codes using UUID to ALL employees (including inactive)
    # This ensures no conflicts with any existing codes
    all_employees = db.query(Employee).filter(Employee.business_id == business_id).all()
    for employee in all_employees:
        employee.employee_code = f"TEMP_UUID_{uuid.uuid4().hex}"
    db.commit()
    
    # Step 2: Assign final codes ONE BY ONE to active employees only
    updated_count = 0
    for employee_id, new_code in new_codes.items():
        # Get fresh employee instance
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if employee:
            employee.employee_code = new_code
            db.commit()  # Commit each update individually
            updated_count += 1
    
    return {
        "success": True,
        "message": f"Successfully regenerated codes for {updated_count} employees",
        "updated_count": updated_count,
        "configuration": {
            "prefix": config.prefix,
            "length": config.length,
            "suffix": config.suffix
        }
    }
