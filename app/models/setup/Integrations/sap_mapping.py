from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class SAPMapping(Base):
    __tablename__ = "sap_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Link to Business (OPTIONAL for backward compatibility)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # -------- Static Fields --------
    # column name in DB = "docType", Python attribute = doc_type
    doc_type = Column("docType", String(10), nullable=False)
    series = Column(String(20), nullable=False)
    bpl = Column(String(20), nullable=False)
    currency = Column(String(10), nullable=False)
    location_code = Column("locationCode", String(20), nullable=False)

    # -------- Salary Components --------
    basic_salary_acct = Column("basicSalaryAcct", String(50), nullable=True)
    basic_salary_tax = Column("basicSalaryTax", String(50), nullable=True)

    hra_acct = Column("hraAcct", String(50), nullable=True)
    hra_tax = Column("hraTax", String(50), nullable=True)

    leave_encash_acct = Column("leaveEncashAcct", String(50), nullable=True)
    leave_encash_tax = Column("leaveEncashTax", String(50), nullable=True)

    bonus_acct = Column("bonusAcct", String(50), nullable=True)
    bonus_tax = Column("bonusTax", String(50), nullable=True)

    gratuity_acct = Column("gratuityAcct", String(50), nullable=True)
    gratuity_tax = Column("gratuityTax", String(50), nullable=True)

    loan_acct = Column("loanAcct", String(50), nullable=True)
    loan_tax = Column("loanTax", String(50), nullable=True)

    overtime_hours_acct = Column("overtimeHoursAcct", String(50), nullable=True)
    overtime_hours_tax = Column("overtimeHoursTax", String(50), nullable=True)

    retention_bonus_acct = Column("retentionBonusAcct", String(50), nullable=True)
    retention_bonus_tax = Column("retentionBonusTax", String(50), nullable=True)

    medical_allowance_acct = Column("medicalAllowanceAcct", String(50), nullable=True)
    medical_allowance_tax = Column("medicalAllowanceTax", String(50), nullable=True)

    special_allowance_acct = Column("specialAllowanceAcct", String(50), nullable=True)
    special_allowance_tax = Column("specialAllowanceTax", String(50), nullable=True)

    overtime_days_acct = Column("overtimeDaysAcct", String(50), nullable=True)
    overtime_days_tax = Column("overtimeDaysTax", String(50), nullable=True)

    conveyance_acct = Column("conveyanceAcct", String(50), nullable=True)
    conveyance_tax = Column("conveyanceTax", String(50), nullable=True)

    telephone_acct = Column("telephoneAcct", String(50), nullable=True)
    telephone_tax = Column("telephoneTax", String(50), nullable=True)

    # -------- Salary Deductions --------
    esi_acct = Column("esiAcct", String(50), nullable=True)
    esi_tax = Column("esiTax", String(50), nullable=True)

    pf_acct = Column("pfAcct", String(50), nullable=True)
    pf_tax = Column("pfTax", String(50), nullable=True)

    voluntary_pf_acct = Column("voluntaryPfAcct", String(50), nullable=True)
    voluntary_pf_tax = Column("voluntaryPfTax", String(50), nullable=True)

    professional_tax_acct = Column("professionalTaxAcct", String(50), nullable=True)
    professional_tax_tax = Column("professionalTaxTax", String(50), nullable=True)

    income_tax_acct = Column("incomeTaxAcct", String(50), nullable=True)
    income_tax_tax = Column("incomeTaxTax", String(50), nullable=True)

    loan_repayment_acct = Column("loanRepaymentAcct", String(50), nullable=True)
    loan_repayment_tax = Column("loanRepaymentTax", String(50), nullable=True)

    loan_interest_acct = Column("loanInterestAcct", String(50), nullable=True)
    loan_interest_tax = Column("loanInterestTax", String(50), nullable=True)

    group_insurance_acct = Column("groupInsuranceAcct", String(50), nullable=True)
    group_insurance_tax = Column("groupInsuranceTax", String(50), nullable=True)

    pf_extra_cont_acct = Column("pfExtraContAcct", String(50), nullable=True)
    pf_extra_cont_tax = Column("pfExtraContTax", String(50), nullable=True)

    labour_welfare_acct = Column("labourWelfareAcct", String(50), nullable=True)
    labour_welfare_tax = Column("labourWelfareTax", String(50), nullable=True)

    gratuity_ded_acct = Column("gratuityDedAcct", String(50), nullable=True)
    gratuity_ded_tax = Column("gratuityDedTax", String(50), nullable=True)

    # 🔄 Relationship to Business
    business = relationship("Business", back_populates="sap_mappings")
