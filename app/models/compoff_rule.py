from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint, Index
from datetime import datetime
from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class CompOffRule(Base):
    __tablename__ = "compoff_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=True)  # weekly_offs / holidays / custom
    max_days = Column(Integer, default=0)
    expiry_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    auto_grant_enabled = Column(Boolean, default=False)
    half_day_hours = Column(Integer, default=0)
    half_day_mins = Column(Integer, default=0)
    full_day_hours = Column(Integer, default=0)
    full_day_mins = Column(Integer, default=0)
    grant_type = Column(String, default="grant_comp_off")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # business scoping
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # relationship to Business
    business = relationship("Business", back_populates="compoff_rules")

    __table_args__ = (
        UniqueConstraint("name", "business_id", "rule_type", name="uq_compoff_name_business_type"),
        Index("ix_compoff_business_type", "business_id", "rule_type"),
    )
  

