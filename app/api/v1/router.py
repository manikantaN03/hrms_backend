"""
API Router - Aggregates all v1 routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.api.v1.deps import get_current_admin, get_current_superadmin, get_current_user
from app.models.user import User

from .endpoints import auth, superadmin, health, files, registration, dev, business, employees, allemployees, dashboard, onboarding, separation, attendance, datacapture, bulkupdate, requests, hrmanagement, payroll, reports, setup_dashboard, crm, profile, master_setup, salary_setup, calendar, project_management, notes, subscriptions, packages, domain, purchase_transaction, documents, help, support, system_stats, preferences, todo, contact_inquiry, public_location, password_reset

from app.api.v1.setup.mastersetup.workflows import router as workflows_router
from app.api.v1.setup.mastersetup.business_unit_files import router as business_unit_files_router
from app.api.v1.setup.salary_and_deductions.salary_components import router as salary_component_router
from app.api.v1.setup.salary_and_deductions.salary_deductions import router as salary_deduction_router
from app.api.v1.setup.salary_and_deductions.salary_structures import router as salary_structure_router
from app.api.v1.setup.salary_and_deductions.salary_structure_rules import router as salary_structure_rule_router
from app.api.v1.setup.salary_and_deductions.time_salary import router as time_salary_router
from app.api.v1.setup.salary_and_deductions.overtime import router as overtime_router
from .setup.Integrations import emailsettings, gatekeeper, sqlserver, api_access, sap_mapping
from app.api.v1.setup.Integrations import biometric_sync
from app.api.v1.setup.employeeselfservice import approvals, user_management
from app.api.v1.setup import maintenance
from app.api.v1.setup.leaves_statutory import (
    attendance_settings,leave_types,
    holidays,
    compoff_rules,
    strike_rules,
    strike_adjustments,
    leave_policies,
    esi_settings,
    epf_settings,
    professional_tax,
    form16,
    tds24q,lwf,tax
)




#=======================================================================
api_router = APIRouter()

# ============================================================================
# 1. User Registration
# ============================================================================

api_router.include_router(
    registration.router,
    tags=["User Registration"]
)

# ============================================================================
# 1.1. Password Reset (Forgot Password)
# ============================================================================

api_router.include_router(
    password_reset.router,
    tags=["Password Reset"]
)

# ============================================================================
# 1.2. Contact Inquiry (PUBLIC - No Auth Required)
# ============================================================================

api_router.include_router(
    contact_inquiry.router,
    prefix="/contact-inquiry",
    tags=["Contact Inquiry"]
)

# ============================================================================
# 1.2. Public Location Info (PUBLIC - No Auth Required)
# ============================================================================

api_router.include_router(
    public_location.router,
    prefix="/public",
    tags=["Public"]
)

# ============================================================================
# 2. Authentication
# ============================================================================

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# ============================================================================
# 3. Dashboard
# ============================================================================

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

# ============================================================================
# 4. All Employees (Consolidated - Single Source of Truth)
# ============================================================================

api_router.include_router(
    allemployees.router,
    prefix="/allemployees",
    tags=["All Employees"]
)

# ============================================================================
# 5. Onboarding
# ============================================================================

api_router.include_router(
    onboarding.router,
    prefix="/onboarding",
    tags=["Onboarding"]
)

# ============================================================================
# 6. Separation
# ============================================================================

api_router.include_router(
    separation.router,
    prefix="/separation",
    tags=["Separation"]
)

# ============================================================================
# 7. Attendance
# ============================================================================

api_router.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["Attendance"]
)

# ============================================================================
# 8. Data Capture
# ============================================================================

api_router.include_router(
    datacapture.router,
    prefix="/datacapture",
    tags=["Data Capture"]
)

# ============================================================================
# 9. Bulk Update
# ============================================================================

api_router.include_router(
    bulkupdate.router,
    prefix="/bulkupdate",
    tags=["Bulk Update"]
)

# ============================================================================
# 10. HR Management
# ============================================================================

api_router.include_router(
    hrmanagement.router,
    prefix="/hrmanagement",
    tags=["HR Management"]
)

# ============================================================================
# 11. Request
# ============================================================================

api_router.include_router(
    requests.router,
    prefix="/requests",
    tags=["Request"]
)

# ============================================================================
# 12. Support (Remote Sessions, Help)
# ============================================================================

api_router.include_router(
    support.router,
    prefix="/support",
    tags=["Support"]
)

api_router.include_router(
    help.router,
    prefix="/help",
    tags=["Help & Documentation"]
)

# ============================================================================
# 13. Payroll
# ============================================================================

api_router.include_router(
    payroll.router,
    prefix="/payroll",
    tags=["Payroll"]
)

# ============================================================================
# 14. Reports
# ============================================================================

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)

# ============================================================================
# 15. Setup
# ============================================================================

api_router.include_router(
    setup_dashboard.router,
    prefix="/setup",
    tags=["Setup"]
)

api_router.include_router(
    salary_setup.router,
    prefix="/setup/salarysetup",
    tags=["Setup"]
)

# Business Unit Files (Image Upload)
api_router.include_router(
    business_unit_files_router,
    prefix="/setup/business-unit-files",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

# Salary Components (Under Setup)
api_router.include_router(
    salary_component_router,
    prefix="/setup/salarysetup/salary-components",
    tags=["Setup"]
)

api_router.include_router(
    salary_deduction_router,
    prefix="/setup/salarysetup/salary-deductions",
    tags=["Setup"]
)

api_router.include_router(
    salary_structure_router,
    prefix="/setup/salarysetup/salary-structures",
    tags=["Setup"]
)

api_router.include_router(
    salary_structure_rule_router,
    prefix="/setup/salarysetup",
    tags=["Setup"]
)

api_router.include_router(
    time_salary_router,
    prefix="/setup/salarysetup/time-salary",
    tags=["Setup"]
)

api_router.include_router(
    overtime_router,
    prefix="/setup/salarysetup/overtime",
    tags=["Setup"]
)

# ============================================================================
# 16. Master Setup (Direct endpoints used by frontend)
# ============================================================================

api_router.include_router(
    master_setup.router,
    tags=["Master Setup"]
)

# ============================================================================
# 16.1. Workflows (Under Master Setup)
# ============================================================================

api_router.include_router(
    workflows_router,
    prefix="/workflows",
    tags=["Master Setup"],
    dependencies=[Depends(get_current_admin)],
)

# ============================================================================
# 16. CRM
# ============================================================================

api_router.include_router(
    crm.router,
    prefix="/crm",
    tags=["CRM"]
)

# ============================================================================
# Business Management (Admin & Superadmin)
# ============================================================================

api_router.include_router(
    business.router,
    prefix="/businesses",
    tags=["Business Management"]
)

# ============================================================================
# Project Management
# ============================================================================

api_router.include_router(
    project_management.router,
    prefix="/project-management",
    tags=["Project Management"]
)

# ============================================================================
# Calendar Management
# ============================================================================

api_router.include_router(
    calendar.router,
    prefix="/calendar",
    tags=["Calendar Management"]
)

# ============================================================================
# Notes Management
# ============================================================================

api_router.include_router(
    notes.router,
    prefix="/notes",
    tags=["Notes Management"]
)

# ============================================================================
# Profile Management
# ============================================================================

api_router.include_router(
    profile.router,
    prefix="/profile",
    tags=["Profile Management"]
)

# ============================================================================
# User Preferences
# ============================================================================

api_router.include_router(
    preferences.router,
    tags=["User Preferences"]
)

# ============================================================================
# TODO/Tasks Management
# ============================================================================

api_router.include_router(
    todo.router,
    prefix="/todo",
    tags=["TODO/Tasks"]
)

# ============================================================================
# Superadmin Endpoints
# ============================================================================

api_router.include_router(
    superadmin.router,
    prefix="/superadmin",
    tags=["Superadmin"]
)

api_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

api_router.include_router(
    packages.router,
    prefix="/superadmin/packages",
    tags=["Packages"]
)

api_router.include_router(
    domain.router,
    prefix="/superadmin/domain",
    tags=["Domain Management"]
)

api_router.include_router(
    purchase_transaction.router,
    prefix="/superadmin/purchase-transactions",
    tags=["Purchase Transaction Management"]
)

# ============================================================================
# File Upload & Document Management
# ============================================================================

api_router.include_router(
    files.router,
    prefix="/upload",
    tags=["File Upload"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["System"]
)

api_router.include_router(
    dev.router,
    prefix="/dev",
    tags=["Developer"]
)

# ============================================================================
# Setup - Leaves & Attendance (Under Setup)
# ============================================================================

api_router.include_router(
    attendance_settings.router,
    prefix="/setup/leaves-attendance-setup/attendance-settings",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    leave_types.router,
    prefix="/setup/leaves-attendance-setup/leave-type",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    leave_policies.router,
    prefix="/setup/leaves-attendance-setup/leave-policies",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    holidays.router,
    prefix="/setup/holidays",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    compoff_rules.router,
    prefix="/setup/compoff-rules",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    strike_rules.router,
    prefix="/setup/strike-rules",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    strike_adjustments.router,
    prefix="/setup/strike-adjustments",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

# ============================================================================
# Setup - Statutory Settings (Under Setup)
# ============================================================================

api_router.include_router(
    esi_settings.router,
    prefix="/setup/esi-settings",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    epf_settings.router,
    prefix="/setup/epf-settings",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    professional_tax.router,
    prefix="/setup/professional-tax",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    form16.router,
    prefix="/setup/form16",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    tds24q.router,
    prefix="/setup/tds24q",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    lwf.router,
    prefix="/setup/lwf",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)   

api_router.include_router(
    tax.router,
    prefix="/setup/tax",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

# ============================================================================
# Setup - ESS (Employee Self Service) (Under Setup)
# ============================================================================

api_router.include_router(
    approvals.router,
    prefix="/setup/ess",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    user_management.router,
    prefix="/setup/ess",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

# ============================================================================
# Setup - Integrations (Under Setup)
# ============================================================================

api_router.include_router(
    emailsettings.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    biometric_sync.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    gatekeeper.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    sqlserver.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    api_access.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

api_router.include_router(
    sap_mapping.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

# ============================================================================
# Setup - Maintenance (Under Setup)
# ============================================================================

api_router.include_router(
    maintenance.router,
    prefix="/setup",
    tags=["Setup"],
    dependencies=[Depends(get_current_admin)],
)

# ============================================================================
# System Statistics (Real-time Backend Analysis)
# ============================================================================

api_router.include_router(
    system_stats.router,
    prefix="/system",
    tags=["System Statistics"]
)
