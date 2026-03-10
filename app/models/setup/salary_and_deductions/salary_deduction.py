from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class SalaryDeduction(Base):
    __tablename__ = "salary_deductions"
    __table_args__ = (
        UniqueConstraint('business_id', 'code', name='uq_salary_deduction_business_code'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 Business scope added
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # reverse relation (one business → many deductions)
    business = relationship("Business", back_populates="salary_deductions")

    # Fields
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)  # Removed unique=True, using composite unique constraint
    type = Column(String(50), nullable=False, default="Fixed")

    active = Column(Boolean, default=True)
    payback_on_exit = Column(Boolean, default=False)

    # required to avoid NOT NULL DB constraint error
    status = Column(String(20), nullable=False, default="Active")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
