"""
Additional Attendance Schemas
Pydantic models for attendance API requests that were missing proper schemas
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal


# ============================================================================
# Daily Punch Download Schema
# ============================================================================

class DailyPunchDownloadRequest(BaseModel):
    """Daily punch download request"""
    punch_date: str = Field(..., description="Date for download in YYYY-MM-DD format", example="2026-02-19")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional filters to apply")
    
    @field_validator('punch_date')
    @classmethod
    def validate_punch_date(cls, v):
        """Validate punch date format"""
        if not v:
            raise ValueError("punch_date is required")
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("punch_date must be in YYYY-MM-DD format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "punch_date": "2026-02-19",
                "filters": {
                    "department_id": 1,
                    "location_id": 2
                }
            }
        }


# ============================================================================
# Add Punch Record Schema
# ============================================================================

class AddPunchRecordRequest(BaseModel):
    """Add punch record request"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    punch_date: str = Field(..., description="Punch date in YYYY-MM-DD format", example="2026-02-19")
    punch_time: str = Field(..., description="Punch time in HH:MM:SS format", example="09:30:00")
    punch_type: str = Field(..., description="Punch type: in, out, break_in, break_out", example="in")
    location: Optional[str] = Field(None, description="Punch location", max_length=255, example="Office Main Gate")
    latitude: Optional[float] = Field(None, description="GPS latitude", ge=-90, le=90, example=12.9716)
    longitude: Optional[float] = Field(None, description="GPS longitude", ge=-180, le=180, example=77.5946)
    is_remote: bool = Field(default=False, description="Is remote punch", example=False)
    device_info: Optional[str] = Field(None, description="Device information", max_length=500, example="Mobile App v1.0")
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500, example="Late due to traffic")
    
    @field_validator('punch_date')
    @classmethod
    def validate_punch_date(cls, v):
        """Validate punch date format - accepts multiple formats"""
        # Try multiple date formats
        date_formats = [
            "%Y-%m-%d",      # 2025-01-12
            "%m/%d/%Y",      # 01/12/2025
            "%d/%m/%Y",      # 12/01/2025
            "%Y/%m/%d",      # 2025/01/12
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(v, fmt)
                # Return in standard format
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        raise ValueError("punch_date must be in YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY format")
    
    @field_validator('punch_time')
    @classmethod
    def validate_punch_time(cls, v):
        """Validate punch time format - accepts HH:MM or HH:MM:SS"""
        # Try HH:MM:SS format first
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            pass
        
        # Try HH:MM format and add seconds
        try:
            parsed_time = datetime.strptime(v, "%H:%M")
            return parsed_time.strftime("%H:%M:00")
        except ValueError:
            raise ValueError("punch_time must be in HH:MM or HH:MM:SS format")
    
    @field_validator('punch_type')
    @classmethod
    def validate_punch_type(cls, v):
        """Validate punch type"""
        valid_types = ['in', 'out', 'break_in', 'break_out']
        if v.lower() not in valid_types:
            raise ValueError(f"punch_type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "punch_date": "2026-02-19",
                "punch_time": "09:30:00",
                "punch_type": "in",
                "location": "Office Main Gate",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "is_remote": False,
                "device_info": "Mobile App v1.0",
                "notes": "On time"
            }
        }


# ============================================================================
# Leave Correction Create Schema
# ============================================================================

