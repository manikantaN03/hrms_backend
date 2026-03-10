from sqlalchemy.orm import Session
from app.repositories.employee_code_repository import (
    get_latest_setting, 
    save_setting,
    regenerate_employee_codes as repo_regenerate_codes
)
from app.schemas.employee_code_config import EmployeeCodeCreate

def save_employee_code_setting(db: Session, business_id: int, payload: EmployeeCodeCreate):
    """Save or update employee code setting"""
    return save_setting(db, business_id, payload)


def get_employee_code_setting(db: Session, business_id: int):
    """Get employee code setting for a business"""
    return get_latest_setting(db, business_id)


def generate_preview_codes(payload: EmployeeCodeCreate):
    """Generate preview codes based on configuration"""
    if not payload.autoCode:
        return []

    codes = []
    for i in range(1, 3):  # preview 2 codes
        num = str(i).zfill(payload.length)
        codes.append(f"{payload.prefix}{num}{payload.suffix}")
    return codes


def regenerate_all_employee_codes(db: Session, business_id: int, sort_by: str = "dateJoining"):
    """Regenerate employee codes for all active employees"""
    return repo_regenerate_codes(db, business_id, sort_by)
