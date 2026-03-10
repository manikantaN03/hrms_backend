from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Designation(BaseModel):
    __tablename__ = "designations"
    
    __table_args__ = (
        UniqueConstraint('business_id', 'name', name='uq_designation_business_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    default = Column(Boolean, nullable=False, default=False)
    employees = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # Business Relationship (each designation belongs to a business)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    business = relationship(
        "Business",
        back_populates="designations",
        passive_deletes=True
    )
    
    # Employee Relationship
    employees_list = relationship("Employee", back_populates="designation")
