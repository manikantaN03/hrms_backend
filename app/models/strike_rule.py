from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base


class StrikeRule(Base):
    __tablename__ = "strike_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String, nullable=False)
    minutes = Column(Integer, default=0)
    strike = Column(String, default="None")
    full_day_only = Column(Boolean, default=False)
    time_adjustment = Column(String, default="No Adjustment")
    round_direction = Column(String, default="next")
    round_minutes = Column(Integer, default=5)

    # business scoping
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # relationship to Business
    business = relationship("Business", back_populates="strike_rules")

    __table_args__ = (
        Index("ix_strike_rules_business_type", "business_id", "rule_type"),
    )
  