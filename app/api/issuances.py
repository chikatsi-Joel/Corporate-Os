from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.check_role import get_current_user, require_any_role, require_role
from app.database.database import get_db
from app.database.models import User, ShareIssuance
from app.schemas.issuance import ShareIssuanceCreate, ShareIssuance as ShareIssuanceSchema, ShareIssuanceWithShareholder, ShareIssuanceWithCertificate
from app.services.issuance_service import IssuanceService
from app.services.user_service import UserService
from app.services.certificate_service import CertificateService
from typing import List
from uuid import UUID
import os
from datetime import datetime

router = APIRouter(prefix="/api/issuances", tags=["issuances"])

@router.get("/", response_model=List[ShareIssuanceWithShareholder],
            dependencies=[require_any_role(['admin', 'actionnaire'])], summary="Liste des émissions d'actions")
async def get_issuances(
    user = Depends(get_current_user), 
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner", example=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des émissions d'actions.
    
    Cette endpoint retourne les émissions d'actions selon le rôle de l'utilisateur :
    - **Admin** : Voir toutes les émissions
    - **Actionnaire** : Voir uniquement ses propres émissions
    
    **Authentification requise** : Token JWT valide
    
    **Paramètres** :
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner (max 1000)
    
    **Retourne** :
    - `200 OK` : Liste des émissions d'actions
    - `401 Unauthorized` : Token invalide ou expiré
 
    """
    if 'admin' in user['realm_access']['roles'] :
        usersId = UserService.get_user_by_email(db, user['email']).id
        issuances = IssuanceService.get_issuances_by_id(db, usersId, skip=skip, limit=limit)
    else:
        issuances = IssuanceService.get_issuances(db, skip=skip, limit=limit)

    res = [
        {
                "id": val.id,
                "shareholder_id": val.shareholder_id,
                "shares_count": val.number_of_shares,
                "share_price": float(val.price_per_share),
                "total_amount": float(val.total_amount),
                "issue_date": val.issue_date,
                "status": val.status,
                "certificate_path": val.certificate_path,
                "created_at": val.created_at,
                "updated_at": val.updated_at,
                "shareholder": {
                    "id": val.shareholder.id,
                    "username": val.shareholder.username,
                    "email": val.shareholder.email,
                    "first_name": val.shareholder.first_name,
                    "last_name": val.shareholder.last_name,
                    "role": val.shareholder.role,
                    "created_at": val.shareholder.created_at,
                    "updated_at": val.shareholder.updated_at
                } if val.shareholder else None
        } for val in issuances
    ]
    print("resultat : ", res)

    return res




@router.post("/", response_model=ShareIssuanceWithCertificate, summary="Créer une émission d'actions",
             dependencies=[require_role('admin')], status_code=status.HTTP_201_CREATED)
async def create_issuance(
    issuance: ShareIssuanceCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle émission d'actions.
    
    Cette endpoint permet de créer une nouvelle émission d'actions pour un actionnaire.
    Le montant total est calculé automatiquement (nombre d'actions x prix par action).
    Un certificat PDF est généré automatiquement.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres** :
    - `issuance` : Données de la nouvelle émission
    
    **Retourne** :
    - `201 Created` : Émission créée avec succès
    - `400 Bad Request` : Données invalides
    - `403 Forbidden` : Accès refusé (pas de rôle admin)
    - `404 Not Found` : Actionnaire non trouvé
    - `409 Conflict` : Émission en conflit
    
    """
    # Vérifier que l'actionnaire existe
    shareholder = UserService.get_user_by_id(db, issuance.shareholder_id)
    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Actionnaire non existant"
        )
    
    # Créer l'émission
    new_issuance = IssuanceService.create_issuance(db, issuance)

    # Publier l'événement d'émission d'actions
    try:
        from core.events import event_bus, Event, EventType
        event = Event(
            type=EventType.AUDIT_LOG,
            payload={
                "action": "create",
                "user_id": "admin",  # À récupérer depuis le contexte utilisateur
                "user_email": "admin@corporate-os.com",  # À récupérer depuis le contexte utilisateur
                "user_role": "admin",  # À récupérer depuis le contexte utilisateur
                "resource_type": "share_issuance",
                "resource_id": str(new_issuance['id']),
                "description": f"Création d'une émission d'actions pour l'actionnaire {new_issuance['shareholder_id']}",
                "issuance_id": str(new_issuance['id']),
                "shareholder_id": str(new_issuance['shareholder_id']),
                "shares_count": new_issuance['shares_count'],
                "share_price": new_issuance['share_price'],
                "total_amount": new_issuance['total_amount'],
                "certificate_path": new_issuance.get('certificate_path'),
                "timestamp": datetime.now().isoformat()
            },
            metadata={
                "source": "issuance_service",
                "operation": "create_issuance"
            }
        )
        event_bus.publish(event)
    except Exception as e:
        print(f"Erreur lors de la publication d'événement: {e}")

    # Ajouter le certificat en base64 si disponible
    certificate_base64 = None
    if new_issuance.get('certificate_path') and os.path.exists(new_issuance['certificate_path']):
        try:
            import base64
            with open(new_issuance['certificate_path'], 'rb') as f:
                certificate_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Erreur lors de la lecture du certificat: {e}")
    
    # Créer la réponse avec le certificat
    response_data = {
        "id": new_issuance['id'],
        "shareholder_id": new_issuance['shareholder_id'],
        "shares_count": new_issuance['shares_count'],
        "share_price": new_issuance['share_price'],
        "total_amount": new_issuance['total_amount'],
        "status": new_issuance['status'],
        "certificate_path": new_issuance.get('certificate_path'),
        "certificate_base64": certificate_base64,
        "created_at": new_issuance['created_at'],
        "updated_at": new_issuance['updated_at']
    }
    
    return response_data


