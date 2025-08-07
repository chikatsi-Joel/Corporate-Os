import enum


class EventTypeEnum(enum.Enum):
    """Types d'événements auditables"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SHAREHOLDER_CREATED = "shareholder_created"
    SHAREHOLDER_UPDATED = "shareholder_updated"
    SHARE_ISSUED = "share_issued"
    CERTIFICATE_GENERATED = "certificate_generated"
    PERMISSION_CHANGED = "permission_changed"
    DATA_EXPORT = "data_export"
    SYSTEM_ERROR = "system_error"
