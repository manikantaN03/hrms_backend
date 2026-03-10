"""
Maintenance Schema
Pydantic models for maintenance API requests and responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime


class MaintenanceResponse(BaseModel):
    """Base maintenance response schema"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class RecalculateSalaryRequest(BaseModel):
    """Request schema for salary recalculation"""
    employee_ids: Optional[List[int]] = Field(
        None, 
        description="Specific employee IDs to recalculate (optional, if not provided all employees will be processed)"
    )
    
    @field_validator('employee_ids')
    @classmethod
    def validate_employee_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Validate employee IDs list"""
        if v is not None:
            if not v:
                raise ValueError("employee_ids list cannot be empty if provided")
            if any(emp_id <= 0 for emp_id in v):
                raise ValueError("All employee IDs must be positive integers")
        return v


class RecalculateSalaryResponse(BaseModel):
    """Response schema for salary recalculation"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    total_employees: int = Field(..., ge=0, description="Total number of employees processed")
    updated_employees: int = Field(..., ge=0, description="Number of employees successfully updated")
    failed_employees: int = Field(..., ge=0, description="Number of employees that failed to update")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors encountered")
    execution_time: str = Field(..., description="Time taken to complete the operation")


class UpdateWorkProfileRequest(BaseModel):
    """Request schema for work profile update"""
    employee_ids: Optional[List[int]] = Field(
        None, 
        description="Specific employee IDs to update (optional, if not provided all employees will be processed)"
    )
    fix_duplicates: bool = Field(
        True, 
        description="Whether to fix duplicate employee records"
    )
    
    @field_validator('employee_ids')
    @classmethod
    def validate_employee_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Validate employee IDs list"""
        if v is not None:
            if not v:
                raise ValueError("employee_ids list cannot be empty if provided")
            if any(emp_id <= 0 for emp_id in v):
                raise ValueError("All employee IDs must be positive integers")
        return v


class UpdateWorkProfileResponse(BaseModel):
    """Response schema for work profile update"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    total_employees: int = Field(..., ge=0, description="Total number of employees processed")
    updated_employees: int = Field(..., ge=0, description="Number of employees successfully updated")
    created_profiles: int = Field(..., ge=0, description="Number of work profiles created")
    fixed_duplicates: int = Field(..., ge=0, description="Number of duplicate records fixed")
    failed_employees: int = Field(..., ge=0, description="Number of employees that failed to update")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors encountered")
    execution_time: str = Field(..., description="Time taken to complete the operation")


class MaintenanceStatusResponse(BaseModel):
    """Response schema for maintenance status"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    employee_statistics: Dict[str, int] = Field(..., description="Employee statistics")
    data_completeness: Dict[str, Any] = Field(..., description="Data completeness metrics")
    recent_activity: Dict[str, Any] = Field(..., description="Recent maintenance activity")
    recommendations: List[Dict[str, Any]] = Field(..., description="Maintenance recommendations")


class DataValidationIssue(BaseModel):
    """Schema for data validation issues"""
    type: str = Field(..., description="Type of issue (missing_data, duplicate_data, etc.)")
    severity: str = Field(..., description="Issue severity (high, medium, low)")
    description: str = Field(..., description="Issue description")
    table: str = Field(..., description="Database table affected")
    field: str = Field(..., description="Database field affected")
    duplicates: Optional[List[str]] = Field(None, description="List of duplicate values (for duplicate_data type)")


class DataValidationResponse(BaseModel):
    """Response schema for data validation"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    validation_date: str = Field(..., description="Date when validation was performed")
    total_issues: int = Field(..., description="Total number of issues found")
    issues_by_severity: Dict[str, int] = Field(..., description="Issues grouped by severity")
    issues: List[DataValidationIssue] = Field(..., description="List of validation issues")
    overall_health: str = Field(..., description="Overall system health (good, fair, needs_attention)")


