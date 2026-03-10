from sqlalchemy.orm import Session
from app.models.setup.salary_and_deductions.salary_component import SalaryComponent, UnitTypeEnum
from app.schemas.setup.salary_and_deductions.salary_component import SalaryComponentCreate, SalaryComponentUpdate


class SalaryComponentRepository:

    def list(self, db: Session, business_id: int):
        return (
            db.query(SalaryComponent)
            .filter(SalaryComponent.business_id == business_id)
            .all()
        )

    def get(self, db: Session, component_id: int):
        return (
            db.query(SalaryComponent)
            .filter(SalaryComponent.id == component_id)
            .first()
        )

    def create(self, db: Session, data: SalaryComponentCreate):
        # Normalize enum -> store the enum value (string) in the model
        unit_type_value = data.unit_type.value if hasattr(data.unit_type, "value") else data.unit_type
        component_type_value = data.component_type.value if hasattr(data, "component_type") and hasattr(data.component_type, "value") else getattr(data, "component_type", None)

        obj = SalaryComponent(
            business_id=data.business_id,
            name=data.name,
            alias=data.alias,
            component_type=component_type_value,
            unit_type=unit_type_value,

            exclude_holidays=data.exclude_holidays,
            exclude_weekoffs=data.exclude_weekoffs,
            is_active=data.active,
            exclude_from_gross=data.exclude_from_gross,
            hide_in_ctc=data.hide_in_ctc_reports,
            not_payable=data.not_payable,
        )

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, db_obj: SalaryComponent, data: SalaryComponentUpdate):
        update_data = data.dict(exclude_unset=True)

        # ❌ business_id should never be updated — ensure safety
        update_data.pop("business_id", None)

        # Map API/schema field names to model column names
        if "active" in update_data:
            update_data["is_active"] = update_data.pop("active")
        if "hide_in_ctc_reports" in update_data:
            update_data["hide_in_ctc"] = update_data.pop("hide_in_ctc_reports")

        # Enum conversion: store enum value string
        if "unit_type" in update_data and update_data["unit_type"] is not None:
            ut = update_data["unit_type"]
            update_data["unit_type"] = ut.value if hasattr(ut, "value") else ut
        if "component_type" in update_data and update_data["component_type"] is not None:
            ct = update_data["component_type"]
            update_data["component_type"] = ct.value if hasattr(ct, "value") else ct

        # Apply updates
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: SalaryComponent):
        db.delete(db_obj)
        db.commit()
        return True

    def check_exists(self, db: Session, alias: str, business_id: int, exclude_id: int = None):
        """Check if a salary component with the given alias exists for the business"""
        query = (
            db.query(SalaryComponent)
            .filter(
                SalaryComponent.alias == alias,
                SalaryComponent.business_id == business_id  # ✅ scoped to business
            )
        )
        
        # Exclude current component when updating
        if exclude_id:
            query = query.filter(SalaryComponent.id != exclude_id)
        
        return query.first()
