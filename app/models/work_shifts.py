from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class WorkShift(BaseModel):
    __tablename__ = "work_shifts"
    
    __table_args__ = (
        UniqueConstraint('business_id', 'code', name='uq_workshift_business_code'),
    )

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    payable_hrs = Column(String(20), nullable=False, default="8:00")
    rules = Column(Integer, nullable=False, default=0)
    default = Column(Boolean, nullable=False, default=False)
    timing = Column(String(255), nullable=True)
    start_buffer_hours = Column(Integer, nullable=False, default=0)
    end_buffer_hours = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # Business scoping
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    business = relationship(
        "Business",
        back_populates="work_shifts",
        passive_deletes=True
    )
    default_for_policies = relationship(
        "ShiftPolicy",
        back_populates="default_shift",
        foreign_keys="ShiftPolicy.default_shift_id",
    )
