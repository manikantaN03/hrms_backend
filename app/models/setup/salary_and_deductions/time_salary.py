from sqlalchemy import Column, Integer, String, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class TimeSalaryRule(Base):
    __tablename__ = "time_salary_rules"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 Business Relationship (Same Style as GatekeeperDevice)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Existing Foreign Key
    component_id = Column(
        Integer,
        ForeignKey("salary_components.id", ondelete="CASCADE"),
        nullable=False
    )

    attendance = Column(String(50), nullable=False)
    shift = Column(String(50), nullable=False)

    early_coming_minutes = Column(Integer, nullable=False)
    in_office_time = Column(Time, nullable=False)
    out_office_time = Column(Time, nullable=False)

    lunch_always_minutes = Column(Integer, nullable=False)
    lunch_working_minutes = Column(Integer, nullable=False)

    late_going_minutes = Column(Integer, nullable=False)
    limit_shift_hours = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    component = relationship("SalaryComponent", backref="time_salary_rules")

    business = relationship(
        "Business",
        back_populates="time_salary_rules"  # You must add this in Business model
    )
