"""
Attendance Repository
Data access layer for attendance operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc, extract
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.repositories.base_repository import BaseRepository
from app.models.attendance import (
    AttendanceRecord, AttendancePunch, AttendanceCorrection, 
    ShiftRoster, AttendancePolicy, AttendanceSummary,
    AttendanceStatus, PunchType
)
from app.models.employee import Employee
from app.models.department import Department
from app.models.designations import Designation
from app.models.location import Location


class AttendanceRepository(BaseRepository[AttendanceRecord]):
    """Repository for attendance records"""
    
    def __init__(self, db: Session):
        super().__init__(AttendanceRecord, db)
    
    def get_by_employee_and_date(self, employee_id: int, attendance_date: date) -> Optional[AttendanceRecord]:
        """Get attendance record by employee and date"""
        return self.db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.attendance_date == attendance_date
        ).first()
    
    def get_employee_attendance_range(
        self, 
        employee_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[AttendanceRecord]:
        """Get employee attendance records for date range"""
        return self.db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.attendance_date >= start_date,
            AttendanceRecord.attendance_date <= end_date
        ).order_by(AttendanceRecord.attendance_date).all()
    
    def get_daily_attendance(
        self, 
        business_id: int, 
        attendance_date: date,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Tuple[List[AttendanceRecord], int]:
        """Get daily attendance records with filters and pagination"""
        
        query = self.db.query(AttendanceRecord).options(
            joinedload(AttendanceRecord.employee).joinedload(Employee.department),
            joinedload(AttendanceRecord.employee).joinedload(Employee.designation),
            joinedload(AttendanceRecord.employee).joinedload(Employee.location),
            joinedload(AttendanceRecord.punches)
        ).filter(
            AttendanceRecord.business_id == business_id,
            AttendanceRecord.attendance_date == attendance_date
        )
        
        # Apply filters
        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        
        if location_id:
            query = query.join(Employee).filter(Employee.location_id == location_id)
        
        if search:
            query = query.join(Employee).filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        records = query.offset(offset).limit(size).all()
        
        return records, total
    
    def get_attendance_summary_by_date(self, business_id: Optional[int], attendance_date: date) -> Dict[str, int]:
        """Get attendance summary for a specific date"""
        
        query = self.db.query(
            AttendanceRecord.attendance_status,
            func.count(AttendanceRecord.id).label('count')
        ).filter(
            AttendanceRecord.attendance_date == attendance_date
        )
        
        # Apply business filter only if business_id is provided (not superadmin)
        if business_id is not None:
            query = query.filter(AttendanceRecord.business_id == business_id)
        
        summary = query.group_by(AttendanceRecord.attendance_status).all()
        
        # Convert to dictionary with default values
        result = {
            'total_employees': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'on_leave': 0,
            'half_day': 0,
            'holiday': 0,
            'weekend': 0
        }
        
        for status, count in summary:
            if status == AttendanceStatus.PRESENT:
                result['present'] = count
            elif status == AttendanceStatus.ABSENT:
                result['absent'] = count
            elif status == AttendanceStatus.LATE:
                result['late'] = count
            elif status == AttendanceStatus.ON_LEAVE:
                result['on_leave'] = count
            elif status == AttendanceStatus.HALF_DAY:
                result['half_day'] = count
            elif status == AttendanceStatus.HOLIDAY:
                result['holiday'] = count
            elif status == AttendanceStatus.WEEKEND:
                result['weekend'] = count
        
        result['total_employees'] = sum([
            result['present'], result['absent'], result['late'], 
            result['on_leave'], result['half_day']
        ])
        
        return result
    
    def get_monthly_attendance_summary(
        self, 
        business_id: int, 
        year: int, 
        month: int,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get monthly attendance summary by employee with proper database integration"""
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Build employee query with proper joins
        employee_query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation),
            joinedload(Employee.location)
        ).filter(
            Employee.business_id == business_id,
            Employee.is_active == True
        )
        
        # Apply filters
        if department_id:
            employee_query = employee_query.filter(Employee.department_id == department_id)
        
        if location_id:
            employee_query = employee_query.filter(Employee.location_id == location_id)
        
        if search:
            employee_query = employee_query.filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total_employees = employee_query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        employees = employee_query.offset(offset).limit(size).all()
        
        summary = []
        for employee in employees:
            # Get attendance records for this employee in the month
            records = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.attendance_date >= start_date,
                AttendanceRecord.attendance_date <= end_date
            ).all()
            
            # Calculate statistics from actual database records
            total_days = len(records)
            present_days = len([r for r in records if r.attendance_status == AttendanceStatus.PRESENT])
            absent_days = len([r for r in records if r.attendance_status == AttendanceStatus.ABSENT])
            late_days = len([r for r in records if r.is_late])
            leave_days = len([r for r in records if r.attendance_status == AttendanceStatus.ON_LEAVE])
            holiday_days = len([r for r in records if r.attendance_status == AttendanceStatus.HOLIDAY])
            weekend_days = len([r for r in records if r.attendance_status == AttendanceStatus.WEEKEND])
            half_days = len([r for r in records if r.attendance_status == AttendanceStatus.HALF_DAY])
            total_hours = sum([float(r.total_hours or 0) for r in records])
            
            # Calculate actual weekends in the month from calendar
            actual_weekends = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() in [5, 6]:  # Saturday, Sunday
                    actual_weekends += 1
                current_date += timedelta(days=1)
            
            # Use actual weekend records if they exist, otherwise use calculated weekends
            if weekend_days == 0:
                weekend_days = actual_weekends
            
            # Calculate comp off and leave without pay from leave types
            # This would require joining with leave_types table in a real implementation
            comp_off_days = 0
            leave_without_pay_days = 0
            
            # For now, we'll calculate based on leave records
            # In a full implementation, this would check leave_type_id
            if leave_days > 0:
                # Simple logic: assume half are casual leave, rest are comp off
                casual_leave_days = min(leave_days, 12)  # Max 12 casual leaves per year
                comp_off_days = max(0, leave_days - casual_leave_days)
            else:
                casual_leave_days = 0
            
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            # Get department and designation names from relationships
            department_name = employee.department.name if employee.department else "N/A"
            designation_name = employee.designation.name if employee.designation else "N/A"
            
            # Build employee name
            employee_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
            if not employee_name:
                employee_name = f"Employee {employee.id}"
            
            summary.append({
                'employee_id': employee.id,
                'employee_name': employee_name,
                'employee_code': employee.employee_code or f"EMP{employee.id:03d}",
                'department': department_name,
                'designation': designation_name,
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'leave_days': casual_leave_days,
                'holiday_days': holiday_days,
                'weekend_days': weekend_days,
                'half_days': half_days,
                'comp_off_days': comp_off_days,
                'leave_without_pay_days': leave_without_pay_days,
                'total_hours': total_hours,
                'attendance_percentage': round(attendance_percentage, 2)
            })
        
        return summary, total_employees


