"""
User Preferences Model
Stores user notification and communication preferences
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from .base import Base


class UserPreferences(Base):
    """
    User preferences for notifications and communication settings
    """
    
    __tablename__ = "user_preferences"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Communication Preferences
    send_email_alerts = Column(Boolean, default=True, nullable=False)
    send_sms_alerts = Column(Boolean, default=False, nullable=False)
    send_browser_push_alerts = Column(Boolean, default=False, nullable=False)
    
    # Alert Preferences
    daily_attendance_summary = Column(Boolean, default=True, nullable=False)
    onboarding_form_updates = Column(Boolean, default=True, nullable=False)
    employee_confirmation_reminders = Column(Boolean, default=True, nullable=False)
    flight_risk_changes = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    
    # Relationships
    user = relationship("User", backref="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, email={self.send_email_alerts}, sms={self.send_sms_alerts})>"
