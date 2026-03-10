from sqlalchemy.orm import Session

from app.models.lwf_models import LWFRate, LWFSettings
from app.models.setup.salary_and_deductions.salary_component import SalaryComponent
 
 
class LWFRepository:

    # ----------------------------
    # Settings
    # ----------------------------

    def get_or_create_settings(self, db: Session, business_id: int):
        """Get LWF settings or create if not exists"""
        settings = db.query(LWFSettings).filter(
            LWFSettings.business_id == business_id
        ).first()
        
        if not settings:
            settings = LWFSettings(
                business_id=business_id,
                is_enabled=False
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings

    def update_settings(self, db: Session, business_id: int, data):
        """Update LWF settings"""
        settings = db.query(LWFSettings).filter(
            LWFSettings.business_id == business_id
        ).first()
        
        if not settings:
            return None
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(settings, key, value)
        
        db.commit()
        db.refresh(settings)
        return settings
 
    # ----------------------------

    # Salary Components (LWF)

    # ----------------------------

    def get_lwf_components(self, db: Session, business_id: int):

        # Return all salary components for the business so the caller
        # can inspect the `is_lwf_applicable` flag and render checkboxes.
        return db.query(SalaryComponent).filter(
            SalaryComponent.business_id == business_id
        ).all()
 
    def toggle_lwf_component(

        self,

        db: Session,

        component_id: int,

        is_lwf_applicable: bool,

        business_id: int,

    ):

        # Ensure the component belongs to the given business before toggling
        component = db.query(SalaryComponent).filter(
            SalaryComponent.id == component_id,
            SalaryComponent.business_id == business_id,
        ).first()

        if not component:
            return None

        component.is_lwf_applicable = is_lwf_applicable
        db.commit()
        db.refresh(component)

        return component
 
    # ----------------------------

    # LWF RATES

    # ----------------------------

    def create_rate(self, db: Session, data):

        rate = LWFRate(**data.dict())

        db.add(rate)

        db.commit()

        db.refresh(rate)

        return rate
 
    def list_rates(self, db: Session):

        return db.query(LWFRate).order_by(

            LWFRate.effective_from.desc()

        ).all()

 