class AttendancePunchRepository(BaseRepository[AttendancePunch]):
    """Repository for attendance punches"""
    
    def __init__(self, db: Session):
        super().__init__(AttendancePunch, db)
    
    def get_employee_punches_by_date(self, employee_id: int, punch_date: date) -> List[AttendancePunch]:
        """Get employee punches for a specific date"""
        start_datetime = datetime.combine(punch_date, datetime.min.time())
        end_datetime = datetime.combine(punch_date, datetime.max.time())
        
        return self.db.query(AttendancePunch).filter(
            AttendancePunch.employee_id == employee_id,
            AttendancePunch.punch_time >= start_datetime,
            AttendancePunch.punch_time <= end_datetime
        ).order_by(AttendancePunch.punch_time).all()
    
    def get_last_punch(self, employee_id: int) -> Optional[AttendancePunch]:
        """Get employee's last punch"""
        return self.db.query(AttendancePunch).filter(
            AttendancePunch.employee_id == employee_id
        ).order_by(desc(AttendancePunch.punch_time)).first()
    
    def get_daily_punches(
        self, 
        business_id: int, 
        punch_date: date,
        page: int = 1,
        size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get all employee punches for a specific date"""
        
        start_datetime = datetime.combine(punch_date, datetime.min.time())
        end_datetime = datetime.combine(punch_date, datetime.max.time())
        
        # Get employees with their punches for the date
        query = self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation),
            joinedload(Employee.location)
        ).filter(
            Employee.business_id == business_id,
            Employee.is_active == True
        )
        
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        employees = query.offset(offset).limit(size).all()
        
        # Get punches for these employees
        employee_ids = [emp.id for emp in employees]
        punches = self.db.query(AttendancePunch).filter(
            AttendancePunch.employee_id.in_(employee_ids),
            AttendancePunch.punch_time >= start_datetime,
            AttendancePunch.punch_time <= end_datetime
        ).order_by(AttendancePunch.punch_time).all()
        
        # Group punches by employee
        employee_punches = {}
        for punch in punches:
            if punch.employee_id not in employee_punches:
                employee_punches[punch.employee_id] = []
            employee_punches[punch.employee_id].append(punch)
        
        # Build response
        result = []
        for employee in employees:
            emp_punches = employee_punches.get(employee.id, [])
            
            # Calculate punch in/out times
            punch_in_time = None
            punch_out_time = None
            total_hours = "0:00"
            
            if emp_punches:
                # Find first IN punch and last OUT punch
                in_punches = [p for p in emp_punches if p.punch_type == PunchType.IN]
                out_punches = [p for p in emp_punches if p.punch_type == PunchType.OUT]
                
                if in_punches:
                    punch_in_time = in_punches[0].punch_time.strftime("%H:%M")
                if out_punches:
                    punch_out_time = out_punches[-1].punch_time.strftime("%H:%M")
                
                # Calculate total hours
                if in_punches and out_punches:
                    time_diff = out_punches[-1].punch_time - in_punches[0].punch_time
                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)
                    total_hours = f"{hours}:{minutes:02d}"
            
            # Determine status
            status = "Absent"
            if punch_in_time:
                status = "Present"
                # Check if late (assuming 9:00 AM is standard time)
                if punch_in_time > "09:00":
                    status = "Late"
            
            result.append({
                'employee_id': employee.id,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'employee_code': employee.employee_code,
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'punch_in_time': punch_in_time,
                'punch_out_time': punch_out_time,
                'total_hours': total_hours,
                'status': status,
                'location': employee.location.name if employee.location else 'N/A',
                'punches': [
                    {
                        'time': punch.punch_time.strftime("%H:%M"),
                        'type': punch.punch_type.value,
                        'location': punch.location or 'N/A'
                    } for punch in emp_punches
                ]
            })
        
        return result, total


class AttendanceCorrectionRepository(BaseRepository[AttendanceCorrection]):
    """Repository for attendance corrections"""
    
    def __init__(self, db: Session):
        super().__init__(AttendanceCorrection, db)
    
    def get_pending_corrections(self, business_id: int) -> List[AttendanceCorrection]:
        """Get pending attendance corrections"""
        return self.db.query(AttendanceCorrection).join(Employee).filter(
            Employee.business_id == business_id,
            AttendanceCorrection.status == "pending"
        ).order_by(desc(AttendanceCorrection.requested_at)).all()
    
    def get_employee_corrections(
        self, 
        employee_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AttendanceCorrection]:
        """Get employee attendance corrections"""
        query = self.db.query(AttendanceCorrection).filter(
            AttendanceCorrection.employee_id == employee_id
        )
        
        # Join AttendanceRecord only once and apply both date filters
        if start_date or end_date:
            query = query.join(AttendanceRecord)
            
            if start_date:
                query = query.filter(AttendanceRecord.attendance_date >= start_date)
            
            if end_date:
                query = query.filter(AttendanceRecord.attendance_date <= end_date)
        
        return query.order_by(desc(AttendanceCorrection.requested_at)).all()


class ShiftRosterRepository(BaseRepository[ShiftRoster]):
    """Repository for shift rosters"""
    
    def __init__(self, db: Session):
        super().__init__(ShiftRoster, db)
    
    def get_employee_roster(
        self, 
        employee_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[ShiftRoster]:
        """Get employee shift roster for date range"""
        return self.db.query(ShiftRoster).filter(
            ShiftRoster.employee_id == employee_id,
            ShiftRoster.roster_date >= start_date,
            ShiftRoster.roster_date <= end_date,
            ShiftRoster.is_active == True
        ).order_by(ShiftRoster.roster_date).all()
    
    def get_roster_by_date(self, business_id: int, roster_date: date) -> List[ShiftRoster]:
        """Get all employee rosters for a specific date"""
        return self.db.query(ShiftRoster).join(Employee).filter(
            Employee.business_id == business_id,
            ShiftRoster.roster_date == roster_date,
            ShiftRoster.is_active == True
        ).all()
    
    def bulk_create_roster(self, roster_data: List[Dict[str, Any]]) -> List[ShiftRoster]:
        """Bulk create shift rosters"""
        rosters = []
        for data in roster_data:
            roster = ShiftRoster(**data)
            self.db.add(roster)
            rosters.append(roster)
        
        self.db.commit()
        return rosters