"""
ESI Settings Repository
Database operations for ESI configuration
"""

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.repositories.base_repository import BaseRepository
from app.models.esi_settings import ESISettings, ESIComponentMapping, ESIRateChange


class ESISettingsRepository(BaseRepository[ESISettings]):
    def __init__(self, db: Session):
        super().__init__(ESISettings, db)
    
    def get_by_business_id(self, business_id: int) -> Optional[ESISettings]:
        """Get ESI settings for a specific business with all relationships"""
        return (
            self.db.query(ESISettings)
            .options(
                joinedload(ESISettings.component_mappings),
                joinedload(ESISettings.rate_changes)
            )
            .filter(ESISettings.business_id == business_id)
            .first()
        )
    
    def create_with_relationships(self, data: dict) -> ESISettings:
        """Create ESI settings with components and rates"""
        component_mappings = data.pop("component_mappings", [])
        rate_changes = data.pop("rate_changes", [])
        
        # Create main settings
        esi_settings = ESISettings(**data)
        self.db.add(esi_settings)
        self.db.flush()
        
        # Add component mappings
        for comp in component_mappings:
            mapping = ESIComponentMapping(
                esi_settings_id=esi_settings.id,
                **comp
            )
            self.db.add(mapping)
        
        # Add rate changes
        for rate in rate_changes:
            rate_change = ESIRateChange(
                esi_settings_id=esi_settings.id,
                **rate
            )
            self.db.add(rate_change)
        
        self.db.commit()
        self.db.refresh(esi_settings)
        return esi_settings


class ESIComponentMappingRepository(BaseRepository[ESIComponentMapping]):
    def __init__(self, db: Session):
        super().__init__(ESIComponentMapping, db)
    
    def get_by_settings_id(self, settings_id: int) -> List[ESIComponentMapping]:
        """Get all component mappings for ESI settings"""
        return (
            self.db.query(ESIComponentMapping)
            .filter(ESIComponentMapping.esi_settings_id == settings_id)
            .all()
        )
    
    def bulk_update_selection(self, component_ids: List[int], is_selected: bool) -> int:
        """Bulk update component selection status"""
        count = (
            self.db.query(ESIComponentMapping)
            .filter(ESIComponentMapping.id.in_(component_ids))
            .update({"is_selected": is_selected}, synchronize_session=False)
        )
        self.db.commit()
        return count


class ESIRateChangeRepository(BaseRepository[ESIRateChange]):
    def __init__(self, db: Session):
        super().__init__(ESIRateChange, db)
    
    def get_by_settings_id(self, settings_id: int) -> List[ESIRateChange]:
        """Get all rate changes for ESI settings"""
        return (
            self.db.query(ESIRateChange)
            .filter(ESIRateChange.esi_settings_id == settings_id)
            .order_by(ESIRateChange.effective_from.desc())
            .all()
        )
    
    def get_active_rate(self, settings_id: int, as_of_date: date = None) -> Optional[ESIRateChange]:
        """Get the active rate for a specific date"""
        if as_of_date is None:
            as_of_date = date.today()
        
        return (
            self.db.query(ESIRateChange)
            .filter(
                ESIRateChange.esi_settings_id == settings_id,
                ESIRateChange.status == "Enabled",
                ESIRateChange.effective_from <= as_of_date
            )
            .order_by(ESIRateChange.effective_from.desc())
            .first()
        )
