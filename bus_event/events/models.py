"""
Modèles pour le système d'événements
"""

from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Types d'événements supportés"""
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    SHAREHOLDER_CREATED = "shareholder.created"
    SHAREHOLDER_UPDATED = "shareholder.updated"
    SHARE_ISSUED = "share.issued"
    CERTIFICATE_GENERATED = "certificate.generated"
    SYSTEM_ERROR = "system.error"
    AUDIT_LOG = "audit.log"
    NOTIFICATION = "notification"


class Event(BaseModel):
    """Modèle d'événement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventHandler:
    """Interface pour les gestionnaires d'événements"""
    
    def handle(self, event: Event) -> bool:
        """
        Traite un événement
        
        Args:
            event: L'événement à traiter
            
        Returns:
            True si l'événement a été traité avec succès, False sinon
        """
        raise NotImplementedError("La méthode handle doit être implémentée")
