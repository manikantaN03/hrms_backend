from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class Location(BaseModel):
    __tablename__ = "locations"

    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)

    location_head = Column(String(255), nullable=True)   
    deputy_head = Column(String(255), nullable=True)

    employees = Column(Integer, default=0)

    is_default = Column(Boolean, default=False)
    map_url = Column(String(500), nullable=True)

    qr_code_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    business = relationship("Business", back_populates="locations")
    
    # Employee Relationship
    employees_list = relationship("Employee", back_populates="location")

    # relationship to Holiday (matches Holiday.location back_populates)
    holidays = relationship("Holiday", back_populates="location", cascade="all, delete-orphan")

    def to_dict(self):
        created = self.created_at.isoformat() if getattr(self, "created_at", None) is not None else None
        updated = self.updated_at.isoformat() if getattr(self, "updated_at", None) is not None else None

        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "state": self.state,
            "locationHead": self.location_head,
            "deputyHead": self.deputy_head,
            "employees": self.employees,
            "isDefault": self.is_default,
            "mapUrl": self.map_url,
            "qrCodeUrl": self.qr_code_url,
            "is_active": self.is_active,
            "created_at": created,
            "updated_at": updated,
        }
