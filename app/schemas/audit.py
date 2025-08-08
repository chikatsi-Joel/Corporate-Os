from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AuditEventBase(BaseModel):
    """Schéma de base pour les événements d'audit"""
    user_id: str = Field(..., description="ID de l'utilisateur")
    action: str = Field(..., description="Action effectuée", example="create")
    resource_type: str = Field(..., description="Type de ressource", example="shareholder")
    resource_id: str = Field(..., description="ID de la ressource")
    description: Optional[str] = Field(None, description="Description de l'action")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Données de l'événement")
    previous_data: Optional[Dict[str, Any]] = Field(None, description="Données précédentes")

class AuditEventCreate(AuditEventBase):
    """Schéma pour la création d'un événement d'audit"""
    pass

class AuditEventUpdate(BaseModel):
    """Schéma pour la mise à jour d'un événement d'audit"""
    description: Optional[str] = Field(None, description="Description de l'action")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Données de l'événement")
    status: Optional[str] = Field(None, description="Statut de l'événement")

class AuditEvent(AuditEventBase):
    """Schéma complet d'un événement d'audit"""
    id: int = Field(..., description="ID unique de l'événement d'audit")
    event_id: str = Field(..., description="UUID de l'événement")
    user_email: Optional[str] = Field(None, description="Email de l'utilisateur")
    user_role: Optional[str] = Field(None, description="Rôle de l'utilisateur")
    status: str = Field(..., description="Statut de l'événement")
    created_at: datetime = Field(..., description="Date de création")
    processed_at: Optional[datetime] = Field(None, description="Date de traitement")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "admin",
                "user_email": "admin@corporate-os.local",
                "user_role": "admin",
                "action": "create",
                "resource_type": "shareholder",
                "resource_id": "456e7890-e89b-12d3-a456-426614174001",
                "description": "Création d'un nouvel actionnaire",
                "event_data": {"username": "john.doe", "email": "john@example.com"},
                "previous_data": None,
                "status": "processed",
                "created_at": "2024-01-01T00:00:00Z",
                "processed_at": "2024-01-01T00:00:01Z"
            }
        }

class AuditEventSummary(BaseModel):
    """Résumé des événements d'audit"""
    total_events: int = Field(..., description="Nombre total d'événements")
    unique_users: int = Field(..., description="Nombre d'utilisateurs uniques")
    resource_types: int = Field(..., description="Nombre de types de ressources")
    last_event_date: Optional[datetime] = Field(None, description="Date du dernier événement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_events": 150,
                "unique_users": 5,
                "resource_types": 3,
                "last_event_date": "2024-01-01T00:00:00Z"
            }
        }

class AuditEventFilter(BaseModel):
    """Filtres pour la recherche d'événements d'audit"""
    user_id: Optional[str] = Field(None, description="ID de l'utilisateur")
    action: Optional[str] = Field(None, description="Action")
    resource_type: Optional[str] = Field(None, description="Type de ressource")
    resource_id: Optional[str] = Field(None, description="ID de la ressource")
    start_date: Optional[datetime] = Field(None, description="Date de début")
    end_date: Optional[datetime] = Field(None, description="Date de fin")
    skip: int = Field(0, ge=0, description="Nombre d'éléments à ignorer")
    limit: int = Field(100, ge=1, le=1000, description="Nombre maximum d'éléments")

class AuditEventStatistics(BaseModel):
    """Statistiques des événements d'audit"""
    action_statistics: list = Field(..., description="Statistiques par action")
    resource_statistics: list = Field(..., description="Statistiques par type de ressource")
    top_users: list = Field(..., description="Top utilisateurs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_statistics": [
                    {"action": "create", "count": 50},
                    {"action": "update", "count": 30},
                    {"action": "delete", "count": 10}
                ],
                "resource_statistics": [
                    {"resource_type": "shareholder", "count": 60},
                    {"resource_type": "share_issuance", "count": 30}
                ],
                "top_users": [
                    {"user_id": "admin", "count": 80},
                    {"user_id": "user1", "count": 20}
                ]
            }
        }
