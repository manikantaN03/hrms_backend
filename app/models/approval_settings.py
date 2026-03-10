from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class ApprovalSettings(BaseModel):
    __tablename__ = "approval_settings"

    # ========================================================================
    # Business Link
    # ========================================================================
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, unique=True)

    # ========================================================================
    # Leave Requests
    # ========================================================================
    leave_request = Column(String(50), default="manager")

    # ========================================================================
    # Missed Punch
    # ========================================================================
    missed_punch = Column(String(50), default="disabled")
    missed_punch_days = Column(Integer, default=7)

    # ========================================================================
    # Comp Off
    # ========================================================================
    comp_off = Column(String(50), default="disabled")
    comp_off_lapse_days = Column(Integer, default=0)
    lapse_monthly = Column(Boolean, default=False)

    # ========================================================================
    # Remote Punch
    # ========================================================================
    remote_punch = Column(Boolean, default=False)
    remote_location = Column(Boolean, default=False)

    # ========================================================================
    # Selfie Punch
    # ========================================================================
    selfie_punch = Column(Boolean, default=False)
    selfie_location = Column(Boolean, default=False)

    # ========================================================================
    # Time Relaxation
    # ========================================================================
    time_relaxation = Column(String(50), default="disabled")
    time_requests = Column(Integer, default=5)
    time_hours = Column(Integer, default=10)

    # ========================================================================
    # Travel Reimbursement
    # ========================================================================
    travel_calc = Column(String(50), default="calculated")

    # ========================================================================
    # Request Approval Settings - Shift Change Request
    # ========================================================================
    shift_change_level1 = Column(String(50), default="")
    shift_change_level2 = Column(String(50), default="")
    shift_change_level3 = Column(String(50), default="")
    shift_change_approvals_required = Column(Integer, default=0)

    # ========================================================================
    # Request Approval Settings - Week Off Change Request
    # ========================================================================
    weekoff_change_level1 = Column(String(50), default="")
    weekoff_change_level2 = Column(String(50), default="")
    weekoff_change_level3 = Column(String(50), default="")
    weekoff_change_approvals_required = Column(Integer, default=0)

    # ========================================================================
    # Status
    # ========================================================================
    is_active = Column(Boolean, default=True, nullable=False)

    # ========================================================================
    # Relationship
    # ========================================================================
    # Use back_populates to match Business.approval_settings and avoid backref conflicts
    business = relationship("Business", back_populates="approval_settings")

    def to_dict(self):
        created = self.created_at.isoformat() if self.created_at else None
        updated = self.updated_at.isoformat() if self.updated_at else None

        return {
            "id": self.id,
            "business_id": self.business_id,
            "leave_request": self.leave_request,
            "missed_punch": self.missed_punch,
            "missed_punch_days": self.missed_punch_days,
            "comp_off": self.comp_off,
            "comp_off_lapse_days": self.comp_off_lapse_days,
            "lapse_monthly": self.lapse_monthly,
            "remote_punch": self.remote_punch,
            "remote_location": self.remote_location,
            "selfie_punch": self.selfie_punch,
            "selfie_location": self.selfie_location,
            "time_relaxation": self.time_relaxation,
            "time_requests": self.time_requests,
            "time_hours": self.time_hours,
            "travel_calc": self.travel_calc,
            "shift_change_level1": self.shift_change_level1,
            "shift_change_level2": self.shift_change_level2,
            "shift_change_level3": self.shift_change_level3,
            "shift_change_approvals_required": self.shift_change_approvals_required,
            "weekoff_change_level1": self.weekoff_change_level1,
            "weekoff_change_level2": self.weekoff_change_level2,
            "weekoff_change_level3": self.weekoff_change_level3,
            "weekoff_change_approvals_required": self.weekoff_change_approvals_required,
            "is_active": self.is_active,
            "created_at": created,
            "updated_at": updated,
        }
