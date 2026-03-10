from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.repositories.lwf_repository import LWFRepository
 
 
class LWFService:
 
    def __init__(self):

        self.repo = LWFRepository()

    # ----------------------------
    # Settings
    # ----------------------------

    def get_or_create_settings(self, db: Session, business_id: int):
        """Get LWF settings or create if not exists"""
        return self.repo.get_or_create_settings(db, business_id)

    def update_settings(self, db: Session, business_id: int, data):
        """Update LWF settings"""
        settings = self.repo.update_settings(db, business_id, data)
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LWF settings not found for the given business",
            )
        return settings
 
    # ----------------------------

    # Components

    # ----------------------------

    def get_lwf_components(self, db: Session, business_id: int):

        return self.repo.get_lwf_components(db, business_id)
 
    def toggle_lwf_component(

        self,

        db: Session,

        component_id: int,

        is_lwf_applicable: bool,

        business_id: int,

    ):

        component = self.repo.toggle_lwf_component(
            db, component_id, is_lwf_applicable, business_id
        )

        if not component:
            # If the component wasn't found for the business, return 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary component not found for the given business",
            )

        return component
 
    # ----------------------------

    # Rates

    # ----------------------------

    def create_rate(self, db: Session, data):

        return self.repo.create_rate(db, data)
 
    def list_rates(self, db: Session):

        return self.repo.list_rates(db)


def get_lwf_service() -> LWFService:
    """Dependency factory for FastAPI to provide a `LWFService` instance."""
    return LWFService()

 