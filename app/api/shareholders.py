from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.core.auth import get_current_user, require_admin
from app.database.models import User
from app.schemas.user import UserCreate, User as UserSchema, UserWithShares
from app.services.user_service import UserService
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/shareholders", tags=["shareholders"])


@router.get("/", response_model=List[UserWithShares], summary="Liste des actionnaires")
async def get_shareholders(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner", example=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des actionnaires avec le total de leurs actions.
    
    Cette endpoint retourne tous les actionnaires de l'entreprise avec le nombre total
    d'actions qu'ils détiennent et la valeur totale de leurs actions.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres** :
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner (max 1000)
    
    **Retourne** :
    - `200 OK` : Liste des actionnaires avec leurs actions
    - `403 Forbidden` : Accès refusé (pas de rôle admin)
    - `401 Unauthorized` : Token invalide ou expiré
    
    **Exemple de réponse** :
    ```json
    [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "john.doe",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "actionnaire",
            "total_shares": 1000,
            "total_value": 50000.0
        }
    ]
    ```
    """
    shareholders = UserService.get_shareholders_with_shares(db, skip=skip, limit=limit)
    return shareholders


@router.post("/", response_model=UserSchema, summary="Créer un actionnaire", status_code=status.HTTP_201_CREATED)
async def create_shareholder(
    shareholder: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel actionnaire.
    
    Cette endpoint permet de créer un nouvel actionnaire dans le système.
    L'actionnaire sera automatiquement associé au rôle "actionnaire".
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres** :
    - `shareholder` : Données du nouvel actionnaire
    
    **Retourne** :
    - `201 Created` : Actionnaire créé avec succès
    - `400 Bad Request` : Données invalides
    - `403 Forbidden` : Accès refusé (pas de rôle admin)
    - `409 Conflict` : Nom d'utilisateur ou email déjà existant
    
    **Exemple de requête** :
    ```json
    {
        "username": "jane.doe",
        "email": "jane.doe@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "role": "actionnaire"
    }
    ```
    """
    # Vérifier si l'utilisateur existe déjà
    existing_user = UserService.get_user_by_username(db, shareholder.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec ce nom d'utilisateur existe déjà"
        )
    
    existing_email = UserService.get_user_by_email(db, shareholder.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Créer l'utilisateur
    new_user = UserService.create_user(db, shareholder)
    return new_user


@router.get("/{shareholder_id}", response_model=UserWithShares, summary="Détails d'un actionnaire")
async def get_shareholder(
    shareholder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les informations détaillées d'un actionnaire spécifique.
    
    Cette endpoint retourne les informations complètes d'un actionnaire,
    incluant le nombre total d'actions qu'il détient et leur valeur.
    
    **Permissions** :
    - Admin : Peut voir tous les actionnaires
    - Actionnaire : Peut voir uniquement ses propres informations
    
    **Paramètres** :
    - `shareholder_id` : Identifiant unique de l'actionnaire
    
    **Retourne** :
    - `200 OK` : Informations de l'actionnaire
    - `403 Forbidden` : Accès refusé
    - `404 Not Found` : Actionnaire non trouvé
    - `401 Unauthorized` : Token invalide ou expiré
    
    **Exemple de réponse** :
    ```json
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "john.doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "actionnaire",
        "total_shares": 1000,
        "total_value": 50000.0
    }
    ```
    """
    # Vérifier les permissions
    if current_user.role != 'admin' and current_user.id != shareholder_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )
    
    shareholder = UserService.get_user_by_id(db, shareholder_id)
    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actionnaire non trouvé"
        )
    
    shareholder_with_shares = UserService.get_user_with_shares(db, shareholder_id)
    if not shareholder_with_shares:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actionnaire non trouvé"
        )
    
    return shareholder_with_shares


@router.get("/{shareholder_id}/summary", summary="Résumé des actions d'un actionnaire")
async def get_shareholder_summary(
    shareholder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère un résumé détaillé des actions d'un actionnaire.
    
    Cette endpoint retourne un résumé complet des actions détenues par un actionnaire,
    incluant le nombre total d'actions, leur valeur, et le pourcentage de participation.
    
    **Permissions** :
    - Admin : Peut voir tous les actionnaires
    - Actionnaire : Peut voir uniquement ses propres informations
    
    **Paramètres** :
    - `shareholder_id` : Identifiant unique de l'actionnaire
    
    **Retourne** :
    - `200 OK` : Résumé des actions de l'actionnaire
    - `403 Forbidden` : Accès refusé
    - `404 Not Found` : Actionnaire non trouvé
    - `401 Unauthorized` : Token invalide ou expiré
    
    **Exemple de réponse** :
    ```json
    {
        "shareholder_id": "123e4567-e89b-12d3-a456-426614174000",
        "total_shares": 1000,
        "total_value": 50000.0,
        "percentage": 25.5,
        "issuances_count": 3,
        "last_issuance_date": "2024-01-01"
    }
    ```
    """
    # Vérifier les permissions
    if current_user.role != 'admin' and current_user.id != shareholder_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )
    
    shareholder = UserService.get_user_by_id(db, shareholder_id)
    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actionnaire non trouvé"
        )
    
    summary = UserService.get_shareholder_summary(db, shareholder_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune information trouvée pour cet actionnaire"
        )
    
    return summary 