from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.attendance_settings import AttendanceSettings
from app.schemas.attendance_settings import AttendanceSettingsUpdate

class AttendanceSettingsService:

    @staticmethod
    def get_settings(business_id: int, db: Session):
        settings = db.query(AttendanceSettings).filter_by(business_id=business_id).first()

        if not settings:
            # Create default settings if none exist
            settings = AttendanceSettings(
                business_id=business_id,
                default_attendance="PRESENT",
                mark_out_on_punch=False,
                punch_count=2,
                enable_manual_attendance=False,
                no_holiday_if_absent=False,
                apply_holiday_one_side=False,
                apply_holiday_either=False,
                no_week_off_if_absent=False,
                apply_week_off_one_side=False,
                apply_week_off_either=False
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return settings

    @staticmethod
    def update_settings(business_id: int, update_data: AttendanceSettingsUpdate, db: Session):
        settings = db.query(AttendanceSettings).filter_by(business_id=business_id).first()

        if not settings:
            # Create settings if they don't exist
            settings = AttendanceSettings(business_id=business_id)
            db.add(settings)

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(settings, key, value)

        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def reset_settings(business_id: int, db: Session):
        settings = db.query(AttendanceSettings).filter_by(business_id=business_id).first()

        if not settings:
            # Create default settings if none exist
            settings = AttendanceSettings(business_id=business_id)
            db.add(settings)

        # Reset to default values
        settings.default_attendance = "PRESENT"
        settings.mark_out_on_punch = False
        settings.punch_count = 2
        settings.enable_manual_attendance = False
        settings.no_holiday_if_absent = False
        settings.apply_holiday_one_side = False
        settings.apply_holiday_either = False
        settings.no_week_off_if_absent = False
        settings.apply_week_off_one_side = False
        settings.apply_week_off_either = False

        db.commit()
        db.refresh(settings)
        return settings