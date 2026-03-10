"""
Employee Summary Response Schemas
Pydantic models for employee summary API responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class ManagerInfo(BaseModel):
    """Manager information schema"""
    name: str
    code: str
    img: str


class DirectReportInfo(BaseModel):
    """Direct report information schema"""
    id: int
    name: str
    code: str
    img: str


class BasicInfo(BaseModel):
    """Employee basic information schema"""
    firstName: str
    lastName: str
    middleName: Optional[str] = ""
    personalEmail: str
    personalPhone: str
    alternatePhone: Optional[str] = ""
    officePhone: Optional[str] = ""
    officialEmail: Optional[str] = ""
    dateOfBirth: Optional[str] = None
    dateOfConfirmation: Optional[str] = None
    dateOfMarriage: Optional[str] = None
    gender: Optional[str] = ""
    maritalStatus: Optional[str] = ""
    bloodGroup: Optional[str] = ""
    nationality: Optional[str] = ""
    religion: Optional[str] = ""
    emergencyContact: Optional[str] = ""
    emergencyPhone: Optional[str] = ""
    fatherName: Optional[str] = ""
    motherName: Optional[str] = ""
    noticePeriod: Optional[str] = ""
    employeeCode: str
    biometricCode: Optional[str] = ""
    passportNumber: Optional[str] = ""
    passportExpiry: Optional[str] = ""
    drivingLicense: Optional[str] = ""
    licenseExpiry: Optional[str] = ""
    currentAddress: Optional[str] = ""
    permanentAddress: Optional[str] = ""
    panNumber: Optional[str] = ""
    aadharNumber: Optional[str] = ""


class WorkProfile(BaseModel):
    """Employee work profile schema"""
    joiningDate: Optional[str] = None
    confirmationDate: Optional[str] = None
    reportingManager: str


class Managers(BaseModel):
    """Employee managers schema"""
    reportingManager: ManagerInfo
    hrManager: ManagerInfo
    indirectManager: ManagerInfo


class ContactDetails(BaseModel):
    """Employee contact details schema"""
    officePhone: Optional[str] = ""
    homePhone: Optional[str] = ""
    emergencyContact: Optional[str] = ""
    personalEmail: str


class HRRecord(BaseModel):
    """Employee HR record schema"""
    dateOfJoining: str
    dateOfConfirmation: str
    dateOfBirth: str


class EmployeeSummaryResponse(BaseModel):
    """Complete employee summary response schema"""
    id: int
    name: str
    code: str
    position: str
    department: str
    location: str
    business: str
    joining: str
    img: str
    active: bool
    email: str
    mobile: str
    basicInfo: BasicInfo
    workProfile: WorkProfile
    managers: Managers
    directReports: List[DirectReportInfo]
    contactDetails: ContactDetails
    hrRecord: HRRecord
    
    class Config:
        from_attributes = True