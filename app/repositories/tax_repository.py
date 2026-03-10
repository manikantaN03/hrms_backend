from typing import List, Optional, Dict, Any
from datetime import date

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from ..models.tax_models import (
    TDSSetting,
    FinancialYear,
    TaxRate,
)
from ..models.setup.salary_and_deductions.salary_component import SalaryComponent


class TaxRepository:
    def __init__(self, db: Session):
        self.db = db

    # TDS Setting
    def get_tds_setting(self, business_id: Optional[int] = None) -> Optional[TDSSetting]:
        q = self.db.query(TDSSetting)
        if business_id is not None:
            q = q.filter(TDSSetting.business_id == business_id)
        return q.first()

    def create_tds_setting(self, deduct_tds: bool, business_id: Optional[int] = None) -> TDSSetting:
        s = TDSSetting(deduct_tds=deduct_tds, business_id=business_id)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def update_tds_setting(self, setting: TDSSetting, deduct_tds: bool) -> TDSSetting:
        setting.deduct_tds = deduct_tds
        setting.updated_at = date.today()
        self.db.commit()
        self.db.refresh(setting)
        return setting

    # Financial Years
    def list_financial_years(self) -> List[FinancialYear]:
        return self.db.query(FinancialYear).order_by(FinancialYear.year.desc()).all()

    def get_financial_year_by_id(self, year_id: int) -> Optional[FinancialYear]:
        return self.db.query(FinancialYear).filter(FinancialYear.id == year_id).first()

    def get_financial_year_by_name(self, year: str) -> Optional[FinancialYear]:
        return self.db.query(FinancialYear).filter(FinancialYear.year == year).first()

    def create_financial_year(self, data: Dict) -> FinancialYear:
        fy = FinancialYear(**data)
        self.db.add(fy)
        self.db.commit()
        self.db.refresh(fy)
        return fy

    def update_financial_year(self, fy: FinancialYear, data: Dict) -> FinancialYear:
        for k, v in data.items():
            setattr(fy, k, v)
        self.db.commit()
        self.db.refresh(fy)
        return fy

    # Salary Components
    def list_salary_components(self, business_id: Optional[int] = None) -> List[SalaryComponent]:
        q = self.db.query(SalaryComponent)
        if business_id is not None:
            q = q.filter(SalaryComponent.business_id == business_id)
        return q.order_by(SalaryComponent.id).all()

    def get_salary_component(self, component_id: int, business_id: Optional[int] = None) -> Optional[SalaryComponent]:
        q = self.db.query(SalaryComponent).filter(SalaryComponent.id == component_id)
        if business_id is not None:
            q = q.filter(SalaryComponent.business_id == business_id)
        return q.first()

    def get_salary_component_by_name(self, name: str, business_id: Optional[int] = None) -> Optional[SalaryComponent]:
        q = self.db.query(SalaryComponent).filter(SalaryComponent.name == name)
        if business_id is not None:
            q = q.filter(SalaryComponent.business_id == business_id)
        return q.first()

    def create_salary_component(self, data: Dict) -> SalaryComponent:
        # expect data may contain 'business_id'
        # Ensure DB NOT NULL columns have sensible defaults when not provided
        if data.get('alias') is None:
            # default alias to name when not provided
            data['alias'] = data.get('name')
        if data.get('unit_type') is None:
            # unit_type is non-nullable in the model; default to a valid enum value
            data['unit_type'] = 'Paid Days'
        comp = SalaryComponent(**data)
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def update_salary_component(self, comp: SalaryComponent, data: Dict) -> SalaryComponent:
        for k, v in data.items():
            setattr(comp, k, v)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    # Tax Rates
    def list_tax_rates(self, financial_year: Optional[str] = None, business_id: Optional[int] = None) -> List[TaxRate]:
        q = self.db.query(TaxRate)
        if financial_year:
            q = q.filter(TaxRate.financial_year == financial_year)

        if business_id is not None:
            items = q.filter(TaxRate.business_id == business_id).order_by(TaxRate.scheme, TaxRate.income_from).all()
            if items:
                return items

        return q.order_by(TaxRate.scheme, TaxRate.income_from).all()

    def get_tax_years(self, business_id: Optional[int] = None) -> List[str]:
        q = self.db.query(TaxRate.financial_year)
        if business_id is not None:
            q = q.filter(TaxRate.business_id == business_id)
        rows = q.distinct().all()
        return [r[0] for r in rows]

    def create_tax_rate(self, data: Dict) -> TaxRate:
        # expect data may include 'business_id'
        tr = TaxRate(**data)
        self.db.add(tr)
        self.db.commit()
        self.db.refresh(tr)
        return tr

    # Bulk helpers for initialization
    def add_many(self, instances: List):
        self.db.add_all(instances)
        self.db.commit()
