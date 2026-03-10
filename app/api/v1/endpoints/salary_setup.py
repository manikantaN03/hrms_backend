"""
Salary Setup API Endpoints
API endpoints for salary setup modules including salary components, deductions, salary structures, time salary, and overtime rules
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.v1.deps import get_current_admin, get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.setup.salary_and_deductions.salary_component import SalaryComponent
from app.models.setup.salary_and_deductions.salary_deduction import SalaryDeduction
from app.models.setup.salary_and_deductions.salary_structure import SalaryStructure
from app.schemas.setup.salary_and_deductions.salary_component import (
    SalaryComponentCreate, SalaryComponentUpdate, SalaryComponentOut
)
from app.schemas.setup.salary_and_deductions.salary_deduction import (
    SalaryDeductionCreate, SalaryDeductionUpdate, SalaryDeductionResponse
)
from app.schemas.setup.salary_and_deductions.salary_structure import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse
)
from app.schemas.setup.salary_and_deductions.time_salary import (
    TimeRuleCreate, TimeRuleUpdate, TimeRuleResponse
)
from app.schemas.setup.salary_and_deductions.overtime import (
    OvertimePolicyCreate, OvertimePolicyUpdate, OvertimePolicyOut,
    OvertimeRuleCreate, OvertimeRuleUpdate, OvertimeRuleOut
)
from app.services.setup.salary_and_deductions.salary_component_service import SalaryComponentService
from app.services.setup.salary_and_deductions.salary_deduction_service import SalaryDeductionService
from app.services.setup.salary_and_deductions.salary_structure_service import SalaryStructureService
from app.services.setup.salary_and_deductions.time_salary_service import TimeSalaryRuleService
from app.services.setup.salary_and_deductions.overtime_service import policy_service, rule_service

router = APIRouter()
salary_component_service = SalaryComponentService()
salary_deduction_service = SalaryDeductionService()
salary_structure_service = SalaryStructureService()
time_salary_service = TimeSalaryRuleService()
overtime_policy_service = policy_service
overtime_rule_service = rule_service

# ============================================================================
# Salary Deduction Endpoints
# ============================================================================

# ============================================================================
# Time Salary Endpoints - REMOVED (Duplicate)
# These endpoints are now handled by /setup/salarysetup/time-salary/ 
# in app/api/v1/setup/salary_and_deductions/time_salary.py
# ============================================================================

# ============================================================================
# Overtime Rules Endpoints
# ============================================================================

# ============================================================================
# Overtime Endpoints - REMOVED (Duplicate)
# These endpoints are now handled by /setup/salarysetup/overtime/ 
# in app/api/v1/setup/salary_and_deductions/overtime.py
# ============================================================================