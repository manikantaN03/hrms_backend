from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    __table_args__ = (
        UniqueConstraint('business_id', 'name', name='uq_salary_structure_business_name'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 NEW FIELD — Every structure belongs to a Business
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = Column(String(120), nullable=False)  # Removed unique=True, using composite unique constraint
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 🔄 Relationship to SalaryStructureRule
    rules = relationship(
        "SalaryStructureRule",
        back_populates="structure",
        cascade="all, delete-orphan"
    )

    # 🔄 Relationship BACK to Business
    business = relationship(
        "Business",
        back_populates="salary_structures"
    )
