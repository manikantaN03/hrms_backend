"""
Application Enums
"""

import enum


class UserRole(str, enum.Enum):
    """
    User role levels - Only 2 types.
    
    SUPERADMIN: System owner, can create admins
    ADMIN: Can self-register or be created by superadmin
    """
    SUPERADMIN = "superadmin"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    """User account status."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"