class CleanupRecord(BaseModel):
    """Schema for cleanup record information"""
    id: int = Field(..., description="Record ID")
    employee_id: Optional[int] = Field(None, description="Associated employee ID")


class CleanupResult(BaseModel):
    """Schema for cleanup operation results"""
    table: str = Field(..., description="Database table")
    count: int = Field(..., description="Number of records affected")
    action: str = Field(..., description="Action performed (delete, would_delete)")
    records: List[CleanupRecord] = Field(..., description="Sample of affected records")


class CleanupResponse(BaseModel):
    """Response schema for cleanup operations"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    cleanup_date: str = Field(..., description="Date when cleanup was performed")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    total_orphaned: int = Field(..., description="Total number of orphaned records")
    cleanup_results: List[CleanupResult] = Field(..., description="Detailed cleanup results")


class OptimizationOperation(BaseModel):
    """Schema for optimization operation results"""
    operation: str = Field(..., description="Type of operation performed")
    table: str = Field(..., description="Database table")
    status: str = Field(..., description="Operation status (success, failed)")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class OptimizationResponse(BaseModel):
    """Response schema for database optimization"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    optimization_date: str = Field(..., description="Date when optimization was performed")
    operations_performed: int = Field(..., description="Total number of operations performed")
    successful_operations: int = Field(..., description="Number of successful operations")
    failed_operations: int = Field(..., description="Number of failed operations")
    results: List[OptimizationOperation] = Field(..., description="Detailed optimization results")


class MaintenanceReportSummary(BaseModel):
    """Schema for maintenance report summary"""
    overall_health: str = Field(..., description="Overall system health")
    total_employees: int = Field(..., description="Total number of employees")
    active_employees: int = Field(..., description="Number of active employees")
    data_issues: int = Field(..., description="Number of data issues")
    orphaned_records: int = Field(..., description="Number of orphaned records")


class MaintenanceReportResponse(BaseModel):
    """Response schema for comprehensive maintenance report"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    report_date: str = Field(..., description="Date when report was generated")
    business_id: Optional[int] = Field(None, description="Business ID filter used")
    summary: MaintenanceReportSummary = Field(..., description="Report summary")
    detailed_status: Dict[str, Any] = Field(..., description="Detailed maintenance status")
    data_validation: Dict[str, Any] = Field(..., description="Data validation results")
    cleanup_preview: Dict[str, Any] = Field(..., description="Cleanup preview results")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Maintenance recommendations")


# Request/Response models for additional maintenance operations
class MaintenanceOperationRequest(BaseModel):
    """Generic request schema for maintenance operations"""
    business_id: Optional[int] = Field(None, description="Business ID filter")
    dry_run: bool = Field(True, description="Whether to perform a dry run")
    include_recommendations: bool = Field(True, description="Whether to include recommendations")


class MaintenanceError(BaseModel):
    """Schema for maintenance operation errors"""
    employee_id: Optional[int] = Field(None, description="Employee ID if applicable")
    employee_code: Optional[str] = Field(None, description="Employee code if applicable")
    employee_name: Optional[str] = Field(None, description="Employee name if applicable")
    error: str = Field(..., description="Error message")
    timestamp: Optional[str] = Field(None, description="Error timestamp")


class MaintenanceRecommendation(BaseModel):
    """Schema for maintenance recommendations"""
    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Recommendation description")
    action: str = Field(..., description="Recommended action")


class MaintenanceStatistics(BaseModel):
    """Schema for maintenance statistics"""
    total_employees: int = Field(..., description="Total number of employees")
    active_employees: int = Field(..., description="Number of active employees")
    inactive_employees: int = Field(..., description="Number of inactive employees")
    incomplete_work_profiles: int = Field(..., description="Number of incomplete work profiles")
    employees_without_salary: int = Field(..., description="Number of employees without salary data")
    profile_completeness_percentage: float = Field(..., description="Work profile completeness percentage")
    recent_updates: int = Field(..., description="Number of recent updates")
    last_maintenance_check: str = Field(..., description="Last maintenance check timestamp")