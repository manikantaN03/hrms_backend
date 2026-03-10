"""
Employee Leave Policy Assignment Model
Many-to-many relationship between employees and leave policies
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class EmployeeLeavePolicy(Base):
    __tablename__ = "employee_leave_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_policy_id = Column(Integer, ForeignKey("leave_policies.id"), nullable=False, index=True)
    
    # Assignment details
    is_active = Column(Boolean, default=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="leave_policy_assignments")
    leave_policy = relationship("LeavePolicy")
    assigned_by_user = relationship("User")
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<EmployeeLeavePolicy(employee_id={self.employee_id}, leave_policy_id={self.leave_policy_id})>"