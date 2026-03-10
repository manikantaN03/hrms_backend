from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class CostCenter(BaseModel):
    __tablename__ = "cost_centers"

    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    name = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)
    employees = Column(Integer, default=0)

    is_active = Column(Boolean, default=True, nullable=False)

    # Use back_populates to match Business.cost_centers and avoid backref conflicts
    business = relationship("Business", back_populates="cost_centers")
    
    # Employee Relationship
    employees_list = relationship("Employee", back_populates="cost_center")

    def to_dict(self):
        created = self.created_at.isoformat() if getattr(self, "created_at", None) is not None else None
        updated = self.updated_at.isoformat() if getattr(self, "updated_at", None) is not None else None

        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "isDefault": self.is_default,
            "employees": self.employees,
            "is_active": self.is_active,
            "created_at": created,
            "updated_at": updated,
        }

    @property
    def isDefault(self):
        return self.is_default
