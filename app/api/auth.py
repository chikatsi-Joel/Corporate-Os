from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import get_current_user
from app.database.models import User
from app.schemas.user import User as UserSchema
from typing import Dict

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/me", response_model=UserSchema, summary="Informations utilisateur connecté")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur connecté.
    
    Cette endpoint retourne les informations de base de l'utilisateur authentifié,
    incluant son identifiant, nom d'utilisateur, email, nom, prénom et rôle.
    
    **Authentification requise** : Token JWT valide
    
    **Retourne** :
    - `200 OK` : Informations de l'utilisateur
    - `401 Unauthorized` : Token invalide ou expiré
    """
    return current_user


@router.get("/profile", summary="Profil complet utilisateur")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Récupère le profil complet de l'utilisateur connecté.
    
    Cette endpoint retourne toutes les informations détaillées de l'utilisateur,
    incluant les métadonnées comme les dates de création et de modification.
    
    **Authentification requise** : Token JWT valide
    
    **Retourne** :
    - `200 OK` : Profil complet de l'utilisateur
    - `401 Unauthorized` : Token invalide ou expiré
    
    **Exemple de réponse** :
    ```json
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "john.doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "admin",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    ```
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    } 