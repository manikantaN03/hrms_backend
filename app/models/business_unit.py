# app/models/business_unit.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class BusinessUnit(BaseModel):
    """
    Business Unit Model

    - Belongs to a Business (company)
    - Used for divisions like "Software Division", "Hardware Division", etc.
    """

    __tablename__ = "business_units"

    # FK to Business
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # Core information (matches your React modal)
    name = Column(String(255), nullable=False)          # Name of Unit
    report_title = Column(String(255), nullable=False)  # Report Title
    is_default = Column(Boolean, nullable=False, default=False)
    employees = Column(Integer, default=0)

    # Branding images (for ImageBanner) - Changed to Text to support base64 images
    header_image_url = Column(Text, nullable=True)
    footer_image_url = Column(Text, nullable=True)

    # Active flag (default: active)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship back to Business
    business = relationship(
        "Business",
        back_populates="business_units",
    )

    def __repr__(self):
        return f"<BusinessUnit(id={self.id}, name='{self.name}', business_id={self.business_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "report_title": self.report_title,
            "is_default": self.is_default,
            "header_image_url": self.header_image_url,
            "footer_image_url": self.footer_image_url,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
