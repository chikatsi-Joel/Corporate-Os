from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from core.events.audit_publisher import AuditPublisher
import requests
from app.database.models import User
from app.services.user_service import UserService
from app.core.check_role import require_role, require_any_role
from fastapi_keycloak_middleware import get_user, FastApiUser

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenRequest(BaseModel):
    """Schéma pour la demande de token"""
    username: str
    password: str
    grant_type: str = "password"


class TokenResponse(BaseModel):
    """Schéma pour la réponse de token"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schéma pour la demande de refresh token"""
    refresh_token: str


class LoginRequest(BaseModel):
    """Modèle pour les données de connexion"""
    username: str
    password: str


class UserInfo(BaseModel):
    """Informations de l'utilisateur"""
    sub: str
    name: Optional[str] = None
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    roles: list[str] = []


@router.post("/login", response_model=TokenResponse, summary="Authentification utilisateur")
async def login(form_data: LoginRequest):

    try:
        token_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
        
        # Créer l'instance AuditPublisher avec gestion d'erreur
        try:
            audit = AuditPublisher()
        except Exception as e:
            print(f"Impossible de créer AuditPublisher: {e}")
            audit = None
        
        token_data = {
            'client_id': settings.keycloak_client_id,
            'client_secret': settings.keycloak_client_secret,
            'grant_type': 'password',
            'username': form_data.username,
            'password': form_data.password,
            'scope': 'openid profile email'  # Scopes pour obtenir plus d'infos
        }
        
        print(f"Tentative d'authentification pour l'utilisateur: {form_data.username}")
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            print(f"Échec authentification Keycloak: {response.status_code} - {response.text}")
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Nom d'utilisateur ou mot de passe incorrect"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur lors de l'authentification"
                )
        
        token_info = response.json()
        
        print("publication pour audit ")
        
        # Publier l'audit seulement si AuditPublisher est disponible
        if audit:
            try:
                audit.publish_for_audit(
                    message=f"Utilisateur {form_data.username} connecté avec succès",
                    notification_type="connexion",
                    metadata={
                        "username": form_data.username,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                print(f"Erreur lors de la publication d'audit: {e}")
        
        # Retourner la réponse formatée
        return TokenResponse(
            access_token=token_info['access_token'],
            token_type='Bearer',
            expires_in=token_info['expires_in'],
            refresh_token=token_info.get('refresh_token'),
            scope=token_info.get('scope')
        )
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau lors de l'authentification: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification temporairement indisponible"
        )
    except Exception as e:
        print(f"Erreur inattendue lors de l'authentification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )



@router.get("/me")
async def get_current_user_info(current_user = require_any_role(['admin', 'actionnaire'])):
    """
    Récupère les informations de l'utilisateur actuel
    
    Args:
        current_user: Utilisateur actuel (injecté automatiquement)
    
    Returns:
        Informations de l'utilisateur
    """
    return {
        "sub": current_user.get('sub', ''),
        "username": current_user.get('preferred_username', ''),
        "last_name": current_user.get('family_name', ''),
        "first_name": current_user.get('given_name', ''),
        "email": current_user.get('email', ''),
        "name": current_user.get('name', ''),
        "roles": current_user.get('realm_access', {}).get('roles', [])
    }



@router.get("/userinfo")
async def get_userinfo(current_user = Depends(get_user)):
    """
    Endpoint pour récupérer les informations utilisateur depuis Keycloak
    Compatible avec l'endpoint userinfo standard OAuth2/OpenID Connect
    
    Args:
        current_user: Utilisateur actuel (injecté automatiquement)
    
    Returns:
        Informations utilisateur depuis Keycloak
    """
    try:
        # Retourner directement les informations de l'utilisateur Keycloak
        return {
            "sub": current_user.get('sub', ''),
            "username": current_user.get('preferred_username', ''),
            "last_name": current_user.get('family_name', ''),
            "first_name": current_user.get('given_name', ''),
            "email": current_user.get('email', ''),
            "name": current_user.get('name', ''),
            "email_verified": current_user.get('email_verified', False),
            "realm_access": current_user.get('realm_access', {}),
            "resource_access": current_user.get('resource_access', {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des informations utilisateur: {str(e)}"
        )