@router.get("/{issuance_id}",
             response_model=ShareIssuanceWithShareholder, summary="Détails d'une émission")
async def get_issuance(
    issuance_id: UUID,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'une émission d'actions spécifique.
    
    Cette endpoint retourne les informations complètes d'une émission d'actions,
    incluant les détails de l'actionnaire associé.
    
    **Permissions** :
    - Admin : Peut voir toutes les émissions
    - Actionnaire : Peut voir uniquement ses propres émissions
    
    **Paramètres** :
    - `issuance_id` : Identifiant unique de l'émission
    
    **Retourne** :
    - `200 OK` : Détails de l'émission
    - `403 Forbidden` : Accès refusé
    - `404 Not Found` : Émission non trouvée
    - `401 Unauthorized` : Token invalide ou expiré

    """
    users = UserService.get_user_by_email(db, user['email'])
    val = IssuanceService.get_issuance_by_id(db, users.id, issuance_id, 'admin' in user['realm_access']['roles'])
    return {
                "id": val.id,
                "shareholder_id": val.shareholder_id,
                "shares_count": val.number_of_shares,
                "share_price": float(val.price_per_share),
                "total_amount": float(val.total_amount),
                "issue_date": val.issue_date,
                "status": val.status,
                "certificate_path": val.certificate_path,
                "created_at": val.created_at,
                "updated_at": val.updated_at,
                "shareholder": {
                    "id": val.shareholder.id,
                    "username": val.shareholder.username,
                    "email": val.shareholder.email,
                    "first_name": val.shareholder.first_name,
                    "last_name": val.shareholder.last_name,
                    "role": val.shareholder.role,
                    "created_at": val.shareholder.created_at,
                    "updated_at": val.shareholder.updated_at
                }
    }

@router.get("/{issuance_id}/certificate", summary="Télécharger le certificat PDF",
            dependencies=[require_any_role(['admin', 'actionnaire'])])
async def download_certificate(
    issuance_id : UUID,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Télécharge le certificat PDF d'une émission d'actions.
    
    Cette endpoint permet de télécharger le certificat PDF généré pour une émission d'actions.
    Le certificat contient les détails de l'émission et est signé numériquement.
    
    **Permissions** :
    - Admin : Peut télécharger tous les certificats
    - Actionnaire : Peut télécharger uniquement ses propres certificats
    
    **Paramètres** :
    - `issuance_id` : Identifiant unique de l'émission
    
    **Retourne** :
    - `200 OK` : Fichier PDF du certificat
    - `403 Forbidden` : Accès refusé
    - `404 Not Found` : Émission ou certificat non trouvé
    - `401 Unauthorized` : Token invalide ou expiré
    """
    from fastapi.responses import FileResponse
    import os
    
    # Récupérer l'émission
    users = UserService.get_user_by_email(db, user['email'])
    issuance = IssuanceService.get_issuance_by_id(
        db, 
        users.id,
        issuance_id, 
        'admin' in user['realm_access']['roles'])
    if not issuance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Émission non trouvée"
        )
        
    # Vérifier que le certificat existe
    if not issuance.certificate_path or not os.path.exists(issuance.certificate_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificat non trouvé"
        )
    
    return FileResponse(
        path=issuance.certificate_path,
        filename=f"certificate_{issuance_id}.pdf",
        media_type="application/pdf"
    )


@router.get("/cap-table/summary", summary="Résumé de la Cap Table",
            dependencies=[require_role('admin')])
async def get_cap_table_summary(
    db: Session = Depends(get_db)
):
    """
    Récupère un résumé complet de la table de capitalisation.
    
    Cette endpoint retourne un résumé détaillé de la Cap Table, incluant :
    - Nombre total d'actions émises
    - Valeur totale de la capitalisation
    - Répartition par actionnaire
    - Pourcentages de participation
    
    **Permissions requises** : Rôle admin uniquement
    
    **Retourne** :
    - `200 OK` : Résumé de la Cap Table
    - `403 Forbidden` : Accès refusé (pas de rôle admin)
    - `401 Unauthorized` : Token invalide ou expiré

    """
    summary = IssuanceService.get_cap_table_summary(db)
    return summary 