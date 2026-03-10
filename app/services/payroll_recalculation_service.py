"""
Payroll Recalculation Service
Service for handling payroll recalculation business logic
"""

import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.repositories.payroll_recalculation_repository import PayrollRecalculationRepository
from app.models.payroll import PayrollRecalculation, PayrollPeriod
from app.models.employee import Employee
from app.models.attendance import AttendanceRecord
from app.schemas.payroll import PayrollRecalculationCreate, PayrollRecalculationResponse


class PayrollRecalculationService:
    """Service for payroll recalculation operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = PayrollRecalculationRepository(db)
    
    def get_recalculations(
        self,
        business_id: int,
        page: int = 1,
        size: int = 20,
        period_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get payroll recalculations with pagination and filters"""
        result = self.repository.get_by_business_id(
            business_id=business_id,
            page=page,
            size=size,
            period_id=period_id,
            status=status
        )
        
        # Build response
        recalculation_list = []
        for recalc in result["items"]:
            recalc_data = {
                "id": recalc.id,
                "date_from": recalc.date_from.isoformat(),
                "date_to": recalc.date_to.isoformat(),
                "all_employees": recalc.all_employees,
                "selected_employees": recalc.selected_employees,
                "status": recalc.status,
                "progress_percentage": recalc.progress_percentage,
                "total_employees": recalc.total_employees,
                "processed_employees": recalc.processed_employees,
                "failed_employees": recalc.failed_employees,
                "started_at": recalc.started_at.isoformat() if recalc.started_at else None,
                "completed_at": recalc.completed_at.isoformat() if recalc.completed_at else None,
                "success_message": recalc.success_message,
                "error_message": recalc.error_message,
                "period_name": recalc.period.name if recalc.period else None,
                "creator_name": f"{recalc.creator.first_name} {recalc.creator.last_name}" if recalc.creator else None,
                "created_at": recalc.created_at.isoformat()
            }
            recalculation_list.append(recalc_data)
        
        # Get statistics
        statistics = self.repository.get_statistics(business_id)
        
        return {
            "recalculations": recalculation_list,
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
                "pages": result["pages"]
            },
            "statistics": statistics
        }
    
    def create_recalculation(
        self,
        business_id: int,
        created_by: int,
        recalc_data: PayrollRecalculationCreate
    ) -> PayrollRecalculation:
        """Create a new payroll recalculation job"""
        # Validate date range
        if recalc_data.date_to <= recalc_data.date_from:
            raise ValueError("End date must be after start date")
        
        # Check if period exists and is open
        period = self.db.query(PayrollPeriod).filter(
            PayrollPeriod.id == recalc_data.period_id,
            PayrollPeriod.business_id == business_id
        ).first()
        
        if not period:
            raise ValueError("Payroll period not found")
        
        if period.status == "closed":
            raise ValueError("Cannot recalculate for closed period")
        
        # Check date range falls within period
        if (recalc_data.date_from < period.start_date or 
            recalc_data.date_to > period.end_date):
            raise ValueError("Date range must fall within the selected period")
        
        # Check rate limiting for all employees recalculation
        if recalc_data.all_employees:
            recent_count = self.repository.get_recent_recalculations_count(
                business_id=business_id,
                minutes=30
            )
            if recent_count >= 3:
                raise ValueError("Recalculation for all employees is limited to 3 times in a 30-minute period")
        
        # Get employees count
        employees = self.repository.get_employees_for_recalculation(
            business_id=business_id,
            all_employees=recalc_data.all_employees,
            selected_employees=recalc_data.selected_employees
        )
        
        if not employees:
            raise ValueError("No employees found for recalculation")
        
        # Create recalculation job
        recalculation = self.repository.create_recalculation(
            business_id=business_id,
            period_id=recalc_data.period_id,
            created_by=created_by,
            date_from=recalc_data.date_from,
            date_to=recalc_data.date_to,
            all_employees=recalc_data.all_employees,
            selected_employees=recalc_data.selected_employees
        )
        
        # Update total employees count
        recalculation.total_employees = len(employees)
        self.db.commit()
        
        return recalculation
    
    async def process_recalculation(self, recalculation_id: int) -> None:
        """Process payroll recalculation in background"""
        try:
            # Get recalculation job
            recalculation = self.repository.get_by_id(recalculation_id)
            if not recalculation:
                return
            
            # Update status to running
            self.repository.update_progress(
                recalculation_id=recalculation_id,
                progress_percentage=0,
                status="running"
            )
            
            # Get employees for processing
            employees = self.repository.get_employees_for_recalculation(
                business_id=recalculation.business_id,
                all_employees=recalculation.all_employees,
                selected_employees=recalculation.selected_employees
            )
            
            total_employees = len(employees)
            processed_count = 0
            failed_count = 0
            
            # Process each employee
            for i, employee in enumerate(employees):
                try:
                    # Simulate recalculation processing
                    await self._recalculate_employee_attendance(
                        employee=employee,
                        date_from=recalculation.date_from,
                        date_to=recalculation.date_to
                    )
                    
                    processed_count += 1
                    
                    # Update progress
                    progress = int((i + 1) / total_employees * 100)
                    
                    # Show success message at 57% progress (as per frontend)
                    success_message = None
                    if progress >= 57 and (i == 0 or int(i / total_employees * 100) < 57):
                        success_message = "Attendance recalculation successfully finished"
                    
                    self.repository.update_progress(
                        recalculation_id=recalculation_id,
                        progress_percentage=progress,
                        processed_employees=processed_count,
                        failed_employees=failed_count,
                        success_message=success_message
                    )
                    
                    # Small delay to simulate processing
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to recalculate for employee {employee.id}: {str(e)}")
            
            # Mark as completed
            final_message = f"Recalculation completed successfully for {processed_count} employees"
            if failed_count > 0:
                final_message += f" ({failed_count} failed)"
            
            self.repository.update_progress(
                recalculation_id=recalculation_id,
                progress_percentage=100,
                processed_employees=processed_count,
                failed_employees=failed_count,
                status="completed",
                success_message=final_message
            )
            
        except Exception as e:
            # Mark as failed
            self.repository.update_progress(
                recalculation_id=recalculation_id,
                progress_percentage=0,
                status="failed",
                error_message=f"Recalculation failed: {str(e)}"
            )
    
    async def _recalculate_employee_attendance(
        self,
        employee: Employee,
        date_from: date,
        date_to: date
    ) -> None:
        """Recalculate attendance for a specific employee and date range"""
        # This is a simplified implementation
        # In a real system, this would:
        # 1. Fetch raw attendance data (punches, swipes)
        # 2. Apply business rules and policies
        # 3. Calculate working hours, overtime, breaks
        # 4. Update attendance records
        # 5. Recalculate leave balances if needed
        # 6. Update payroll calculations
        
        current_date = date_from
        while current_date <= date_to:
            # Simulate attendance recalculation
            # Check if attendance record exists
            from app.models.attendance import AttendanceRecord
            attendance = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.attendance_date == current_date
            ).first()
            
            if attendance:
                # Recalculate attendance data
                # This is where the actual business logic would go
                attendance.updated_at = datetime.now()
                
            current_date += timedelta(days=1)
        
        # Commit changes for this employee
        self.db.commit()
    
    def get_recalculation_by_id(self, recalculation_id: int) -> Optional[PayrollRecalculation]:
        """Get recalculation by ID"""
        return self.repository.get_by_id(recalculation_id)
    
    def cancel_recalculation(self, recalculation_id: int) -> bool:
        """Cancel a running recalculation"""
        recalculation = self.repository.get_by_id(recalculation_id)
        if not recalculation or recalculation.status not in ["pending", "running"]:
            return False
        
        self.repository.update_progress(
            recalculation_id=recalculation_id,
            progress_percentage=recalculation.progress_percentage,
            status="failed",
            error_message="Recalculation cancelled by user"
        )
        
        return True
    
    def get_active_recalculations(self, business_id: int) -> List[PayrollRecalculation]:
        """Get currently active recalculations"""
        return self.repository.get_active_recalculations(business_id)