class LeaveCorrectionCreateRequest(BaseModel):
    """Leave correction create request"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    correction_date: str = Field(..., description="Correction date in YYYY-MM-DD format", example="2026-02-19")
    original_status: str = Field(..., description="Original attendance status", max_length=50, example="ABSENT")
    corrected_status: str = Field(..., description="Corrected attendance status", max_length=50, example="PRESENT")
    reason: str = Field(..., description="Reason for correction", min_length=10, max_length=500, example="Employee was present but punch was missed due to biometric device malfunction")
    supporting_documents: Optional[List[str]] = Field(None, description="Supporting document URLs", example=["doc1.pdf", "doc2.pdf"])
    
    @field_validator('correction_date')
    @classmethod
    def validate_correction_date(cls, v):
        """Validate correction date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("correction_date must be in YYYY-MM-DD format")
    
    @field_validator('original_status', 'corrected_status')
    @classmethod
    def validate_status(cls, v):
        """Validate status values"""
        valid_statuses = ['PRESENT', 'ABSENT', 'HALF_DAY', 'LATE', 'ON_LEAVE', 'HOLIDAY', 'WEEKEND', 'COMP_OFF', 'LEAVE_WITHOUT_PAY']
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "correction_date": "2026-02-19",
                "original_status": "ABSENT",
                "corrected_status": "PRESENT",
                "reason": "Employee was present but punch was missed due to biometric device malfunction",
                "supporting_documents": ["attendance_proof.pdf"]
            }
        }


# ============================================================================
# Shift Roster Request Schema
# ============================================================================

class ShiftRosterRequestCreate(BaseModel):
    """Shift roster request create"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    roster_date: str = Field(..., description="Roster date in YYYY-MM-DD format", example="2026-02-19")
    shift_id: int = Field(..., description="Shift ID", gt=0, example=5)
    reason: str = Field(..., description="Reason for shift change", min_length=10, max_length=500, example="Need to attend family function")
    custom_start_time: Optional[str] = Field(None, description="Custom start time in HH:MM:SS format", example="10:00:00")
    custom_end_time: Optional[str] = Field(None, description="Custom end time in HH:MM:SS format", example="18:00:00")
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500, example="Will complete pending work next day")
    
    @field_validator('roster_date')
    @classmethod
    def validate_roster_date(cls, v):
        """Validate roster date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("roster_date must be in YYYY-MM-DD format")
    
    @field_validator('custom_start_time', 'custom_end_time')
    @classmethod
    def validate_time(cls, v):
        """Validate time format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM:SS format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "roster_date": "2026-02-19",
                "shift_id": 5,
                "reason": "Need to attend family function",
                "custom_start_time": "10:00:00",
                "custom_end_time": "18:00:00",
                "notes": "Will complete pending work next day"
            }
        }


# ============================================================================
# Shift Roster Approval Schema
# ============================================================================

class ShiftRosterApprovalRequest(BaseModel):
    """Shift roster approval/rejection request"""
    remarks: Optional[str] = Field(None, description="Approval/rejection remarks", max_length=500, example="Approved as per business requirement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "remarks": "Approved as per business requirement"
            }
        }


# ============================================================================
# Daily Punch Add Schema
# ============================================================================

class DailyPunchAddRequest(BaseModel):
    """Daily punch add request"""
    employee_id: Optional[int] = Field(None, description="Employee ID", gt=0, example=123)
    employee_name: Optional[str] = Field(None, description="Employee name (alternative to employee_id)", max_length=255, example="Minal Devidas Mahajan")
    punch_date: Optional[str] = Field(None, description="Punch date in YYYY-MM-DD format (defaults to today)", example="2026-02-19")
    punch_time: Optional[str] = Field(None, description="Punch time in HH:MM:SS format (defaults to current time)", example="09:30:00")
    punch_type: str = Field(..., description="Punch type: in, out, break_in, break_out", example="in")
    location: Optional[str] = Field(None, description="Punch location", max_length=255, example="Office Main Gate")
    is_manual: bool = Field(default=True, description="Is manual entry", example=True)
    is_remote: bool = Field(default=False, description="Is remote punch", example=False)
    device_info: Optional[str] = Field(None, description="Device information", max_length=500, example="Manual Entry")
    reason: Optional[str] = Field(None, description="Reason for manual entry", max_length=500, example="Biometric device was not working")
    
    @model_validator(mode='after')
    def validate_employee(self):
        """Ensure either employee_id or employee_name is provided"""
        if not self.employee_id and not self.employee_name:
            raise ValueError("Either employee_id or employee_name must be provided")
        return self
    
    @model_validator(mode='after')
    def set_defaults(self):
        """Set default date and time if not provided"""
        from datetime import datetime
        
        if not self.punch_date:
            self.punch_date = datetime.now().strftime("%Y-%m-%d")
        
        if not self.punch_time:
            self.punch_time = datetime.now().strftime("%H:%M:%S")
        
        return self
    
    @field_validator('punch_date')
    @classmethod
    def validate_punch_date(cls, v):
        """Validate punch date format - accepts multiple formats"""
        # Try multiple date formats
        date_formats = [
            "%Y-%m-%d",      # 2025-01-12
            "%m/%d/%Y",      # 01/12/2025
            "%d/%m/%Y",      # 12/01/2025
            "%Y/%m/%d",      # 2025/01/12
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(v, fmt)
                # Return in standard format
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        raise ValueError("punch_date must be in YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY format")
    
    @field_validator('punch_time')
    @classmethod
    def validate_punch_time(cls, v):
        """Validate punch time format - accepts HH:MM or HH:MM:SS"""
        # Try HH:MM:SS format first
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            pass
        
        # Try HH:MM format and add seconds
        try:
            parsed_time = datetime.strptime(v, "%H:%M")
            return parsed_time.strftime("%H:%M:00")
        except ValueError:
            raise ValueError("punch_time must be in HH:MM or HH:MM:SS format")
    
    @field_validator('punch_type')
    @classmethod
    def validate_punch_type(cls, v):
        """Validate punch type"""
        valid_types = ['in', 'out', 'break_in', 'break_out']
        if v.lower() not in valid_types:
            raise ValueError(f"punch_type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "punch_date": "2026-02-19",
                "punch_time": "09:30:00",
                "punch_type": "in",
                "location": "Office Main Gate",
                "is_manual": True,
                "reason": "Biometric device was not working"
            }
        }


# ============================================================================
# Attendance Employee Update Schema
# ============================================================================

class AttendanceEmployeeUpdateRequest(BaseModel):
    """Attendance employee update request"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    month: str = Field(..., description="Month in format 'MMM-YYYY'", example="FEB-2026")
    attendance_data: Optional[Dict[str, Any]] = Field(None, description="Attendance data to update (legacy)")
    attendance_updates: Optional[List[Dict[str, Any]]] = Field(None, description="List of attendance updates")
    
    @model_validator(mode='after')
    def validate_updates(self):
        """Ensure either attendance_data or attendance_updates is provided"""
        if not self.attendance_data and not self.attendance_updates:
            raise ValueError("Either attendance_data or attendance_updates must be provided")
        return self
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not v:
            raise ValueError("Month is required")
        
        try:
            month_str, year_str = v.split('-')
            year = int(year_str)
            
            valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            if month_str not in valid_months:
                raise ValueError(f"Invalid month. Must be one of: {', '.join(valid_months)}")
            
            if year < 2020 or year > 2030:
                raise ValueError("Year must be between 2020 and 2030")
                
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid month format. Use format like 'FEB-2026'")
            raise e
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "month": "FEB-2026",
                "attendance_data": {
                    "present_days": 20,
                    "absent_days": 2,
                    "leave_days": 3
                }
            }
        }


