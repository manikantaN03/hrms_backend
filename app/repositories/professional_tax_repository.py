"""
Professional Tax Repository
Database operations for Professional Tax configuration
"""

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.repositories.base_repository import BaseRepository
from app.models.professional_tax import ProfessionalTaxSettings, PTComponentMapping, ProfessionalTaxRate


class ProfessionalTaxSettingsRepository(BaseRepository[ProfessionalTaxSettings]):
    def __init__(self, db: Session):
        super().__init__(ProfessionalTaxSettings, db)
    
    def get_by_business_id(self, business_id: int) -> Optional[ProfessionalTaxSettings]:
        """Get Professional Tax settings for a specific business with all relationships"""
        return (
            self.db.query(ProfessionalTaxSettings)
            .options(
                joinedload(ProfessionalTaxSettings.component_mappings),
                joinedload(ProfessionalTaxSettings.tax_rates)
            )
            .filter(ProfessionalTaxSettings.business_id == business_id)
            .first()
        )
    
    def create_with_relationships(self, data: dict) -> ProfessionalTaxSettings:
        """Create Professional Tax settings with components and rates"""
        component_mappings = data.pop("component_mappings", [])
        tax_rates = data.pop("tax_rates", [])
        
        # Create main settings
        pt_settings = ProfessionalTaxSettings(**data)
        self.db.add(pt_settings)
        self.db.flush()
        
        # Add component mappings
        for comp in component_mappings:
            mapping = PTComponentMapping(
                pt_settings_id=pt_settings.id,
                **comp
            )
            self.db.add(mapping)
        
        # Add tax rates
        for rate in tax_rates:
            tax_rate = ProfessionalTaxRate(
                pt_settings_id=pt_settings.id,
                **rate
            )
            self.db.add(tax_rate)
        
        self.db.commit()
        self.db.refresh(pt_settings)
        return pt_settings


class PTComponentMappingRepository(BaseRepository[PTComponentMapping]):
    def __init__(self, db: Session):
        super().__init__(PTComponentMapping, db)
    
    def get_by_settings_id(self, settings_id: int) -> List[PTComponentMapping]:
        """Get all component mappings for PT settings"""
        return (
            self.db.query(PTComponentMapping)
            .filter(PTComponentMapping.pt_settings_id == settings_id)
            .all()
        )
    
    def bulk_update_selection(self, component_ids: List[int], is_selected: bool) -> int:
        """Bulk update component selection status"""
        count = (
            self.db.query(PTComponentMapping)
            .filter(PTComponentMapping.id.in_(component_ids))
            .update({"is_selected": is_selected}, synchronize_session=False)
        )
        self.db.commit()
        return count


class ProfessionalTaxRateRepository(BaseRepository[ProfessionalTaxRate]):
    def __init__(self, db: Session):
        super().__init__(ProfessionalTaxRate, db)
    
    def get_by_settings_id(self, settings_id: int) -> List[ProfessionalTaxRate]:
        """Get all tax rates for PT settings"""
        return (
            self.db.query(ProfessionalTaxRate)
            .filter(ProfessionalTaxRate.pt_settings_id == settings_id)
            .order_by(
                ProfessionalTaxRate.state,
                ProfessionalTaxRate.effective_from.desc(),
                ProfessionalTaxRate.salary_above
            )
            .all()
        )
    
    def get_by_state(self, settings_id: int, state: str) -> List[ProfessionalTaxRate]:
        """Get tax rates for a specific state"""
        return (
            self.db.query(ProfessionalTaxRate)
            .filter(
                ProfessionalTaxRate.pt_settings_id == settings_id,
                ProfessionalTaxRate.state == state
            )
            .order_by(
                ProfessionalTaxRate.effective_from.desc(),
                ProfessionalTaxRate.salary_above
            )
            .all()
        )
    
    def get_applicable_rate(
        self,
        settings_id: int,
        state: str,
        salary: float,
        month: str = "All Months",
        gender: str = "All Genders",
        as_of_date: date = None
    ) -> Optional[ProfessionalTaxRate]:
        """Get the applicable tax rate for given parameters"""
        if as_of_date is None:
            as_of_date = date.today()
        
        # Try specific month and gender first
        rate = (
            self.db.query(ProfessionalTaxRate)
            .filter(
                ProfessionalTaxRate.pt_settings_id == settings_id,
                ProfessionalTaxRate.state == state,
                ProfessionalTaxRate.salary_above <= salary,
                ProfessionalTaxRate.month == month,
                ProfessionalTaxRate.gender == gender,
                ProfessionalTaxRate.effective_from <= as_of_date
            )
            .order_by(
                ProfessionalTaxRate.effective_from.desc(),
                ProfessionalTaxRate.salary_above.desc()
            )
            .first()
        )
        
        if rate:
            return rate
        
        # Fallback to All Months and All Genders
        return (
            self.db.query(ProfessionalTaxRate)
            .filter(
                ProfessionalTaxRate.pt_settings_id == settings_id,
                ProfessionalTaxRate.state == state,
                ProfessionalTaxRate.salary_above <= salary,
                ProfessionalTaxRate.month == "All Months",
                ProfessionalTaxRate.gender == "All Genders",
                ProfessionalTaxRate.effective_from <= as_of_date
            )
            .order_by(
                ProfessionalTaxRate.effective_from.desc(),
                ProfessionalTaxRate.salary_above.desc()
            )
            .first()
        )
