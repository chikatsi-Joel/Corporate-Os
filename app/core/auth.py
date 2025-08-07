from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from app.core.config import settings
from app.database.database import get_db
from app.database.models import User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Configuration Keycloak pour client public
keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm,
    verify=True
)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Vérifie le token JWT et retourne l'utilisateur actuel"""
    try:
        # Vérifier le token avec Keycloak
        token_info = keycloak_openid.decode_token(
            credentials.credentials,
            key=keycloak_openid.public_key(),
            options={
                "verify_signature": True,
                "verify_aud": False,
                "exp": True
            }
        )
        
        # Extraire l'ID utilisateur de Keycloak
        keycloak_id = token_info.get('sub')
        if not keycloak_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        # Rechercher l'utilisateur dans la base de données
        user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
        if not user:
            # Créer l'utilisateur s'il n'existe pas
            user = create_user_from_keycloak(token_info, db)
        
        return user
        
    except Exception as e:
        logger.error(f"Erreur d'authentification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )


def create_user_from_keycloak(token_info: dict, db: Session) -> User:
    """Crée un nouvel utilisateur à partir des informations Keycloak"""
    try:
        # Extraire les informations de l'utilisateur
        keycloak_id = token_info.get('sub')
        username = token_info.get('preferred_username')
        email = token_info.get('email')
        first_name = token_info.get('given_name', '')
        last_name = token_info.get('family_name', '')
        
        # Déterminer le rôle (par défaut actionnaire)
        role = 'actionnaire'
        if 'admin' in token_info.get('realm_access', {}).get('roles', []):
            role = 'admin'
        
        # Créer l'utilisateur
        user = User(
            keycloak_id=keycloak_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de l'utilisateur"
        )


def require_admin(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur a le rôle admin"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Rôle admin requis."
        )
    return current_user


def require_actionnaire(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur a le rôle actionnaire"""
    if current_user.role != 'actionnaire':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Rôle actionnaire requis."
        )
    return current_user 