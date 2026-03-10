"""
EPF Settings Repository
Database operations for EPF configuration
"""

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.repositories.base_repository import BaseRepository
from app.models.epf_settings import EPFSettings, EPFComponentMapping, EPFRateChange


class EPFSettingsRepository(BaseRepository[EPFSettings]):
    def __init__(self, db: Session):
        super().__init__(EPFSettings, db)
    
    def get_by_business_id(self, business_id: int) -> Optional[EPFSettings]:
        """Get EPF settings for a specific business with all relationships"""
        return (
            self.db.query(EPFSettings)
            .options(
                joinedload(EPFSettings.component_mappings),
                joinedload(EPFSettings.rate_changes)
            )
            .filter(EPFSettings.business_id == business_id)
            .first()
        )
    
    def create_with_relationships(self, data: dict) -> EPFSettings:
        """Create EPF settings with components and rates"""
        component_mappings = data.pop("component_mappings", [])
        rate_changes = data.pop("rate_changes", [])
        
        # Create main settings
        epf_settings = EPFSettings(**data)
        self.db.add(epf_settings)
        self.db.flush()
        
        # Add component mappings
        for comp in component_mappings:
            mapping = EPFComponentMapping(
                epf_settings_id=epf_settings.id,
                **comp
            )
            self.db.add(mapping)
        
        # Add rate changes
        for rate in rate_changes:
            rate_change = EPFRateChange(
                epf_settings_id=epf_settings.id,
                **rate
            )
            self.db.add(rate_change)
        
        self.db.commit()
        self.db.refresh(epf_settings)
        return epf_settings


class EPFComponentMappingRepository(BaseRepository[EPFComponentMapping]):
    def __init__(self, db: Session):
        super().__init__(EPFComponentMapping, db)
    
    def get_by_settings_id(self, settings_id: int) -> List[EPFComponentMapping]:
        """Get all component mappings for EPF settings"""
        return (
            self.db.query(EPFComponentMapping)
            .filter(EPFComponentMapping.epf_settings_id == settings_id)
            .all()
        )
    
    def bulk_update_selection(self, component_ids: List[int], is_selected: bool) -> int:
        """Bulk update component selection status"""
        count = (
            self.db.query(EPFComponentMapping)
            .filter(EPFComponentMapping.id.in_(component_ids))
            .update({"is_selected": is_selected}, synchronize_session=False)
        )
        self.db.commit()
        return count


class EPFRateChangeRepository(BaseRepository[EPFRateChange]):
    def __init__(self, db: Session):
        super().__init__(EPFRateChange, db)
    
    def get_by_settings_id(self, settings_id: int) -> List[EPFRateChange]:
        """Get all rate changes for EPF settings"""
        return (
            self.db.query(EPFRateChange)
            .filter(EPFRateChange.epf_settings_id == settings_id)
            .order_by(EPFRateChange.effective_from.desc())
            .all()
        )
    
    def get_active_rate(self, settings_id: int, as_of_date: date = None) -> Optional[EPFRateChange]:
        """Get the active rate for a specific date"""
        if as_of_date is None:
            as_of_date = date.today()
        
        return (
            self.db.query(EPFRateChange)
            .filter(
                EPFRateChange.epf_settings_id == settings_id,
                EPFRateChange.status == "Enabled",
                EPFRateChange.effective_from <= as_of_date
            )
            .order_by(EPFRateChange.effective_from.desc())
            .first()
        )
