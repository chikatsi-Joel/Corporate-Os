from enum import Enum

class AuditEnum(Enum):
    """Types d'événements auditables"""
    EMISSION = "Emission réussie"
    CONNEXION = "Connexion réussie"
