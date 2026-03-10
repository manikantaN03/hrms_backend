from datetime import date
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from ..repositories.tax_repository import TaxRepository
from ..models.tax_models import (
    TDSSetting,
    FinancialYear,
    TaxRate,
)
from ..models.setup.salary_and_deductions.salary_component import SalaryComponent


class TaxService:
    def __init__(self, db: Session):
        self.repo = TaxRepository(db)

    # TDS
    def get_tds_setting(self, business_id: Optional[int] = None) -> Optional[TDSSetting]:
        setting = self.repo.get_tds_setting(business_id=business_id)
        if not setting:
            setting = self.repo.create_tds_setting(False, business_id=business_id)
        return setting

    def update_tds_setting(self, deduct_tds: bool, business_id: Optional[int] = None) -> TDSSetting:
        setting = self.repo.get_tds_setting(business_id=business_id)
        if not setting:
            return self.repo.create_tds_setting(deduct_tds, business_id=business_id)
        return self.repo.update_tds_setting(setting, deduct_tds)

    # Financial Years
    def list_financial_years(self) -> List[FinancialYear]:
        return self.repo.list_financial_years()

    def create_financial_year(self, data: Dict, business_id: Optional[int] = None) -> FinancialYear:
        # Expect keys: year, open, start_date (date), end_date (date)
        if business_id is not None:
            data["business_id"] = business_id
        return self.repo.create_financial_year(data)

    def update_financial_year(self, year_id: str | int, data: Dict) -> Optional[FinancialYear]:
        # Accept either numeric PK or year string (e.g. "2025-26").
        fy = None
        try:
            # if it's an integer-like value, try by id
            if isinstance(year_id, int) or (isinstance(year_id, str) and year_id.isdigit()):
                fy = self.repo.get_financial_year_by_id(int(year_id))
        except Exception:
            fy = None

        if not fy:
            # fallback: try lookup by year name
            fy = self.repo.get_financial_year_by_name(str(year_id))

        if not fy:
            return None

        return self.repo.update_financial_year(fy, data)

    # Salary Components
    def list_salary_components(self, business_id: Optional[int] = None) -> List[SalaryComponent]:
        return self.repo.list_salary_components(business_id=business_id)

    def create_salary_component(self, data: Dict, business_id: Optional[int] = None) -> SalaryComponent:
        if business_id is not None:
            data["business_id"] = business_id
        return self.repo.create_salary_component(data)

    def update_salary_component_category(self, component_id: int, category_field: str, value: bool, business_id: Optional[int] = None) -> Optional[SalaryComponent]:
        comp = self.repo.get_salary_component(component_id, business_id=business_id)
        if not comp:
            return None
        setattr(comp, category_field, value)
        return self.repo.update_salary_component(comp, {})

    # Tax Rates
    def list_tax_rates(self, financial_year: Optional[str] = None, business_id: Optional[int] = None) -> List[TaxRate]:
        return self.repo.list_tax_rates(financial_year, business_id=business_id)

    def get_available_tax_years(self, business_id: Optional[int] = None) -> List[str]:
        # Prefer business-specific years; if none found, fall back to global years
        years = self.repo.get_tax_years(business_id=business_id)
        if not years and business_id is not None:
            years = self.repo.get_tax_years(business_id=None)
        return years

    def create_tax_rate(self, data: Dict, business_id: Optional[int] = None) -> TaxRate:
        if business_id is not None:
            data["business_id"] = business_id
        return self.repo.create_tax_rate(data)

    # Initialize default data
    def initialize_default_data(self, business_id: Optional[int] = None) -> Dict:
        # skip if any FinancialYear exists
        existing = self.repo.list_financial_years()
        if existing:
            return {"message": "Data already initialized", "status": "skipped"}

        try:
            # TDS
            tds = TDSSetting(deduct_tds=False, business_id=business_id)

            # Financial Years
            fy1 = FinancialYear(year="2024-25", open=True, start_date=date(2024,4,1), end_date=date(2025,3,31), business_id=business_id)
            fy2 = FinancialYear(year="2025-26", open=False, start_date=date(2025,4,1), end_date=date(2026,3,31), business_id=business_id)

            # Salary components
            comps = [
                SalaryComponent(name="Basic Salary", alias="Basic", component_type="Fixed", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="House Rent Allowance", alias="HRA", component_type="Fixed", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Special Allowance", alias="SA", component_type="Fixed", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Medical Allowance", alias="MDA", component_type="Fixed", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Leave Encashment", alias="LE", component_type="Manual", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Bonus", alias="Bonus", component_type="Manual", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Conveyance Allowance", alias="CA", component_type="Fixed", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Telephone Allowance", alias="TA", component_type="Fixed", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Gratuity", alias="Gratuity", component_type="Manual", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Loan", alias="Loan", component_type="System", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Overtime (Hours)", alias="OT-H", component_type="System", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Overtime (Days)", alias="OT-D", component_type="System", unit_type="Paid Days", business_id=business_id),
                SalaryComponent(name="Retention Bonus", alias="RB", component_type="System", unit_type="Paid Days", business_id=business_id),
            ]

            # Tax rates
            tax_rates = [
                TaxRate(financial_year="2025-26", scheme="Old Scheme", category="< 60 Yr.", income_from=250001, fixed_tax=0, progressive_rate=5, business_id=business_id),
                TaxRate(financial_year="2025-26", scheme="Old Scheme", category="< 60 Yr.", income_from=500001, fixed_tax=12500, progressive_rate=20, business_id=business_id),
                TaxRate(financial_year="2025-26", scheme="New Scheme", category="All", income_from=800001, fixed_tax=20000, progressive_rate=10, business_id=business_id),
                TaxRate(financial_year="2025-26", scheme="New Scheme", category="All", income_from=1600001, fixed_tax=120000, progressive_rate=20, business_id=business_id),
            ]

            # Persist
            self.repo.db.add(tds)
            self.repo.add_many([fy1, fy2] + comps + tax_rates)

            return {
                "message": "Default data initialized successfully",
                "status": "success",
                "data": {
                    "financial_years": 2,
                    "salary_components": len(comps),
                    "tax_rates": len(tax_rates)
                }
            }

        except Exception:
            self.repo.db.rollback()
            raise
 
 
def get_tax_service(db: Session) -> TaxService:
     return TaxService(db)
