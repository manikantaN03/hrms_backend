from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class StrikeAdjustment(Base):
    __tablename__ = "strike_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    strike_type = Column(String(50), nullable=False)
    strike_range_from = Column(Integer, nullable=False)
    strike_range_to = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # business scoping
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # Relationship to Business
    business = relationship("Business", back_populates="strike_adjustments")

    __table_args__ = (
        Index("ix_strike_adjustments_business_type", "business_id", "strike_type"),
    )
