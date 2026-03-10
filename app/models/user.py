from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Index, text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base
from ..schemas.enums import UserRole, UserStatus

class User(Base):
    """
    User model - Only 2 types: SUPERADMIN and ADMIN.
    
    SUPERADMIN: Created via database initialization only
    ADMIN: Can self-register or be created by superadmin
    """
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    mobile = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # OTP Verification Fields
    email_otp = Column(String(6), nullable=True)
    otp_created_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    
    # Role and Status - Only 2 roles: SUPERADMIN and ADMIN
    role = Column(
        SQLEnum(UserRole, native_enum=False, create_constraint=False),
        nullable=False,
        default=UserRole.ADMIN  # Default to ADMIN for registrations
    )
    status = Column(
        SQLEnum(UserStatus, native_enum=False, create_constraint=False),
        nullable=False,
        default=UserStatus.ACTIVE
    )
    
    # Company/Admin specific fields
    account_url = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    plan_name = Column(String(100), nullable=True)
    plan_type = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=True, default="USD")
    language = Column(String(50), nullable=True, default="English")
    profile_image = Column(String(500), nullable=True)
    
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
    created_by = Column(Integer, nullable=True)
    
    # Relationships
    ai_queries = relationship("AIReportQuery", back_populates="user")
    generated_reports = relationship("GeneratedReport", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    feedback = relationship("UserFeedback", back_populates="user")
    tasks = relationship("TodoTask", foreign_keys="TodoTask.user_id", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('ix_users_email_status', 'email', 'status'),
        Index('ix_users_role_status', 'role', 'status'),
        Index('ix_users_mobile', 'mobile'),
        Index('ix_users_email_otp', 'email_otp'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"