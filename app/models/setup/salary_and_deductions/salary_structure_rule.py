from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float
from sqlalchemy.orm import relationship
from app.models.base import Base


class SalaryStructureRule(Base):
    __tablename__ = "salary_structure_rules"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Each rule belongs to a specific business
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 🔹 Parent salary structure
    structure_id = Column(
        Integer,
        ForeignKey("salary_structures.id", ondelete="CASCADE"),
        nullable=False
    )

    # 🔹 Component or deduction reference
    component_id = Column(Integer, nullable=False)

    # 🔹 "Fixed" or "Percentage"
    calculation_type = Column(String(20), nullable=False)

    # 🔹 Amount or %
    value = Column(Float, nullable=False)

    # 🔹 Ordering position
    sequence = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 🔄 Relationship to SalaryStructure
    structure = relationship("SalaryStructure", back_populates="rules")

    # 🔄 Relationship back to Business (optional but recommended)
    business = relationship("Business", back_populates="salary_structure_rules")
