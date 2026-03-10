"""
Maintenance Service
Business logic for system maintenance operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from datetime import datetime, timedelta
import time
import logging

from app.repositories.maintenance_repository import MaintenanceRepository
from app.models.employee import Employee, EmployeeSalary
from app.models.datacapture import EmployeeDeduction

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Service for maintenance operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.maintenance_repo = MaintenanceRepository(db)
    
    def recalculate_salary_totals(
        self,
        business_id: Optional[int] = None,
        employee_ids: Optional[List[int]] = None,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recalculate salary totals for employees
        
        Args:
            business_id: Business ID filter
            employee_ids: Specific employee IDs to recalculate (optional)
            updated_by: User ID who initiated the recalculation
            
        Returns:
            Dictionary with recalculation results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting salary recalculation for business_id: {business_id}")
            
            result = self.maintenance_repo.recalculate_salary_totals(
                business_id=business_id,
                employee_ids=employee_ids,
                updated_by=updated_by
            )
            
            execution_time = round(time.time() - start_time, 2)
            result["execution_time"] = f"{execution_time} seconds"
            
            logger.info(f"Salary recalculation completed in {execution_time} seconds")
            logger.info(f"Results: {result['updated_employees']} updated, {result['failed_employees']} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to recalculate salary totals: {str(e)}")
            raise Exception(f"Failed to recalculate salary totals: {str(e)}")
    
    def update_work_profile_records(
        self,
        business_id: Optional[int] = None,
        employee_ids: Optional[List[int]] = None,
        fix_duplicates: bool = True,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update work profile records for employees
        
        Args:
            business_id: Business ID filter
            employee_ids: Specific employee IDs to update (optional)
            fix_duplicates: Whether to fix duplicate records
            updated_by: User ID who initiated the update
            
        Returns:
            Dictionary with update results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting work profile update for business_id: {business_id}")
            
            result = self.maintenance_repo.update_work_profile_records(
                business_id=business_id,
                employee_ids=employee_ids,
                fix_duplicates=fix_duplicates,
                updated_by=updated_by
            )
            
            execution_time = round(time.time() - start_time, 2)
            result["execution_time"] = f"{execution_time} seconds"
            
            logger.info(f"Work profile update completed in {execution_time} seconds")
            logger.info(f"Results: {result['updated_employees']} updated, {result['created_profiles']} created, {result['fixed_duplicates']} duplicates fixed")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update work profile records: {str(e)}")
            raise Exception(f"Failed to update work profile records: {str(e)}")
    
    def get_maintenance_status(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get maintenance status and statistics
        
        Args:
            business_id: Business ID filter
            
        Returns:
            Dictionary with maintenance status information
        """
        try:
            status_info = self.maintenance_repo.get_maintenance_status(business_id)
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get maintenance status: {str(e)}")
            raise Exception(f"Failed to get maintenance status: {str(e)}")
    
    def validate_data_integrity(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate data integrity and identify potential issues
        
        Args:
            business_id: Business ID filter
            
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info(f"Starting data integrity validation for business_id: {business_id}")
            
            validation_result = self.maintenance_repo.validate_data_integrity(business_id)
            
            logger.info("Data integrity validation completed")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate data integrity: {str(e)}")
            raise Exception(f"Failed to validate data integrity: {str(e)}")
    
    def cleanup_orphaned_records(
        self,
        business_id: Optional[int] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up orphaned records in the database
        
        Args:
            business_id: Business ID filter
            dry_run: If True, only identify orphaned records without deleting
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            logger.info(f"Starting orphaned records cleanup (dry_run: {dry_run}) for business_id: {business_id}")
            
            cleanup_result = self.maintenance_repo.cleanup_orphaned_records(
                business_id=business_id,
                dry_run=dry_run
            )
            
            logger.info(f"Orphaned records cleanup completed. Found {cleanup_result.get('total_orphaned', 0)} orphaned records")
            
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned records: {str(e)}")
            raise Exception(f"Failed to cleanup orphaned records: {str(e)}")
    
    def optimize_database_performance(
        self,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Optimize database performance by updating statistics and rebuilding indexes
        
        Args:
            business_id: Business ID filter
            
        Returns:
            Dictionary with optimization results
        """
        try:
            logger.info(f"Starting database optimization for business_id: {business_id}")
            
            optimization_result = self.maintenance_repo.optimize_database_performance(business_id)
            
            logger.info("Database optimization completed")
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Failed to optimize database performance: {str(e)}")
            raise Exception(f"Failed to optimize database performance: {str(e)}")
    
    def generate_maintenance_report(
        self,
        business_id: Optional[int] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive maintenance report
        
        Args:
            business_id: Business ID filter
            include_recommendations: Whether to include maintenance recommendations
            
        Returns:
            Dictionary with maintenance report
        """
        try:
            logger.info(f"Generating maintenance report for business_id: {business_id}")
            
            report = self.maintenance_repo.generate_maintenance_report(
                business_id=business_id,
                include_recommendations=include_recommendations
            )
            
            logger.info("Maintenance report generated successfully")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate maintenance report: {str(e)}")
            raise Exception(f"Failed to generate maintenance report: {str(e)}")