from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from app.core.auth import request_token, get_current_user, oauth2_scheme
from app.database.models import User
import httpx
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


@router.post("/token", response_model=TokenResponse)
async def get_token(token_request: TokenRequest):
    """
    Demande un token d'accès à Keycloak
    
    Args:
        token_request: Informations de connexion et type de grant
    
    Returns:
        TokenResponse avec les informations du token
    """
    try:
        token_data = request_token(
            username=token_request.username,
            password=token_request.password,
            grant_type=token_request.grant_type
        )
        
        return TokenResponse(
            access_token=token_data.get("access_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 300),
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la demande de token: {str(e)}"
        )


@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """
    Rafraîchit un token d'accès à partir d'un refresh token
    
    Args:
        refresh_request: Refresh token
    
    Returns:
        TokenResponse avec les nouvelles informations du token
    """
    try:
        token_data = request_token(
            username="",  # Pas besoin pour refresh_token
            password=refresh_request.refresh_token,
            grant_type="refresh_token"
        )
        
        return TokenResponse(
            access_token=token_data.get("access_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 300),
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du rafraîchissement du token: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur actuel
    
    Args:
        current_user: Utilisateur actuel (injecté automatiquement)
    
    Returns:
        Informations de l'utilisateur
    """
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "keycloak_id": current_user.keycloak_id
    }



# Endpoint pour tester l'authentification selon votre exemple
@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    """
    Endpoint de test pour vérifier l'authentification
    
    Args:
        token: Token JWT (injecté automatiquement)
    
    Returns:
        Token reçu
    """
    return {"token": token}


@router.get("/userinfo")
async def get_userinfo(token: str = Depends(oauth2_scheme)):
    """
    Endpoint pour récupérer les informations utilisateur depuis Keycloak
    Compatible avec l'endpoint userinfo standard OAuth2/OpenID Connect
    
    Args:
        token: Token JWT (injecté automatiquement)
    
    Returns:
        Informations utilisateur depuis Keycloak
    """
    try:
        # URL de l'endpoint userinfo de Keycloak
        userinfo_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/userinfo"
        
        with httpx.Client() as client:
            response = client.get(userinfo_url, headers={
                "Authorization": f"Bearer {token}"
            })
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré"
            )
        
        userinfo_data = response.json()
        return userinfo_data
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification indisponible"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des informations utilisateur: {str(e)}"
        )


@router.post("/introspect")
async def introspect_token(token: str = Depends(oauth2_scheme)):
    """
    Endpoint pour introspecter un token
    Compatible avec l'endpoint d'introspection standard OAuth2
    
    Args:
        token: Token JWT (injecté automatiquement)
    
    Returns:
        Informations d'introspection du token
    """
    try:
        # URL de l'endpoint d'introspection de Keycloak
        introspect_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token/introspect"
        
        with httpx.Client() as client:
            response = client.post(introspect_url, data={
                "token": token,
                "client_id": settings.keycloak_client_id
            })
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        introspect_data = response.json()
        return introspect_data
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification indisponible"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'introspection du token: {str(e)}"
        ) 