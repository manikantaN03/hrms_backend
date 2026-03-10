from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CamelModel(BaseModel):
    class Config:
        # pydantic v2 replacement for orm_mode
        from_attributes = True
        # allow both field name & alias when parsing
        populate_by_name = True


class SAPMappingBase(CamelModel):
    # ---------- Static fields ----------
    doc_type: str = Field(
        min_length=1,
        max_length=10,
        alias="docType",
        serialization_alias="docType",
        description="Document type for SAP (e.g., JE for Journal Entry)"
    )
    series: str = Field(
        min_length=1,
        max_length=20,
        description="Series prefix for SAP documents"
    )
    bpl: str = Field(
        min_length=1,
        max_length=20,
        description="Business Place ID"
    )
    currency: str = Field(
        min_length=3,
        max_length=10,
        description="Currency code (e.g., INR, USD)"
    )
    location_code: str = Field(
        min_length=1,
        max_length=20,
        alias="locationCode",
        serialization_alias="locationCode",
        description="Location code for SAP"
    )
    
    @field_validator('doc_type', 'series', 'bpl', 'currency', 'location_code')
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
        """Validate that required fields are not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format"""
        v = v.strip().upper()
        if len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters (e.g., INR, USD)")
        if not v.isalpha():
            raise ValueError("Currency code must contain only alphabetic characters")
        return v

    # ---------- Salary Components ----------
    basic_salary_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="basicSalaryAcct",
        serialization_alias="basicSalaryAcct",
        description="Basic salary account code"
    )
    basic_salary_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="basicSalaryTax",
        serialization_alias="basicSalaryTax",
        description="Basic salary tax code"
    )

    hra_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="hraAcct",
        serialization_alias="hraAcct",
        description="HRA account code"
    )
    hra_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="hraTax",
        serialization_alias="hraTax",
        description="HRA tax code"
    )

    leave_encash_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="leaveEncashAcct",
        serialization_alias="leaveEncashAcct",
        description="Leave encashment account code"
    )
    leave_encash_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="leaveEncashTax",
        serialization_alias="leaveEncashTax",
        description="Leave encashment tax code"
    )

    bonus_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="bonusAcct",
        serialization_alias="bonusAcct",
        description="Bonus account code"
    )
    bonus_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="bonusTax",
        serialization_alias="bonusTax",
        description="Bonus tax code"
    )

    gratuity_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="gratuityAcct",
        serialization_alias="gratuityAcct",
        description="Gratuity account code"
    )
    gratuity_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="gratuityTax",
        serialization_alias="gratuityTax",
        description="Gratuity tax code"
    )

    loan_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="loanAcct",
        serialization_alias="loanAcct",
        description="Loan account code"
    )
    loan_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="loanTax",
        serialization_alias="loanTax",
        description="Loan tax code"
    )

    overtime_hours_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="overtimeHoursAcct",
        serialization_alias="overtimeHoursAcct",
        description="Overtime hours account code"
    )
    overtime_hours_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="overtimeHoursTax",
        serialization_alias="overtimeHoursTax",
        description="Overtime hours tax code"
    )

    retention_bonus_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="retentionBonusAcct",
        serialization_alias="retentionBonusAcct",
        description="Retention bonus account code"
    )
    retention_bonus_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="retentionBonusTax",
        serialization_alias="retentionBonusTax",
        description="Retention bonus tax code"
    )

    medical_allowance_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="medicalAllowanceAcct",
        serialization_alias="medicalAllowanceAcct",
        description="Medical allowance account code"
    )
    medical_allowance_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="medicalAllowanceTax",
        serialization_alias="medicalAllowanceTax",
        description="Medical allowance tax code"
    )

    special_allowance_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="specialAllowanceAcct",
        serialization_alias="specialAllowanceAcct",
        description="Special allowance account code"
    )
    special_allowance_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="specialAllowanceTax",
        serialization_alias="specialAllowanceTax",
        description="Special allowance tax code"
    )

    overtime_days_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="overtimeDaysAcct",
        serialization_alias="overtimeDaysAcct",
        description="Overtime days account code"
    )
    overtime_days_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="overtimeDaysTax",
        serialization_alias="overtimeDaysTax",
        description="Overtime days tax code"
    )

    conveyance_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="conveyanceAcct",
        serialization_alias="conveyanceAcct",
        description="Conveyance account code"
    )
    conveyance_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="conveyanceTax",
        serialization_alias="conveyanceTax",
        description="Conveyance tax code"
    )

    telephone_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="telephoneAcct",
        serialization_alias="telephoneAcct",
        description="Telephone account code"
    )
    telephone_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="telephoneTax",
        serialization_alias="telephoneTax",
        description="Telephone tax code"
    )

    # ---------- Salary Deductions ----------
    esi_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="esiAcct",
        serialization_alias="esiAcct",
        description="ESI account code"
    )
    esi_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="esiTax",
        serialization_alias="esiTax",
        description="ESI tax code"
    )

    pf_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="pfAcct",
        serialization_alias="pfAcct",
        description="PF account code"
    )
    pf_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="pfTax",
        serialization_alias="pfTax",
        description="PF tax code"
    )

    voluntary_pf_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="voluntaryPfAcct",
        serialization_alias="voluntaryPfAcct",
        description="Voluntary PF account code"
    )
    voluntary_pf_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="voluntaryPfTax",
        serialization_alias="voluntaryPfTax",
        description="Voluntary PF tax code"
    )

    professional_tax_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="professionalTaxAcct",
        serialization_alias="professionalTaxAcct",
        description="Professional tax account code"
    )
    professional_tax_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="professionalTaxTax",
        serialization_alias="professionalTaxTax",
        description="Professional tax tax code"
    )

    income_tax_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="incomeTaxAcct",
        serialization_alias="incomeTaxAcct",
        description="Income tax account code"
    )
    income_tax_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="incomeTaxTax",
        serialization_alias="incomeTaxTax",
        description="Income tax tax code"
    )

    loan_repayment_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="loanRepaymentAcct",
        serialization_alias="loanRepaymentAcct",
        description="Loan repayment account code"
    )
    loan_repayment_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="loanRepaymentTax",
        serialization_alias="loanRepaymentTax",
        description="Loan repayment tax code"
    )

    loan_interest_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="loanInterestAcct",
        serialization_alias="loanInterestAcct",
        description="Loan interest account code"
    )
    loan_interest_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="loanInterestTax",
        serialization_alias="loanInterestTax",
        description="Loan interest tax code"
    )

    group_insurance_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="groupInsuranceAcct",
        serialization_alias="groupInsuranceAcct",
        description="Group insurance account code"
    )
    group_insurance_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="groupInsuranceTax",
        serialization_alias="groupInsuranceTax",
        description="Group insurance tax code"
    )

    pf_extra_cont_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="pfExtraContAcct",
        serialization_alias="pfExtraContAcct",
        description="PF extra contribution account code"
    )
    pf_extra_cont_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="pfExtraContTax",
        serialization_alias="pfExtraContTax",
        description="PF extra contribution tax code"
    )

    labour_welfare_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="labourWelfareAcct",
        serialization_alias="labourWelfareAcct",
        description="Labour welfare account code"
    )
    labour_welfare_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="labourWelfareTax",
        serialization_alias="labourWelfareTax",
        description="Labour welfare tax code"
    )

    gratuity_ded_acct: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="gratuityDedAcct",
        serialization_alias="gratuityDedAcct",
        description="Gratuity deduction account code"
    )
    gratuity_ded_tax: Optional[str] = Field(
        default=None,
        max_length=50,
        alias="gratuityDedTax",
        serialization_alias="gratuityDedTax",
        description="Gratuity deduction tax code"
    )
    
    @field_validator(
        'basic_salary_acct', 'basic_salary_tax', 'hra_acct', 'hra_tax',
        'leave_encash_acct', 'leave_encash_tax', 'bonus_acct', 'bonus_tax',
        'gratuity_acct', 'gratuity_tax', 'loan_acct', 'loan_tax',
        'overtime_hours_acct', 'overtime_hours_tax', 'retention_bonus_acct', 'retention_bonus_tax',
        'medical_allowance_acct', 'medical_allowance_tax', 'special_allowance_acct', 'special_allowance_tax',
        'overtime_days_acct', 'overtime_days_tax', 'conveyance_acct', 'conveyance_tax',
        'telephone_acct', 'telephone_tax', 'esi_acct', 'esi_tax', 'pf_acct', 'pf_tax',
        'voluntary_pf_acct', 'voluntary_pf_tax', 'professional_tax_acct', 'professional_tax_tax',
        'income_tax_acct', 'income_tax_tax', 'loan_repayment_acct', 'loan_repayment_tax',
        'loan_interest_acct', 'loan_interest_tax', 'group_insurance_acct', 'group_insurance_tax',
        'pf_extra_cont_acct', 'pf_extra_cont_tax', 'labour_welfare_acct', 'labour_welfare_tax',
        'gratuity_ded_acct', 'gratuity_ded_tax'
    )
    @classmethod
    def validate_optional_codes(cls, v: Optional[str]) -> Optional[str]:
        """Validate optional account/tax codes - strip whitespace and reject empty strings"""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        return v


class SAPMappingCreate(SAPMappingBase):
    # can be omitted if you always use path param for business_id
    business_id: Optional[int] = Field(alias="businessId", default=None)


class SAPMappingUpdate(SAPMappingBase):
    business_id: Optional[int] = Field(alias="businessId", default=None)


class SAPMappingResponse(SAPMappingBase):
    id: int
    business_id: Optional[int] = Field(default=None, serialization_alias="businessId")
    created_at: Optional[datetime] = Field(default=None, serialization_alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, serialization_alias="updatedAt")


class SAPMappingOut(SAPMappingResponse):
    """Alias/shortcut if you want a clearer name in routes."""
    pass
