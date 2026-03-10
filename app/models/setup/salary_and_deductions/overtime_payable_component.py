# app/models/setup/salary_and_deductions/overtime_payable_component.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class OvertimePolicyPayableComponent(Base):
    """
    Junction table linking overtime policies to salary components
    that are payable for overtime calculation
    """
    __tablename__ = "overtime_policy_payable_components"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    policy_id = Column(
        Integer,
        ForeignKey("overtime_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    component_id = Column(
        Integer,
        ForeignKey("salary_components.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Status
    is_payable = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    policy = relationship("OvertimePolicy", backref="payable_components")
    component = relationship("SalaryComponent", backref="overtime_policies")
    business = relationship("Business")

    def __repr__(self):
        return f"<OvertimePolicyPayableComponent policy_id={self.policy_id} component_id={self.component_id}>"
