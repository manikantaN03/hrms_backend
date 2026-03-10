from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Grade(BaseModel):
    __tablename__ = "grades"
    
    __table_args__ = (
        UniqueConstraint('business_id', 'name', name='uq_grade_business_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    employees = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # FK -> Business
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationship to Business
    business = relationship(
        "Business",
        back_populates="grades",
        foreign_keys=[business_id],
        passive_deletes=True,
    )
    
    # Employee Relationship
    employees_list = relationship("Employee", back_populates="grade")
