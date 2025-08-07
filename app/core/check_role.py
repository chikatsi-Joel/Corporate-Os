from fastapi import Depends, HTTPException, Request, status
from typing import List, Optional, Union, Dict, Any
from fastapi_keycloak_middleware import get_user


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Récupère l'utilisateur courant depuis le middleware Keycloak
    
    Args:
        request: Objet Request FastAPI
        
    Returns:
        Dict[str, Any]: Informations de l'utilisateur
        
    Raises:
        HTTPException: Si l'utilisateur n'est pas authentifié
    """
    try:
        user = await get_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )


def require_role(required_role: str):
    """
    Décorateur de dépendance pour vérifier qu'un utilisateur a un rôle spécifique
    
    Args:
        required_role (str): Le rôle requis
        
    Returns:
        Dependency: Une dépendance FastAPI qui vérifie le rôle
    """
    async def role_dependency(request: Request):
        user = await get_current_user(request)
        
        # Récupération des rôles de l'utilisateur
        realm_access = user.get("realm_access", {})
        roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        
        # Log pour debug (à supprimer en production)
        print(f"User roles: {roles}, Required role: {required_role}")
        
        # Vérification du rôle
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' is required"
            )
        
        return user
    
    return Depends(role_dependency)


def require_any_role(required_roles: List[str]):
    """
    Décorateur de dépendance pour vérifier qu'un utilisateur a au moins un des rôles spécifiés
    
    Args:
        required_roles (List[str]): Liste des rôles acceptés
        
    Returns:
        Dependency: Une dépendance FastAPI qui vérifie les rôles
    """
    async def role_dependency(request: Request):
        user = await get_current_user(request)
        
        # Récupération des rôles de l'utilisateur
        print(user)
        realm_access = user.get("realm_access", {})
        user_roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        
        # Vérification qu'au moins un rôle correspond
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles is required: {', '.join(required_roles)}"
            )
        
        return user
    
    return Depends(role_dependency)



def require_all_roles(required_roles: List[str]):
    """
    Décorateur de dépendance pour vérifier qu'un utilisateur a tous les rôles spécifiés
    
    Args:
        required_roles (List[str]): Liste des rôles requis
        
    Returns:
        Dependency: Une dépendance FastAPI qui vérifie les rôles
    """
    async def role_dependency(request: Request):
        user = await get_current_user(request)
        
        # Récupération des rôles de l'utilisateur
        realm_access = user.get("realm_access", {})
        user_roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        
        # Vérification que tous les rôles sont présents
        missing_roles = [role for role in required_roles if role not in user_roles]
        if missing_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required roles: {', '.join(missing_roles)}"
            )
        
        return user
    
    return Depends(role_dependency)

