"""
Business Model
Represents companies/organizations created by admin users
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import BaseModel


class Business(BaseModel):
    """
    Business (Company) entity created by an admin user.
    
    An admin can create and manage multiple businesses.
    Each business represents a separate company/organization.
    """
    
    __tablename__ = "businesses"
    
    # ========================================================================
    # Ownership
    # ========================================================================
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # ========================================================================
    # Core Business Identity
    # ========================================================================
    business_name = Column(String(255), nullable=False, index=True)
    gstin = Column(String(15), nullable=True, unique=True, index=True)
    is_authorized = Column(Boolean, default=False, nullable=False)
    
    # ========================================================================
    # Legal & Address Details
    # ========================================================================
    pan = Column(String(10), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    state = Column(String(100), nullable=False, index=True)
    constitution = Column(String(100), nullable=False)
    
    # ========================================================================
    # Product & Subscription
    # ========================================================================
    product = Column(String(100), nullable=False)
    plan = Column(String(50), nullable=False)
    employee_count = Column(Integer, nullable=False, default=1)
    billing_frequency = Column(String(50), nullable=False)
    biometric_license_count = Column(Integer, nullable=False, default=3)
    
    # ========================================================================
    # Business URL (for multi-tenancy)
    # ========================================================================
    business_url = Column(String(255), nullable=True, unique=True)
    
    # ========================================================================
    # Business Preferences
    # ========================================================================
    currency = Column(String(10), nullable=True, default="USD")
    language = Column(String(50), nullable=True, default="English")
    
    # ========================================================================
    # Status
    # ========================================================================
    is_active = Column(Boolean, default=True, nullable=False)
    
    # ========================================================================
    # Relationships
    # ========================================================================
    owner = relationship("User", backref="businesses")

    business_units = relationship(
        "BusinessUnit",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    locations = relationship(
        "Location",
        back_populates="business",
        cascade="all, delete-orphan"
    )
       #  NCOST CENTERS RELATIONSHIP
    cost_centers = relationship(
        "CostCenter",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    # DEPARTMENTS RELATIONSHIP
    departments = relationship(
        "Department",
        back_populates="business",
        cascade="all, delete-orphan",
    )
        #  APPROVAL SETTINGS RELATIONSHIP (ONE-TO-ONE)
    approval_settings = relationship(
        "ApprovalSettings",
        back_populates="business",
        cascade="all, delete-orphan",
        uselist=False   #  One Business → One ApprovalSettings row
    )
    employee_code_settings = relationship("EmployeeCodeSetting",back_populates="business",cascade="all, delete-orphan")
    exit_reasons = relationship("ExitReason",back_populates="business",cascade="all, delete-orphan")
    helpdesk_categories = relationship("HelpdeskCategory",back_populates="business",cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="business", cascade="all, delete-orphan")
    weekoff_policies = relationship(
                "WeekOffPolicy",
                back_populates="business",
                cascade="all, delete-orphan",
        )
    # Visit types (e.g., client visit categories)
    visit_types = relationship(
        "VisitType",
        back_populates="business",
        cascade="all, delete-orphan",
    )
 
    # Shift policies and shifts
    shift_policies = relationship(
        "ShiftPolicy",
        back_populates="business",
        cascade="all, delete-orphan",
    )
 
    
 
    # One-to-one business information
    business_information = relationship(
        "BusinessInformation",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan",
    )

    grades = relationship(
        "Grade",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    designations = relationship(
        "Designation",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    work_shifts = relationship(
        "WorkShift",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    
    email_mailboxes = relationship(

        "EmailMailbox",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    biometric_devices = relationship(

        "BiometricDevice",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    gatekeeper_devices = relationship(

        "GatekeeperDevice",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    sqlserver_sources = relationship(

        "SqlServerSource",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    sap_mappings = relationship(

        "SAPMapping",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    api_access = relationship(

        "APIAccess",

        back_populates="business",

        cascade="all, delete-orphan",

        uselist=False,

    )
       # One-to-one relationship to attendance settings
    attendance_settings = relationship(
        "AttendanceSettings",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan"
    )
    # One-to-one relationships to statutory settings
    esi_settings = relationship(
        "ESISettings",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan"
    )
    epf_settings = relationship(
        "EPFSettings",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan"
    )
    professional_tax_settings = relationship(
        "ProfessionalTaxSettings",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan"
    )
    # One-to-many relationship to leave types
    leave_types = relationship(
        "LeaveType",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    # One-to-many relationship to leave policies
    leave_policies = relationship(
        "LeavePolicy",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    # One-to-many relationship to overtime policies
    overtime_policies = relationship(
        "OvertimePolicy",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    # One-to-many relationship to strike adjustments
    strike_adjustments = relationship(
        "StrikeAdjustment",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    # One-to-many relationship to strike rules
    strike_rules = relationship(
        "StrikeRule",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    # One-to-many relationship to comp off rules
    compoff_rules = relationship(
        "CompOffRule",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    employer_info = relationship(
        "EmployerInfo",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    # Name must match PersonResponsible.back_populates (was referencing 'person_responsibles')
    person_responsibles = relationship(
        "PersonResponsible",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    cit_info = relationship(
        "CitInfo",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    tds_24q_info = relationship(
        "TDS24Q",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    lwf_settings = relationship(
        "LWFSettings",
        back_populates="business",
        cascade="all, delete-orphan",
        uselist=False
    )

    lwf_rates = relationship(
        "LWFRate",
        back_populates="business",
        cascade="all, delete-orphan"    
    )
    financial_years = relationship(
        "FinancialYear",
        back_populates="business",
        cascade="all, delete-orphan"    
    )
    tax_rates = relationship(
        "TaxRate",
        back_populates="business",
        cascade="all, delete-orphan"    
    )
    holidays = relationship(
        "Holiday",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    
    # Calendar events relationship
    calendar_events = relationship(
        "CalendarEvent",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    
    # Project management relationships
    projects = relationship(
        "Project",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    
    # Notes management relationships
    notes = relationship(
        "Note",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    # ========================================================================

    # ✔ ADDED — Your Salary Setup Components (Business-Scoped)

    # ========================================================================
 
    # 1 Salary Components

    salary_components = relationship(

        "SalaryComponent",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    # 2 Salary Deductions

    salary_deductions = relationship(

        "SalaryDeduction",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    #  Time Salary Rules

    time_salary_rules = relationship(

        "TimeSalaryRule",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    # 4Overtime Policies

    overtime_policies = relationship(

        "OvertimePolicy",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    #  Overtime Rules

    overtime_rules = relationship(

        "OvertimeRule",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    # Salary Structures

    salary_structures = relationship(

        "SalaryStructure",

        back_populates="business",

        cascade="all, delete-orphan",

    )
 
    # 7 Salary Structure Rules

    salary_structure_rules = relationship(

        "SalaryStructureRule",

        back_populates="business",

        cascade="all, delete-orphan",

    )
    
    # Employee Management
    employees = relationship(
        "Employee",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    
    # Onboarding Management
    onboarding_forms = relationship(
        "OnboardingForm",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    
    # ========================================================================
    # Indexes for performance
    # ========================================================================
    __table_args__ = (
        Index('ix_businesses_owner_active', 'owner_id', 'is_active'),
        Index('ix_businesses_gstin_active', 'gstin', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Business(id={self.id}, name='{self.business_name}', owner_id={self.owner_id})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'business_name': self.business_name,
            'gstin': self.gstin,
            'is_authorized': self.is_authorized,
            'pan': self.pan,
            'address': self.address,
            'city': self.city,
            'pincode': self.pincode,
            'state': self.state,
            'constitution': self.constitution,
            'product': self.product,
            'plan': self.plan,
            'employee_count': self.employee_count,
            'billing_frequency': self.billing_frequency,
            'business_url': self.business_url,
            'currency': self.currency,
            'language': self.language,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }