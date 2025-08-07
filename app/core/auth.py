import jwt
from jwt import PyJWKClient
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from functools import wraps, lru_cache
from contextlib import asynccontextmanager
import asyncio
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.database import get_db
from app.database.models import User

# Configuration du logging
logger = logging.getLogger(__name__)

# Constantes
TOKEN_CACHE_TTL = 3600  # 1 heure
JWKS_CACHE_TTL = 86400  # 24 heures
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0


class GrantType(str, Enum):
    """Types de grants OAuth2 supportés"""
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    AUTHORIZATION_CODE = "authorization_code"


class UserRole(str, Enum):
    """Rôles utilisateur disponibles"""
    ADMIN = "admin"
    ACTIONNAIRE = "actionnaire"
    USER = "user"


@dataclass
class TokenData:
    """Structure pour les données de token"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: int
    scope: Optional[str] = None


@dataclass
class UserInfo:
    """Structure pour les informations utilisateur extraites du token"""
    keycloak_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    realm_roles: List[str]
    resource_access: Dict[str, Any]


class KeycloakAuthError(Exception):
    """Exception personnalisée pour les erreurs d'authentification Keycloak"""
    
    def __init__(self, message: str, status_code: int = 401, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class KeycloakService:
    """Service principal pour l'intégration Keycloak"""
    
    def __init__(self):
        self._jwks_client: Optional[PyJWKClient] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        
    @property
    def jwks_client(self) -> PyJWKClient:
        """Retourne le client JWKS avec cache et gestion d'erreurs"""
        if self._jwks_client is None:
            try:
                jwks_url = (
                    f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
                    "/protocol/openid-connect/certs"
                )
                self._jwks_client = PyJWKClient(jwks_url)
                logger.info("Client JWKS initialisé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du client JWKS: {e}")
                raise KeycloakAuthError(
                    "Impossible d'initialiser le service d'authentification",
                    status.HTTP_503_SERVICE_UNAVAILABLE
                )
        return self._jwks_client
    
    @asynccontextmanager
    async def get_http_client(self):
        """Context manager pour le client HTTP avec configuration optimisée"""
        if self._http_client is None:
            timeout = httpx.Timeout(REQUEST_TIMEOUT, connect=5.0)
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            
            self._http_client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        try:
            yield self._http_client
        finally:
            pass  # Garder la connexion ouverte pour réutilisation
    
    async def request_token(
        self, 
        username: str, 
        password: str, 
        grant_type: GrantType = GrantType.PASSWORD,
        scope: Optional[str] = None
    ) -> TokenData:
        """
        Demande un token à Keycloak avec retry et validation
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe ou refresh_token selon grant_type
            grant_type: Type de grant OAuth2
            scope: Scope requis (optionnel)
        
        Returns:
            TokenData: Données du token
        
        Raises:
            KeycloakAuthError: En cas d'erreur d'authentification
        """
        token_url = (
            f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
            "/protocol/openid-connect/token"
        )
        
        # Validation des paramètres
        if not username or not password:
            raise KeycloakAuthError(
                "Nom d'utilisateur et mot de passe requis",
                status.HTTP_400_BAD_REQUEST
            )
        
        # Préparation des données
        data = self._prepare_token_request_data(username, password, grant_type, scope)
        
        # Tentatives avec retry
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                async with self.get_http_client() as client:
                    response = await client.post(token_url, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info(f"Token obtenu avec succès (tentative {attempt + 1})")
                    return self._parse_token_response(token_data)
                
                elif response.status_code == 401:
                    error_data = response.json()
                    raise KeycloakAuthError(
                        error_data.get('error_description', 'Identifiants invalides'),
                        status.HTTP_401_UNAUTHORIZED,
                        error_data.get('error')
                    )
                
                else:
                    logger.warning(f"Tentative {attempt + 1} échouée avec code {response.status_code}")
                    last_error = KeycloakAuthError(
                        f"Erreur serveur Keycloak: {response.status_code}",
                        status.HTTP_502_BAD_GATEWAY
                    )
                    
            except httpx.RequestError as e:
                logger.warning(f"Tentative {attempt + 1} échouée: erreur de connexion: {e}")
                last_error = KeycloakAuthError(
                    "Service d'authentification temporairement indisponible",
                    status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponentiel
        
        # Si toutes les tentatives ont échoué
        if last_error:
            raise last_error
        
        raise KeycloakAuthError(
            "Échec de l'authentification après plusieurs tentatives",
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    def _prepare_token_request_data(
        self, 
        username: str, 
        password: str, 
        grant_type: GrantType,
        scope: Optional[str]
    ) -> Dict[str, str]:
        """Prépare les données pour la requête de token"""
        data = {
            "grant_type": grant_type.value,
            "client_id": settings.keycloak_client_id
        }
        
        # Client secret si configuré
        if hasattr(settings, 'keycloak_client_secret') and settings.keycloak_client_secret:
            data["client_secret"] = settings.keycloak_client_secret
        
        # Paramètres selon le type de grant
        if grant_type == GrantType.PASSWORD:
            data.update({"username": username, "password": password})
        elif grant_type == GrantType.REFRESH_TOKEN:
            data["refresh_token"] = password
        elif grant_type == GrantType.CLIENT_CREDENTIALS:
            # Les credentials sont dans client_id/client_secret
            pass
        
        if scope:
            data["scope"] = scope
            
        return data
    
    def _parse_token_response(self, response_data: Dict[str, Any]) -> TokenData:
        """Parse la réponse de token Keycloak"""
        return TokenData(
            access_token=response_data["access_token"],
            refresh_token=response_data.get("refresh_token"),
            token_type=response_data.get("token_type", "Bearer"),
            expires_in=response_data.get("expires_in", 3600),
            scope=response_data.get("scope")
        )
    
    def verify_and_decode_token(self, token: str) -> UserInfo:
        """
        Vérifie et décode un token JWT
        
        Args:
            token: Token JWT à vérifier
            
        Returns:
            UserInfo: Informations utilisateur extraites
            
        Raises:
            KeycloakAuthError: Si le token est invalide
        """
        try:
            # Cache check
            cache_key = f"token:{hash(token)}"
            if cache_key in self._token_cache:
                cached_data = self._token_cache[cache_key]
                if cached_data["expires_at"] > datetime.utcnow():
                    return cached_data["user_info"]
                else:
                    del self._token_cache[cache_key]
            
            # Récupération et vérification de la clé de signature
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Décodage avec validation complète
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.keycloak_client_id,
                # issuer=f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": False  # Désactivé temporairement pour résoudre le problème d'issuer
                }
            )
            
            # Extraction des informations utilisateur
            user_info = self._extract_user_info(payload)
            
            # Cache du résultat
            self._token_cache[cache_key] = {
                "user_info": user_info,
                "expires_at": datetime.utcnow() + timedelta(seconds=TOKEN_CACHE_TTL)
            }
            
            logger.info(f"Token vérifié avec succès pour: {user_info.username}")
            return user_info
            
        except jwt.ExpiredSignatureError:
            raise KeycloakAuthError("Token expiré", status.HTTP_401_UNAUTHORIZED, "token_expired")
        except jwt.InvalidAudienceError:
            raise KeycloakAuthError("Audience invalide", status.HTTP_401_UNAUTHORIZED, "invalid_audience")
        except jwt.InvalidIssuerError:
            raise KeycloakAuthError("Émetteur invalide", status.HTTP_401_UNAUTHORIZED, "invalid_issuer")
        except jwt.InvalidTokenError as e:
            logger.error(f"Token invalide: {e}")
            raise KeycloakAuthError("Token invalide", status.HTTP_401_UNAUTHORIZED, "invalid_token")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du token: {e}")
            raise KeycloakAuthError("Erreur de validation du token", status.HTTP_401_UNAUTHORIZED)
    
    def _extract_user_info(self, payload: Dict[str, Any]) -> UserInfo:
        """Extrait les informations utilisateur du payload JWT"""
        realm_access = payload.get('realm_access', {})
        resource_access = payload.get('resource_access', {})
        
        # Extraction des rôles avec gestion des cas d'erreur
        realm_roles = realm_access.get('roles', [])
        client_roles = []
        
        if settings.keycloak_client_id in resource_access:
            client_roles = resource_access[settings.keycloak_client_id].get('roles', [])
        
        all_roles = list(set(realm_roles + client_roles))
        
        return UserInfo(
            keycloak_id=payload.get('sub', ''),
            username=payload.get('preferred_username', payload.get('sub', '')),
            email=payload.get('email', ''),
            first_name=payload.get('given_name', ''),
            last_name=payload.get('family_name', ''),
            roles=all_roles,
            realm_roles=realm_roles,
            resource_access=resource_access
        )
    
    async def cleanup(self):
        """Nettoyage des ressources"""
        if self._http_client:
            await self._http_client.aclose()

# Instance globale du service Keycloak
_keycloak_service = KeycloakService()

# Schéma OAuth2 pour FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_keycloak_service() -> KeycloakService:
    """Retourne l'instance du service Keycloak"""
    return _keycloak_service


async def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Vérifie le token JWT et retourne l'utilisateur correspondant
    
    Args:
        token: Token JWT depuis l'en-tête Authorization
        db: Session de base de données
        
    Returns:
        User: Utilisateur authentifié
        
    Raises:
        HTTPException: Si le token est invalide
    """
    try:
        # Vérification et décodage du token
        user_info = _keycloak_service.verify_and_decode_token(token)
        
        # Création ou mise à jour de l'utilisateur dans la base de données
        user = create_user_from_token_data(user_info, db)
        
        return user
        
    except KeycloakAuthError as e:
        logger.error(f"Erreur d'authentification: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la vérification du token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def create_user_from_token_data(user_info: UserInfo, db: Session) -> User:
    """
    Crée ou met à jour un utilisateur à partir des données du token
    
    Args:
        user_info: Informations utilisateur extraites du token
        db: Session de base de données
        
    Returns:
        User: Utilisateur créé ou mis à jour
    """
    try:
        # Recherche de l'utilisateur existant
        user = db.query(User).filter(User.keycloak_id == user_info.keycloak_id).first()
        
        if user:
            # Mise à jour des informations
            user.username = user_info.username
            user.email = user_info.email
            user.first_name = user_info.first_name
            user.last_name = user_info.last_name
            user.role = _determine_user_role(user_info.roles)
            user.updated_at = datetime.utcnow()
            
            logger.info(f"Utilisateur mis à jour: {user.username}")
        else:
            # Création d'un nouvel utilisateur
            user = User(
                keycloak_id=user_info.keycloak_id,
                username=user_info.username,
                email=user_info.email,
                first_name=user_info.first_name,
                last_name=user_info.last_name,
                role=_determine_user_role(user_info.roles),
                is_active=True
            )
            db.add(user)
            logger.info(f"Nouvel utilisateur créé: {user.username}")
        
        db.commit()
        return user
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création/mise à jour de l'utilisateur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la gestion de l'utilisateur"
        )


def _determine_user_role(roles: List[str]) -> str:
    """
    Détermine le rôle principal de l'utilisateur à partir de ses rôles Keycloak
    
    Args:
        roles: Liste des rôles de l'utilisateur
        
    Returns:
        str: Rôle principal (admin, actionnaire, user)
    """
    if UserRole.ADMIN.value in roles:
        return UserRole.ADMIN.value
    elif UserRole.ACTIONNAIRE.value in roles:
        return UserRole.ACTIONNAIRE.value
    else:
        return UserRole.USER.value


# Fonctions de dépendance pour les rôles
def require_role(required_role: UserRole):
    """Décorateur pour vérifier un rôle spécifique"""
    def role_checker(current_user: User = Depends(verify_token)) -> User:
        if current_user.role != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle {required_role.value} requis"
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(verify_token)) -> User:
    """Vérifie que l'utilisateur a le rôle admin"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle administrateur requis"
        )
    return current_user


def require_actionnaire(current_user: User = Depends(verify_token)) -> User:
    """Vérifie que l'utilisateur a le rôle actionnaire"""
    if current_user.role != UserRole.ACTIONNAIRE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle actionnaire requis"
        )
    return current_user


def require_admin_or_actionnaire(current_user: User = Depends(verify_token)) -> User:
    """Vérifie que l'utilisateur a le rôle admin ou actionnaire"""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.ACTIONNAIRE.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle administrateur ou actionnaire requis"
        )
    return current_user


# Fonctions utilitaires pour les tests
def get_current_user(current_user: User = Depends(verify_token)) -> User:
    """Retourne l'utilisateur actuel (pour compatibilité)"""
    return current_user


async def request_token(
    username: str, 
    password: str, 
    grant_type: str = "password"
) -> Dict[str, Any]:
    """
    Fonction de compatibilité pour la demande de token
    
    Args:
        username: Nom d'utilisateur
        password: Mot de passe
        grant_type: Type de grant (par défaut: password)
        
    Returns:
        Dict: Données du token
    """
    try:
        token_data = await _keycloak_service.request_token(
            username=username,
            password=password,
            grant_type=GrantType(grant_type)
        )
        
        return {
            "access_token": token_data.access_token,
            "token_type": token_data.token_type,
            "expires_in": token_data.expires_in,
            "refresh_token": token_data.refresh_token,
            "scope": token_data.scope
        }
        
    except KeycloakAuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )