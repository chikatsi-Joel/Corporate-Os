from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.keycloak_service import keycloak_service
from app.core.keycloak_config import keycloak_config
from typing import Optional, Dict, Any

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Obtenir l'utilisateur actuel depuis Keycloak"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_info = keycloak_service.verify_token(credentials.credentials)
    if token_info is None:
        raise credentials_exception
    
    user_info = keycloak_service.get_user_info(credentials.credentials)
    if user_info is None:
        raise credentials_exception
    
    user_info['roles'] = keycloak_service.get_user_roles(credentials.credentials)
    
    return user_info

def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Vérifier que l'utilisateur actuel est admin"""
    if not keycloak_service.is_admin(current_user.get('sub', '')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - Admin role required"
        )
    return current_user

def get_current_shareholder(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Vérifier que l'utilisateur actuel est actionnaire"""
    if not keycloak_service.is_shareholder(current_user.get('sub', '')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - Shareholder role required"
        )
    return current_user

def get_user_id_from_token(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """Extraire l'ID utilisateur du token"""
    return current_user.get('sub', '')

def get_user_roles_from_token(current_user: Dict[str, Any] = Depends(get_current_user)) -> list:
    """Extraire les rôles utilisateur du token"""
    return current_user.get('roles', []) 