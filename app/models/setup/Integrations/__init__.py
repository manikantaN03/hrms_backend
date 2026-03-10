# This module contains integration-related models
# Models are imported here to ensure they're registered with SQLAlchemy's registry
# before relationships are resolved

from .emailsettings import EmailMailbox, EmailSmtpConfig, EmailOAuthConfig, EmailTestLog
from .biometricsync import BiometricDevice, BiometricSyncLog
from .gatekeeper import GatekeeperDevice
from .sqlserver import SqlServerSource, SqlServerSyncLog
from .sap_mapping import SAPMapping
from .api_access import APIAccess

__all__ = [
    "EmailMailbox",
    "EmailSmtpConfig",
    "EmailOAuthConfig",
    "EmailTestLog",
    "BiometricDevice",
    "BiometricSyncLog",
    "GatekeeperDevice",
    "SqlServerSource",
    "SqlServerSyncLog",
    "SAPMapping",
    "APIAccess",
]
