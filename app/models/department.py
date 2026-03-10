from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class Department(BaseModel):
    __tablename__ = "departments"

    # ========================================================================
    # Foreign Key → Business
    # ========================================================================
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    # ========================================================================
    # Department Fields
    # ========================================================================
    name = Column(String(255), nullable=False)
    head = Column(String(255), nullable=False)
    deputy_head = Column(String(255), nullable=True)

    is_default = Column(Boolean, default=False)
    employees = Column(Integer, default=0)

    is_active = Column(Boolean, default=True, nullable=False)

    # ========================================================================
    # Relationship → Business (aligns with Business.departments back_populates)
    # ========================================================================
    business = relationship("Business", back_populates="departments")
    
    # ========================================================================
    # Relationship → Employees
    # ========================================================================
    employees_list = relationship("Employee", back_populates="department")

    # ========================================================================
    # Dictionary Response Helper (Same as CostCenter)
    # ========================================================================
    def to_dict(self):
        created = (
            self.created_at.isoformat()
            if getattr(self, "created_at", None) is not None
            else None
        )
        updated = (
            self.updated_at.isoformat()
            if getattr(self, "updated_at", None) is not None
            else None
        )

        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "head": self.head,
            "deputy_head": self.deputy_head,
            "isDefault": self.is_default,
            "employees": self.employees,
            "is_active": self.is_active,
            "created_at": created,
            "updated_at": updated,
        }

    # ========================================================================
    # Property Alias (Same as CostCenter)
    # ========================================================================
    @property
    def isDefault(self):
        return self.is_default

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', business_id={self.business_id})>"