# ============================================================================
# Attendance Employee Export Schema
# ============================================================================

class AttendanceEmployeeExportRequest(BaseModel):
    """Attendance employee export request"""
    month: str = Field(..., description="Month in format 'MMM-YYYY'", example="FEB-2026")
    employee_ids: Optional[List[int]] = Field(None, description="List of employee IDs to export", example=[123, 456])
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")
    format: str = Field(default="csv", description="Export format: csv, excel", example="csv")
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not v:
            raise ValueError("Month is required")
        
        try:
            month_str, year_str = v.split('-')
            year = int(year_str)
            
            valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            if month_str not in valid_months:
                raise ValueError(f"Invalid month. Must be one of: {', '.join(valid_months)}")
            
            if year < 2020 or year > 2030:
                raise ValueError("Year must be between 2020 and 2030")
                
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid month format. Use format like 'FEB-2026'")
            raise e
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate export format"""
        valid_formats = ['csv', 'excel', 'xlsx']
        if v.lower() not in valid_formats:
            raise ValueError(f"format must be one of: {', '.join(valid_formats)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "month": "FEB-2026",
                "employee_ids": [123, 456, 789],
                "filters": {
                    "department_id": 1,
                    "location_id": 2
                },
                "format": "csv"
            }
        }


# ============================================================================
# Attendance Employee Upload Schema
# ============================================================================

class AttendanceEmployeeUploadRequest(BaseModel):
    """Attendance employee upload request"""
    month: str = Field(..., description="Month in format 'MMM-YYYY'", example="FEB-2026")
    action: str = Field(default="merge", description="Upload action: merge, replace", example="merge")
    validate_only: bool = Field(default=False, description="Only validate without saving", example=False)
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not v:
            raise ValueError("Month is required")
        
        try:
            month_str, year_str = v.split('-')
            year = int(year_str)
            
            valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            if month_str not in valid_months:
                raise ValueError(f"Invalid month. Must be one of: {', '.join(valid_months)}")
            
            if year < 2020 or year > 2030:
                raise ValueError("Year must be between 2020 and 2030")
                
            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid month format. Use format like 'FEB-2026'")
            raise e
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action"""
        valid_actions = ['merge', 'replace']
        if v.lower() not in valid_actions:
            raise ValueError(f"action must be one of: {', '.join(valid_actions)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "month": "FEB-2026",
                "action": "merge",
                "validate_only": False
            }
        }


