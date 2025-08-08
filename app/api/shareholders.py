from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.database import get_db
from app.database.models import User
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema, UserWithShares
from app.services.user_service import UserService
from app.core.check_role import get_current_user, require_role, require_any_role
from app.services.keycloak_service import KeycloakService
from app.core.config import settings

router = APIRouter(prefix="/shareholders", tags=["shareholders"])

keycloak_service = KeycloakService(
    server_url=settings.keycloak_url,
    realm_name=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret=settings.keycloak_client_secret,
    admin_username=settings.keycloak_admin_username,
    admin_password=settings.keycloak_admin_password
)

@router.get("/", response_model=List[UserWithShares], 
            dependencies=[require_role('admin')], summary="Liste des actionnaires")
async def get_shareholders(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner", example=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de tous les actionnaires avec leurs informations d'actions.
    
    Cette endpoint retourne une liste paginée de tous les actionnaires
    avec le nombre total d'actions qu'ils détiennent et leur valeur.
    
    **Permissions requises** : Rôle admin uniquement
    
    **Paramètres de requête** :
    - `skip` : Nombre d'éléments à ignorer (pagination)
    - `limit` : Nombre maximum d'éléments à retourner
    
    **Retourne** :
    - `200 OK` : Liste des actionnaires
    - `403 Forbidden` : Accès refusé (pas de rôle admin)
    - `401 Unauthorized` : Token invalide ou expiré
    
    **Exemple de réponse** :
    ```json
    [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "gweunshy",
            "email": "gweunshy@example.com",
            "first_name": "Gradi",
            "last_name": "Joel",
            "role": "actionnaire",
            "total_shares": 1000,
            "total_value": 50000.0
        }
    ]
    ```
    """
    
    shareholders = UserService.get_shareholders_with_shares(db, skip=skip, limit=limit)
    return shareholders


@router.post("/", response_model=UserSchema, summary="Créer un actionnaire", status_code=status.HTTP_201_CREATED,
             dependencies=[require_role('admin')])
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
        "username": "chikatsi",
        "email": "chikatsi@gmail.com",
        "first_name": "Chikatsi",
        "last_name": "Joel",
        "role": "actionnaire",
        "password": "securepassword123"
    }
    ```
    """
    
    # Vérifier si l'email existe déjà
    existing_email = UserService.get_user_by_email(db, shareholder.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Vérifier si le nom d'utilisateur existe déjà
    existing_username = UserService.get_user_by_username(db, shareholder.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec ce nom d'utilisateur existe déjà"
        )
    
    try:
        keycloak_response = keycloak_service.create_user(
            username=shareholder.username,
            email=shareholder.email,
            password=shareholder.password,
            first_name=shareholder.first_name,
            last_name=shareholder.last_name,
            role=shareholder.role
        )
        
        shareholder.keycloak_id = keycloak_response.get('id')
        new_user = UserService.create_user(db, shareholder)


        
        return new_user
        
    except HTTPException as e:
        # Relever l'exception HTTP existante
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'actionnaire: {str(e)}"
        )


@router.get("/{shareholder_id}", response_model=UserWithShares, 
            dependencies=[require_any_role(['admin', 'actionnaire'])], summary="Détails d'un actionnaire")
async def get_shareholder(
    shareholder_id: UUID,
    user = Depends(get_current_user),
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
        "username": "gweunshy",
        "email": "gweunshy@gmail.com",
        "first_name": "Gradi",
        "last_name": "Joel",
        "role": "actionnaire",
        "total_shares": 1000,
        "total_value": 50000.0
    }
    ```
    """
    
    
    shareholder = UserService.get_user_by_id(db, shareholder_id)
    print(f"{user['realm_access']['roles']} and {('admin' not in user['realm_access']['roles'])}")
    
    
    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actionnaire non trouvé"
        )
    
    if (shareholder.email != user['email'] or ('admin' not in user['realm_access']['roles'])):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vous n'avez pas le droit."
        )
    
    print("sharefolder : ", shareholder)
    
    shareholder_with_shares = UserService.get_user_with_shares(db, shareholder_id)
    if not shareholder_with_shares:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actionnaire non trouvé"
        )
    
    return shareholder_with_shares


@router.get("/{shareholder_id}/summary", 
            dependencies=[require_any_role(['admin', 'actionnaire'])],
            summary="Résumé des actions d'un actionnaire")
async def get_shareholder_summary(
    shareholder_id: UUID,
    user = Depends(get_current_user),
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
    - `200 OK` : Résumé des actions
    - `403 Forbidden` : Accès refusé
    - `404 Not Found` : Actionnaire non trouvé
    - `401 Unauthorized` : Token invalide ou expiré
    
    **Exemple de réponse** :
    ```json
    {
        "shareholder_id": "123e4567-e89b-12d3-a456-426614174000",
        "total_shares": 1000,
        "total_value": 50000.0,
        "total_issuances": 5,
        "average_price": 50.0,
        "last_issuance_date": "2024-01-15"
    }
    ```
    """
    
    from app.services.issuance_service import IssuanceService
    
    shareholder = UserService.get_user_by_id(db, shareholder_id)
    if shareholder.email != user['email'] and 'admin' not in user['realm_access']['roles']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas le droit de voir ce résumé"
        )
    
    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actionnaire non trouvé"
        )
    
    summary = IssuanceService.get_shareholder_summary(db, shareholder_id)
    if not summary:
        # Si aucun résumé n'est trouvé, retourner un résumé vide
        summary = {
            "shareholder_id": str(shareholder_id),
            "total_shares": 0,
            "total_value": 0.0,
            "total_issuances": 0,
            "average_price": 0.0,
            "last_issuance_date": None
        }
    
    return summary 