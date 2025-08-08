"""
API pour la gestion des événements d'audit
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.schemas.audit import (
    AuditEvent, AuditEventCreate, AuditEventUpdate, AuditEventSummary,
    AuditEventFilter, AuditEventStatistics
)
from ...audit.service.audit_service import AuditEventService
from app.core.check_role import require_role

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=List[AuditEvent], 
            dependencies=[require_role('admin')], summary="Liste des événements d'audit")
async def get_audit_events(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    user_id: Optional[str] = Query(None, description="Filtrer par ID utilisateur"),
    action: Optional[str] = Query(None, description="Filtrer par action"),
    resource_type: Optional[str] = Query(None, description="Filtrer par type de ressource"),
    resource_id: Optional[str] = Query(None, description="Filtrer par ID de ressource"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des événements d'audit avec filtres optionnels.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner
    - `user_id` : Filtrer par ID utilisateur
    - `action` : Filtrer par action
    - `resource_type` : Filtrer par type de ressource
    - `resource_id` : Filtrer par ID de ressource
    - `start_date` : Date de début
    - `end_date` : Date de fin
    
    **Retourne** :
    - `200 OK` : Liste des événements d'audit
    - `403 Forbidden` : Accès refusé (pas de rôle admin)
    """
    events = AuditEventService.get_events(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date
    )
    return events


@router.get("/events/{audit_id}", response_model=AuditEvent,
            dependencies=[require_role('admin')], summary="Détails d'un événement d'audit")
async def get_audit_event(
    audit_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'un événement d'audit spécifique.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres** :
    - `audit_id` : ID de l'événement d'audit
    
    **Retourne** :
    - `200 OK` : Détails de l'événement d'audit
    - `404 Not Found` : Événement non trouvé
    - `403 Forbidden` : Accès refusé
    """
    event = AuditEventService.get_by_id(db, audit_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Événement d'audit non trouvé"
        )
    return event


@router.get("/events/user/{user_id}", response_model=List[AuditEvent],
            dependencies=[require_role('admin')], summary="Événements d'audit d'un utilisateur")
async def get_user_audit_events(
    user_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    db: Session = Depends(get_db)
):
    """
    Récupère les événements d'audit d'un utilisateur spécifique.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres** :
    - `user_id` : ID de l'utilisateur
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner
    
    **Retourne** :
    - `200 OK` : Liste des événements d'audit de l'utilisateur
    - `403 Forbidden` : Accès refusé
    """
    events = AuditEventService.get_user_activity(db, user_id, skip, limit)
    return events


@router.get("/events/resource/{resource_type}/{resource_id}", response_model=List[AuditEvent],
            dependencies=[require_role('admin')], summary="Événements d'audit d'une ressource")
async def get_resource_audit_events(
    resource_type: str,
    resource_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    db: Session = Depends(get_db)
):
    """
    Récupère les événements d'audit pour une ressource spécifique.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres** :
    - `resource_type` : Type de ressource
    - `resource_id` : ID de la ressource
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner
    
    **Retourne** :
    - `200 OK` : Liste des événements d'audit de la ressource
    - `403 Forbidden` : Accès refusé
    """
    events = AuditEventService.get_resource_history(db, resource_type, resource_id, skip, limit)
    return events


@router.get("/summary", response_model=AuditEventSummary,
            dependencies=[require_role('admin')], summary="Résumé des événements d'audit")
async def get_audit_summary(
    user_id: Optional[str] = Query(None, description="ID de l'utilisateur (optionnel)"),
    db: Session = Depends(get_db)
):
    """
    Récupère un résumé des événements d'audit.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `user_id` : ID de l'utilisateur (optionnel, pour filtrer par utilisateur)
    
    **Retourne** :
    - `200 OK` : Résumé des événements d'audit
    - `403 Forbidden` : Accès refusé
    """
    


@router.get("/statistics", response_model=AuditEventStatistics,
            dependencies=[require_role('admin')], summary="Statistiques des événements d'audit")
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db)
):
    """
    Récupère des statistiques détaillées des événements d'audit.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `start_date` : Date de début (optionnel)
    - `end_date` : Date de fin (optionnel)
    
    **Retourne** :
    - `200 OK` : Statistiques des événements d'audit
    - `403 Forbidden` : Accès refusé
    """


@router.get("/search", response_model=List[AuditEvent],
            dependencies=[require_role('admin')], summary="Recherche dans les événements d'audit")
async def search_audit_events(
    q: str = Query(..., description="Terme de recherche"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    db: Session = Depends(get_db)
):
    """
    Recherche dans les événements d'audit.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `q` : Terme de recherche
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner
    
    **Retourne** :
    - `200 OK` : Liste des événements d'audit correspondants
    - `403 Forbidden` : Accès refusé
    """


@router.get("/export", dependencies=[require_role('admin')], summary="Export des événements d'audit")
async def export_audit_events(
    format: str = Query("json", description="Format d'export (json, csv)"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db)
):
    """
    Exporte les événements d'audit.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `format` : Format d'export (json, csv)
    - `start_date` : Date de début (optionnel)
    - `end_date` : Date de fin (optionnel)
    
    **Retourne** :
    - `200 OK` : Données exportées
    - `400 Bad Request` : Format non supporté
    - `403 Forbidden` : Accès refusé
    """
    if format.lower() not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'export non supporté. Utilisez 'json' ou 'csv'"
        )
    
    exported_data = AuditEventService.export_audit_events(db, format, start_date, end_date)
    
    if format.lower() == "json":
        return {"data": exported_data}
    else:
        from fastapi.responses import Response
        return Response(
            content=exported_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_events_{datetime.now().strftime('%Y%m%d')}.csv"}
        )


@router.post("/cleanup", dependencies=[require_role('admin')], summary="Nettoyage des anciens événements d'audit")
async def cleanup_old_audit_events(
    days_to_keep: int = Query(365, ge=1, description="Nombre de jours à conserver"),
    db: Session = Depends(get_db)
):
    """
    Nettoie les anciens événements d'audit.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `days_to_keep` : Nombre de jours à conserver
    
    **Retourne** :
    - `200 OK` : Nombre d'événements supprimés
    - `403 Forbidden` : Accès refusé
    """
    deleted_count = AuditEventService.cleanup_old_audit_events(db, days_to_keep)
    return {
        "message": f"{deleted_count} anciens événements d'audit supprimés",
        "deleted_count": deleted_count
    }