# ============================================================================
# Daily Attendance Punch Add Schema
# ============================================================================

class DailyAttendancePunchAddRequest(BaseModel):
    """Daily attendance punch add request"""
    employee_id: int = Field(..., description="Employee ID", gt=0, example=123)
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-02-19")
    punch_time: str = Field(..., description="Punch time in HH:MM:SS format", example="09:30:00")
    punch_type: str = Field(..., description="Punch type: in, out, break_in, break_out", example="in")
    location: Optional[str] = Field(None, description="Punch location", max_length=255, example="Office Main Gate")
    latitude: Optional[float] = Field(None, description="GPS latitude", ge=-90, le=90, example=12.9716)
    longitude: Optional[float] = Field(None, description="GPS longitude", ge=-180, le=180, example=77.5946)
    is_remote: bool = Field(default=False, description="Is remote punch", example=False)
    is_manual: bool = Field(default=False, description="Is manual entry", example=False)
    device_info: Optional[str] = Field(None, description="Device information", max_length=500, example="Mobile App v1.0")
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500, example="On time")
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format - accepts multiple formats"""
        # Try multiple date formats
        date_formats = [
            "%Y-%m-%d",      # 2025-01-12
            "%m/%d/%Y",      # 01/12/2025
            "%d/%m/%Y",      # 12/01/2025
            "%Y/%m/%d",      # 2025/01/12
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(v, fmt)
                # Return in standard format
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        raise ValueError("date must be in YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY format")
    
    @field_validator('punch_time')
    @classmethod
    def validate_punch_time(cls, v):
        """Validate punch time format - accepts HH:MM or HH:MM:SS"""
        # Try HH:MM:SS format first
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            pass
        
        # Try HH:MM format and add seconds
        try:
            parsed_time = datetime.strptime(v, "%H:%M")
            return parsed_time.strftime("%H:%M:00")
        except ValueError:
            raise ValueError("punch_time must be in HH:MM or HH:MM:SS format")
    
    @field_validator('punch_type')
    @classmethod
    def validate_punch_type(cls, v):
        """Validate punch type"""
        valid_types = ['in', 'out', 'break_in', 'break_out']
        if v.lower() not in valid_types:
            raise ValueError(f"punch_type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 123,
                "date": "2026-02-19",
                "punch_time": "09:30:00",
                "punch_type": "in",
                "location": "Office Main Gate",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "is_remote": False,
                "is_manual": False,
                "device_info": "Mobile App v1.0",
                "notes": "On time"
            }
        }
