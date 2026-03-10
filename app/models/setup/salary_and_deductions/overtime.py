# app/models/setup/salary_and_deductions/overtime.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


# ======================================================================
#                           OVERTIME POLICY
# ======================================================================

class OvertimePolicy(Base):
    __tablename__ = "overtime_policies"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Business Relationship (same pattern as Gatekeeper)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Original fields
    policy_name = Column(String(255), nullable=False, unique=True)

    # Relationship → OvertimeRule
    rules = relationship(
        "OvertimeRule",
        back_populates="policy",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Reverse relationship back to Business
    business = relationship("Business", back_populates="overtime_policies")

    def __repr__(self):
        return f"<OvertimePolicy id={self.id} policy_name='{self.policy_name}'>"


# ======================================================================
#                           OVERTIME RULE
# ======================================================================

class OvertimeRule(Base):
    __tablename__ = "overtime_rules"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Business Relation
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key → Policy
    policy_id = Column(
        Integer,
        ForeignKey("overtime_policies.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationship back to Policy
    policy = relationship("OvertimePolicy", back_populates="rules")

    # Original rule fields
    attendance_type = Column(String(50), nullable=False)

    time_basis = Column(String(50), nullable=False)
    from_hrs = Column(Integer, nullable=False)
    from_mins = Column(Integer, nullable=False)
    to_hrs = Column(Integer, nullable=False)
    to_mins = Column(Integer, nullable=False)

    calculation_method = Column(String(50), nullable=False)
    multiplier = Column(Integer, nullable=False)

    overtime_mins_type = Column(String(50), nullable=False)
    fixed_mins = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Reverse relationship back to Business
    business = relationship("Business", back_populates="overtime_rules")

    def __repr__(self):
        return f"<OvertimeRule id={self.id} policy_id={self.policy_id}>"
